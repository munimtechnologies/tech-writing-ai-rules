#!/usr/bin/env python3
# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""md_copy_check: find the traces a broken Markdown copy of a docs page leaves.

Docs sites serve Markdown copies of their pages to AI agents (asked for with
`Accept: text/markdown`, or at the llms.txt convention's `<page>.md` address).
Study 10 of github.com/munimtechnologies/tech-writing-ai-rules (read 2026-11-11)
found that most copies keep the page, but that a copy fails silently when the
export skips a template or component: a placeholder such as "**Snippet**
component (self-closing)", an unrendered `<PriorityBoardingBanner />`, a section
heading with nothing under it, a copy that is only a title, or a copy that is
one line of MDX code. This script looks for those traces in the copy itself.

    python md_copy_check.py copy.md [more.md | folder ...] [--json]
    python md_copy_check.py --url https://docs.example.com/some/page/

Python 3 standard library only. No network unless --url is given. Exit codes:
0 no error or warning, 1 at least one, 2 usage error.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

VERSION = "0.1.0"
USER_AGENT = "md-copy-check/%s (+https://github.com/munimtechnologies/tech-writing-ai-rules)" % VERSION
MAX_BYTES = 3000000
MIN_WORDS = 20

SEVERITY = {
    "component-placeholder": "error",
    "mdx-code": "error",
    "self-closing-component": "warning",
    "template-include": "warning",
    "empty-section": "warning",
    "near-empty": "warning",
    "component-tag": "info",
    "template-tag": "info",
    "dangling-lead-in": "info",
}
HINT = {
    "component-placeholder": "the export wrote a placeholder where a component's content should be; that content is not in the copy",
    "mdx-code": "MDX source code is in the copy; the page's content may not have been rendered",
    "self-closing-component": "a component tag with no content in the copy; whatever it renders on the page (a banner, a note, a shared block) is probably missing",
    "template-include": "an include or partial was not rendered; its text is not in the copy",
    "empty-section": "a heading with nothing under it before the next heading of the same or a higher level; check the page for what belongs here",
    "near-empty": "the copy has almost no text outside headings and code; compare it with the page",
    "component-tag": "a component tag was left in the copy; check that its content is there too",
    "template-tag": "a template tag was left in the copy (usually harmless, such as an icon or anchor)",
    "dangling-lead-in": "a sentence ending with ':' is not followed by a list, table, code or quote; the part it introduces may be missing",
}
ORDER = {"error": 0, "warning": 1, "info": 2}

FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^[ \t]{0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*#*[ \t]*$")
INLINE_CODE_RE = re.compile(r"(`+)[^`\n]*?\1")
COMPONENT_RE = re.compile(r"<([A-Z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)*)(?=[\s/>])([^<>\n]*)>")
PLACEHOLDER_RE = re.compile(r"\*\*[A-Za-z][\w.-]*\*\*[ \t]+component\b|\bcomponent[ \t]+\(self-closing\)", re.I)
MDX_RE = re.compile(r"^[ \t]*(?:export[ \t]+(?:const|let|var|default|function)\b|import[ \t]+\S.*[ \t]from[ \t]+['\"])")
TEMPLATE_RE = re.compile(r"\{%.*?%\}|\{\{[<%].*?[%>]\}\}")
INCLUDE_WORD_RE = re.compile(r"^\{(?:%|\{[<%])-?[ \t]*(?:include|include_relative|partial|snippet|render|readfile|import)\b", re.I)
BREAK_ONLY_RE = re.compile(r"^(?:[ \t]*(?:<br[ \t]*/?>|<!--.*?-->|&nbsp;|\\))*[ \t]*$", re.I)
LIST_RE = re.compile(r"^[ \t]*(?:[-*+]|\d{1,9}[.)])[ \t]+")
LINK_DEST_RE = re.compile(r"\]\([^)\s]*(?:[ \t]+\"[^\"]*\")?\)")
WORD_RE = re.compile(r"[^\W_]+")


def finding(code, line, text):
    return {"code": code, "severity": SEVERITY[code], "line": line, "text": text.strip()[:120],
            "hint": HINT[code]}


def body_start(lines):
    """Index of the first line after an optional YAML front matter block (leading blank
    lines and HTML comment lines are skipped first)."""
    i = 0
    while i < len(lines) and (not lines[i].strip() or re.match(r"^\s*<!--.*-->\s*$", lines[i])):
        i += 1
    if i < len(lines) and lines[i].strip() == "---":
        for j in range(i + 1, len(lines)):
            if lines[j].strip() in ("---", "..."):
                return j + 1
        return i  # unterminated: treat as body
    return i


def scan_lines(lines, start):
    """Lines after the front matter as (index, kind, info): kind is 'fence' for a line
    inside or opening/closing a fenced code block, 'heading' (info = level), 'blank' or 'text'."""
    out = []
    fence = ""
    for i in range(start, len(lines)):
        line = lines[i]
        if fence:
            s = line.strip()
            if len(s) >= len(fence) and set(s) == {fence[0]}:
                fence = ""
            out.append((i, "fence", 0))
            continue
        m = FENCE_RE.match(line)
        if m:
            fence = m.group(1)
            out.append((i, "fence", 0))
            continue
        if not line.strip():
            out.append((i, "blank", 0))
            continue
        h = HEADING_RE.match(line)
        if h:
            out.append((i, "heading", len(h.group(1))))
            continue
        out.append((i, "text", 0))
    return out


def is_structured(line):
    """A line that starts a list, table, quote, indented code, HTML block or image."""
    if LIST_RE.match(line):
        return True
    s = line.lstrip(" ")
    if line.startswith("\t") or len(line) - len(s) >= 4:
        return True
    return s[:1] in ("|", ">", "<", "!", "$") or s.startswith("![")


def check_text(text, min_words=MIN_WORDS):
    """(findings, words) for one Markdown copy."""
    lines = (text or "").splitlines()
    start = body_start(lines)
    rows = scan_lines(lines, start)
    found = []
    words = 0

    for i, kind, _level in rows:
        if kind != "text":
            continue
        line = lines[i]
        n = i + 1
        if MDX_RE.match(line):
            found.append(finding("mdx-code", n, line))
            continue
        bare = INLINE_CODE_RE.sub(" ", line)
        if PLACEHOLDER_RE.search(bare):
            found.append(finding("component-placeholder", n, line))
        for m in TEMPLATE_RE.finditer(bare):
            code = "template-include" if INCLUDE_WORD_RE.match(m.group(0)) else "template-tag"
            found.append(finding(code, n, m.group(0)))
        for m in COMPONENT_RE.finditer(bare):
            name = m.group(1)
            if not any(c.islower() for c in name):
                continue  # <PROJECT_ID>-style placeholder, not a component
            selfclosing = m.group(2).rstrip().endswith("/")
            found.append(finding("self-closing-component" if selfclosing else "component-tag", n, m.group(0)))
        if not BREAK_ONLY_RE.match(line):
            plain = TEMPLATE_RE.sub(" ", bare)
            plain = COMPONENT_RE.sub(" ", plain)
            plain = LINK_DEST_RE.sub("] ", plain)
            plain = re.sub(r"</?[A-Za-z][^<>\n]*>", " ", plain)
            words += len(WORD_RE.findall(plain))

    # empty sections: a heading with no content before the next heading of the same
    # or a higher level (or the end of the copy)
    for pos, (i, kind, level) in enumerate(rows):
        if kind != "heading":
            continue
        has_content = False
        next_level = 0
        for j, kind2, level2 in rows[pos + 1:]:
            if kind2 == "heading":
                next_level = level2
                break
            if kind2 == "fence" or (kind2 == "text" and not BREAK_ONLY_RE.match(lines[j])):
                has_content = True
                break
        if not has_content and (next_level == 0 or next_level <= level):
            found.append(finding("empty-section", i + 1, lines[i]))

    # dangling lead-ins: a plain paragraph ending with ':' followed by nothing, a heading
    # or another plain paragraph
    blocks = []  # (first index, last index, kind of first row)
    cur = None
    for i, kind, _level in rows:
        if kind == "blank":
            if cur:
                blocks.append(cur)
                cur = None
            continue
        if cur is None:
            cur = [i, i, kind]
        elif kind == "heading" or cur[2] == "heading" or (kind == "fence") != (cur[2] == "fence"):
            blocks.append(cur)
            cur = [i, i, kind]
        else:
            cur[1] = i
    if cur:
        blocks.append(cur)
    for k, (first, last, kind) in enumerate(blocks):
        if kind != "text" or is_structured(lines[first]) or LIST_RE.match(lines[last]):
            continue
        if not lines[last].rstrip().endswith(":"):
            continue
        nxt = blocks[k + 1] if k + 1 < len(blocks) else None
        if nxt is None or nxt[2] == "heading" or (nxt[2] == "text" and not is_structured(lines[nxt[0]])):
            found.append(finding("dangling-lead-in", last + 1, lines[last]))

    if words < min_words:
        found.append(finding("near-empty", start + 1 if start < len(lines) else 1,
                             "%d words outside headings and code" % words))
    found.sort(key=lambda f: (f["line"], ORDER[f["severity"]], f["code"]))
    return found, words


# ---------------------------------------------------------------- fetching a live copy

def md_suffix_url(url):
    """The llms.txt convention's Markdown address: <path>.md ('/' -> '/index.md')."""
    p = urllib.parse.urlsplit(url)
    if p.path.endswith(".md"):
        return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, p.query, ""))
    path = p.path.rstrip("/") or "/index"
    return urllib.parse.urlunsplit((p.scheme, p.netloc, path + ".md", "", ""))


