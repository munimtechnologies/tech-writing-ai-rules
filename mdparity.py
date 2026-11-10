#!/usr/bin/env python3
# Copyright 2026 Munim, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
"""mdparity 0.1.0: does the Markdown copy a docs site serves to AI agents keep what its page shows people?

Study 10 of tech-writing-ai-rules. Many docs sites now answer an agent's request for Markdown
(`Accept: text/markdown`, or the llms.txt convention's `<page>.md` address) with a separate
document. Study 9 found 13 of 18 company docs sites doing it, and study 8 found that Microsoft
Learn's copies drop the article's last section and its AI note. This tool measures, page by
page, how much of what the HTML page shows is also in the Markdown copy, with a separate count
for callouts (notes, tips, warnings, cautions), code blocks and headings.

Frame (fixed in the pre-registration): every page of study 9's published pages.csv that was
readable and had a Markdown copy, asked for the same way (`Accept: text/markdown` when that
worked, otherwise `<page>.md`), plus 30 Microsoft Learn pages drawn with
random.Random("study10|learn") from study 8's counted pages that had a Markdown copy. Both CSV
files are read from a pinned commit of the repository, and their SHA-256 is recorded.

For each page the tool fetches the served HTML (no scripts are run) and the Markdown copy, takes
the page's main content (<main>, else role=main, else the largest <article>, else <body>; a large
<article> inside <main> is preferred), drops navigation, headers, footers, buttons, hidden
decoration and common page chrome, and splits it into blocks:

  prose    p, li, td, th, dt, dd, figcaption, summary with no such block inside (>= 8 words)
  heading  h2, h3, h4
  code     pre
  callout  the outermost element whose class names an admonition, callout, alert, notice,
           warning, caution, danger, important, note or tip, or whose role is note or alert
           (>= 3 words after a leading kind word such as "Warning"); grouped as "warning"
           (warning, caution, danger, important, error, critical) or "note"

A block counts as present in the Markdown copy when its words (lower case, letters and digits
only) appear there: blocks under 5 words as an exact word sequence, longer blocks when at least
80% of their 5-word shingles do. Link targets, HTML/MDX tags, template tags and comments are
removed from the Markdown outside code fences first.

No page text is published: missing.csv keeps at most 160 characters of each missing block, and
the full texts go to evidence/ for the hand check only.

Usage: python mdparity.py --out-dir OUT [--wait-prereg-minutes 240] [--no-prereg-check]
Outputs: pages.csv, sites.csv, missing.csv, mdparity.json, MDPARITY_AUTO.md, evidence/.
Standard library only. Apache-2.0.
Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""

import argparse
import collections
import csv
import datetime
import gzip
import hashlib
import html as htmlmod
import io
import json
import os
import random
import re
import statistics
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser

VERSION = "0.1.0"
USER_AGENT = ("tech-writing-ai-rules-mdparity/%s (+https://github.com/munimtechnologies/"
              "tech-writing-ai-rules; mv2@munimtech.com)" % VERSION)
REPO = "munimtechnologies/tech-writing-ai-rules"
REPO_API = "https://api.github.com/repos/%s/commits" % REPO
PREREG_PATH = "census/2026-11-md-copy-parity/PREREGISTRATION.md"
FRAME_COMMIT = "af74d232303eb5e1039d0c4c66acb11f727a184f"
RAW = "https://raw.githubusercontent.com/%s/%s/" % (REPO, FRAME_COMMIT)
VENDOR_PAGES = RAW + "census/2026-11-vendor-docs-ai-labels/pages.csv"
LEARN_PAGES = RAW + "census/2026-11-ms-learn-ai-shown/pages.csv"
LEARN_SAMPLE = 30
LEARN_SEED = "study10|learn"
DELAY = 1.0
MAX_BYTES = 3000000
MIN_PROSE_WORDS = 8
MIN_CALLOUT_WORDS = 3
MIN_COUNTED_PROSE = 3
SHINGLE = 5
CONTAIN = 0.8
MISSING_PER_PAGE = 60
SNIPPET = 160
SITE_MIN = 15
ACCEPT_HTML = "text/html,application/xhtml+xml"
ACCEPT_MD = "text/markdown"

HTML_START_RE = re.compile(r"<(?:!doctype\s+html|html[\s>])", re.I)
BLOCKED_RE = re.compile(r"_cf_chl_opt|<title>\s*Just a moment|<title>\s*Access Denied|"
                        r"_Incapsula_Resource|px-captcha|captcha-delivery", re.I)

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr",
        "param", "keygen"}
AUTO_CLOSE = {"p", "li", "dt", "dd", "tr", "td", "th", "option"}
BLOCKISH = {"p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "table", "tr", "td", "th",
            "thead", "tbody", "section", "article", "aside", "main", "header", "footer", "nav", "blockquote",
            "details", "summary", "dt", "dd", "dl", "figure", "figcaption", "br", "hr"}
DROP_TAGS = {"script", "style", "noscript", "template", "svg", "button", "select", "nav", "header", "footer",
             "iframe", "input", "textarea", "object", "canvas", "dialog"}
DROP_ROLES = {"navigation", "banner", "contentinfo", "search", "complementary"}
CHROME_RE = re.compile(
    r"^(?:toc|table-of-contents|on-this-page|breadcrumbs?|sidebar|side-nav|sidenav|feedback|pagination|pager|"
    r"edit-page|edit-this-page|page-nav|prev-next|navbar|menu|skip-link|copy-button|copy-code|clipboard|"
    r"anchor|header-anchor|heading-anchor|hash-link|anchorjs-link|visually-hidden|sr-only|"
    r"screen-reader-text|cookie-banner|cookie-consent|was-this-helpful|page-rating)$")
CALLOUT_TAGS = {"div", "aside", "section", "blockquote", "p"}
CALLOUT_TOKEN_RE = re.compile(r"^(?:[a-z0-9]+[-_]+)*(?:admonition|callout|alert|notice|warning|caution|danger|"
                              r"important|note|tip)(?:[-_]+[a-z0-9]+)*$")
WARN_RE = re.compile(r"warning|caution|danger|important|error|critical")
KIND_WORDS = {"note", "notes", "warning", "caution", "danger", "important", "tip", "tips", "info", "notice",
              "alert", "attention", "hint", "remarque"}
TAB_RE = re.compile(r"^tab[-_]?(?:pane|panel|content)$")
PROSE_TAGS = {"p", "li", "td", "th", "dt", "dd", "figcaption", "summary"}
HEAD_TAGS = {"h2", "h3", "h4"}
STRUCT_TAGS = PROSE_TAGS | {"h1", "h2", "h3", "h4", "h5", "h6", "pre"}

FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
LINK_DEST_RE = re.compile(r"\]\(\s*<?[^)\s>]*>?(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
REF_DEF_RE = re.compile(r"^[ \t]{0,3}\[[^\]]+\]:[ \t]*\S+.*$", re.M)
MD_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
MD_TAG_RE = re.compile(r"</?[A-Za-z][A-Za-z0-9.:_-]*(?:\s[^<>]*)?/?>")
SHORTCODE_RE = re.compile(r"\{\{[<%].*?[%>]\}\}", re.S)
LIQUID_RE = re.compile(r"\{%.*?%\}", re.S)
MD_MARKER_RE = re.compile(
    r"^[ \t]*>[ \t]*\[![A-Za-z]+\]|^[ \t]*:{3,}[ \t]*[A-Za-z]+|^[ \t]*!!![ \t]+[A-Za-z]+|"
    r"^[ \t]*\.\.[ \t]+[A-Za-z]+::|"
    r"<(?:Callout|Admonition|Note|Warning|Tip|Info|Caution|Danger|Aside|Alert|Important)\b|"
    r"\{\{[<%][ \t]*(?:note|warning|caution|tip|callout|alert|admonition|important|danger)\b|"
    r"^[ \t]*>[ \t]*\*\*(?:note|warning|caution|tip|important|danger)\b", re.I | re.M)

PAGE_COLUMNS = ["site", "url", "method", "md_url", "status", "html_status", "html_ctype", "md_status", "md_ctype",
                "main", "counted", "html_words", "md_words", "prose", "prose_present", "coverage", "heading",
                "heading_present", "code", "code_present", "callout", "callout_present", "warn", "warn_present",
                "tab", "tab_present", "md_markers"]
COUNT_KEYS = ["prose", "prose_present", "heading", "heading_present", "code", "code_present", "callout",
              "callout_present", "warn", "warn_present", "tab", "tab_present"]
SITE_COLUMNS = ["site", "sampled", "counted", "median_coverage", "md_html_words"] + COUNT_KEYS + ["md_markers"]
MISSING_COLUMNS = ["site", "url", "kind", "group", "in_tab", "words", "text"]


# ---------------------------------------------------------------- HTML tree

class Node(object):
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = attrs
        self.children = []
        self.parent = parent


class TreeBuilder(HTMLParser):
    """A forgiving tree: void elements never open, an end tag closes up to its last open match
    (or is ignored), and p/li/dt/dd/tr/td/th/option close an open sibling of the same tag."""

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = {}
        for k, v in attrs:
            k = (k or "").lower()
            if k and k not in a:
                a[k] = v if v is not None else ""
        if tag in AUTO_CLOSE and len(self.stack) > 1 and self.stack[-1].tag == tag:
            self.stack.pop()
        node = Node(tag, a, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        tag = tag.lower()
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if data:
            self.stack[-1].children.append(data)


def parse_html(text):
    b = TreeBuilder()
    try:
        b.feed(text or "")
        b.close()
    except Exception:  # malformed markup: keep what was built
        pass
    return b.root


def iter_nodes(node):
    """Elements below and including node, in document order (no recursion)."""
    stack = [node]
    while stack:
        n = stack.pop()
        yield n
        stack.extend(reversed([c for c in n.children if isinstance(c, Node)]))


def classes(node):
    return (node.attrs.get("class") or "").lower().split()


def is_callout(n):
    if n.tag not in CALLOUT_TAGS:
        return False
    if (n.attrs.get("role") or "").lower() in ("note", "alert"):
        return True
    if any(CALLOUT_TOKEN_RE.match(t) for t in classes(n)):
        return True
    return any(k.startswith("data-") and ("callout" in k or "admonition" in k) for k in n.attrs)


def dropped(n):
    if n.tag in DROP_TAGS:
        return True
    if (n.attrs.get("aria-hidden") or "").lower() == "true":
        return True
    callout = is_callout(n)
    if n.tag == "aside" and not callout:
        return True
    if (n.attrs.get("role") or "").lower() in DROP_ROLES and not callout:
        return True
    toks = classes(n) + [(n.attrs.get("id") or "").lower()]
    return (not callout) and any(CHROME_RE.match(t) for t in toks if t)


def node_text(node, skip=dropped):
    """Visible text below node; block elements are separated by new lines, inline ones are not."""
    out = []
    stack = [node]
    while stack:
        n = stack.pop()
        if isinstance(n, str):
            out.append(n)
            continue
        if n is not node and skip is not None and skip(n):
            continue
        if n.tag in BLOCKISH:
            out.append("\n")
            stack.append("\n")
        stack.extend(reversed(n.children))
    return "".join(out)


def word_count(node):
    return len(words(node_text(node)))


def pick_main(root):
    """(element, how) for the page's main content."""
    nodes = list(iter_nodes(root))
    mains = [n for n in nodes if n.tag == "main"]
    how = "main"
    if not mains:
        mains = [n for n in nodes if (n.attrs.get("role") or "").lower() == "main"]
        how = "role=main"
    if mains:
        best = max(mains, key=word_count)
        arts = [n for n in iter_nodes(best) if n.tag == "article" and n is not best]
        if arts:
            art = max(arts, key=word_count)
            if word_count(art) * 2 >= word_count(best):
                return art, how + ">article"
        return best, how
    arts = [n for n in nodes if n.tag == "article"]
    if arts:
        return max(arts, key=word_count), "article"
    bodies = [n for n in nodes if n.tag == "body"]
    if bodies:
        return bodies[0], "body"
    return root, "root"


