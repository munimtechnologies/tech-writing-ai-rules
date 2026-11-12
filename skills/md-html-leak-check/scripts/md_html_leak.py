#!/usr/bin/env python3
# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""md_html_leak: measure raw HTML markup in a Markdown copy served to AI agents.

Docs sites now serve a Markdown copy of each page (a `<page>.md` address,
`Accept: text/markdown`, or links in llms.txt). Static site generators often
build that copy by rendering the page's shortcodes or components with the same
templates they use for HTML, so the copy can carry the HTML of tab sets,
alerts, cards, highlighted code and embedded widgets: Bootstrap class names,
ARIA attributes, inline scripts and styles. The words are usually still there,
but an agent has to read through the markup, and a widget that is filled in by
a script in the browser (an API explorer, for example) leaves only an empty
element.

This script reads Markdown text and reports, outside fenced code, inline code
and HTML comments:

  - every HTML tag it can tell from prose (`List<String>` and placeholders
    such as `<name>` or `<path>` without attributes are not counted),
  - which tags are structural (anything but simple inline tags such as
    `<a>`, `<em>`, `<br>`, `<kbd>`, `<sup>`),
  - markup characters (the tags themselves plus script and style bodies) as a
    share of the copy's non-code characters,
  - where the markup likely comes from, by signature: Docsy shortcodes
    (tabpane, alert, card, imgproc, pageinfo, blocks, swaggerui, redoc,
    iframe), Hugo's code highlighter, Mermaid, or plain HTML by element type.
    Tags with no signature of their own inherit the source of the element
    they sit in.

Attribution is a sign to check, not proof: a site may write the same class
names by hand. Python standard library only; network only with --url.

    python md_html_leak.py page.md
    python md_html_leak.py copies/ --json
    python md_html_leak.py --url https://www.example.com/docs/page/index.md
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

VERSION = "0.1.0"
USER_AGENT = ("md_html_leak/%s (+https://github.com/munimtechnologies/tech-writing-ai-rules; "
              "mv2@munimtech.com)" % VERSION)

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param",
        "source", "track", "wbr"}
# Element names that are almost never used as prose placeholders.
UNAMBIGUOUS = {
    "a", "abbr", "article", "aside", "audio", "b", "blockquote", "br", "button", "center",
    "cite", "code", "dd", "del", "details", "div", "dl", "dt", "em", "figcaption", "figure",
    "font", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "i",
    "iframe", "img", "ins", "kbd", "li", "main", "mark", "nav", "ol", "p", "picture", "pre",
    "q", "redoc", "s", "script", "section", "small", "span", "strong", "style", "sub",
    "summary", "sup", "svg", "table", "tbody", "td", "tfoot", "th", "thead", "tr", "u", "ul",
    "video",
}
# Real element names that docs also use as placeholders (`<path>`, `<source>`):
# counted only with attributes, as a closing tag, or self-closed.
AMBIGUOUS = {
    "address", "area", "base", "bdi", "bdo", "body", "canvas", "caption", "circle", "col",
    "colgroup", "data", "datalist", "defs", "dfn", "dialog", "embed", "fieldset", "g", "head",
    "html", "input", "label", "legend", "line", "link", "map", "menu", "meta", "meter",
    "noscript", "object", "optgroup", "option", "output", "param", "path", "polygon",
    "polyline", "progress", "rect", "rp", "rt", "ruby", "samp", "search", "select", "slot",
    "source", "symbol", "template", "textarea", "time", "title", "track", "use", "var", "wbr",
}
INLINE_OK = {"a", "abbr", "b", "br", "cite", "code", "del", "em", "i", "img", "ins", "kbd",
             "mark", "q", "s", "samp", "small", "span", "strong", "sub", "sup", "u", "var",
             "wbr"}
TABLE = {"table", "thead", "tbody", "tfoot", "tr", "td", "th", "caption", "colgroup", "col"}
SVG = {"svg", "g", "path", "circle", "rect", "line", "polygon", "polyline", "use", "defs",
       "symbol"}

