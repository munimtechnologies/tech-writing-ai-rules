#!/usr/bin/env python3
# Copyright 2026 Munim, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
"""includereach 0.1.0: do AI labels in include files reach the readers of the articles that use them?

Study 13 of tech-writing-ai-rules. Microsoft Learn articles pull shared text in from include
files (`[!INCLUDE [title](path)]`). Some include files carry their own AI-use label
(`ai-usage: ai-assisted` / `ai-generated`); the 2026-11-11 label check counted 262 of them in
four repos. Learn shows its end-of-article AI note per article (study 8). This tool asks whether
an article that pulls in an AI-labelled include, but carries no AI label of its own, tells its
readers anything about AI.

1. Shallow, sparse clones (Markdown and docfx.json only, learnlabels.git_clone) of the four
   repos. Every Markdown file's front matter is read (learnlabels.describe_file) and every
   INCLUDE reference is resolved to a repo path (relative to the including file; `~/` from the
   nearest docfx.json folder; nested includes followed).
2. Hosts: articles that reach at least one AI-labelled include file. H0 = the article has no
   AI key at all; H1 = the article itself has `ai-usage: ai-assisted` or `ai-generated`.
   Hosts with another AI key are counted but not sampled.
3. A seeded draw of up to PER_H0 H0 and PER_H1 H1 hosts per repo. Each is found on Learn and
   read as Markdown, as served HTML and rendered in headless Chromium, with learnshown 0.2.0's
   check_page (unchanged), plus learnshown's positive control.

Usage: python includereach.py --out-dir OUT [--render] [--wait-prereg-minutes 240] [--no-prereg-check]

Outputs: hosts.csv (every host: paths, keys and values only), pages.csv (the sample, live
columns), includereach.json, INCLUDEREACH_AUTO.md. No article text is kept except the matched
AI note sentence (at most 200 characters). Standard library, git, learnlabels.py 0.1.0 and
learnshown.py 0.2.0 (Playwright for --render). Apache-2.0.
Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""

import argparse
import collections
import csv
import datetime
import json
import os
import posixpath
import random
import re
import shutil
import sys
import tempfile
import time

import learnlabels as ll
import learnshown as ls

VERSION = "0.1.0"
PREREG_PATH = "census/2026-11-ms-learn-include-labels/PREREG.md"
REPOS = ("MicrosoftDocs/fabric-docs", "dotnet/AspNetCore.Docs", "MicrosoftDocs/entra-docs", "dotnet/docs")
BRANCH = "main"
PER_H0 = 15
PER_H1 = 5
MAX_DEPTH = 6
LABELS = ("ai-assisted", "ai-generated")
MIN_P = {"P1": 20, "P2": 8, "P3": 20}

INCLUDE_RE = re.compile(r"\[!INCLUDE\s*\[[^\]\n]*\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'][^\"'\n]*[\"'])?\s*\)\s*\]", re.I)

HOST_COLUMNS = ["repo", "path", "group", "own_key", "own_value", "labelled_includes", "first_include",
                "include_values", "depth"]
PAGE_COLUMNS = ["repo", "path", "group", "own_key", "own_value", "labelled_includes", "first_include",
                "url", "url_rule", "tried", "final_url", "mapped", "md_status", "md_served", "md_ai_key",
                "md_ai_value", "html_status", "html_ai_key", "html_ai_value", "note_html", "note_html_text",
                "render_status", "note_rendered", "note_rendered_text", "note_md", "note_md_text"]


# ---------------------------------------------------------------- include references

def include_targets(text):
    """Raw targets of every INCLUDE reference in a Markdown text, in order, without repeats."""
    out = []
    for m in INCLUDE_RE.finditer(text or ""):
        t = m.group(1).strip()
        if t not in out:
            out.append(t)
    return out


def docset_root(path, docfx_dirs):
    """The deepest folder holding a docfx.json that contains `path` ('' for the repo root)."""
    best = None
    for d in docfx_dirs:
        if d == "" or path.startswith(d + "/"):
            if best is None or len(d) > len(best):
                best = d
    return best or ""


def resolve(src_path, target, docfx_dirs=()):
    """Repo-relative path that `target` (as written in `src_path`) points to, or '' if it leaves
    the repo or is a web address. Anchors and queries are dropped."""
    t = (target or "").strip().replace("\\", "/")
    t = t.split("#")[0].split("?")[0]
    if not t or "://" in t or t.lower().startswith("mailto:"):
        return ""
    if t.startswith("~/"):
        base = docset_root(src_path, docfx_dirs)
        joined = posixpath.join(base, t[2:]) if base else t[2:]
    elif t.startswith("/"):
        joined = t.lstrip("/")
    else:
        joined = posixpath.join(posixpath.dirname(src_path), t)
    norm = posixpath.normpath(joined)
    if norm.startswith("..") or norm in (".", ""):
        return ""
    return norm


def build_graph(texts, docfx_dirs=()):
    """{path: [resolved include paths]} for every file in `texts` ({path: text}). Targets that
    differ only in case from a known file are matched to it."""
    lower = {p.lower(): p for p in texts}
    graph = {}
    for p, text in texts.items():
        out = []
        for t in include_targets(text):
            r = resolve(p, t, docfx_dirs)
            if not r:
                continue
            r = r if r in texts else lower.get(r.lower(), r)
            if r != p and r not in out:
                out.append(r)
        graph[p] = out
    return graph


def reached(start, graph, max_depth=MAX_DEPTH):
    """{include path: depth} for every file reachable from `start` through INCLUDE references
    (depth 1 = included directly). Cycles are cut; depth is the shortest chain."""
    seen = {}
    frontier = [start]
    for depth in range(1, max_depth + 1):
        nxt = []
        for p in frontier:
            for q in graph.get(p, ()):
                if q != start and q not in seen:
                    seen[q] = depth
                    nxt.append(q)
        frontier = nxt
        if not frontier:
            break
    return seen


def find_hosts(repo, files, graph):
    """Host rows for every article that reaches an AI-labelled include file.
    `files` = learnlabels.describe_file dicts. group: H0 (no AI key), H1 (ai-usage with an AI
    value), HX (another AI key or value)."""
    labelled = {f["path"]: f["category"] for f in files if f.get("include") and f.get("category") in LABELS}
    hosts = []
    for f in files:
        if not f.get("is_article"):
            continue
        r = reached(f["path"], graph)
        hits = sorted((d, p) for p, d in r.items() if p in labelled)
        if not hits:
            continue
        cat = f.get("category") or ""
        if cat == "":
            group = "H0"
        elif f.get("ai_key") == "ai-usage" and cat in LABELS:
            group = "H1"
        else:
            group = "HX"
        values = collections.Counter(labelled[p] for _d, p in hits)
        hosts.append({"repo": repo, "path": f["path"], "group": group, "own_key": f.get("ai_key", ""),
                      "own_value": f.get("ai_value", ""), "labelled_includes": len(hits),
                      "first_include": hits[0][1], "depth": hits[0][0],
                      "include_values": ";".join("%s=%d" % kv for kv in sorted(values.items())),
                      "_title": ""})
    return hosts


def labelled_used(files, graph):
    """(AI-labelled include paths, the subset reached from at least one article)."""
    labelled = sorted(f["path"] for f in files if f.get("include") and f.get("category") in LABELS)
    lset = set(labelled)
    used = set()
    for f in files:
        if f.get("is_article"):
            used.update(p for p in reached(f["path"], graph) if p in lset)
    return labelled, used


def draw_hosts(hosts, repo, per_h0=PER_H0, per_h1=PER_H1):
    """Seeded draw of up to per_h0 H0 and per_h1 H1 hosts of one repo, in path order."""
    picked = []
    for group, per in (("H0", per_h0), ("H1", per_h1)):
        pool = sorted((h for h in hosts if h["repo"] == repo and h["group"] == group), key=lambda h: h["path"])
        if len(pool) > per:
            pool = random.Random("study13|%s|%s" % (repo, group)).sample(pool, per)
        picked.extend(sorted(pool, key=lambda h: h["path"]))
    return picked


# ---------------------------------------------------------------- one repo

def read_repo(root, read_text=None):
    """(files, texts, docfx_dirs, titles) for a cloned repo: describe_file dicts for every
    Markdown file, {path: its INCLUDE references only} (to keep memory small), the folders
    holding a docfx.json, and {path: front matter title}."""
    read_text = read_text or ls.read_text
    files, texts, docfx_dirs, titles = [], {}, [], {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        rel_dir = ll.norm_path(os.path.relpath(dirpath, root))
        rel_dir = "" if rel_dir == "." else rel_dir
        for name in sorted(filenames):
            low = name.lower()
            if low == "docfx.json":
                docfx_dirs.append(rel_dir)
            if not low.endswith(".md"):
                continue
            rel = posixpath.join(rel_dir, name) if rel_dir else name
            try:
                text = read_text(os.path.join(dirpath, name))
            except OSError:
                continue
            texts[rel] = "\n".join(m.group(0) for m in INCLUDE_RE.finditer(text))
            head = text[:ll.HEAD_BYTES]
            files.append(ll.describe_file(rel, head))
            fm = ll.front_matter(head)
            titles[rel] = ll.parse_fields(fm).get("title", "") if fm is not None else ""
    return files, texts, docfx_dirs, titles


# ---------------------------------------------------------------- summary and predictions

def pct(k, n):
    return round(100.0 * k / n, 2) if n else None


def summarise(hosts, pages, controls, repo_rows, note_field="note_rendered"):
    nf = note_field
    ok = [p for p in pages if p.get("mapped") == "yes" and p.get("html_status") == 200]
    if nf == "note_rendered":
        ok = [p for p in ok if p.get("render_status") == 200]
    h0 = [p for p in ok if p["group"] == "H0"]
    h1 = [p for p in ok if p["group"] == "H1"]
    h0md = [p for p in ok if p["group"] == "H0" and p.get("md_served")]
    pos = [c for c in controls if c.get("stratum") == "control-positive"]
    g1 = bool(pos) and bool(pos[0].get(nf))
    g2 = len(h0) >= MIN_P["P1"]

    def grade(name, k, n, holds, needs=True):
        graded = needs and n >= MIN_P[name]
        return {"k": k, "n": n, "value_pct": pct(k, n), "held": holds(k, n) if graded else None}

    preds = collections.OrderedDict()
    k = sum(1 for p in h0 if p.get(nf))
    preds["P1"] = grade("P1", k, len(h0), lambda k, n: 100 * k <= 5 * n, needs=g1)
    k = sum(1 for p in h1 if p.get(nf))
    preds["P2"] = grade("P2", k, len(h1), lambda k, n: 100 * k >= 90 * n, needs=g1)
    k = sum(1 for p in h0md if p.get("md_ai_key"))
    preds["P3"] = grade("P3", k, len(h0md), lambda k, n: 100 * k <= 5 * n)

    by_repo = collections.OrderedDict()
    for r in repo_rows:
        name = r["repo"]
        hs = [h for h in hosts if h["repo"] == name]
        by_repo[name] = {"status": r.get("status"), "commit": r.get("commit", ""),
                         "markdown": r.get("markdown", 0), "articles": r.get("articles", 0),
                         "labelled_includes": r.get("labelled_includes", 0),
                         "labelled_includes_used": r.get("labelled_includes_used", 0),
                         "hosts": len(hs), "H0": sum(1 for h in hs if h["group"] == "H0"),
                         "H1": sum(1 for h in hs if h["group"] == "H1"),
                         "HX": sum(1 for h in hs if h["group"] == "HX"),
                         "sampled": sum(1 for p in pages if p["repo"] == name),
                         "counted": sum(1 for p in ok if p["repo"] == name),
                         "H0_note": sum(1 for p in h0 if p["repo"] == name and p.get(nf)),
                         "H1_note": sum(1 for p in h1 if p["repo"] == name and p.get(nf))}
    status = collections.Counter(p.get("mapped") for p in pages)
    notes = collections.Counter(p.get(nf + "_text") for p in ok if p.get(nf))
    return collections.OrderedDict([
        ("note_measure", nf), ("hosts", len(hosts)),
        ("hosts_by_group", dict(collections.Counter(h["group"] for h in hosts))),
        ("pages_sampled", len(pages)), ("mapped_status", dict(status)), ("counted", len(ok)),
        ("H0_counted", len(h0)), ("H1_counted", len(h1)), ("H0_md_served", len(h0md)),
        ("by_repo", by_repo), ("note_texts", dict(notes.most_common(10))),
        ("controls", [{k2: c.get(k2) for k2 in ("stratum", "url", "html_status", "mapped", "render_status",
                                                 "note_rendered", "note_rendered_text", "note_html", "md_ai_key")}
                      for c in controls]),
        ("gates", {"G1": {"positive_control_note": g1, "passed": g1},
                   "G2": {"H0_counted": len(h0), "needed": MIN_P["P1"], "passed": g2}}),
        ("predictions", preds),
    ])


def report(meta, s):
    yn = {True: "yes", False: "no", None: "n/a"}
    out = ["# includereach %s: do AI labels in include files reach readers? (automatic report)" % VERSION, "",
           "First pass written by the tool. The graded result is in RESULT.md.", "",
           "- Started %s, finished %s." % (meta["started"], meta.get("finished")),
           "- Pre-registration first committed: %s." % (
               meta["prereg"].get("committed_at") or "not found (%s)" % meta["prereg"].get("error")),
           "- Note measure: %s. Hosts found: %d (%s). Pages sampled: %d; counted: %d (H0 %d, H1 %d)." % (
               s["note_measure"], s["hosts"], ", ".join("%s %d" % kv for kv in sorted(s["hosts_by_group"].items())),
               s["pages_sampled"], s["counted"], s["H0_counted"], s["H1_counted"]),
           "- Gates: G1 %s, G2 %s." % (yn[s["gates"]["G1"]["passed"]], yn[s["gates"]["G2"]["passed"]]),
           "", "## Predictions (automatic; boundaries as pre-registered)", "", "| | k | n | % | held |",
           "|---|---|---|---|---|"]
    for k, p in s["predictions"].items():
        out.append("| %s | %d | %d | %s | %s |" % (k, p["k"], p["n"], p["value_pct"], yn[p["held"]]))
    out += ["", "## By repo", "",
            "| repo | status | Markdown | articles | labelled includes | used by an article | hosts | H0 | H1 | HX | "
            "sampled | counted | H0 with note | H1 with note |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, v in s["by_repo"].items():
        out.append("| %s | %s | %s | %s | %s | %s | %d | %d | %d | %d | %d | %d | %d | %d |" % (
            name, v["status"], v["markdown"], v["articles"], v["labelled_includes"], v["labelled_includes_used"],
            v["hosts"], v["H0"], v["H1"], v["HX"], v["sampled"], v["counted"], v["H0_note"], v["H1_note"]))
    out += ["", "## Note sentences seen", ""]
    out += ["- %d x \"%s\"" % (n, t) for t, n in s["note_texts"].items()] or ["- none"]
    out += ["", "## Controls", ""] + ["- %s" % json.dumps(c) for c in s["controls"]]
    return "\n".join(out) + "\n"


def write_csv(path, rows, columns):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in columns})


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv=None, opener=None, cloner=None, fetch=None, sleep=time.sleep, renderer=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--prereg-path", default=PREREG_PATH)
    ap.add_argument("--no-prereg-check", action="store_true")
    ap.add_argument("--wait-prereg-minutes", type=float, default=0)
    ap.add_argument("--repos", default=",".join(REPOS))
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    meta = {"version": VERSION, "learnlabels_version": ll.VERSION, "learnshown_version": ls.VERSION,
            "started": utcnow(), "settings": {"per_h0": PER_H0, "per_h1": PER_H1, "render": a.render,
                                               "max_depth": MAX_DEPTH}}

    def dump(obj):
        with open(os.path.join(a.out_dir, "includereach.json"), "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=1, default=str)

    if a.no_prereg_check:
        meta["prereg"] = {"committed_at": None, "error": "not checked"}
    else:
        meta["prereg"] = ll.wait_for_prereg(a.prereg_path, a.wait_prereg_minutes, opener, sleep)
        if a.wait_prereg_minutes > 0 and meta["prereg"].get("committed_at") is None:
            print("pre-registration %s not found; nothing was read" % a.prereg_path)
            dump(meta)
            return 3

    render = close = None
    if a.render:
        try:
            render, close = (renderer or ls.make_renderer)()
        except Exception as exc:
            meta["error"] = "renderer: %s: %s" % (type(exc).__name__, exc)
            print("cannot start the renderer (%s); nothing was read" % meta["error"])
            dump(meta)
            return 5
    note_field = "note_rendered" if render else "note_html"

    cloner = cloner or ll.git_clone
    fetch = fetch or ls.default_fetch
    work = tempfile.mkdtemp(prefix="includereach-")
    repo_rows, hosts, pages = [], [], []
    for repo in [r for r in a.repos.split(",") if r]:
        dest = os.path.join(work, repo.replace("/", "__"))
        err, commit = cloner(repo, BRANCH, dest)
        row = {"repo": repo, "status": err or "read", "commit": commit}
        if not err:
            files, texts, docfx_dirs, titles = read_repo(dest)
            graph = build_graph(texts, docfx_dirs)
            maps = ls.find_docfx(dest)
            hs = find_hosts(repo, files, graph)
            labelled, used = labelled_used(files, graph)
            row.update(markdown=len(files), articles=sum(1 for f in files if f.get("is_article")),
                       labelled_includes=len(labelled), labelled_includes_used=len(used))
            picked = draw_hosts(hs, repo)
            for p in picked:
                p["_cands"] = ls.candidate_urls(p["path"], maps)
                p["url"] = p["_cands"][0][1] if p["_cands"] else ""
                p["_title"] = titles.get(p["path"], "")
            hosts.extend(hs)
            pages.extend(picked)
            print("%s: %d Markdown, %d labelled includes (%d used), %d hosts, %d sampled" % (
                repo, len(files), len(labelled), len(used), len(hs), len(picked)), flush=True)
        else:
            print("%s: %s" % (repo, err), flush=True)
        repo_rows.append(row)
        shutil.rmtree(dest, ignore_errors=True)
    shutil.rmtree(work, ignore_errors=True)

    allowed, meta["robots_status"] = ls.robots_ok(fetch)
    controls = []
    for name, repo, path, url in ls.CONTROLS[:1]:
        controls.append(ls.check_page({"repo": repo, "path": path, "stratum": name, "url": url},
                                      fetch, sleep, allowed, render))
    for i, p in enumerate(pages, 1):
        ls.check_page(p, fetch, sleep, allowed, render)
        if i % 10 == 0:
            print("checked %d of %d pages" % (i, len(pages)), flush=True)
    if close:
        close()

    summary = summarise(hosts, pages, controls, repo_rows, note_field)
    meta["finished"] = utcnow()
    write_csv(os.path.join(a.out_dir, "hosts.csv"), hosts, HOST_COLUMNS)
    write_csv(os.path.join(a.out_dir, "pages.csv"), pages, PAGE_COLUMNS)
    dump({"meta": meta, "repos": repo_rows, "summary": summary})
    text = report(meta, summary)
    with open(os.path.join(a.out_dir, "INCLUDEREACH_AUTO.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    print(text)
    return 0 if any(r["status"] == "read" for r in repo_rows) else 4


if __name__ == "__main__":
    sys.exit(main())