def has_struct_below(n):
    for d in iter_nodes(n):
        if d is not n and d.tag in STRUCT_TAGS:
            return True
    return False


def callout_group(n, text):
    hay = " ".join(classes(n)) + " " + " ".join(v for k, v in n.attrs.items() if k.startswith("data-"))
    hay += " " + " ".join(words(text)[:2])
    return "warning" if WARN_RE.search(hay.lower()) else "note"


def blocks(main):
    """Blocks of the main content in document order: dicts with kind, text, group, in_tab."""
    out = []
    stack = [(main, False, False)]
    while stack:
        n, in_tab, in_call = stack.pop()
        if n is not main and dropped(n):
            continue
        tab = in_tab or (n.attrs.get("role") or "").lower() == "tabpanel" or any(TAB_RE.match(t)
                                                                               for t in classes(n))
        call = in_call
        if not in_call and is_callout(n):
            text = node_text(n)
            out.append({"kind": "callout", "text": text, "group": callout_group(n, text), "in_tab": tab})
            call = True
        if n.tag == "pre":
            out.append({"kind": "code", "text": node_text(n), "group": "", "in_tab": tab})
            continue
        if n.tag in HEAD_TAGS:
            out.append({"kind": "heading", "text": node_text(n), "group": "", "in_tab": tab})
            continue
        if n.tag in PROSE_TAGS and not has_struct_below(n):
            out.append({"kind": "prose", "text": node_text(n), "group": "", "in_tab": tab})
            continue
        for c in reversed([c for c in n.children if isinstance(c, Node)]):
            stack.append((c, tab, call))
    return out


