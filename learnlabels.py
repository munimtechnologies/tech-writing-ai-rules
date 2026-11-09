#!/usr/bin/env python3
# Copyright 2026 Munim, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
"""learnlabels 0.1.0: census of AI-use labels in Microsoft Learn's public documentation repos.

Study 7 of tech-writing-ai-rules. Microsoft's Learn-wide authoring instructions ask that
Markdown "created or substantially modified with AI assistance" carry an `ai-usage` front
matter entry (`ai-generated` or `ai-assisted`). Microsoft Learn is retiring most of its
public documentation repos by the end of December 2026, so this is a snapshot while they
can still be read.

The tool lists the public repos of the MicrosoftDocs GitHub organisation, builds the
pre-registered frame (no forks, no archived repos, no localized copies, pushed since
2026-05-01, largest first), and reads repos in that order until TARGET repos with at least
MIN_ARTICLES articles have been read. Each repo gets a shallow, blob-filtered clone with only
Markdown files and docfx.json checked out (git sparse checkout). It reads the YAML front
matter of every Markdown file and nothing else, deletes each clone straight after, and
records no author names.

Usage: python learnlabels.py --out-dir OUT [--wait-prereg-minutes 300] [--target 30]
                             [--max-clones 50] [--min-articles 200] [--no-prereg-check]

Outputs: frame.csv, files.csv, labelled.csv, docfx_ai.csv, census.json, LEARNLABELS_AUTO.md.
Standard library only, plus the git command line. Apache-2.0.
Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""

import argparse
import collections
import csv
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

VERSION = "0.1.0"
ORG = "MicrosoftDocs"
USER_AGENT = ("tech-writing-ai-rules-learnlabels/%s (+https://github.com/munimtechnologies/"
              "tech-writing-ai-rules; mv2@munimtech.com)" % VERSION)
REPO_API = "https://api.github.com/repos/munimtechnologies/tech-writing-ai-rules/commits"
ORG_API = "https://api.github.com/orgs/%s/repos" % ORG
PREREG_PATH = "census/2026-11-ms-learn-ai-labels/PREREGISTRATION.md"
PUSHED_SINCE = "2026-05-01"
TARGET_READ = 30
MAX_CLONES = 50
MIN_ARTICLES = 200
CLONE_TIMEOUT = 1800
HEAD_BYTES = 16384
GATE_REPOS = 15
GATE_ARTICLES = 20000
MIN_GROUP = 100

LOCALE_RE = re.compile(r"\.[a-z]{2,3}(?:-[a-z0-9]{2,4})+$", re.I)
AI_KEY_RE = re.compile(r"^(?:ms\.)?ai[-_.]?usage$", re.I)
AI_TOKEN_RE = re.compile(r"(?<![a-z0-9])ai-(?:generated|assisted|gen[a-z0-9-]*)", re.I)
AI_WORD_RE = re.compile(r"(?<![a-z])ai(?![a-z])")
KV_RE = re.compile(r"^([A-Za-z0-9_.\-]+)[ \t]*:(?:[ \t]+(.*))?$")
INCLUDE_DIRS = {"includes", "include", "_includes"}
TEXT_KEYS = {"title", "description", "summary", "keywords", "titlesuffix"}
AI_CATS = ("ai-assisted", "ai-generated", "other-ai")

FILE_COLUMNS = ["repo", "path", "is_article", "include", "ai_key", "ai_value", "category",
                "year", "ms_topic", "other_tokens"]
FRAME_COLUMNS = ["rank", "repo", "size_kb", "default_branch", "pushed_at", "status", "commit",
                 "md", "articles", "ai_labelled", "ai_assisted", "ai_generated", "other_ai",
                 "non_ai_label", "include_ai_labelled"]


# ---------------------------------------------------------------- front matter

def unquote(val):
    """Strip one pair of matching quotes, or a trailing ' # comment' from an unquoted value."""
    v = (val or "").strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        return v[1:-1].strip()
    if v[:1] not in ("'", '"'):
        i = v.find(" #")
        if i >= 0:
            v = v[:i].rstrip()
    return v


def front_matter(text):
    """Return the lines inside a leading YAML front matter block, or None if there is none."""
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, min(len(lines), 400)):
        if lines[i].strip() in ("---", "..."):
            return lines[1:i]
    return None


def parse_fields(lines):
    """Top-level `key: value` pairs; indented lines, list items and comments are skipped."""
    fields = collections.OrderedDict()
    for line in lines:
        if not line or line[0] in " \t#-":
            continue
        m = KV_RE.match(line.rstrip())
        if m and m.group(1) not in fields:
            fields[m.group(1)] = unquote(m.group(2) or "")
    return fields


def ai_label(fields):
    """The first key that names AI usage (ai-usage, ms.ai-usage, ai.usage, ...) and its value."""
    for key, val in (fields or {}).items():
        if AI_KEY_RE.match(key):
            return key, val
    return "", ""


def category(key, value):
    """'' (no AI key), 'ai-assisted', 'ai-generated', 'other-ai' or 'non-ai'."""
    if not key:
        return ""
    v = (value or "").strip().lower()
    if v in ("ai-assisted", "ai-generated"):
        return v
    if AI_WORD_RE.search(v):
        return "other-ai"
    return "non-ai"


def other_ai_tokens(lines, ai_key):
    """AI tokens (ai-generated, ai-assisted, ai-gen...) on front matter lines other than the
    AI key itself and the free-text keys (title, description, ...)."""
    found = []
    for line in lines or []:
        if line and line[0] not in " \t#-":
            m = KV_RE.match(line.rstrip())
            if m and ((ai_key and m.group(1) == ai_key) or m.group(1).lower() in TEXT_KEYS):
                continue
        for t in AI_TOKEN_RE.findall(line):
            t = t.lower()
            if t not in found:
                found.append(t)
    return found


def date_year(val):
    """Year of an ms.date value (MM/DD/YYYY or YYYY-MM-DD...), or None."""
    v = unquote(val or "")
    m = re.match(r"^\d{1,2}/\d{1,2}/(\d{4})(?!\d)", v)
    if not m:
        m = re.match(r"^(\d{4})-\d{1,2}-\d{1,2}", v)
    if not m:
        return None
    y = int(m.group(1))
    return y if 1990 <= y <= 2100 else None


def norm_path(path):
    return path.replace("\\", "/")


def is_include(path):
    parts = norm_path(path).lower().split("/")
    return any(p in INCLUDE_DIRS for p in parts[:-1])


def describe_file(relpath, text):
    lines = front_matter(text)
    fields = parse_fields(lines) if lines is not None else collections.OrderedDict()
    key, val = ai_label(fields)
    include = is_include(relpath)
    year = date_year(fields.get("ms.date", ""))
    return {
        "path": norm_path(relpath),
        "is_article": bool(fields) and "title" in fields and not include,
        "include": include,
        "ai_key": key,
        "ai_value": val[:60],
        "category": category(key, val),
        "year": year,
        "ms_topic": fields.get("ms.topic", "")[:40],
        "other_tokens": ";".join(other_ai_tokens(lines, key)),
    }


# ---------------------------------------------------------------- docfx.json

def load_json_loose(text):
    try:
        return json.loads(text)
    except ValueError:
        return None


def docfx_ai(obj):
    """AI-usage entries set for many files at once in docfx.json (globalMetadata/fileMetadata)."""
    out = []
    if not isinstance(obj, dict):
        return out
    build = obj.get("build") if isinstance(obj.get("build"), dict) else obj
    gm = build.get("globalMetadata")
    if isinstance(gm, dict):
        for k, v in gm.items():
            if AI_KEY_RE.match(str(k)):
                out.append(("globalMetadata", str(k), "", str(v)))
    fm = build.get("fileMetadata")
    if isinstance(fm, dict):
        for k, v in fm.items():
            if AI_KEY_RE.match(str(k)) and isinstance(v, dict):
                for glob, val in v.items():
                    out.append(("fileMetadata", str(k), str(glob), str(val)))
    return out


# ---------------------------------------------------------------- one repo

def read_head(path, n=HEAD_BYTES):
    with open(path, "rb") as fh:
        return fh.read(n).decode("utf-8", "replace")


def scan_repo(root):
    """Describe every Markdown file under root (dot folders skipped) and every docfx.json AI entry."""
    files, docfx = [], []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = norm_path(os.path.relpath(full, root))
            low = name.lower()
            if low.endswith(".md"):
                try:
                    files.append(describe_file(rel, read_head(full)))
                except OSError:
                    continue
            elif low == "docfx.json":
                try:
                    with open(full, "rb") as fh:
                        obj = load_json_loose(fh.read().decode("utf-8-sig", "replace"))
                except OSError:
                    obj = None
                for where, key, glob, value in docfx_ai(obj):
                    docfx.append({"path": rel, "where": where, "key": key, "glob": glob,
                                  "value": value[:60]})
    return files, docfx


def repo_stats(files):
    arts = [f for f in files if f["is_article"]]
    cats = collections.Counter(f["category"] for f in arts)
    return {
        "md": len(files),
        "articles": len(arts),
        "ai_labelled": sum(cats[c] for c in AI_CATS),
        "ai_assisted": cats["ai-assisted"],
        "ai_generated": cats["ai-generated"],
        "other_ai": cats["other-ai"],
        "non_ai_label": cats["non-ai"],
        "include_ai_labelled": sum(1 for f in files if f["include"] and f["category"] in AI_CATS),
    }


def run_git(args, cwd=None, timeout=CLONE_TIMEOUT):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_LFS_SKIP_SMUDGE="1", GCM_INTERACTIVE="never")
    p = subprocess.run(["git"] + args, cwd=cwd, env=env, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=timeout)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def git_clone(full_name, branch, dest, timeout=CLONE_TIMEOUT):
    """Shallow, blob-filtered clone with only Markdown and docfx.json checked out.
    Returns (error or None, commit sha)."""
    url = "https://github.com/%s.git" % full_name
    steps = [
        (["clone", "--quiet", "--depth", "1", "--filter=blob:none", "--sparse", "--branch", branch,
          url, dest], None),
        (["sparse-checkout", "set", "--no-cone", "*.md", "*.MD", "*.Md", "docfx.json"], dest),
    ]
    try:
        for args, cwd in steps:
            rc, _out, err = run_git(args, cwd, timeout)
            if rc != 0:
                lines = err.strip().splitlines() or ["exit %d" % rc]
                return "%s failed: %s" % (args[0], lines[-1][:200]), ""
        rc, out, _err = run_git(["rev-parse", "HEAD"], dest, 60)
        return None, (out.strip() if rc == 0 else "")
    except subprocess.TimeoutExpired:
        return "timeout", ""
    except OSError as exc:
        return "git not available (%s)" % type(exc).__name__, ""


# ---------------------------------------------------------------- GitHub listing and frame

def http_get(url, opener=None, accept="application/vnd.github+json"):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    if opener is not None:
        return opener(req)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def list_org(opener=None, sleep=time.sleep, retry_wait=3700, max_pages=30):
    """Every public repo of the org, via the REST API (100 per page). One retry per page after
    retry_wait seconds, for the unauthenticated rate limit."""
    repos = []
    for page in range(1, max_pages + 1):
        url = ORG_API + "?" + urllib.parse.urlencode(
            {"type": "public", "sort": "full_name", "per_page": 100, "page": page})
        data, last = None, ""
        for attempt in range(2):
            try:
                data = json.loads(http_get(url, opener))
                break
            except Exception as exc:  # network, HTTP 403 rate limit, bad JSON
                last = type(exc).__name__
                if attempt == 0:
                    sleep(retry_wait)
        if data is None:
            raise RuntimeError("org listing failed on page %d (%s)" % (page, last))
        if not isinstance(data, list):
            raise RuntimeError("unexpected org listing answer on page %d" % page)
        repos.extend(data)
        if len(data) < 100:
            break
    return repos


def exclusion(r, since=PUSHED_SINCE):
    name = r.get("name") or ""
    if r.get("fork"):
        return "fork"
    if r.get("archived"):
        return "archived"
    if r.get("private") or (r.get("visibility") or "public") != "public":
        return "not public"
    if LOCALE_RE.search(name):
        return "localized copy"
    if (r.get("pushed_at") or "") < since:
        return "not pushed since %s" % since
    return ""


def build_frame(repos, since=PUSHED_SINCE):
    """(eligible repos sorted by size, largest first, then name; Counter of exclusion reasons)."""
    eligible, excluded = [], collections.Counter()
    for r in repos:
        if not isinstance(r, dict) or not r.get("full_name"):
            excluded["bad entry"] += 1
            continue
        why = exclusion(r, since)
        if why:
            excluded[why] += 1
            continue
        eligible.append({"full_name": r["full_name"], "size": int(r.get("size") or 0),
                         "default_branch": r.get("default_branch") or "main",
                         "pushed_at": r.get("pushed_at") or ""})
    eligible.sort(key=lambda e: (-e["size"], e["full_name"].lower()))
    return eligible, excluded


# ---------------------------------------------------------------- pre-registration check

def prereg_commit(path, opener=None):
    url = REPO_API + "?" + urllib.parse.urlencode({"path": path, "per_page": 100})
    try:
        data = json.loads(http_get(url, opener))
    except Exception as exc:
        return {"committed_at": None, "error": type(exc).__name__}
    if not isinstance(data, list):
        return {"committed_at": None, "error": "unexpected API answer"}
    if not data:
        return {"committed_at": None, "error": "no commit touches %s yet" % path}
    first = data[-1]
    return {"committed_at": first["commit"]["committer"]["date"], "sha": first["sha"], "error": None}


def wait_for_prereg(path, minutes, opener=None, sleep=time.sleep, every=900):
    """Poll every 15 minutes (the unauthenticated GitHub API allows 60 calls an hour)."""
    prereg = prereg_commit(path, opener)
    waited = 0
    while prereg.get("committed_at") is None and waited < minutes * 60:
        sleep(every)
        waited += every
        prereg = prereg_commit(path, opener)
    prereg["waited_seconds"] = waited
    return prereg


# ---------------------------------------------------------------- summary and predictions

def pct(a, b):
    return round(100.0 * a / b, 2) if b else None


def summarise(files, rows):
    arts = [f for f in files if f["is_article"]]
    n = len(arts)
    ai = [f for f in arts if f["category"] in AI_CATS]
    cats = collections.Counter(f["category"] for f in arts)
    read_rows = [r for r in rows if r.get("status") == "read"]

    by_year = collections.OrderedDict()
    for y in sorted(set(f["year"] for f in arts if f["year"] is not None)):
        ya = [f for f in arts if f["year"] == y]
        yl = sum(1 for f in ya if f["category"] in AI_CATS)
        by_year[str(y)] = {"articles": len(ya), "ai_labelled": yl, "pct": pct(yl, len(ya))}
    no_year = [f for f in arts if f["year"] is None]
    by_year["none"] = {"articles": len(no_year),
                       "ai_labelled": sum(1 for f in no_year if f["category"] in AI_CATS),
                       "pct": pct(sum(1 for f in no_year if f["category"] in AI_CATS), len(no_year))}

    topics = collections.Counter(f["ms_topic"] or "(none)" for f in arts)
    topic_ai = collections.Counter(f["ms_topic"] or "(none)" for f in ai)
    by_topic = [{"ms_topic": t, "articles": c, "ai_labelled": topic_ai[t], "pct": pct(topic_ai[t], c)}
                for t, c in topics.most_common() if c >= MIN_GROUP]

    tokens = collections.Counter()
    for f in arts:
        for t in (f["other_tokens"].split(";") if f["other_tokens"] else []):
            tokens[t] += 1
    keys = collections.Counter(f["ai_key"] for f in arts if f["ai_key"])
    values = collections.Counter(f["ai_value"].strip().lower() for f in arts if f["ai_key"])

    preds = collections.OrderedDict()
    # P1: 5% <= AI-labelled share of articles <= 35% (inclusive)
    preds["P1"] = {"value_pct": pct(len(ai), n),
                   "held": (5 * n <= 100 * len(ai) <= 35 * n) if n else None}
    # P2: ai-assisted at least 3 times ai-generated
    assisted, generated = cats["ai-assisted"], cats["ai-generated"]
    preds["P2"] = {"ai_assisted": assisted, "ai_generated": generated,
                   "ratio": round(assisted / generated, 2) if generated else None,
                   "held": (assisted >= 3 * generated) if (assisted or generated) else None}
    # P3: at least 75% of AI-labelled articles with a known year have ms.date in 2025 or later
    known = [f for f in ai if f["year"] is not None]
    recent = sum(1 for f in known if f["year"] >= 2025)
    preds["P3"] = {"value_pct": pct(recent, len(known)), "known_year": len(known),
                   "held": (100 * recent >= 75 * len(known)) if known else None}
    # P4: labelled share among ms.date 2026 articles >= 3 x the share among ms.date <= 2024
    a26 = [f for f in arts if f["year"] == 2026]
    old = [f for f in arts if f["year"] is not None and f["year"] <= 2024]
    l26 = sum(1 for f in a26 if f["category"] in AI_CATS)
    lold = sum(1 for f in old if f["category"] in AI_CATS)
    p4 = None
    if len(a26) >= MIN_GROUP and len(old) >= MIN_GROUP:
        p4 = (l26 > 0) and (l26 * len(old) >= 3 * lold * len(a26))
    preds["P4"] = {"share_2026_pct": pct(l26, len(a26)), "n_2026": len(a26),
                   "share_le2024_pct": pct(lold, len(old)), "n_le2024": len(old),
                   "ratio": round((l26 / len(a26)) / (lold / len(old)), 2)
                   if (a26 and old and lold) else None,
                   "held": p4}
    # P5: at least 80% of read repos have at least one AI-labelled article
    with_label = sum(1 for r in read_rows if int(r.get("ai_labelled") or 0) > 0)
    preds["P5"] = {"repos_with_label": with_label, "repos_read": len(read_rows),
                   "value_pct": pct(with_label, len(read_rows)),
                   "held": (100 * with_label >= 80 * len(read_rows)) if read_rows else None}
    # P6: fewer than 10% of AI-labelled articles use a key other than `ai-usage` or a value
    # other than ai-assisted / ai-generated (case ignored)
    nonc = sum(1 for f in ai if f["ai_key"] != "ai-usage" or f["category"] == "other-ai")
    preds["P6"] = {"noncanonical": nonc, "value_pct": pct(nonc, len(ai)),
                   "held": (100 * nonc < 10 * len(ai)) if ai else None}

    gate = len(read_rows) >= GATE_REPOS and n >= GATE_ARTICLES
    return collections.OrderedDict([
        ("repos_read", len(read_rows)),
        ("articles", n),
        ("md_files", len(files)),
        ("ai_labelled", len(ai)),
        ("ai_labelled_pct", pct(len(ai), n)),
        ("categories", dict(cats)),
        ("include_ai_labelled", sum(1 for f in files if f["include"] and f["category"] in AI_CATS)),
        ("ai_keys", dict(keys)),
        ("ai_values", dict(values.most_common(20))),
        ("other_tokens", dict(tokens.most_common(20))),
        ("by_year", by_year),
        ("by_topic", by_topic),
        ("gate", {"repos_read": len(read_rows), "articles": n, "passed": gate}),
        ("predictions", preds),
    ])


# ---------------------------------------------------------------- output

def write_csv(path, rows, columns):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in columns})


def report(meta, summary, rows):
    s = summary
    out = ["# learnlabels %s: AI-use labels in Microsoft Learn's public docs repos (automatic report)" % VERSION,
           "",
           "First pass written by the tool. The graded result is in RESULT.md.",
           "",
           "- Started %s, finished %s." % (meta["started"], meta["finished"]),
           "- Pre-registration first committed: %s." % (meta["prereg"].get("committed_at")
                                                       or "not found (%s)" % meta["prereg"].get("error")),
           "- Org repos listed: %d; eligible: %d; excluded: %s." % (
               meta["listed"], meta["eligible"],
               ", ".join("%s %d" % kv for kv in sorted(meta["excluded"].items())) or "none"),
           "- Repos read: %d (gate needs %d); articles: %d (gate needs %d); gate %s." % (
               s["repos_read"], GATE_REPOS, s["articles"], GATE_ARTICLES,
               "PASSED" if s["gate"]["passed"] else "FAILED"),
           "- AI-labelled articles: %d (%s%%). Categories: %s." % (
               s["ai_labelled"], s["ai_labelled_pct"],
               ", ".join("%s %d" % (k or "unlabelled", v) for k, v in sorted(s["categories"].items()))),
           "- Keys: %s. Other AI tokens: %s." % (
               ", ".join("%s %d" % kv for kv in sorted(s["ai_keys"].items())) or "none",
               ", ".join("%s %d" % kv for kv in s["other_tokens"].items()) or "none"),
           "",
           "## Predictions (automatic; boundaries as pre-registered)",
           "",
           "| | value | held |",
           "|---|---|---|"]
    for k, p in s["predictions"].items():
        shown = {kk: vv for kk, vv in p.items() if kk != "held"}
        out.append("| %s | %s | %s |" % (k, json.dumps(shown), {True: "yes", False: "no", None: "n/a"}[p["held"]]))
    out += ["", "## By ms.date year", "", "| year | articles | AI-labelled | % |", "|---|---|---|---|"]
    for y, v in s["by_year"].items():
        out.append("| %s | %d | %d | %s |" % (y, v["articles"], v["ai_labelled"], v["pct"]))
    out += ["", "## Repos", "", "| rank | repo | status | articles | AI-labelled | assisted | generated |",
            "|---|---|---|---|---|---|---|"]
    for r in rows:
        if r["status"] == "not reached":
            continue
        out.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            r["rank"], r["repo"], r["status"], r.get("articles", ""), r.get("ai_labelled", ""),
            r.get("ai_assisted", ""), r.get("ai_generated", "")))
    return "\n".join(out) + "\n"


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv=None, opener=None, cloner=None, sleep=time.sleep, scanner=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--target", type=int, default=TARGET_READ)
    ap.add_argument("--max-clones", type=int, default=MAX_CLONES)
    ap.add_argument("--min-articles", type=int, default=MIN_ARTICLES)
    ap.add_argument("--since", default=PUSHED_SINCE)
    ap.add_argument("--prereg-path", default=PREREG_PATH)
    ap.add_argument("--no-prereg-check", action="store_true")
    ap.add_argument("--wait-prereg-minutes", type=float, default=0)
    ap.add_argument("--work-dir", default=None)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    meta = {"version": VERSION, "started": utcnow(), "settings": {
        "org": ORG, "since": a.since, "target": a.target, "max_clones": a.max_clones,
        "min_articles": a.min_articles}}

    if a.no_prereg_check:
        meta["prereg"] = {"committed_at": None, "error": "not checked"}
    else:
        meta["prereg"] = wait_for_prereg(a.prereg_path, a.wait_prereg_minutes, opener, sleep)
        if a.wait_prereg_minutes > 0 and meta["prereg"].get("committed_at") is None:
            print("pre-registration %s not found after %s minutes (%s); nothing was read"
                  % (a.prereg_path, a.wait_prereg_minutes, meta["prereg"].get("error")))
            with open(os.path.join(a.out_dir, "census.json"), "w", encoding="utf-8") as fh:
                json.dump(meta, fh, indent=1)
            return 3

    try:
        repos = list_org(opener, sleep)
    except RuntimeError as exc:
        print("cannot list %s: %s" % (ORG, exc))
        meta["error"] = str(exc)
        with open(os.path.join(a.out_dir, "census.json"), "w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=1)
        return 4
    eligible, excluded = build_frame(repos, a.since)
    meta.update(listed=len(repos), eligible=len(eligible), excluded=dict(excluded))
    print("listed %d repos, %d eligible" % (len(repos), len(eligible)))

    cloner = cloner or git_clone
    scanner = scanner or scan_repo
    work = a.work_dir or tempfile.mkdtemp(prefix="learnlabels-")
    rows, all_files, docfx_rows = [], [], []
    read = clones = 0
    for rank, r in enumerate(eligible, 1):
        row = {"rank": rank, "repo": r["full_name"], "size_kb": r["size"],
               "default_branch": r["default_branch"], "pushed_at": r["pushed_at"],
               "status": "not reached", "commit": ""}
        if read < a.target and clones < a.max_clones:
            clones += 1
            dest = os.path.join(work, "r%03d" % rank)
            t0 = time.time()
            err, commit = cloner(r["full_name"], r["default_branch"], dest)
            if err:
                row["status"] = err
            else:
                files, docfx = scanner(dest)
                st = repo_stats(files)
                row.update(st)
                row["commit"] = commit
                if st["articles"] >= a.min_articles:
                    row["status"] = "read"
                    read += 1
                    for f in files:
                        f["repo"] = r["full_name"]
                        all_files.append(f)
                    for d in docfx:
                        d["repo"] = r["full_name"]
                        docfx_rows.append(d)
                else:
                    row["status"] = "too few articles"
            shutil.rmtree(dest, ignore_errors=True)
            print("%3d %-55s %-18s %6s articles %6s labelled (%.0fs)" % (
                rank, r["full_name"], row["status"][:18], row.get("articles", ""),
                row.get("ai_labelled", ""), time.time() - t0))
            sys.stdout.flush()
        rows.append(row)
    if not a.work_dir:
        shutil.rmtree(work, ignore_errors=True)

    summary = summarise(all_files, rows)
    meta["finished"] = utcnow()
    meta["clones"] = clones
    write_csv(os.path.join(a.out_dir, "frame.csv"), rows, FRAME_COLUMNS)
    write_csv(os.path.join(a.out_dir, "files.csv"), all_files, FILE_COLUMNS)
    write_csv(os.path.join(a.out_dir, "labelled.csv"),
              [f for f in all_files if f["category"] in AI_CATS], FILE_COLUMNS)
    write_csv(os.path.join(a.out_dir, "docfx_ai.csv"), docfx_rows,
              ["repo", "path", "where", "key", "glob", "value"])
    with open(os.path.join(a.out_dir, "census.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "summary": summary}, fh, indent=1)
    text = report(meta, summary, rows)
    with open(os.path.join(a.out_dir, "LEARNLABELS_AUTO.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
