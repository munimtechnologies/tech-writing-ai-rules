#!/usr/bin/env python3
# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""Run the docs-ai-label-check skill's checker over the Markdown of a few public Microsoft
Learn docs repos (shallow, sparse, Markdown and docfx.json only) and write a per-repo summary
and a list of findings. A tool check, not a pre-registered study: it tests the checker on real
repos and compares its counts with study 7 (2026-11-09). No article text is written out.

Usage: python labelcheck_repos.py --out-dir /out [--work /tmp/lc]
"""

import argparse
import csv
import datetime
import importlib.util
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKER = os.path.join(HERE, "skills", "docs-ai-label-check", "scripts", "ai_label_check.py")

# (repo, sparse patterns). Whole-repo scans read every *.md and docfx.json.
ALL_MD = ["*.md", "docfx.json"]
REPOS = [
    ("MicrosoftDocs/azure-docs", ["/articles/sre-agent/**/*.md", "/articles/container-apps/**/*.md",
                                  "/docfx.json", "/articles/docfx.json"]),
    ("MicrosoftDocs/fabric-docs", ALL_MD),
    ("MicrosoftDocs/SupportArticles-docs", ALL_MD),
    ("MicrosoftDocs/dynamics-365-customer-engagement", ALL_MD),
    ("MicrosoftDocs/visualstudio-docs", ALL_MD),
    ("MicrosoftDocs/entra-docs", ALL_MD),
    ("dotnet/docs", ALL_MD),
    ("dotnet/AspNetCore.Docs", ALL_MD),
    ("MicrosoftDocs/PowerShell-Docs", ALL_MD),
]
CODES = ["variant-key", "bad-value", "empty-value", "other-value", "duplicate-key", "nested",
         "commented", "stray-token", "include-label"]
REPO_COLUMNS = (["repo", "scope", "status", "commit", "markdown", "with_front_matter",
                 "ai_assisted", "ai_generated"] + [c.replace("-", "_") for c in CODES] +
                ["variant_keys"])
FINDING_COLUMNS = ["repo", "path", "line", "severity", "code", "key", "value", "fixable"]


def load_checker(path=CHECKER):
    spec = importlib.util.spec_from_file_location("ai_label_check", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(args, cwd=None, timeout=1800):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True,
                          timeout=timeout)


def sparse_clone(repo, patterns, dest):
    """Shallow, blob-less clone that checks out only the files matching the patterns."""
    url = "https://github.com/%s.git" % repo
    r = git(["clone", "--depth", "1", "--filter=blob:none", "--no-checkout", "--quiet", url, dest])
    if r.returncode != 0:
        return "clone-failed: " + (r.stderr or "").strip()[-200:], ""
    r = git(["sparse-checkout", "set", "--no-cone"] + patterns, cwd=dest)
    if r.returncode != 0:
        return "sparse-failed: " + (r.stderr or "").strip()[-200:], ""
    r = git(["checkout", "--quiet"], cwd=dest, timeout=3600)
    if r.returncode != 0:
        return "checkout-failed: " + (r.stderr or "").strip()[-200:], ""
    head = git(["rev-parse", "HEAD"], cwd=dest).stdout.strip()
    return "ok", head


def summarise(repo, scope, status, commit, rep):
    row = {"repo": repo, "scope": scope, "status": status, "commit": commit}
    if rep is None:
        return row
    row.update({"markdown": rep["markdown"], "with_front_matter": rep["with_front_matter"],
                "ai_assisted": rep["labelled"]["ai-assisted"],
                "ai_generated": rep["labelled"]["ai-generated"]})
    for c in CODES:
        row[c.replace("-", "_")] = rep["counts"].get(c, 0)
    keys = {}
    for f in rep["findings"]:
        if f["code"] in ("variant-key", "duplicate-key", "nested", "commented"):
            keys[f["key"]] = keys.get(f["key"], 0) + 1
    row["variant_keys"] = ";".join("%s=%d" % kv for kv in sorted(keys.items()))
    return row


def finding_rows(repo, rep):
    rows = []
    for f in rep["findings"]:
        rows.append({"repo": repo, "path": f["path"].lstrip("./"), "line": f["line"],
                     "severity": f["severity"], "code": f["code"], "key": f["key"][:40],
                     "value": (f["value"] or "")[:40], "fixable": "yes" if f.get("fix") else ""})
    return rows


def write_csv(path, rows, columns):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def report_md(meta, rows):
    lines = ["# docs-ai-label-check on %d Learn docs repos (tool check)" % len(rows), "",
             "Read %s to %s UTC by ai_label_check.py %s. Shallow sparse clones (Markdown and "
             "docfx.json only). Not a pre-registered study." % (meta["started"], meta["finished"],
                                                                 meta["checker_version"]), "",
             "| Repo | Scope | Status | Markdown | ai-assisted | ai-generated | variant-key | "
             "bad-value | nested | commented | stray-token | Variant keys |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["repo"], r["scope"], r["status"].split(":")[0], r.get("markdown", ""),
            r.get("ai_assisted", ""), r.get("ai_generated", ""), r.get("variant_key", ""),
            r.get("bad_value", ""), r.get("nested", ""), r.get("commented", ""),
            r.get("stray_token", ""), r.get("variant_keys", "")))
    lines += ["", "Study 7 (2026-11-09, 30 largest MicrosoftDocs repos) counted 122 `ms.ai-usage` "
              "(about 114 in Azure SRE Agent's docs) and 47 `ai.usage` (mostly support articles), "
              "and 23 labels outside a top-level key.", ""]
    return "\n".join(lines)


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--work", default="/tmp/labelcheck")
    ap.add_argument("--only", default="", help="comma-separated repos (default: all)")
    args = ap.parse_args(argv)
    lc = load_checker()
    os.makedirs(args.out_dir, exist_ok=True)
    os.makedirs(args.work, exist_ok=True)
    only = [s for s in args.only.split(",") if s]
    meta = {"started": utcnow(), "checker_version": lc.VERSION, "repos": []}
    rows, frows = [], []
    for repo, patterns in REPOS:
        if only and repo not in only:
            continue
        scope = "all" if patterns == ALL_MD else ",".join(p.strip("/").split("/**")[0]
                                                         for p in patterns if p.endswith(".md"))
        dest = os.path.join(args.work, repo.replace("/", "__"))
        shutil.rmtree(dest, ignore_errors=True)
        t0 = utcnow()
        try:
            status, commit = sparse_clone(repo, patterns, dest)
        except subprocess.TimeoutExpired:
            status, commit = "timeout", ""
        rep = None
        if status == "ok":
            cwd = os.getcwd()
            os.chdir(dest)
            try:
                rep = lc.scan(["."])
            finally:
                os.chdir(cwd)
            frows.extend(finding_rows(repo, rep))
        rows.append(summarise(repo, scope, status, commit, rep))
        meta["repos"].append({"repo": repo, "status": status, "commit": commit, "started": t0,
                              "finished": utcnow()})
        print("%s: %s %s" % (repo, status, json.dumps(rows[-1])), flush=True)
        shutil.rmtree(dest, ignore_errors=True)
    meta["finished"] = utcnow()
    write_csv(os.path.join(args.out_dir, "repos.csv"), rows, REPO_COLUMNS)
    write_csv(os.path.join(args.out_dir, "findings.csv"), frows, FINDING_COLUMNS)
    with open(os.path.join(args.out_dir, "labelcheck.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "repos": rows}, fh, indent=1)
    with open(os.path.join(args.out_dir, "LABELCHECK_AUTO.md"), "w", encoding="utf-8") as fh:
        fh.write(report_md(meta, rows))
    ok = sum(1 for r in rows if r["status"] == "ok")
    print("done: %d of %d repos read" % (ok, len(rows)))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