# ---------------------------------------------------------------- words and Markdown

def words(text):
    t = unicodedata.normalize("NFKC", text or "").lower()
    return re.findall(r"[^\W_]+", t)


def strip_kind(ws):
    ws = list(ws)
    for _ in range(2):
        if ws and ws[0] in KIND_WORDS:
            ws = ws[1:]
    return ws


def md_plain(md):
    """Markdown -> text. Outside code fences: comments, link targets, reference definitions,
    template tags and HTML/MDX tags are removed and entities decoded. Fence lines are dropped;
    code inside fences is kept as it is."""
    out, buf = [], []
    state = {"fence": ""}

    def flush():
        if buf:
            t = "\n".join(buf)
            t = MD_COMMENT_RE.sub(" ", t)
            t = LINK_DEST_RE.sub("] ", t)
            t = REF_DEF_RE.sub(" ", t)
            t = SHORTCODE_RE.sub(" ", t)
            t = LIQUID_RE.sub(" ", t)
            t = MD_TAG_RE.sub(" ", t)
            out.append(htmlmod.unescape(t))
            del buf[:]

    for line in (md or "").splitlines():
        fence = state["fence"]
        if fence:
            s = line.strip()
            if len(s) >= len(fence) and set(s) == {fence[0]}:
                state["fence"] = ""
            else:
                out.append(line)
            continue
        m = FENCE_RE.match(line)
        if m:
            flush()
            state["fence"] = m.group(1)
            continue
        buf.append(line)
    flush()
    return "\n".join(out)


