#!/usr/bin/env python3
# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""mdcheck_frame: the runner for study 11 of tech-writing-ai-rules.

It runs the md-copy-check skill's checker (skills/md-copy-check/scripts/md_copy_check.py,
version 0.1.0, unchanged) over a fresh read of the Markdown copies of study 10's 384
counted pages, and computes the gate and the predictions fixed in
census/2026-11-md-copy-check-frame/PREREG.md.

    python mdcheck_frame.py --out-dir out --wait-prereg-minutes 240
    python mdcheck_frame.py --out-dir out --repo . --no-prereg-check

Python 3 standard library only. One request per second; robots.txt honoured.
Outputs: pages.csv, findings.csv, sample.csv, context.csv, mdcheck_frame.json,
MDCHECK_AUTO.md, and copies/ and html/ folders (the sites' text, not republished).
"""

import argparse
import csv
import hashlib
import html as htmllib
import importlib.util
import io
import json
import os
import random
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

VERSION = "0.1.0"
TOOL_VERSION = "0.1.0"
RAW = "https://raw.githubusercontent.com/munimtechnologies/tech-writing-ai-rules/main/"
PREREG_PATH = "census/2026-11-md-copy-check-frame/PREREG.md"
PREREG_ID = "PREREG-ID: mdcheck-frame-2026-11"
PAGES_PATH = "census/2026-11-md-copy-parity/pages.csv"
TOOL_PATH = "skills/md-copy-check/scripts/md_copy_check.py"
UA = "mdcheck-frame/%s (+https://github.com/munimtechnologies/tech-writing-ai-rules)" % VERSION
SEED = 20261111
WARN_SAMPLE = 20
GATE_COPIES = 350
ACCEPT_MD = "text/markdown"
ACCEPT_SUFFIX = "text/markdown, text/plain;q=0.9, */*;q=0.1"
MAX_BYTES = 3000000

# (id, group, page URL as in study 10's pages.csv, marker the 2026-11-11 copy lacked)
KNOWN = [
    ("K1", "trace", "https://docs.netlify.com/resources/troubleshooting/fix-a-failed-deploy/",
     "control costs for Agent"),
    ("K2", "trace", "https://docs.railway.com/networking/cdn", "This feature is in beta"),
    ("K3", "trace", "https://docs.docker.com/reference/cli/sbx/volume/create/",
     "The volume name must be unique per account"),
    ("K4", "trace", "https://docs.docker.com/reference/cli/sbx/volume/rm/",
     "Volumes attached to active sandboxes"),
    ("K5", "trace", "https://docs.newrelic.com/docs/release-notes/diagnostics-release-notes/diagnostics-cli-release-notes/",
     "DotNet/Agent/Installed"),
    ("K6", "trace", "https://docs.cloud.google.com/compute/docs/tutorials/ml-inference-t4",
     "create a project instead of selecting an existing project"),
    ("K7", "trace", "https://docs.cloud.google.com/compute/docs/instances/sql-server/configure-failover-cluster-instance-with-multi-writer",
     "create a project instead of selecting an existing project"),
    ("N1", "notrace", "https://devcenter.heroku.com/articles/popsql", "currently in beta"),
    ("N2", "notrace", "https://docs.datadoghq.com/security/code_security/static_analysis/static_analysis_rules/typescript-express/path-traversal/",
     "static-analysis.datadog.yml"),
    ("N3", "notrace", "https://vercel.com/docs/sandbox/concepts/drives", "Slack-based Contentful assistant"),
]

PAGE_FIELDS = ["site", "idx", "url", "copy_url", "method", "group", "known_id", "status", "ctype",
               "got_copy", "words", "errors", "warnings", "infos", "codes", "flagged", "marker_present"]
FINDING_FIELDS = ["site", "idx", "url", "code", "severity", "line", "text"]
SAMPLE_FIELDS = ["why", "site", "idx", "url", "errors", "warnings", "codes"]
CONTEXT_FIELDS = ["why", "site", "idx", "url", "code", "severity", "line", "text", "html_ok",
                  "html_context", "real", "note"]


def utcnow():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def norm(text):
    """Text for the marker check: straight quotes, no Markdown escapes, emphasis, code
    ticks or link brackets, whitespace collapsed."""
    t = text or ""
    for a, b in (("\u2018", "'"), ("\u2019", "'"), ("\u201c", '"'), ("\u201d", '"'), ("\u00a0", " ")):
        t = t.replace(a, b)
    t = re.sub(r"\\([^\w\s])", r"\1", t)
    for ch in "*`[]":
        t = t.replace(ch, "")
    return re.sub(r"\s+", " ", t).strip()


def has_marker(text, marker):
    return norm(marker) in norm(text)


def group_of(url):
    """(id, group, marker) for a page URL; group is 'trace', 'notrace' or 'other'."""
    for kid, group, kurl, marker in KNOWN:
        if url == kurl:
            return kid, group, marker
    return "", "other", ""


def copy_request(row):
    """(URL, Accept header) study 10 used for this page's copy."""
    if (row.get("method") or "") == "suffix" and row.get("md_url"):
        return row["md_url"], ACCEPT_SUFFIX
    return row["url"], ACCEPT_MD


def read_frame(pages_text):
    """Counted rows of study 10's pages.csv, each with its 0-based row number as idx."""
    frame = []
    for idx, row in enumerate(csv.DictReader(io.StringIO(pages_text))):
        if str(row.get("counted", "")).strip().lower() == "true":
            r = dict(row)
            r["idx"] = idx
            frame.append(r)
    return frame


# ---------------------------------------------------------------- network

def fetch(url, accept, timeout=30):
    """(status, content type, text); status 0 on a network error."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status = getattr(r, "status", 200)
            ctype = r.headers.get("Content-Type", "") or ""
            body = r.read(MAX_BYTES)
    except urllib.error.HTTPError as e:
        return e.code, "", ""
    except Exception as e:  # timeouts, DNS and TLS errors, bad URLs
        return 0, "", str(e)[:200]
    return status, ctype, body.decode("utf-8", "replace")


class Robots:
    """robots.txt per host (a 401 or 403 forbids the host; other failures allow it)."""

    def __init__(self, fetcher=fetch):
        self.fetcher = fetcher
        self.cache = {}

    def allowed(self, url):
        p = urllib.parse.urlsplit(url)
        base = "%s://%s" % (p.scheme, p.netloc)
        if base not in self.cache:
            rp = urllib.robotparser.RobotFileParser()
            status, _ctype, text = self.fetcher(base + "/robots.txt", "text/plain")
            if status == 200:
                rp.parse(text.splitlines())
            elif status in (401, 403):
                rp.disallow_all = True
            else:
                rp.allow_all = True
            self.cache[base] = rp
        return self.cache[base].can_fetch(UA, url)


def get_public(no_prereg_check, wait_minutes, fetcher=fetch, pause=300):
    """The pre-registration, pages.csv and the checker from main, waiting up to
    wait_minutes for the pre-registration to appear. None if they never do."""
    deadline = time.time() + wait_minutes * 60
    while True:
        got = {}
        for path in (PREREG_PATH, PAGES_PATH, TOOL_PATH):
            status, _ctype, text = fetcher(RAW + path, "text/plain, */*")
            if status == 200 and (text or "").strip():
                got[path] = text
        ready = PAGES_PATH in got and TOOL_PATH in got
        if not no_prereg_check:
            ready = ready and PREREG_ID in got.get(PREREG_PATH, "")
        if ready:
            return got
        if time.time() >= deadline:
            return None
        time.sleep(pause)


def read_local(repo):
    files = {}
    for path in (PREREG_PATH, PAGES_PATH, TOOL_PATH):
        fp = os.path.join(repo, *path.split("/"))
        if os.path.exists(fp):
            with open(fp, encoding="utf-8") as f:
                files[path] = f.read()
    return files


def load_tool(text):
    folder = tempfile.mkdtemp(prefix="mdcheck-tool-")
    path = os.path.join(folder, "md_copy_check.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    spec = importlib.util.spec_from_file_location("md_copy_check", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- measuring

def save(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def measure(frame, tool, out_dir=None, fetcher=fetch, robots=None, sleep=1.0, log=None):
    """Fetch each frame page's copy and run the checker. (page rows, finding rows)."""
    results, findings = [], []
    key = {"error": "errors", "warning": "warnings", "info": "infos"}
    for n, row in enumerate(frame):
        url = row["url"]
        req_url, accept = copy_request(row)
        kid, group, marker = group_of(url)
        rec = {"site": row.get("site", ""), "idx": row["idx"], "url": url, "copy_url": req_url,
               "method": row.get("method", ""), "group": group, "known_id": kid, "status": "",
               "ctype": "", "got_copy": False, "words": "", "errors": 0, "warnings": 0, "infos": 0,
               "codes": "", "flagged": False, "marker_present": ""}
        if robots is not None and not robots.allowed(req_url):
            rec["status"] = "robots"
            results.append(rec)
            continue
        status, ctype, text = fetcher(req_url, accept)
        if sleep:
            time.sleep(sleep)
        rec["status"], rec["ctype"] = status, ctype
        if tool.looks_like_markdown(status, ctype, text):
            found, words = tool.check_text(text)
            rec["got_copy"] = True
            rec["words"] = words
            for f in found:
                rec[key[f["severity"]]] += 1
                findings.append({"site": rec["site"], "idx": rec["idx"], "url": url, "code": f["code"],
                                 "severity": f["severity"], "line": f["line"], "text": f["text"]})
            rec["codes"] = ";".join(sorted({f["code"] for f in found}))
            rec["flagged"] = rec["errors"] + rec["warnings"] > 0
            if marker:
                rec["marker_present"] = has_marker(text, marker)
            if out_dir:
                save(os.path.join(out_dir, "copies", rec["site"], "%03d.md" % rec["idx"]), text)
        results.append(rec)
        if log and (n + 1) % 25 == 0:
            log("%d of %d pages read" % (n + 1, len(frame)))
    return results, findings


def draw_sample(results, seed=SEED, k=WARN_SAMPLE):
    """Every O page with an error, then a seeded draw of k O pages with warnings only."""
    others = [r for r in results if r["group"] == "other" and r["got_copy"]]
    errs = sorted((r for r in others if r["errors"] > 0), key=lambda r: r["idx"])
    warn_only = sorted((r for r in others if r["errors"] == 0 and r["warnings"] > 0), key=lambda r: r["idx"])
    picked = random.Random(seed).sample(warn_only, min(k, len(warn_only)))
    picked.sort(key=lambda r: r["idx"])
    return [dict(r, why="error") for r in errs] + [dict(r, why="warning-sample") for r in picked]


def html_to_text(page):
    t = re.sub(r"(?is)<(script|style|noscript|svg)\b.*?</\1\s*>", " ", page or "")
    t = re.sub(r"(?s)<!--.*?-->", " ", t)
    t = re.sub(r"(?i)<br\s*/?>|</(p|div|li|h[1-6]|tr|section|article|pre|table|ul|ol|dd|dt)>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = htmllib.unescape(t)
    t = re.sub(r"[ \t\r\f\v]+", " ", t)
    t = re.sub(r"\s*\n\s*", "\n", t)
    return t.strip()


def heading_text(line):
    s = re.sub(r"^\s{0,3}#{1,6}\s*", "", line or "")
    s = re.sub(r"\{%.*?%\}|\{#[^}]*\}", "", s)
    s = re.sub(r"\s#+\s*$", "", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = s.replace("*", "").replace("`", "")
    return re.sub(r"\s+", " ", s).strip()


def context_after(page_text, heading, n=300):
    h = (heading or "").strip()
    if not h or not page_text:
        return ""
    i = page_text.lower().find(h.lower())
    if i < 0:
        return ""
    return page_text[i + len(h):i + len(h) + n].strip()


def fetch_contexts(sample, findings, out_dir=None, robots=None, sleep=1.0, fetcher=fetch):
    """Hand-check template: one row per error or warning on each sampled page."""
    by_idx = {}
    for f in findings:
        by_idx.setdefault(f["idx"], []).append(f)
    rows = []
    for r in sample:
        page_text = ""
        if robots is None or robots.allowed(r["url"]):
            status, _ctype, body = fetcher(r["url"], "text/html")
            if sleep:
                time.sleep(sleep)
            if status == 200 and body:
                if out_dir:
                    save(os.path.join(out_dir, "html", r["site"], "%03d.html" % r["idx"]), body)
                page_text = html_to_text(body)
        for f in by_idx.get(r["idx"], []):
            if f["severity"] == "info":
                continue
            ctx = context_after(page_text, heading_text(f["text"])) if f["code"] == "empty-section" else ""
            rows.append({"why": r["why"], "site": r["site"], "idx": r["idx"], "url": r["url"],
                         "code": f["code"], "severity": f["severity"], "line": f["line"], "text": f["text"],
                         "html_ok": bool(page_text), "html_context": ctx, "real": "", "note": ""})
    return rows


# ---------------------------------------------------------------- grading

def grade(results, findings, gate=GATE_COPIES):
    got = [r for r in results if r["got_copy"]]
    out = {"gates": {"G1": {"copies": len(got), "frame": len(results), "passed": len(got) >= gate}}}
    p = {}

    def broken(group):
        return [r for r in got if r["group"] == group and r["marker_present"] is False]

    def fixed(group):
        return [r["known_id"] for r in got if r["group"] == group and r["marker_present"] is True]

    kb = broken("trace")
    caught = [r["known_id"] for r in kb if r["flagged"]]
    p["P1"] = {"still_broken": [r["known_id"] for r in kb], "caught": caught, "fixed": fixed("trace"),
               "held": (len(caught) >= len(kb) - 1) if kb else None}
    k7 = [r for r in kb if r["known_id"] == "K7"]
    p["P2"] = {"k7_still_broken": bool(k7), "k7_flagged": bool(k7 and k7[0]["flagged"]),
               "held": (not k7[0]["flagged"]) if k7 else None}
    nb = broken("notrace")
    nflag = [r["known_id"] for r in nb if r["flagged"]]
    p["P3"] = {"still_broken": [r["known_id"] for r in nb], "flagged": nflag, "fixed": fixed("notrace"),
               "held": (len(nflag) <= 1) if nb else None}
    others = [r for r in got if r["group"] == "other"]
    flagged = [r for r in others if r["flagged"]]
    share = len(flagged) / len(others) if others else 0.0
    p["P4"] = {"flagged": len(flagged), "others": len(others), "share": round(share, 4),
               "held": (0.05 <= share <= 0.25) if others else None}
    other_idx = {r["idx"] for r in others}
    pages_by_code = {}
    for f in findings:
        if f["idx"] in other_idx and f["severity"] == "warning":
            pages_by_code.setdefault(f["code"], set()).add(f["idx"])
    ranked = sorted(((c, len(s)) for c, s in pages_by_code.items()), key=lambda kv: (-kv[1], kv[0]))
    top_ok = bool(ranked) and ranked[0][0] == "empty-section" and (len(ranked) == 1 or ranked[0][1] > ranked[1][1])
    p["P5"] = {"pages_by_warning_code": dict(ranked), "held": top_ok if ranked else None}
    p["P6"] = {"held": None, "note": "graded by hand from context.csv"}
    err_pages = [r for r in others if r["errors"] > 0]
    p["P7"] = {"error_pages": len(err_pages), "held": len(err_pages) <= 5}
    out["predictions"] = p
    per_site = {}
    for r in got:
        s = per_site.setdefault(r["site"], {"copies": 0, "flagged": 0, "errors": 0})
        s["copies"] += 1
        s["flagged"] += 1 if r["flagged"] else 0
        s["errors"] += 1 if r["errors"] else 0
    codes = {}
    for f in findings:
        codes.setdefault(f["code"], {"findings": 0, "pages": set()})
        codes[f["code"]]["findings"] += 1
        codes[f["code"]]["pages"].add(f["idx"])
    out["descriptive"] = {
        "per_site": per_site,
        "codes": {c: {"findings": v["findings"], "pages": len(v["pages"])} for c, v in sorted(codes.items())},
        "no_copy": [r["url"] for r in results if not r["got_copy"]],
    }
    return out


def verdict(v):
    return {True: "held", False: "failed", None: "not gradable"}[v]


def auto_md(meta, grades):
    g = grades["gates"]["G1"]
    p = grades["predictions"]
    lines = [
        "# Study 11: md-copy-check on study 10's frame (automatic output)",
        "",
        "mdcheck_frame %s; md_copy_check %s (sha256 %s); read %s to %s." % (
            meta["version"], meta["tool_version"], meta["tool_sha256"][:12], meta["read_started"], meta["finished"]),
        "",
        "- G1: %d of %d pages have a copy (%s)." % (g["copies"], g["frame"], "passed" if g["passed"] else "FAILED"),
        "- P1: K still broken %s; flagged %s; fixed since 2026-11-11 %s: %s." % (
            ", ".join(p["P1"]["still_broken"]) or "none", ", ".join(p["P1"]["caught"]) or "none",
            ", ".join(p["P1"]["fixed"]) or "none", verdict(p["P1"]["held"])),
        "- P2: K7 still broken %s, flagged %s: %s." % (p["P2"]["k7_still_broken"], p["P2"]["k7_flagged"],
                                                        verdict(p["P2"]["held"])),
        "- P3: N still broken %s; flagged %s; fixed %s: %s." % (
            ", ".join(p["P3"]["still_broken"]) or "none", ", ".join(p["P3"]["flagged"]) or "none",
            ", ".join(p["P3"]["fixed"]) or "none", verdict(p["P3"]["held"])),
        "- P4: %d of %d other pages flagged (%.1f%%): %s." % (p["P4"]["flagged"], p["P4"]["others"],
                                                             100 * p["P4"]["share"], verdict(p["P4"]["held"])),
        "- P5: pages per warning code %s: %s." % (json.dumps(p["P5"]["pages_by_warning_code"]),
                                                  verdict(p["P5"]["held"])),
        "- P6: graded by hand (context.csv).",
        "- P7: %d other pages with an error: %s." % (p["P7"]["error_pages"], verdict(p["P7"]["held"])),
        "",
        "Per site (copies, flagged, with an error):",
        "",
    ]
    for site, s in sorted(grades["descriptive"]["per_site"].items()):
        lines.append("- %s: %d, %d, %d" % (site, s["copies"], s["flagged"], s["errors"]))
    lines += ["", "Made by MV2 of Munim, Inc., with AI agents working in his name.", ""]
    return "\n".join(lines)


def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Study 11: run md-copy-check over study 10's frame.")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--repo", help="read the three input files from a local clone instead of GitHub")
    ap.add_argument("--no-prereg-check", action="store_true")
    ap.add_argument("--wait-prereg-minutes", type=float, default=0)
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--limit", type=int, default=0, help="read only the first N frame pages (for trials)")
    ap.add_argument("--version", action="version", version="mdcheck_frame " + VERSION)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    started = utcnow()

    if a.repo:
        files = read_local(a.repo)
        if not a.no_prereg_check and PREREG_ID not in files.get(PREREG_PATH, ""):
            files = None
    else:
        files = get_public(a.no_prereg_check, a.wait_prereg_minutes)
    if not files or PAGES_PATH not in files or TOOL_PATH not in files:
        print("stopped: the pre-registration, pages.csv or md_copy_check.py is not available", file=sys.stderr)
        return 3
    tool = load_tool(files[TOOL_PATH])
    tool_version = getattr(tool, "VERSION", "")
    if tool_version != TOOL_VERSION:
        print("stopped: md_copy_check is %r, the pre-registration names %s" % (tool_version, TOOL_VERSION),
              file=sys.stderr)
        return 4
    frame = read_frame(files[PAGES_PATH])
    if a.limit:
        frame = frame[:a.limit]
    print("frame: %d counted pages; md_copy_check %s" % (len(frame), tool_version))

    robots = Robots()
    read_started = utcnow()
    results, findings = measure(frame, tool, a.out_dir, fetch, robots, a.sleep, log=print)
    sample = draw_sample(results)
    contexts = fetch_contexts(sample, findings, a.out_dir, robots, a.sleep)
    grades = grade(results, findings)
    meta = {"version": VERSION, "tool_version": tool_version, "tool_sha256": sha256(files[TOOL_PATH]),
            "pages_sha256": sha256(files[PAGES_PATH]),
            "prereg_sha256": sha256(files[PREREG_PATH]) if PREREG_PATH in files else "",
            "started": started, "read_started": read_started, "finished": utcnow(), "seed": SEED}

    write_csv(os.path.join(a.out_dir, "pages.csv"), results, PAGE_FIELDS)
    write_csv(os.path.join(a.out_dir, "findings.csv"), findings, FINDING_FIELDS)
    write_csv(os.path.join(a.out_dir, "sample.csv"), sample, SAMPLE_FIELDS)
    write_csv(os.path.join(a.out_dir, "context.csv"), contexts, CONTEXT_FIELDS)
    with open(os.path.join(a.out_dir, "mdcheck_frame.json"), "w", encoding="utf-8") as f:
        json.dump(dict(meta, **grades), f, indent=1)
    with open(os.path.join(a.out_dir, "MDCHECK_AUTO.md"), "w", encoding="utf-8") as f:
        f.write(auto_md(meta, grades))
    print(auto_md(meta, grades))
    return 0


if __name__ == "__main__":
    sys.exit(main())
