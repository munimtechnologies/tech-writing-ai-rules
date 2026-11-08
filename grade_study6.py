"""Grade study 6 (census/2026-11-llms-txt-agents) from the hand coding, exactly as PREREGISTRATION.md says.

Inputs: coding.csv (the tool's coding_template.csv with the code columns filled by the coder: yes/no) and
the tool's probes.csv (for the gate). Writes grades.json and prints a Markdown summary.

    python grade_study6.py --coding census/2026-11-llms-txt-agents/coding.csv \
        --probes census/2026-11-llms-txt-agents/probes.csv --out census/2026-11-llms-txt-agents/grades.json

Standard library only. Made by MV2 of Munim, Inc., with AI agents working in his name. Apache-2.0.
"""
import argparse
import csv
import json
import re
import sys

VERSION = "0.1.0"
CODES = ("directive", "cite", "promote", "source", "usage", "action", "limit", "override", "other")
SUBCODES = CODES[1:]
YES, NO = {"yes", "y", "1", "true"}, {"no", "n", "0", "false", ""}
QUOTE_MAX = 200


class CodingError(ValueError):
    pass


def flag(value, field, rid, allow_blank):
    v = (value or "").strip().lower()
    if v in YES:
        return True
    if v in NO and (v or allow_blank):
        return False
    raise CodingError("%s: %s=%r is not yes/no" % (rid, field, value))


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def parse_coding(rows):
    """Checked rows: every file coded, sub-codes only on directive files, quote length within limit."""
    out, seen = [], set()
    for r in rows:
        rid = (r.get("id") or "").strip()
        if not rid or rid in seen:
            raise CodingError("missing or repeated id %r" % rid)
        seen.add(rid)
        c = {"id": rid, "published": (r.get("published") or "").strip(),
             "recall": (r.get("recall_sample") or "").strip() == "1",
             "directive": flag(r.get("directive"), "directive", rid, allow_blank=False)}
        for k in SUBCODES:
            c[k] = flag(r.get(k), k, rid, allow_blank=True)
            if c[k] and not c["directive"]:
                raise CodingError("%s: %s=yes but directive=no" % (rid, k))
        quote = (r.get("quote") or "").strip()
        if len(quote) > QUOTE_MAX:
            raise CodingError("%s: quote has %d characters (max %d)" % (rid, len(quote), QUOTE_MAX))
        if c["directive"] and not quote:
            raise CodingError("%s: directive=yes needs a quote" % rid)
        c["template"] = (r.get("template") or "").strip().lower() in YES
        out.append(c)
    return out


def year(published):
    m = re.match(r"(\d{4})", published or "")
    return m.group(1) if m else ""


def share(k, n):
    return None if n == 0 else round(k / n, 4)


def gate(probes):
    n = len(probes)
    reached = sum(1 for p in probes if (p.get("reached") or "").strip() == "1")
    valid = sum(1 for p in probes if (p.get("kind") or "").strip() == "valid")
    ok = n > 0 and reached / n >= 0.60 and valid >= 200
    return {"unique_urls": n, "reached": reached, "reached_share": share(reached, n), "valid": valid, "held": ok}


def grade(coding, probes):
    g1 = gate(probes)
    n = len(coding)
    d = [c for c in coding if c["directive"]]
    nd = len(d)
    counts = {k: sum(1 for c in coding if c[k]) for k in CODES}
    by_year = {}
    for y in ("2025", "2026"):
        grp = [c for c in coding if year(c["published"]) == y]
        by_year[y] = {"files": len(grp), "directive": sum(1 for c in grp if c["directive"]),
                      "share": share(sum(1 for c in grp if c["directive"]), len(grp))}
    recall = [c for c in coding if c["recall"]]
    recall_dir = sum(1 for c in recall if c["directive"])

    def verdict(value, test):
        if not g1["held"]:
            return "not graded (G1 failed)"
        if value is None:
            return "not graded (no files)"
        return "held" if test(value) else "failed"

    p1 = share(nd, n)
    p2 = share(counts["promote"], nd)
    p3 = share(counts["action"], nd)
    p4 = share(counts["override"], n)
    preds = {
        "P1": {"text": "10% to 40% of CODE files have DIRECTIVE", "value": p1, "count": "%d of %d" % (nd, n),
               "verdict": verdict(p1, lambda v: 0.10 <= v <= 0.40)},
        "P2": {"text": "PROMOTE in at least 25% of directive files", "value": p2,
               "count": "%d of %d" % (counts["promote"], nd), "verdict": verdict(p2, lambda v: v >= 0.25)},
        "P3": {"text": "ACTION in at least 20% of directive files", "value": p3,
               "count": "%d of %d" % (counts["action"], nd), "verdict": verdict(p3, lambda v: v >= 0.20)},
        "P4": {"text": "OVERRIDE in at most 2% of CODE files", "value": p4,
               "count": "%d of %d" % (counts["override"], n), "verdict": verdict(p4, lambda v: v <= 0.02)},
    }
    a, b = by_year["2026"], by_year["2025"]
    if not g1["held"]:
        v5 = "not graded (G1 failed)"
    elif a["files"] < 30 or b["files"] < 30:
        v5 = "not graded (fewer than 30 files in a year group)"
    else:
        v5 = "held" if a["share"] > b["share"] else "failed"
    preds["P5"] = {"text": "DIRECTIVE share higher among files listed in 2026 than in 2025",
                   "value": [a["share"], b["share"]],
                   "count": "2026: %d of %d; 2025: %d of %d" % (a["directive"], a["files"], b["directive"], b["files"]),
                   "verdict": v5}
    return {"version": VERSION, "gate": g1, "code_files": n, "counts": counts, "by_year": by_year,
            "template_directive_files": sum(1 for c in d if c["template"]),
            "recall": {"files": len(recall), "directive": recall_dir, "lower_bound": recall_dir >= 3},
            "predictions": preds}


def markdown(res):
    g = res["gate"]
    lines = ["G1: %d of %d unique URLs reached (%s), %d valid files: %s" % (
        g["reached"], g["unique_urls"], pct(g["reached_share"]), g["valid"], "held" if g["held"] else "FAILED"), "",
        "| Prediction | Result | Verdict |", "|---|---|---|"]
    for k, p in res["predictions"].items():
        lines.append("| %s: %s | %s | %s |" % (k, p["text"], p["count"], p["verdict"]))
    r = res["recall"]
    lines += ["", "Recall check: %d of %d cue-free files hold a directive%s." % (
        r["directive"], r["files"], " (P1 is a lower bound)" if r["lower_bound"] else "")]
    return "\n".join(lines)


def pct(v):
    return "n/a" if v is None else "%.1f%%" % (100 * v)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--coding", required=True)
    ap.add_argument("--probes", required=True)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    try:
        res = grade(parse_coding(read_csv(a.coding)), read_csv(a.probes))
    except CodingError as e:
        print("coding error:", e, file=sys.stderr)
        return 2
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1)
    print(markdown(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