def shingles(ws, k=SHINGLE):
    return {tuple(ws[i:i + k]) for i in range(len(ws) - k + 1)}


class Corpus(object):
    """The words of a Markdown copy, for presence tests."""

    def __init__(self, md):
        self.words = words(md_plain(md))
        self.joined = " " + " ".join(self.words) + " "
        self.shingles = shingles(self.words)

    def has(self, ws):
        if not ws:
            return True
        if len(ws) < SHINGLE:
            return (" " + " ".join(ws) + " ") in self.joined
        sh = shingles(ws)
        hit = sum(1 for s in sh if s in self.shingles)
        return hit >= CONTAIN * len(sh)


def md_markers(md):
    return len(MD_MARKER_RE.findall(md or ""))


# ---------------------------------------------------------------- comparing one page

def compare(html, md):
    """(counts, missing, main_how, html_words, md_words, block_lines) for one page."""
    main, how = pick_main(parse_html(html))
    corpus = Corpus(md)
    counts = collections.Counter({k: 0 for k in COUNT_KEYS})
    missing, lines = [], []
    html_words = 0
    for b in blocks(main):
        ws = words(b["text"])
        kind = b["kind"]
        if kind == "callout":
            ws = strip_kind(ws)
            if len(ws) < MIN_CALLOUT_WORDS:
                continue
        elif kind == "prose":
            html_words += len(ws)
            if len(ws) < MIN_PROSE_WORDS:
                continue
        elif not ws:
            continue
        ok = corpus.has(ws)
        counts[kind] += 1
        counts[kind + "_present"] += int(ok)
        if kind == "callout" and b["group"] == "warning":
            counts["warn"] += 1
            counts["warn_present"] += int(ok)
        if kind == "prose" and b["in_tab"]:
            counts["tab"] += 1
            counts["tab_present"] += int(ok)
        flat = re.sub(r"\s+", " ", b["text"]).strip()
        lines.append("%s\t%s\t%s\t%s" % ("present" if ok else "MISSING", kind, b["group"] or "-", flat))
        if not ok and (kind == "callout" or len(missing) < MISSING_PER_PAGE):
            missing.append({"kind": kind, "group": b["group"], "in_tab": b["in_tab"], "words": len(ws),
                            "text": flat[:SNIPPET]})
    return counts, missing, how, html_words, len(corpus.words), lines


