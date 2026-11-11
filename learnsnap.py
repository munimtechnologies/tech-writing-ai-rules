#!/usr/bin/env python3
# Copyright 2026 Munim, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
"""learnsnap 0.1.0: how fast do AI-use labels change in Microsoft Learn's public docs repos?

Study 12 of tech-writing-ai-rules. Study 7 read the AI-use labels (`ai-usage: ai-assisted` or
`ai-generated` in YAML front matter) of every Markdown file in the 30 largest active
MicrosoftDocs repos on 2026-11-09 and published every labelled file with each repo's commit.
Microsoft Learn is retiring most public docs repos by the end of December 2026 (they become
private). This tool takes a later snapshot and compares it with study 7, file by file:

- panel: study 7's 30 read repos. Each file labelled now is 'kept', 'key-fixed' (a variant key
  such as ms.ai-usage became ai-usage), 'label-changed', or a new label on a file that already
  existed at study 7's commit ('new-label-existing-file') or did not ('new-label-new-file').
  Each file labelled at study 7 that is no longer labelled is 'label-removed' or 'file-gone'.
  Whether a path existed at study 7's commit comes from `git ls-tree` of that commit
  (fetched without file contents).
- breadth: every other active repo (same frame rules as study 7) is read once and counted.
- retirement: each of study 7's 129 eligible repos is 'public', 'archived', 'not public',
  or 'renamed to ...'.

Usage: python learnsnap.py --wave 1|2 --out-dir OUT [--wait-prereg-minutes 240]
                           [--study7-dir DIR] [--no-prereg-check] [--max-clones 200]

Needs learnlabels.py (study 7's tool, 0.1.0) next to it, and the git command line.
Outputs: frame.csv, labelled.csv, changes.csv, snapshot.json, LEARNSNAP_AUTO.md.
Reads front matter only and records no author names. Standard library only. Apache-2.0.
Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""

import argparse
import collections
import csv
import datetime
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error

import learnlabels as LL

VERSION = "0.1.0"
STUDY_DIR = "census/2026-11-ms-learn-label-change"
PREREG_PATH = STUDY_DIR + "/PREREG.md"
RAW = "https://raw.githubusercontent.com/munimtechnologies/tech-writing-ai-rules/main/"
STUDY7_DIR = "census/2026-11-ms-learn-ai-labels"
A_TIME = "2026-11-09T11:21:00Z"
WAVE2_NOT_BEFORE = "2026-12-14T00:00:00Z"
REPO_API = "https://api.github.com/repos/"
MAX_CLONES = 200
MAX_LOOKUPS = 40
GATE_PANEL = 25
AI_CATS = LL.AI_CATS
NEW_KINDS = ("new-label-existing-file", "new-label-new-file", "new-label-unknown-file")

FRAME_COLUMNS = ["rank", "repo", "group", "study7_status", "status_now", "read", "size_kb",
                 "default_branch", "pushed_at", "commit_a", "commit", "a_tree", "md", "articles",
                 "ai_labelled", "ai_assisted", "ai_generated", "other_ai", "non_ai_label",
                 "include_ai_labelled"]
CHANGE_COLUMNS = ["repo", "path", "change", "key_a", "value_a", "key_b", "value_b",
                  "is_article_b", "year_b"]


# ---------------------------------------------------------------- inputs

def read_csv_text(text):
    return list(csv.DictReader(io.StringIO(text)))


def load_study7(study7_dir=None, opener=None):
    """(frame rows, labelled rows) of study 7, from a local folder or the published repo."""
    out = []
    for name in ("frame.csv", "labelled.csv"):
        if study7_dir:
            with open(os.path.join(study7_dir, name), encoding="utf-8") as fh:
                text = fh.read()
        else:
            data = LL.http_get(RAW + STUDY7_DIR + "/" + name, opener, accept="text/plain")
            text = data.decode("utf-8")
        out.append(read_csv_text(text))
    return out[0], out[1]


# ---------------------------------------------------------------- repo status

def repo_status(name, listed):
    """'public' or 'archived' if the org listing has the repo, else 'not listed'."""
    r = listed.get(name.lower())
    if r is None:
        return "not listed"
    if r.get("archived"):
        return "archived"
    return "public"


def api_lookup(name, opener=None):
    """Status of a repo the org listing no longer shows: 'not public' (HTTP 404: private or
    deleted), 'renamed to X', 'archived', 'public' or 'lookup failed (...)'."""
    try:
        data = json.loads(LL.http_get(REPO_API + name, opener))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return "not public"
        return "lookup failed (HTTP %d)" % exc.code
    except Exception as exc:  # network, bad JSON
        return "lookup failed (%s)" % type(exc).__name__
    if not isinstance(data, dict):
        return "lookup failed (bad answer)"
    if data.get("private"):
        return "not public"
    full = data.get("full_name") or ""
    if full and full.lower() != name.lower():
        return "renamed to " + full
    if data.get("archived"):
        return "archived"
    return "public"


# ---------------------------------------------------------------- study 7's tree

def a_tree(dest, sha, timeout=LL.CLONE_TIMEOUT):
    """Markdown paths in study 7's commit, or None if that commit cannot be fetched."""
    if not sha:
        return None
    try:
        rc, _out, _err = LL.run_git(["fetch", "--quiet", "--depth", "1", "--filter=blob:none",
                                     "origin", sha], dest, timeout)
        if rc != 0:
            return None
        rc, out, _err = LL.run_git(["ls-tree", "-r", "-z", "--name-only", sha], dest, timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None
    if rc != 0:
        return None
    return set(p for p in out.split("\0") if p.lower().endswith(".md"))


# ---------------------------------------------------------------- comparison

def change_row(path, a_row, b_file, change):
    a_row = a_row or {}
    b_file = b_file or {}
    return {"repo": "", "path": path, "change": change,
            "key_a": a_row.get("ai_key", ""), "value_a": a_row.get("ai_value", ""),
            "key_b": b_file.get("ai_key", ""), "value_b": b_file.get("ai_value", ""),
            "is_article_b": b_file.get("is_article", ""), "year_b": b_file.get("year", "")}


def compare(a_rows, b_files, a_paths):
    """Change rows for one repo.
    a_rows: study 7's labelled rows for the repo; b_files: the new scan (every Markdown file);
    a_paths: Markdown paths at study 7's commit, or None if unknown."""
    a = {}
    for r in a_rows:
        a[r["path"]] = r
    b = {}
    for f in b_files:
        b[f["path"]] = f
    out = []
    for path in sorted(b):
        f = b[path]
        if f["category"] not in AI_CATS:
            continue
        r = a.get(path)
        if r is None:
            if a_paths is None:
                kind = "new-label-unknown-file"
            elif path in a_paths:
                kind = "new-label-existing-file"
            else:
                kind = "new-label-new-file"
        elif r["ai_key"] == f["ai_key"] and r["category"] == f["category"]:
            kind = "kept"
        elif r["ai_key"] != "ai-usage" and f["ai_key"] == "ai-usage":
            kind = "key-fixed"
        else:
            kind = "label-changed"
        out.append(change_row(path, r, f, kind))
    for path in sorted(a):
        f = b.get(path)
        if f is None:
            out.append(change_row(path, a[path], None, "file-gone"))
        elif f["category"] not in AI_CATS:
            out.append(change_row(path, a[path], f, "label-removed"))
    return out


# ---------------------------------------------------------------- summary and predictions

def pct(a, b):
    return round(100.0 * a / b, 2) if b else None


def days_between(a, b):
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    da = datetime.datetime.strptime(a, fmt)
    db = datetime.datetime.strptime(b, fmt)
    return round((db - da).total_seconds() / 86400.0, 3)


def as_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def summarise(rows, changes, wave, days):
    c = collections.Counter(ch["change"] for ch in changes)
    new = sum(c[k] for k in NEW_KINDS)
    existing = c["new-label-existing-file"]
    known_new = existing + c["new-label-new-file"]
    variant = [ch for ch in changes if ch["key_a"] and ch["key_a"] != "ai-usage"]
    fixed = sum(1 for ch in variant if ch["change"] == "key-fixed")

    s7 = [r for r in rows if r["group"] != "new"]
    not_public = sum(1 for r in s7 if r["status_now"] == "not public")
    archived = sum(1 for r in s7 if r["status_now"] == "archived")
    renamed = sum(1 for r in s7 if r["status_now"].startswith("renamed"))
    retired = not_public + archived

    panel_read = [r for r in rows if r["group"] == "panel" and r["read"] == "read"]
    panel_tree = [r for r in panel_read if r.get("a_tree") == "yes"]
    panel_articles = sum(as_int(r.get("articles")) for r in panel_read)
    panel_labelled = sum(as_int(r.get("ai_labelled")) for r in panel_read)
    other = [r for r in rows if r["group"] != "panel" and r["read"] == "read"]
    other20 = [r for r in other if as_int(r.get("articles")) >= 20]
    other20_lab = sum(1 for r in other20 if as_int(r.get("ai_labelled")) > 0)
    other_articles = sum(as_int(r.get("articles")) for r in other)
    other_labelled = sum(as_int(r.get("ai_labelled")) for r in other)
    per_day = round(new / days, 2) if days > 0 else None

    preds = collections.OrderedDict()
    if wave == 1:
        preds["G1"] = {"panel_read": len(panel_read), "panel_with_a_tree": len(panel_tree),
                       "held": len(panel_read) >= GATE_PANEL and len(panel_tree) >= GATE_PANEL}
        preds["P1"] = {"new_labels": new, "days": days, "per_day": per_day,
                       "held": (5 * days <= new <= 60 * days) if days > 0 else None}
        preds["P2"] = {"existing_file": existing, "known_new": known_new,
                       "existing_pct": pct(existing, known_new),
                       "held": (2 * existing >= known_new) if known_new >= 20 else None}
        preds["P3"] = {"label_removed": c["label-removed"], "new_labels": new,
                       "held": (10 * c["label-removed"] < new) if new else None}
        preds["P4"] = {"variant_a": len(variant), "key_fixed": fixed,
                       "held": (fixed <= 10) if variant else None}
        preds["P5"] = {"study7_repos": len(s7), "not_public": not_public, "archived": archived,
                       "held": retired <= 15}
        preds["P6"] = {"repos_20plus": len(other20), "with_label": other20_lab,
                       "pct": pct(other20_lab, len(other20)),
                       "held": (30 * len(other20) <= 100 * other20_lab <= 80 * len(other20))
                       if len(other20) >= 10 else None}
        preds["P7"] = {"articles": other_articles, "ai_labelled": other_labelled,
                       "pct": pct(other_labelled, other_articles),
                       "held": (2 * other_articles <= 100 * other_labelled <= 15 * other_articles)
                       if other_articles >= 1000 else None}
    else:
        enough = len(panel_read) >= 10
        preds["W2-P1"] = {"study7_repos": len(s7), "not_public": not_public, "archived": archived,
                          "retired_pct": pct(retired, len(s7)),
                          "held": (25 * len(s7) <= 100 * retired <= 95 * len(s7)) if s7 else None}
        preds["W2-P2"] = {"panel_read": len(panel_read), "new_labels": new, "days": days,
                          "per_day": per_day,
                          "held": (5 * days <= new <= 60 * days) if (enough and days > 0) else None}
        preds["W2-P3"] = {"variant_a": len(variant), "key_fixed": fixed,
                          "held": (fixed <= 20) if (enough and variant) else None}

    return collections.OrderedDict([
        ("wave", wave),
        ("days_since_study7", days),
        ("changes", dict(c)),
        ("new_labels", new),
        ("new_labels_per_day", per_day),
        ("variant_a", len(variant)),
        ("key_fixed", fixed),
        ("study7_repos", len(s7)),
        ("not_public", not_public),
        ("archived", archived),
        ("renamed", renamed),
        ("panel_read", len(panel_read)),
        ("panel_with_a_tree", len(panel_tree)),
        ("panel_articles", panel_articles),
        ("panel_labelled", panel_labelled),
        ("panel_labelled_pct", pct(panel_labelled, panel_articles)),
        ("other_read", len(other)),
        ("other_articles", other_articles),
        ("other_labelled", other_labelled),
        ("other_labelled_pct", pct(other_labelled, other_articles)),
        ("predictions", preds),
    ])


# ---------------------------------------------------------------- output

def report(meta, s, rows):
    out = ["# learnsnap %s: AI-use labels in Microsoft Learn's public docs repos, wave %d "
           "(automatic report)" % (VERSION, s["wave"]),
           "",
           "First pass written by the tool. The graded result is in RESULT.md.",
           "",
           "- Started %s, finished %s; %s days after study 7 (%s)." % (
               meta["started"], meta["finished"], s["days_since_study7"], A_TIME),
           "- Pre-registration first committed: %s." % (
               meta["prereg"].get("committed_at") or "not found (%s)" % meta["prereg"].get("error")),
           "- Study 7's %d eligible repos now: %d not public, %d archived, %d renamed." % (
               s["study7_repos"], s["not_public"], s["archived"], s["renamed"]),
           "- Panel: %d of study 7's 30 read repos read again (%d with study 7's tree); "
           "%d articles, %d AI-labelled (%s%%)." % (
               s["panel_read"], s["panel_with_a_tree"], s["panel_articles"], s["panel_labelled"],
               s["panel_labelled_pct"]),
           "- Changes since study 7: %s." % (
               ", ".join("%s %d" % kv for kv in sorted(s["changes"].items())) or "none"),
           "- New labels: %d (%s a day). Variant keys at study 7: %d, fixed: %d." % (
               s["new_labels"], s["new_labels_per_day"], s["variant_a"], s["key_fixed"]),
           "- Other active repos read: %d; %d articles, %d AI-labelled (%s%%)." % (
               s["other_read"], s["other_articles"], s["other_labelled"], s["other_labelled_pct"]),
           "",
           "## Predictions (automatic; boundaries as pre-registered)",
           "",
           "| | value | held |",
           "|---|---|---|"]
    for k, p in s["predictions"].items():
        shown = dict((kk, vv) for kk, vv in p.items() if kk != "held")
        out.append("| %s | %s | %s |" % (k, json.dumps(shown),
                                         {True: "yes", False: "no", None: "n/a"}[p["held"]]))
    out += ["", "## Repos", "",
            "| repo | group | status now | read | articles | AI-labelled |",
            "|---|---|---|---|---|---|"]
    for r in rows:
        out.append("| %s | %s | %s | %s | %s | %s |" % (
            r["repo"], r["group"], r["status_now"], r["read"], r.get("articles", ""),
            r.get("ai_labelled", "")))
    return "\n".join(out) + "\n"


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1)