# (label, pattern) checked in order on each opening tag's text.
SIGNATURES = [
    ("docsy:tabpane", re.compile(
        r'class="[^"]*\b(?:nav-tabs|tab-content|tab-pane|tab-body|nav-item|nav-link)\b'
        r'|\bid="tabs-\d+-|data-bs-toggle="tab"')),
    ("docsy:alert", re.compile(r'class="[^"]*\balert\b')),
    ("docsy:pageinfo", re.compile(r'class="[^"]*\bpageinfo\b')),
    ("docsy:imgproc", re.compile(r'\btd-post-card\b|\bcard-img-top\b')),
    ("docsy:card", re.compile(
        r'\btd-card\b|\btd-card-group\b|\bcard-group\b'
        r'|class="card-(?:header|body|title|text|footer)\b')),
    ("docsy:blocks", re.compile(
        r'\btd-box\b|\btd-cover-block|\btd-block-\d|\btd-anchor-no-extra-offset\b'
        r'|\btd-arrow-down\b|\btd-overlay\b|class="col-lg-4 mb-5 mb-lg-0 text-center"')),
    ("docsy:swaggerui", re.compile(r'docsy_swagger_ui|swagger-ui')),
    ("docsy:redoc", re.compile(r'^<redoc\b|redoc-container|id="myBtn"')),
    ("docsy:iframe", re.compile(r'^<iframe\b[^>]*resizeIframe')),
    ("hugo:highlight", re.compile(r'class="[^"]*\b(?:highlight|chroma)\b')),
    ("diagram:mermaid", re.compile(r'class="[^"]*\bmermaid\b')),
]
SCRIPT_SIGNATURES = [
    ("docsy:swaggerui", re.compile(r"SwaggerUIBundle|docsy_swagger_ui")),
    ("docsy:redoc", re.compile(r"\bredoc\b|myBtn", re.I)),
    ("docsy:iframe", re.compile(r"resizeIframe")),
]

BOOLEAN_ATTRS = {"allowfullscreen", "async", "autoplay", "checked", "controls", "defer",
                 "disabled", "hidden", "loop", "muted", "open", "playsinline", "readonly",
                 "required", "selected", "sandbox"}
ATTRS_RE = re.compile(r"""^(?:\s+[A-Za-z_:@][-\w:.@]*(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'=<>`]+))?)*\s*$""")
TAG_RE = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9-]*)((?:\s[^<>]*?)?)\s*(/?)>")
FENCE_RE = re.compile(r"^((?:[ \t]*>)*[ \t]*)(`{3,}|~{3,})(.*)$")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
RAWTEXT_RE = re.compile(r"<(script|style)\b[^>]*>(.*?)</\1\s*>", re.S | re.I)


class UsageError(Exception):
    pass


def _blank(chars, start, end):
    for i in range(start, end):
        if chars[i] != "\n":
            chars[i] = " "


def mask_code(text):
    """Return (masked text, code character count); fenced and inline code become spaces."""
    chars = list(text)
    code = 0
    lines = text.split("\n")
    pos = 0
    fence = None  # (char, length)
    starts = []
    for line in lines:
        starts.append(pos)
        pos += len(line) + 1
    for idx, line in enumerate(lines):
        start = starts[idx]
        end = start + len(line)
        if fence is not None:
            m = FENCE_RE.match(line)
            _blank(chars, start, end)
            code += len(line)
            if m and m.group(2)[0] == fence[0] and len(m.group(2)) >= fence[1] \
                    and not m.group(3).strip():
                fence = None
            continue
        m = FENCE_RE.match(line)
        if m and not (m.group(2)[0] == "`" and "`" in m.group(3)):
            fence = (m.group(2)[0], len(m.group(2)))
            _blank(chars, start, end)
            code += len(line)
            continue
        # inline code spans on this line
        i = 0
        while i < len(line):
            if line[i] != "`":
                i += 1
                continue
            j = i
            while j < len(line) and line[j] == "`":
                j += 1
            run = j - i
            k = j
            close = -1
            while k < len(line):
                if line[k] == "`":
                    m2 = k
                    while m2 < len(line) and line[m2] == "`":
                        m2 += 1
                    if m2 - k == run:
                        close = k
                        break
                    k = m2
                else:
                    k += 1
            if close < 0:
                i = j
                continue
            _blank(chars, start + i, start + close + run)
            code += close + run - i
            i = close + run
    return "".join(chars), code