# ---------------------------------------------------------------- HTTP

def base_of(url):
    try:
        p = urllib.parse.urlsplit(url or "")
    except ValueError:
        return ""
    return "%s://%s" % (p.scheme, p.netloc)


def md_suffix_url(url):
    """The llms.txt convention's Markdown address: <path>.md ('/' -> '/index.md')."""
    p = urllib.parse.urlsplit(url)
    path = p.path.rstrip("/") or "/index"
    return urllib.parse.urlunsplit((p.scheme, p.netloc, path + ".md", "", ""))


def body_text(body, limit=MAX_BYTES):
    body = body or b""
    if body[:2] == b"\x1f\x8b":
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(body)) as gz:
                body = gz.read(limit)
        except (OSError, EOFError):
            return ""
    return body.decode("utf-8", "replace")


def is_html(text, ctype):
    ct = (ctype or "").lower()
    if "markdown" in ct:
        return False
    if "html" in ct:
        return True
    return bool(HTML_START_RE.match((text or "").lstrip("\ufeff \t\r\n")[:200]))


def blocked(status, text):
    return status in (401, 403, 429, 503) or (len(text or "") < 30000 and bool(BLOCKED_RE.search(text or "")))


def md_ok(status, ctype, text):
    """Study 9's rule for a served Markdown copy."""
    if status != 200 or not (text or "").strip() or is_html(text, ctype):
        return False
    ct = (ctype or "").lower()
    if "markdown" in ct:
        return True
    head = text.lstrip("\ufeff \t\r\n")
    return ("text/plain" in ct or not ct) and (head.startswith("---") or head.startswith("#"))


def default_fetch(url, accept, limit=MAX_BYTES):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.headers.get("Content-Type", ""), resp.geturl(), resp.read(limit)
    except urllib.error.HTTPError as exc:
        return exc.code, "", url, b""
    except Exception as exc:  # network errors, timeouts, bad URLs
        return 0, type(exc).__name__, url, b""


def polite_fetch(fetch, url, accept, sleep, limit=MAX_BYTES):
    sleep(DELAY)
    got = fetch(url, accept, limit)
    if got[0] in (429, 503):
        sleep(60)
        got = fetch(url, accept, limit)
    return got


def make_robots(fetch, sleep):
    """base -> function(url) -> allowed, cached per host. An unreadable robots.txt allows everything."""
    cache = {}

    def robots_for(base):
        if base not in cache:
            st, ct, _f, body = polite_fetch(fetch, base + "/robots.txt", "text/plain", sleep)
            text = body_text(body) if st == 200 else ""
            if is_html(text, ct):
                text = ""
            rp = urllib.robotparser.RobotFileParser()
            rp.parse(text.splitlines())
            cache[base] = lambda u, rp=rp: rp.can_fetch(USER_AGENT, u)
        return cache[base]
    return robots_for


def check_page(entry, fetch, sleep, robots_for):
    """(row, missing rows, evidence) for one frame entry."""
    url = entry["url"]
    md_url = url if entry["method"] == "accept" else md_suffix_url(url)
    row = {c: "" for c in PAGE_COLUMNS}
    row.update(site=entry["site"], url=url, method=entry["method"], md_url=md_url, counted=False, status="")
    if not robots_for(base_of(url))(url) or not robots_for(base_of(md_url))(md_url):
        row["status"] = "robots"
        return row, [], None
    st, ct, _final, body = polite_fetch(fetch, url, ACCEPT_HTML, sleep)
    html = body_text(body)
    row.update(html_status=st, html_ctype=(ct or "")[:60])
    if blocked(st, html):
        row["status"] = "blocked"
        return row, [], None
    if st != 200 or not is_html(html, ct):
        row["status"] = "html-unreadable"
        return row, [], None
    st2, ct2, _f2, body2 = polite_fetch(fetch, md_url, ACCEPT_MD, sleep)
    md = body_text(body2)
    row.update(md_status=st2, md_ctype=(ct2 or "")[:60])
    if not md_ok(st2, ct2, md):
        row["status"] = "md-missing"
        return row, [], None
    counts, missing, how, html_words, md_words, lines = compare(html, md)
    row.update(counts)
    row.update(main=how, html_words=html_words, md_words=md_words, md_markers=md_markers(md))
    if counts["prose"] >= MIN_COUNTED_PROSE:
        row.update(status="ok", counted=True, coverage=round(counts["prose_present"] / float(counts["prose"]), 4))
    else:
        row["status"] = "few-blocks"
    miss = [dict(site=entry["site"], url=url, **m) for m in missing]
    return row, miss, {"md": md, "blocks": "\n".join(lines)}


