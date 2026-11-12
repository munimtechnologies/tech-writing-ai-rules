#!/usr/bin/env python3
# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""Run hugo_layout_check.py on a few public Hugo docs repos (a tool check, not a study).

For each repo it makes a shallow, blob-filtered, sparse clone with only the
layouts folder, the config files and the content files' Markdown, HTML and
content-adapter sources checked out, runs the checker unchanged, and writes:

  repos.csv          one row per repo: commit, templates read, Markdown templates, counts
  findings.csv       one row per finding: repo, code, severity, layout, templates, uses
  <owner>__<repo>.json   the checker's full report
  HUGOLAYOUT_AUTO.md a short summary

    python hugolayout_repos.py --out-dir out --work /tmp/hugolayout
    python hugolayout_repos.py --out-dir out --work /tmp/hl --repo docker/docs
"""

import argparse
import csv
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time

VERSION = "0.1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
CHECKER = os.path.join(HERE, "skills", "hugo-md-layout-check", "scripts", "hugo_layout_check.py")

REPOS = ["docker/docs", "open-telemetry/opentelemetry.io"]
SPARSE = ["/layouts/", "/config/", "/hugo.yaml", "/hugo.yml", "/hugo.toml", "/hugo.json",
          "/config.yaml", "/config.yml", "/config.toml", "/config.json",
          "/content/**/*.md", "/content/**/*.markdown", "/content/**/*.html",
          "/content/**/*.gotmpl"]


def load_checker():
    spec = importlib.util.spec_from_file_location("hugo_layout_check", CHECKER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(args, cwd=None, timeout=1800):
    return subprocess.run(["git"] + args, cwd=cwd, check=True, capture_output=True,
                          text=True, timeout=timeout).stdout.strip()


def clone(repo, dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    git(["clone", "--depth", "1", "--filter=blob:none", "--no-checkout",
         "https://github.com/%s.git" % repo, dest])
    git(["sparse-checkout", "set", "--no-cone"] + SPARSE, cwd=dest)
    git(["checkout"], cwd=dest)
    return git(["rev-parse", "HEAD"], cwd=dest)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--repo", action="append", help="owner/name (repeatable); default: the built-in list")
    args = ap.parse_args(argv)
    hl = load_checker()
    os.makedirs(args.out_dir, exist_ok=True)
    os.makedirs(args.work, exist_ok=True)
    repos = args.repo or REPOS
    rows, frows = [], []
    for repo in repos:
        slug = repo.replace("/", "__")
        dest = os.path.join(args.work, slug)
        started = time.time()
        row = {"repo": repo, "commit": "", "status": "", "templates": "", "markdown_templates": "",
               "errors": "", "warnings": "", "info": "", "seconds": ""}
        try:
            row["commit"] = clone(repo, dest)
            if not os.path.isdir(os.path.join(dest, "layouts")):
                row["status"] = "no-layouts"
            else:
                report = hl.check_project(dest)
                report["repo"] = repo
                report["commit"] = row["commit"]
                report["root"] = repo
                with open(os.path.join(args.out_dir, slug + ".json"), "w", encoding="utf-8") as fh:
                    json.dump(report, fh, indent=2, ensure_ascii=False)
                row.update(status="ok", templates=report["templates"],
                           markdown_templates=len(report["markdown_templates"]),
                           errors=report["counts"]["error"], warnings=report["counts"]["warning"],
                           info=report["counts"]["info"])
                for f in report["findings"]:
                    frows.append({
                        "repo": repo, "commit": row["commit"], "code": f["code"],
                        "severity": f["severity"], "layout": f["layout"] or "",
                        "templates": ";".join(f["templates"]), "uses": len(f["uses"]),
                        "first_uses": ";".join("%s (%s)" % (u["file"], u["how"]) for u in f["uses"][:3]),
                        "strong": ";".join(f["signals"].get("strong", [])) if f["signals"] else "",
                        "weak": ";".join(f["signals"].get("weak", [])) if f["signals"] else "",
                    })
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
            row["status"] = "error: %s" % str(exc)[:200]
        row["seconds"] = round(time.time() - started, 1)
        rows.append(row)
        shutil.rmtree(dest, ignore_errors=True)
        print("%s: %s" % (repo, row["status"]), flush=True)
    with open(os.path.join(args.out_dir, "repos.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["repo"])
        w.writeheader()
        w.writerows(rows)
    fields = ["repo", "commit", "code", "severity", "layout", "templates", "uses", "first_uses",
              "strong", "weak"]
    with open(os.path.join(args.out_dir, "findings.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(frows)
    lines = ["# hugo_layout_check %s on public Hugo docs repos (runner %s)" % (hl.VERSION, VERSION), "",
             "| Repo | Commit | Status | Templates | Markdown templates | Errors | Warnings | Info |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["repo"], r["commit"][:12], r["status"], r["templates"], r["markdown_templates"],
            r["errors"], r["warnings"], r["info"]))
    lines += ["", "| Repo | Severity | Code | Layout | Uses | Strong signals |", "|---|---|---|---|---|---|"]
    for f in frows:
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            f["repo"], f["severity"], f["code"], f["layout"], f["uses"], f["strong"]))
    with open(os.path.join(args.out_dir, "HUGOLAYOUT_AUTO.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return 0 if all(r["status"] in ("ok", "no-layouts") for r in rows) else 3


if __name__ == "__main__":
    sys.exit(main())