def default_label(name):
    if name in TABLE:
        return "html:table"
    if name in ("details", "summary"):
        return "html:details"
    if name == "iframe":
        return "html:iframe"
    if name in ("figure", "figcaption"):
        return "html:figure"
    if name in ("script", "style"):
        return "html:script-style"
    if name in SVG:
        return "html:svg"
    if name in INLINE_OK:
        return "html:inline"
    return "html:other"


def signature(tag_text):
    for label, rx in SIGNATURES:
        if rx.search(tag_text):
            return label
    return None


def attrs_ok(attrs):
    """True if the text after a tag name reads as HTML attributes, not prose."""
    a = attrs.strip()
    if not a:
        return True
    if not ATTRS_RE.match(attrs):
        return False
    if "=" in a:
        return True
    return all(w.lower() in BOOLEAN_ATTRS for w in a.split())


def counts_as_tag(close, name, attrs, selfclose):
    """Tell an HTML tag from prose: `<String>`, `<name>`, `<your-image-name>`,
    `<path to file>` and `<a few words>` are not counted."""
    if name != name.lower():
        return False
    if not (name in UNAMBIGUOUS or name in AMBIGUOUS or "-" in name):
        return False
    if close:
        return not attrs.strip()
    if not attrs_ok(attrs):
        return False
    if name in UNAMBIGUOUS:
        return True
    # placeholders and custom elements: only with real attributes or self-closed
    return bool("=" in attrs or selfclose)