# ---------------------------------------------------------------- frame

def read_csv_text(text):
    return list(csv.DictReader(io.StringIO(text.lstrip("\ufeff"))))


def vendor_frame(rows):
    """Study 9 pages that were readable and had a Markdown copy, in file order, one per URL."""
    out, seen = [], set()
    for r in rows:
        if (r.get("control") or "").strip() or r.get("readable") != "True":
            continue
        if r.get("md_accept") == "True":
            method = "accept"
        elif r.get("md_suffix") == "True":
            method = "suffix"
        else:
            continue
        url = (r.get("url") or "").strip()
        if url and url not in seen:
            seen.add(url)
            out.append({"site": r["site"], "url": url, "method": method})
    return out


def learn_frame(rows, n=LEARN_SAMPLE, seed=LEARN_SEED):
    """n study 8 counted pages with a Markdown copy, drawn with random.Random(seed)."""
    pool = sorted({((r.get("repo") or ""), (r.get("path") or ""), (r.get("final_url") or r.get("url") or "").strip())
                   for r in rows if r.get("stratum") in ("A", "B", "C", "U") and r.get("mapped") == "yes"
                   and r.get("md_served") == "True"})
    pool = [p for p in pool if p[2]]
    picked = sorted(random.Random(seed).sample(pool, min(n, len(pool))))
    return [{"site": "mslearn", "url": u, "method": "accept"} for _r, _p, u in picked]


def load_frame_file(src, fetch):
    """(text, sha256) of a frame CSV given as a path or an https URL."""
    if src.startswith("https://"):
        st, _ct, _f, body = fetch(src, "text/csv,text/plain,*/*", 50000000)
        if st != 200:
            raise IOError("could not read %s (HTTP %s)" % (src, st))
        data = body or b""
    else:
        with open(src, "rb") as fh:
            data = fh.read()
    return data.decode("utf-8", "replace"), hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------- summary and grades

def ratio_at_least(k, n, num, den):
    """k / n >= num / den in integers."""
    return k * den >= n * num