def default_fetch(url, accept):
    """(status, content type, text) for one GET; status 0 on a network error."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status = getattr(r, "status", 200)
            ctype = r.headers.get("Content-Type", "") or ""
            body = r.read(MAX_BYTES)
    except urllib.error.HTTPError as e:
        return e.code, "", ""
    except (urllib.error.URLError, OSError, ValueError) as e:
        return 0, "", str(e)
    return status, ctype, body.decode("utf-8", "replace")


def looks_like_markdown(status, ctype, text):
    if status != 200 or not (text or "").strip():
        return False
    head = text.lstrip()[:200].lower()
    if head.startswith("<!doctype html") or head.startswith("<html"):
        return False
    c = (ctype or "").lower()
    return "markdown" in c or c.startswith("text/plain") or c == ""


def get_copy(url, fetch=default_fetch):
    """(text, url used, method) for a page's Markdown copy, or (None, None, reason)."""
    status, ctype, text = fetch(url, "text/markdown")
    if looks_like_markdown(status, ctype, text):
        return text, url, "accept"
    md_url = md_suffix_url(url)
    status2, ctype2, text2 = fetch(md_url, "text/markdown, text/plain;q=0.9, */*;q=0.1")
    if looks_like_markdown(status2, ctype2, text2):
        return text2, md_url, "md-suffix"
    return None, None, "no Markdown copy (Accept: HTTP %s %s; .md: HTTP %s %s)" % (
        status, ctype or "-", status2, ctype2 or "-")