# ---------------------------------------------------------------- main

def main(argv=None, opener=None, cloner=None, scanner=None, tree=None, lookup=None,
         sleep=time.sleep, now=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--wave", type=int, choices=(1, 2), required=True)
    ap.add_argument("--study7-dir", default=None)
    ap.add_argument("--no-prereg-check", action="store_true")
    ap.add_argument("--wait-prereg-minutes", type=float, default=0)
    ap.add_argument("--max-clones", type=int, default=MAX_CLONES)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    now = now or LL.utcnow
    meta = {"version": VERSION, "learnlabels_version": LL.VERSION, "wave": a.wave,
            "started": now(), "study7_time": A_TIME}
    out_json = os.path.join(a.out_dir, "snapshot.json")

    if a.wave == 2 and meta["started"] < WAVE2_NOT_BEFORE:
        print("wave 2 may not start before %s; nothing was read" % WAVE2_NOT_BEFORE)
        meta["error"] = "too early for wave 2"
        write_json(out_json, meta)
        return 5

    if a.no_prereg_check:
        meta["prereg"] = {"committed_at": None, "error": "not checked"}
    else:
        meta["prereg"] = LL.wait_for_prereg(PREREG_PATH, a.wait_prereg_minutes, opener, sleep)
        if meta["prereg"].get("committed_at") is None:
            print("pre-registration %s not found (%s); nothing was read"
                  % (PREREG_PATH, meta["prereg"].get("error")))
            write_json(out_json, meta)
            return 3

    try:
        frame7, lab7 = load_study7(a.study7_dir, opener)
        repos = LL.list_org(opener, sleep)
    except Exception as exc:
        print("cannot load inputs: %s %s" % (type(exc).__name__, exc))
        meta["error"] = "%s %s" % (type(exc).__name__, exc)
        write_json(out_json, meta)
        return 4

    listed = {}
    for r in repos:
        if isinstance(r, dict) and r.get("full_name"):
            listed[r["full_name"].lower()] = r
    eligible, _excluded = LL.build_frame(repos, LL.PUSHED_SINCE)
    eligible_set = set(e["full_name"].lower() for e in eligible)
    s7_set = set(row["repo"].lower() for row in frame7)
    panel_set = set(row["repo"].lower() for row in frame7 if row.get("status") == "read")
    lookup = lookup or (lambda name: api_lookup(name, opener))
    meta.update(listed=len(repos), eligible_now=len(eligible), study7_eligible=len(frame7))

    rows, lookups = [], 0
    for row in frame7:
        name = row["repo"]
        status = repo_status(name, listed)
        if status == "not listed":
            if lookups < MAX_LOOKUPS:
                lookups += 1
                status = lookup(name)
            else:
                status = "not listed (not looked up)"
        lr = listed.get(name.lower()) or {}
        rows.append({"rank": row.get("rank", ""), "repo": name,
                     "group": "panel" if name.lower() in panel_set else "study7-other",
                     "study7_status": row.get("status", ""), "status_now": status, "read": "",
                     "size_kb": lr.get("size", ""),
                     "default_branch": lr.get("default_branch") or row.get("default_branch") or "main",
                     "pushed_at": lr.get("pushed_at", ""), "commit_a": row.get("commit", ""),
                     "commit": "", "a_tree": ""})
    for e in eligible:
        if e["full_name"].lower() not in s7_set:
            rows.append({"rank": "", "repo": e["full_name"], "group": "new", "study7_status": "",
                         "status_now": "public", "read": "", "size_kb": e["size"],
                         "default_branch": e["default_branch"], "pushed_at": e["pushed_at"],
                         "commit_a": "", "commit": "", "a_tree": ""})

    by_repo_a = collections.defaultdict(list)
    for r in lab7:
        by_repo_a[r["repo"].lower()].append(r)

    cloner = cloner or LL.git_clone
    scanner = scanner or LL.scan_repo
    tree = tree or a_tree
    work = tempfile.mkdtemp(prefix="learnsnap-")
    labelled, changes, clones = [], [], 0
    for i, row in enumerate(rows):
        key = row["repo"].lower()
        if row["group"] == "panel":
            want = row["status_now"] in ("public", "archived")
        else:
            want = key in eligible_set
        if not want:
            row["read"] = "not read"
            continue
        if clones >= a.max_clones:
            row["read"] = "over clone limit"
            continue
        clones += 1
        dest = os.path.join(work, "r%03d" % i)
        t0 = time.time()
        err, commit = cloner(row["repo"], row["default_branch"], dest)
        if err:
            row["read"] = err
        else:
            files, _docfx = scanner(dest)
            row.update(LL.repo_stats(files))
            row["commit"] = commit
            row["read"] = "read"
            for f in files:
                if f["category"] in AI_CATS:
                    g = dict(f)
                    g["repo"] = row["repo"]
                    labelled.append(g)
            if row["group"] == "panel":
                paths = tree(dest, row["commit_a"])
                row["a_tree"] = "yes" if paths is not None else "no"
                for ch in compare(by_repo_a.get(key, []), files, paths):
                    ch["repo"] = row["repo"]
                    changes.append(ch)
        shutil.rmtree(dest, ignore_errors=True)
        print("%-55s %-12s %-10s %6s articles %6s labelled (%.0fs)" % (
            row["repo"], row["group"], row["read"][:10], row.get("articles", ""),
            row.get("ai_labelled", ""), time.time() - t0))
        sys.stdout.flush()
    shutil.rmtree(work, ignore_errors=True)

    meta["finished"] = now()
    meta["clones"] = clones
    meta["lookups"] = lookups
    days = days_between(A_TIME, meta["started"])
    summary = summarise(rows, changes, a.wave, days)
    LL.write_csv(os.path.join(a.out_dir, "frame.csv"), rows, FRAME_COLUMNS)
    LL.write_csv(os.path.join(a.out_dir, "labelled.csv"), labelled, LL.FILE_COLUMNS)
    LL.write_csv(os.path.join(a.out_dir, "changes.csv"), changes, CHANGE_COLUMNS)
    write_json(out_json, {"meta": meta, "summary": summary})
    text = report(meta, summary, rows)
    with open(os.path.join(a.out_dir, "LEARNSNAP_AUTO.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