def summarise(rows):
    by_site = collections.OrderedDict()
    for r in rows:
        by_site.setdefault(r["site"], []).append(r)
    sites = []
    for sid, rs in by_site.items():
        c = [r for r in rs if r["counted"]]
        srow = {"site": sid, "sampled": len(rs), "counted": len(c)}
        for k in COUNT_KEYS + ["md_markers"]:
            srow[k] = sum(int(r[k] or 0) for r in c)
        srow["median_coverage"] = round(statistics.median([r["coverage"] for r in c]), 4) if c else ""
        ratios = [int(r["md_words"]) / float(r["html_words"]) for r in c if int(r["html_words"] or 0) > 0]
        srow["md_html_words"] = round(statistics.median(ratios), 3) if ratios else ""
        sites.append(srow)
    counted = [r for r in rows if r["counted"]]
    tot = {k: sum(int(r[k] or 0) for r in counted) for k in COUNT_KEYS}
    big = [s for s in sites if s["counted"] >= SITE_MIN]
    out = {"sampled": len(rows), "counted": len(counted), "totals": tot,
           "status": dict(collections.Counter(r["status"] for r in rows)),
           "median_coverage": round(statistics.median([r["coverage"] for r in counted]), 4) if counted else None,
           "sites_counted_min": len(big)}

    g1 = len(big) >= 10 and len(counted) >= 250
    callout_sites = sum(1 for s in sites if s["callout"] > 0)
    g2 = tot["callout"] >= 40 and callout_sites >= 5
    out["gates"] = {"G1": {"sites": len(big), "counted": len(counted), "passed": g1},
                    "G2": {"callouts": tot["callout"], "sites": callout_sites, "passed": g2}}
    preds = {}
    med = out["median_coverage"]
    preds["P1"] = {"value": med, "held": (med is not None and med >= 0.90) if g1 else None}
    low = [s["site"] for s in big if s["median_coverage"] != "" and s["median_coverage"] < 0.80]
    preds["P2"] = {"value": len(low), "sites": low, "held": (len(low) >= 3) if g1 else None}
    lost = tot["callout"] - tot["callout_present"]
    preds["P3"] = {"k": lost, "n": tot["callout"],
                   "held": ratio_at_least(lost, tot["callout"], 1, 20) if (g1 and g2) else None}
    lossy = [s["site"] for s in sites if s["callout"] >= 5
             and ratio_at_least(s["callout"] - s["callout_present"], s["callout"], 1, 4)]
    preds["P4"] = {"value": len(lossy), "sites": lossy, "held": (len(lossy) >= 1) if (g1 and g2) else None}
    preds["P5"] = {"k": tot["code_present"], "n": tot["code"],
                   "held": ratio_at_least(tot["code_present"], tot["code"], 19, 20)
                   if (g1 and tot["code"] >= 50) else None}
    preds["P6"] = {"k": tot["heading_present"], "n": tot["heading"],
                   "held": ratio_at_least(tot["heading_present"], tot["heading"], 19, 20)
                   if (g1 and tot["heading"] >= 50) else None}
    out["predictions"] = preds
    note_n = tot["callout"] - tot["warn"]
    note_p = tot["callout_present"] - tot["warn_present"]
    out["descriptive"] = {
        "warning_callouts": [tot["warn_present"], tot["warn"]],
        "note_callouts": [note_p, note_n],
        "tab_prose": [tot["tab_present"], tot["tab"]],
        "other_prose": [tot["prose_present"] - tot["tab_present"], tot["prose"] - tot["tab"]],
    }
    return out, sites


# ---------------------------------------------------------------- output

def write_csv(path, rows, columns):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def pct(k, n):
    return "%.1f%%" % (100.0 * k / n) if n else "n/a"


def report(meta, s, sites):
    t = s["totals"]
    lines = ["# mdparity %s: automatic summary (study 10)" % VERSION, "",
             "Started %s, finished %s. Pre-registration commit: %s." % (
                 meta.get("started"), meta.get("finished"), (meta.get("prereg") or {}).get("committed_at")),
             "", "Pages in frame: %d; counted: %d; status: %s." % (s["sampled"], s["counted"], json.dumps(s["status"])),
             "", "| Gate / prediction | Value | Held |", "|---|---|---|"]
    for g, v in s["gates"].items():
        lines.append("| %s | %s | %s |" % (g, json.dumps({k: x for k, x in v.items() if k != "passed"}),
                                          "passed" if v["passed"] else "FAILED"))
    for p, v in s["predictions"].items():
        val = "%s / %s" % (v["k"], v["n"]) if "k" in v else json.dumps(v["value"])
        if "sites" in v:
            val += " " + ", ".join(v["sites"])
        lines.append("| %s | %s | %s |" % (p, val, {True: "yes", False: "no", None: "not graded"}[v["held"]]))
    lines += ["", "Pooled: prose %s, headings %s, code %s, callouts %s (warning group %s)." % (
        pct(t["prose_present"], t["prose"]), pct(t["heading_present"], t["heading"]),
        pct(t["code_present"], t["code"]), pct(t["callout_present"], t["callout"]),
        pct(t["warn_present"], t["warn"])), "",
        "| Site | Counted | Median prose coverage | Headings | Code | Callouts | Warning callouts | MD/HTML words |",
        "|---|---|---|---|---|---|---|---|"]
    for r in sites:
        lines.append("| %s | %d/%d | %s | %d/%d | %d/%d | %d/%d | %d/%d | %s |" % (
            r["site"], r["counted"], r["sampled"], r["median_coverage"], r["heading_present"], r["heading"],
            r["code_present"], r["code"], r["callout_present"], r["callout"], r["warn_present"], r["warn"],
            r["md_html_words"]))
    return "\n".join(lines) + "\n"


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def http_get(url, opener=None):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    if opener is not None:
        return opener(req)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


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
    prereg = prereg_commit(path, opener)
    waited = 0
    while prereg.get("committed_at") is None and waited < minutes * 60:
        sleep(every)
        waited += every
        prereg = prereg_commit(path, opener)
    prereg["waited_seconds"] = waited
    return prereg