# ---------------------------------------------------------------- command line

def iter_inputs(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = sorted(d for d in dirs if not d.startswith("."))
                for f in sorted(files):
                    if f.lower().endswith((".md", ".markdown")):
                        yield os.path.join(root, f)
        else:
            yield p


def main(argv=None, fetch=default_fetch, out=None):
    out = out or sys.stdout
    ap = argparse.ArgumentParser(description="Find traces of lost content in Markdown copies of docs pages.")
    ap.add_argument("paths", nargs="*", help="Markdown copies (files or folders)")
    ap.add_argument("--url", action="append", default=[], help="a live docs page; its Markdown copy is fetched")
    ap.add_argument("--json", action="store_true", help="print JSON")
    ap.add_argument("--min-words", type=int, default=MIN_WORDS)
    ap.add_argument("--version", action="version", version="md_copy_check " + VERSION)
    a = ap.parse_args(argv)
    if not a.paths and not a.url:
        ap.print_usage(sys.stderr)
        return 2

    results = []
    bad_input = False
    for path in iter_inputs(a.paths):
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as e:
            results.append({"source": path, "error": str(e), "findings": [], "words": 0})
            bad_input = True
            continue
        fs, w = check_text(text, a.min_words)
        results.append({"source": path, "findings": fs, "words": w})
    for url in a.url:
        text, used, how = get_copy(url, fetch)
        if text is None:
            results.append({"source": url, "error": how, "findings": [], "words": 0})
            continue
        fs, w = check_text(text, a.min_words)
        results.append({"source": url, "copy_url": used, "method": how, "findings": fs, "words": w})

    counts = {"error": 0, "warning": 0, "info": 0}
    for r in results:
        for f in r["findings"]:
            counts[f["severity"]] += 1
    if a.json:
        out.write(json.dumps({"version": VERSION, "results": results, "counts": counts}, indent=1) + "\n")
    else:
        for r in results:
            if r.get("error"):
                out.write("== %s: %s\n" % (r["source"], r["error"]))
                continue
            via = " (%s, %s)" % (r["method"], r["copy_url"]) if r.get("method") else ""
            out.write("== %s%s: %d words, %d findings\n" % (r["source"], via, r["words"], len(r["findings"])))
            hinted = set()
            for f in r["findings"]:
                out.write("%s %s line %d: %s\n" % (f["severity"], f["code"], f["line"], f["text"]))
                if f["code"] not in hinted:
                    out.write("    -> %s\n" % f["hint"])
                    hinted.add(f["code"])
        out.write("== %d copies checked; %d errors, %d warnings, %d info\n" % (
            len(results), counts["error"], counts["warning"], counts["info"]))
    if bad_input:
        return 2
    return 1 if counts["error"] or counts["warning"] else 0


if __name__ == "__main__":
    sys.exit(main())