def scan(text):
    """Measure HTML markup in Markdown text. Returns a dict (see module doc)."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    masked, code_chars = mask_code(text)
    comments = 0
    comment_chars = 0
    mchars = list(masked)
    for m in COMMENT_RE.finditer(masked):
        comments += 1
        comment_chars += m.end() - m.start()
        _blank(mchars, m.start(), m.end())
    masked = "".join(mchars)

    labels = {}
    markup_chars = 0
    tags = 0
    structural = 0
    examples = []

    def add(label, n_tags, n_chars):
        e = labels.setdefault(label, {"tags": 0, "chars": 0})
        e["tags"] += n_tags
        e["chars"] += n_chars

    # Script and style bodies are markup, not content; blank them so their
    # contents are not read as tags.
    rawtext = []
    mchars = list(masked)
    for m in RAWTEXT_RE.finditer(masked):
        body_start, body_end = m.start(2), m.end(2)
        body = m.group(2)
        label = None
        for lab, rx in SCRIPT_SIGNATURES:
            if rx.search(body):
                label = lab
                break
        rawtext.append((m.start(), label, body_end - body_start))
        _blank(mchars, body_start, body_end)
    masked = "".join(mchars)
    raw_at = {pos: (label, n) for pos, label, n in rawtext}

    stack = []
    for m in TAG_RE.finditer(masked):
        close, name, attrs, selfclose = m.group(1), m.group(2), m.group(3) or "", m.group(4)
        if not counts_as_tag(close, name, attrs, selfclose):
            continue
        tag_text = m.group(0)
        if close:
            label = None
            for k in range(len(stack) - 1, -1, -1):
                if stack[k][0] == name:
                    label = stack[k][1]
                    del stack[k:]
                    break
            if label is None:
                label = default_label(name)
        else:
            label = signature(tag_text)
            if label is None and name in ("script", "style") and m.start() in raw_at:
                label = raw_at[m.start()][0]
            if label is None:
                parent = stack[-1][1] if stack else None
                if parent and not parent.startswith("html:"):
                    label = parent
                else:
                    label = default_label(name)
            if name not in VOID and not selfclose:
                stack.append((name, label))
        n = len(tag_text)
        if not close and m.start() in raw_at:
            n += raw_at[m.start()][1]
        tags += 1
        markup_chars += n
        add(label, 1, n)
        if name not in INLINE_OK:
            structural += 1
            if len(examples) < 3:
                examples.append(tag_text[:120])

    text_chars = len(text) - code_chars - comment_chars
    share = (markup_chars / text_chars) if text_chars > 0 else 0.0
    source_labels = sorted(l for l in labels if not l.startswith("html:"))
    return {
        "chars": len(text),
        "text_chars": text_chars,
        "code_chars": code_chars,
        "comments": comments,
        "tags": tags,
        "structural_tags": structural,
        "markup_chars": markup_chars,
        "markup_share": round(share, 4),
        "labels": {k: labels[k] for k in sorted(labels)},
        "docsy_labels": [l for l in source_labels if l.startswith("docsy:")],
        "source_labels": source_labels,
        "examples": examples,
    }


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "text/markdown, text/plain;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(5_000_000)
            ctype = resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        raise UsageError("HTTP %s for %s" % (exc.code, url))
    except (urllib.error.URLError, OSError) as exc:
        raise UsageError("could not fetch %s: %s" % (url, exc))
    text = body.decode("utf-8", errors="replace")
    if looks_like_html(text):
        raise UsageError("%s returned HTML (%s), not a Markdown copy" % (url, ctype or "no type"))
    return text


def looks_like_html(text):
    head = text.lstrip()[:300].lower()
    return head.startswith("<!doctype html") or head.startswith("<html")


def iter_files(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs.sort()
                for f in sorted(files):
                    if f.lower().endswith((".md", ".markdown", ".txt")):
                        yield os.path.join(root, f)
        elif os.path.isfile(p):
            yield p
        else:
            raise UsageError("not a file or folder: %s" % p)


def render_text(name, r):
    lines = ["%s: %d tags (%d structural), markup %.1f%% of %d non-code characters"
             % (name, r["tags"], r["structural_tags"], 100 * r["markup_share"], r["text_chars"])]
    for label, e in r["labels"].items():
        lines.append("  %-18s %4d tags %7d chars" % (label, e["tags"], e["chars"]))
    for ex in r["examples"]:
        lines.append("  e.g. %s" % ex)
    return "\n".join(lines)


def main(argv=None, out=None):
    out = out or sys.stdout
    ap = argparse.ArgumentParser(
        description="Measure raw HTML markup in Markdown copies served to AI agents.")
    ap.add_argument("paths", nargs="*", help="Markdown files or folders ('-' reads stdin)")
    ap.add_argument("--url", action="append", default=[],
                    help="fetch a live Markdown copy (repeatable)")
    ap.add_argument("--json", action="store_true", help="print JSON")
    ap.add_argument("--version", action="version", version="md_html_leak " + VERSION)
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    if not args.paths and not args.url:
        print("error: give a file, a folder, '-' or --url", file=sys.stderr)
        return 2
    results = []
    try:
        for p in args.paths:
            if p == "-":
                results.append(("<stdin>", scan(sys.stdin.read())))
                continue
            for f in iter_files([p]):
                with open(f, encoding="utf-8", errors="replace") as fh:
                    results.append((f.replace(os.sep, "/"), scan(fh.read())))
        for u in args.url:
            results.append((u, scan(fetch(u))))
    except UsageError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    if args.json:
        out.write(json.dumps({"tool": "md_html_leak", "version": VERSION,
                              "results": [dict(r, source=n) for n, r in results]},
                             indent=2, ensure_ascii=False) + "\n")
    else:
        out.write("md_html_leak %s\n" % VERSION)
        for n, r in results:
            out.write(render_text(n, r) + "\n")
        out.write("Each source label is a sign to check against the page, not proof.\n")
    return 1 if any(r["structural_tags"] for _, r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