def main(argv=None, fetch=None, sleep=time.sleep, opener=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--vendor-pages", default=VENDOR_PAGES, help="study 9 pages.csv (path or https URL)")
    ap.add_argument("--learn-pages", default=LEARN_PAGES, help="study 8 pages.csv (path or https URL)")
    ap.add_argument("--learn-sample", type=int, default=LEARN_SAMPLE)
    ap.add_argument("--prereg-path", default=PREREG_PATH)
    ap.add_argument("--no-prereg-check", action="store_true")
    ap.add_argument("--wait-prereg-minutes", type=float, default=0)
    ap.add_argument("--no-evidence", action="store_true")
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    meta = {"version": VERSION, "started": utcnow(),
            "settings": {"min_prose_words": MIN_PROSE_WORDS, "min_callout_words": MIN_CALLOUT_WORDS,
                         "shingle": SHINGLE, "contain": CONTAIN, "min_counted_prose": MIN_COUNTED_PROSE,
                         "learn_sample": a.learn_sample, "learn_seed": LEARN_SEED}}

    def dump(obj):
        with open(os.path.join(a.out_dir, "mdparity.json"), "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=1, default=str)

    if a.no_prereg_check:
        meta["prereg"] = {"committed_at": None, "error": "not checked"}
    else:
        meta["prereg"] = wait_for_prereg(a.prereg_path, a.wait_prereg_minutes, opener, sleep)
        if a.wait_prereg_minutes > 0 and meta["prereg"].get("committed_at") is None:
            print("pre-registration %s not found; nothing was read" % a.prereg_path)
            dump({"meta": meta})
            return 3

    fetch = fetch or default_fetch
    vtext, vsha = load_frame_file(a.vendor_pages, fetch)
    ltext, lsha = load_frame_file(a.learn_pages, fetch)
    meta["frame_files"] = {"vendor_pages": {"source": a.vendor_pages, "sha256": vsha},
                           "learn_pages": {"source": a.learn_pages, "sha256": lsha}}
    frame = vendor_frame(read_csv_text(vtext)) + learn_frame(read_csv_text(ltext), a.learn_sample)
    meta["frame_pages"] = len(frame)
    print("frame: %d pages" % len(frame))
    sys.stdout.flush()

    robots_for = make_robots(fetch, sleep)
    rows, missing = [], []
    for i, entry in enumerate(frame):
        row, miss, ev = check_page(entry, fetch, sleep, robots_for)
        rows.append(row)
        missing.extend(miss)
        if ev is not None and not a.no_evidence:
            d = os.path.join(a.out_dir, "evidence", entry["site"])
            os.makedirs(d, exist_ok=True)
            stem = os.path.join(d, "%03d" % i)
            with open(stem + ".md", "w", encoding="utf-8") as fh:
                fh.write("<!-- %s -->\n" % row["md_url"] + ev["md"])
            with open(stem + ".blocks.tsv", "w", encoding="utf-8") as fh:
                fh.write("# %s\n" % entry["url"] + ev["blocks"] + "\n")
        print("%3d %-12s %-15s prose %s/%s callout %s/%s %s" % (
            i, entry["site"], row["status"], row["prose_present"], row["prose"], row["callout_present"],
            row["callout"], entry["url"]))
        sys.stdout.flush()

    summary, sites = summarise(rows)
    meta["finished"] = utcnow()
    write_csv(os.path.join(a.out_dir, "pages.csv"), rows, PAGE_COLUMNS)
    write_csv(os.path.join(a.out_dir, "sites.csv"), sites, SITE_COLUMNS)
    write_csv(os.path.join(a.out_dir, "missing.csv"), missing, MISSING_COLUMNS)
    dump({"meta": meta, "summary": summary, "sites": sites})
    text = report(meta, summary, sites)
    with open(os.path.join(a.out_dir, "MDPARITY_AUTO.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
