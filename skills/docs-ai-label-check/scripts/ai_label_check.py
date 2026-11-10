#!/usr/bin/env python3
# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""docs-ai-label-check: find AI-usage labels in Microsoft Learn style (DocFX) Markdown front
matter that readers may never see.

Microsoft's Learn-wide Copilot instructions (shipped in public docs repos, for example
MicrosoftDocs/entra-docs/.github/copilot-instructions.md) ask for a top-level front matter
entry `ai-usage: ai-assisted` or `ai-usage: ai-generated`, and Microsoft's principles for
AI-generated content promise readers a note at the end of every such article. Study 8 of
github.com/munimtechnologies/tech-writing-ai-rules (2026-11-10) found that the note was shown
on 131 of 131 sampled pages labelled `ai-usage`, and on 0 of 33 pages labelled `ms.ai-usage`
or `ai.usage`. This script finds such variant keys, labels that YAML never reads (nested or
commented out), odd values, and, with --require, articles with no label at all.

Python 3 standard library only. No network unless --url is given.

Exit codes: 0 no error or warning, 1 at least one error or warning, 2 usage error.
"""

import argparse
import json
import os
import re
import sys
import urllib.request

VERSION = "0.1.0"
CANONICAL_KEY = "ai-usage"
VALUES = ("ai-assisted", "ai-generated")
# Spellings that study 8 checked on rendered Learn pages (0 of 33 showed the note).
OBSERVED_VARIANTS = ("ms.ai-usage", "ai.usage")
STUDY8 = ("https://github.com/munimtechnologies/tech-writing-ai-rules/blob/main/census/"
          "2026-11-ms-learn-ai-shown/RESULT.md")
USER_AGENT = ("docs-ai-label-check/%s (+https://github.com/munimtechnologies/"
              "tech-writing-ai-rules; mv2@munimtech.com)" % VERSION)

KEY_PAT = r"(?:ms[._-]?)?ai[-_. ]?usage"
AI_KEY_RE = re.compile(r"^%s$" % KEY_PAT, re.I)
KV_RE = re.compile(r"^([A-Za-z0-9_.\-]+)[ \t]*:(?:[ \t]+(.*?))?[ \t]*$")
NESTED_RE = re.compile(r"^[ \t]*(?:-[ \t]+)?[\"']?(%s)[\"']?[ \t]*:[ \t]*(.*?)[ \t]*$" % KEY_PAT,
                       re.I)
COMMENT_RE = re.compile(r"^[ \t]*#+[ \t]*(?:-[ \t]+)?(%s)[ \t]*:[ \t]*(.*?)[ \t]*$" % KEY_PAT,
                        re.I)
TOKEN_RE = re.compile(r"(?<![a-z0-9])ai[-_](?:generated|assisted)(?![a-z0-9])", re.I)
TEXT_KEYS = {"title", "description", "summary", "keywords", "titlesuffix"}
MD_EXT = (".md", ".markdown")
SKIP_DIRS = {".git", "node_modules", "_site", "obj", "bin", ".vs", "_themes", ".github"}
INCLUDE_DIRS = {"includes", "include", "_includes"}
SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}


# ---------------------------------------------------------------- helpers

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


def norm_value(val):
    """Lower-case a value and turn spaces/underscores into hyphens ('AI Assisted' -> 'ai-assisted')."""
    return re.sub(r"[\s_]+", "-", unquote(val).strip().lower())


def front_matter_span(lines):
    """(start, end) indexes of the lines strictly inside a leading '---' block, or None.
    `lines` keep their line endings."""
    if not lines:
        return None
    first = lines[0].lstrip("﻿").strip()
    if first != "---":
        return None
    for i in range(1, min(len(lines), 600)):
        if lines[i].strip() in ("---", "..."):
            return 1, i
    return None


def is_include(relpath):
    parts = relpath.replace("\\", "/").lower().split("/")
    return any(p in INCLUDE_DIRS for p in parts[:-1])


def finding(path, line, severity, code, key, value, message, fix=None):
    return {"path": path, "line": line, "severity": severity, "code": code, "key": key,
            "value": value, "message": message, "fix": fix}


def variant_message(key):
    if key in OBSERVED_VARIANTS:
        return ("key '%s' is not the documented 'ai-usage'; in study 8 (2026-11-10) 0 of 33 "
                "Learn pages labelled ms.ai-usage or ai.usage showed readers the AI note, while "
                "131 of 131 labelled ai-usage did" % key)
    return ("key '%s' is not the documented 'ai-usage' (Learn metadata keys are case-sensitive); "
            "this spelling was not tested, but ms.ai-usage and ai.usage showed no note" % key)


def value_check(path, line, key, raw):
    """Findings for the value of an AI key."""
    val = unquote(raw)
    if val in VALUES:
        return []
    norm = norm_value(raw)
    if norm in VALUES:
        return [finding(path, line, "error", "bad-value", key, val,
                        "value '%s' is not written exactly '%s' (values are matched as written; "
                        "not tested on Learn)" % (val, norm), fix=norm)]
    if not val:
        return [finding(path, line, "warning", "empty-value", key, val,
                        "AI key with an empty value: write ai-assisted or ai-generated, or remove "
                        "the key if no AI was used")]
    if "ai" in re.split(r"[^a-z]+", val.lower()):
        return [finding(path, line, "warning", "bad-value", key, val,
                        "value '%s' is neither ai-assisted nor ai-generated" % val)]
    return [finding(path, line, "info", "other-value", key, val,
                    "value '%s' is not one of Microsoft's two AI values; no AI note is expected "
                    "for it" % val)]


# ---------------------------------------------------------------- one Markdown text

def check_text(relpath, text, require=False):
    """Check one Markdown file's front matter. Returns (summary, findings).
    summary = {'front_matter': bool, 'label': 'ai-assisted'|'ai-generated'|'' (canonical, valid),
               'include': bool}"""
    lines = text.splitlines(True)
    span = front_matter_span(lines)
    include = is_include(relpath)
    summary = {"front_matter": span is not None, "label": "", "include": include}
    out = []
    if span is None:
        if require and not include:
            out.append(finding(relpath, 1, "error", "missing", "", "",
                               "no YAML front matter, so no ai-usage label"))
        return summary, out
    start, end = span
    top_keys = []          # (line_no, key, raw_value) for top-level AI keys
    stray = []             # (line_no, key, token) on other front matter lines
    current = ""           # the top-level key the following indented lines belong to
    for i in range(start, end):
        line = lines[i].rstrip("\r\n")
        lno = i + 1
        if not line.strip():
            continue
        if line[0] not in " \t#-":
            m = KV_RE.match(line)
            if not m:
                current = ""
                continue
            key, raw = m.group(1), m.group(2) or ""
            current = key
            if AI_KEY_RE.match(key):
                top_keys.append((lno, key, raw))
            elif key.lower() not in TEXT_KEYS:
                for t in TOKEN_RE.findall(raw):
                    stray.append((lno, key, t))
            continue
        cm = COMMENT_RE.match(line)
        if cm:
            out.append(finding(relpath, lno, "warning", "commented", cm.group(1), unquote(cm.group(2)),
                               "AI label inside a YAML comment: YAML ignores it, so the page "
                               "carries no label. Uncomment it as a top-level 'ai-usage:' line "
                               "if it is meant"))
            continue
        nm = NESTED_RE.match(line)
        if nm:
            out.append(finding(relpath, lno, "warning", "nested", nm.group(1), unquote(nm.group(2)),
                               "AI label is not a top-level key (indented or a list item, for "
                               "example under ms.custom), so it is not the 'ai-usage' entry "
                               "Microsoft's instructions ask for. Move it to the top level if it "
                               "is meant"))
            continue
        if line.lstrip().startswith("#") or current.lower() in TEXT_KEYS:
            continue
        for t in TOKEN_RE.findall(line):
            stray.append((lno, current, t))

    canonical = [k for k in top_keys if k[1] == CANONICAL_KEY]
    for lno, key, raw in top_keys:
        if key == CANONICAL_KEY:
            out.extend(value_check(relpath, lno, key, raw))
            if not summary["label"] and unquote(raw) in VALUES:
                summary["label"] = unquote(raw)
        elif canonical:
            out.append(finding(relpath, lno, "warning", "duplicate-key", key, unquote(raw),
                               "both 'ai-usage' and '%s' are set; remove '%s'" % (key, key)))
        else:
            fixed_value = norm_value(raw) if norm_value(raw) in VALUES else None
            out.append(finding(relpath, lno, "error", "variant-key", key, unquote(raw),
                               variant_message(key),
                               fix=(CANONICAL_KEY + ": " + fixed_value) if fixed_value else None))
            if not fixed_value:
                out.extend(value_check(relpath, lno, key, raw))
    if not top_keys:
        for lno, key, tok in stray:
            out.append(finding(relpath, lno, "warning", "stray-token", key, tok,
                               "'%s' appears in front matter%s but there is no top-level "
                               "'ai-usage' key" % (tok, (" (in '%s')" % key) if key else "")))
        has_any = any(f["code"] in ("commented", "nested", "stray-token") for f in out)
        if require and not include and not has_any:
            out.append(finding(relpath, start, "error", "missing", "", "",
                               "no ai-usage label (asked for with --require: add 'ai-usage: "
                               "ai-assisted' or 'ai-usage: ai-generated' if AI helped write it)"))
    if include and (top_keys or any(f["code"] in ("commented", "nested") for f in out)):
        out.append(finding(relpath, start, "info", "include-label", "", "",
                           "AI label in an include file: Learn shows the note per article, so "
                           "label the articles that use this include (not tested)"))
    return summary, out


# ---------------------------------------------------------------- docfx.json

def check_docfx(relpath, text):
    """Variant keys or odd values set for many files at once in docfx.json."""
    out = []
    try:
        obj = json.loads(text)
    except ValueError:
        return out
    if not isinstance(obj, dict):
        return out
    build = obj.get("build") if isinstance(obj.get("build"), dict) else obj
    gm = build.get("globalMetadata")
    if isinstance(gm, dict):
        for k, v in gm.items():
            if AI_KEY_RE.match(str(k)):
                out.extend(_docfx_entry(relpath, "globalMetadata", str(k), "", v))
    fm = build.get("fileMetadata")
    if isinstance(fm, dict):
        for k, v in fm.items():
            if AI_KEY_RE.match(str(k)) and isinstance(v, dict):
                for glob, val in v.items():
                    out.extend(_docfx_entry(relpath, "fileMetadata", str(k), str(glob), val))
    return out


def _docfx_entry(relpath, where, key, glob, val):
    out = []
    label = "%s %s%s" % (where, key, (" for '%s'" % glob) if glob else "")
    if key != CANONICAL_KEY:
        f = finding(relpath, 0, "error", "variant-key", key, str(val), variant_message(key))
        f["message"] += " (%s in docfx.json)" % label
        out.append(f)
    for f in value_check(relpath, 0, key, str(val)):
        f["message"] += " (%s in docfx.json)" % label
        out.append(f)
    return out


# ---------------------------------------------------------------- files and fixes

def read_text(path):
    with open(path, "rb") as fh:
        data = fh.read()
    try:
        return data.decode("utf-8"), True
    except UnicodeDecodeError:
        return data.decode("utf-8", "replace"), False


def iter_files(paths):
    for p in paths:
        if os.path.isfile(p):
            yield p
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for name in sorted(files):
                low = name.lower()
                if low.endswith(MD_EXT) or low == "docfx.json":
                    yield os.path.join(root, name)


def apply_fixes(text, findings):
    """Return text with fixable front matter findings applied (variant-key renames, value
    spelling). Line endings and everything else are kept."""
    lines = text.splitlines(True)
    changed = False
    for f in findings:
        if not f.get("fix") or f["line"] < 1 or f["code"] not in ("variant-key", "bad-value"):
            continue
        i = f["line"] - 1
        if i >= len(lines):
            continue
        body = lines[i].rstrip("\r\n")
        ending = lines[i][len(body):]
        m = KV_RE.match(body)
        if not m or m.group(1) != f["key"]:
            continue
        if f["code"] == "variant-key":
            new = f["fix"]
        else:
            new = "%s: %s" % (f["key"], f["fix"])
        if new != body:
            lines[i] = new + ending
            changed = True
    return ("".join(lines), True) if changed else (text, False)


def scan(paths, require=False, fix=False, write=False):
    report = {"version": VERSION, "files": 0, "markdown": 0, "with_front_matter": 0,
              "labelled": {"ai-assisted": 0, "ai-generated": 0}, "counts": {}, "findings": [],
              "fixed_files": [], "fixable": 0}
    for path in iter_files(paths):
        rel = os.path.relpath(path) if not os.path.isabs(paths[0]) else path
        rel = rel.replace("\\", "/")
        try:
            text, clean = read_text(path)
        except OSError as exc:
            report["findings"].append(finding(rel, 0, "warning", "unreadable", "", "", str(exc)))
            continue
        report["files"] += 1
        if os.path.basename(path).lower() == "docfx.json":
            fs = check_docfx(rel, text)
        else:
            report["markdown"] += 1
            summary, fs = check_text(rel, text, require=require)
            if summary["front_matter"]:
                report["with_front_matter"] += 1
            if summary["label"]:
                report["labelled"][summary["label"]] += 1
            fixable = [f for f in fs if f.get("fix") and f["line"] > 0]
            report["fixable"] += len(fixable)
            if fix and fixable:
                new, changed = apply_fixes(text, fixable)
                if changed and clean:
                    if write:
                        with open(path, "wb") as fh:
                            fh.write(new.encode("utf-8"))
                    report["fixed_files"].append(rel)
        report["findings"].extend(fs)
    for f in report["findings"]:
        report["counts"][f["code"]] = report["counts"].get(f["code"], 0) + 1
    report["findings"].sort(key=lambda f: (SEVERITY_ORDER[f["severity"]], f["path"], f["line"]))
    return report


# ---------------------------------------------------------------- live page

def check_url(url, opener=None, timeout=30):
    """Ask a Learn page for its Markdown copy (Accept: text/markdown) and check the AI key in
    its YAML header, which carries the label as authored (study 8: 164 of 164 labelled copies).
    The reader-facing note itself is added by page scripts and is in neither the served HTML
    nor the Markdown copy, so this checks the label, not the note."""
    req = urllib.request.Request(url, headers={"Accept": "text/markdown",
                                               "User-Agent": USER_AGENT})
    op = opener or urllib.request.build_opener()
    with op.open(req, timeout=timeout) as resp:
        ctype = resp.headers.get("Content-Type", "")
        body = resp.read(2_000_000).decode("utf-8", "replace")
    if "markdown" not in ctype.lower() and not body.lstrip("﻿").startswith("---"):
        return {"url": url, "markdown": False, "label": "", "findings": [
            finding(url, 0, "warning", "no-markdown", "", "",
                    "the site did not return a Markdown copy (Content-Type '%s')" % ctype)]}
    summary, fs = check_text(url, body)
    return {"url": url, "markdown": True, "label": summary["label"], "findings": fs}


# ---------------------------------------------------------------- output

def print_report(rep, max_findings, out=sys.stdout):
    shown = rep["findings"][:max_findings] if max_findings >= 0 else rep["findings"]
    for f in shown:
        loc = "%s:%d" % (f["path"], f["line"]) if f["line"] else f["path"]
        out.write("%s: %s %s: %s\n" % (loc, f["severity"], f["code"], f["message"]))
        if f.get("fix"):
            out.write("    fix: %s\n" % (f["fix"] if f["code"] == "variant-key"
                                         else "%s: %s" % (f["key"], f["fix"])))
    hidden = len(rep["findings"]) - len(shown)
    if hidden > 0:
        out.write("... %d more findings (use --max-findings -1 or --json)\n" % hidden)
    counts = ", ".join("%s %d" % kv for kv in sorted(rep["counts"].items())) or "none"
    out.write("== %d Markdown files, %d with front matter; labelled ai-usage: ai-assisted %d, "
              "ai-generated %d; findings: %s\n" % (rep["markdown"], rep["with_front_matter"],
                                                   rep["labelled"]["ai-assisted"],
                                                   rep["labelled"]["ai-generated"], counts))
    if rep["fixed_files"]:
        verb = "fixed" if rep.get("written") else "would fix (add --write)"
        out.write("== %s %d files\n" % (verb, len(rep["fixed_files"])))


def exit_code(findings):
    return 1 if any(f["severity"] in ("error", "warning") for f in findings) else 0


def main(argv=None, opener=None, out=sys.stdout):
    ap = argparse.ArgumentParser(
        prog="ai_label_check.py",
        description="Find AI-usage labels in Learn-style docs front matter that readers may never "
                    "see (variant keys, nested or commented labels, odd values).")
    ap.add_argument("paths", nargs="*", default=["."], help="files or folders (default: .)")
    ap.add_argument("--require", action="store_true",
                    help="also report articles with no ai-usage label (use on files AI helped write)")
    ap.add_argument("--fix", action="store_true",
                    help="plan safe fixes (variant key -> ai-usage, value spelling); prints them")
    ap.add_argument("--write", action="store_true", help="with --fix: write the fixes to the files")
    ap.add_argument("--url", action="append", default=[],
                    help="check a live Learn page's label via its Markdown copy (network)")
    ap.add_argument("--json", action="store_true", help="print JSON")
    ap.add_argument("--max-findings", type=int, default=200)
    ap.add_argument("--version", action="version", version=VERSION)
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    if args.write and not args.fix:
        sys.stderr.write("--write needs --fix\n")
        return 2
    if args.url:
        results = []
        for u in args.url:
            try:
                results.append(check_url(u, opener=opener))
            except Exception as exc:  # network errors are reported, not raised
                results.append({"url": u, "markdown": False, "label": "", "findings": [
                    finding(u, 0, "warning", "fetch-failed", "", "", str(exc)[:200])]})
        if args.json:
            out.write(json.dumps({"version": VERSION, "pages": results}, indent=1) + "\n")
        else:
            for r in results:
                out.write("== %s: markdown=%s label=%s\n" % (r["url"], "yes" if r["markdown"]
                                                             else "no", r["label"] or "none"))
                for f in r["findings"]:
                    out.write("   %s %s: %s\n" % (f["severity"], f["code"], f["message"]))
        return exit_code([f for r in results for f in r["findings"]])
    for p in args.paths:
        if not os.path.exists(p):
            sys.stderr.write("no such file or folder: %s\n" % p)
            return 2
    rep = scan(args.paths, require=args.require, fix=args.fix, write=args.write)
    rep["written"] = bool(args.write)
    if args.json:
        out.write(json.dumps(rep, indent=1) + "\n")
    else:
        print_report(rep, args.max_findings, out=out)
    remaining = rep["findings"]
    if args.write:
        fixed = set(rep["fixed_files"])
        remaining = [f for f in remaining
                     if not (f["path"] in fixed and f.get("fix") and f["line"] > 0)]
    return exit_code(remaining)


if __name__ == "__main__":
    sys.exit(main())
