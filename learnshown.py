#!/usr/bin/env python3
# Copyright 2026 Munim, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
"""learnshown 0.2.0: does Microsoft Learn tell its readers, people and agents, that an article was made with AI?

Study 8 of tech-writing-ai-rules. Microsoft's principles for AI-generated content say: "All
articles that contain any AI-generated content include text acknowledging the role of AI.
You'll see this text at the end of the article." Authors mark such articles with an AI-usage
front matter entry (study 7 counts those labels). This tool checks what the published pages
actually show.

It builds study 7's frame of MicrosoftDocs repos (it imports learnlabels.py 0.1.0 for the
frame, the sparse clone and the front matter parser), reads repos in size order until
TARGET repos with at least MIN_LABELLED AI-labelled articles have been read, and draws up to
PER_STRATUM articles per repo from each pre-registered stratum by a seeded random draw:

  A  key exactly `ai-usage`, value ai-assisted       B  key exactly `ai-usage`, value ai-generated
  C  another AI key spelling (ms.ai-usage, ai.usage, ...) with ai-assisted or ai-generated
  D  an AI key whose value names AI in another form   U  no AI key (unlabelled)

0.2.0 (study 8, amendment 1). Each article's live URL is found by trying candidates in order:
the base path of the nearest docfx.json's `globalMetadata.breadcrumb_path` (a final
`breadcrumb` / `bread` folder dropped), its first segment, 0.1.0's `build.dest` rule (each also
in lower case), and last the first 5 en-us results of Learn's public search API for the
article's title. The first candidate whose fetched form names this exact repo file as its source
(`source_path` / `original_content_git_url`) is used; pages no candidate confirms are reported,
not counted. Each page is then fetched twice from learn.microsoft.com: as HTML (what people are
served) and as Markdown (`Accept: text/markdown`, what agents such as Copilot Chat and Claude
Code ask for). With --render, each counted page is also loaded in headless Chromium
(Playwright), so text that page scripts add is seen; the acknowledgement predictions are then
graded on the rendered text. The tool records whether each form carries the AI label and a
sentence acknowledging AI, and which of the source's level-2 headings the Markdown copy keeps.
No article text is kept, only the matched disclosure sentence (at most 200 characters).

Usage: python learnshown.py --out-dir OUT [--render] [--wait-prereg-minutes 240] [--no-prereg-check]

Outputs: frame.csv, pages.csv, shown.json, LEARNSHOWN_AUTO.md.
Standard library only, plus the git command line and learnlabels.py (and Playwright for
--render). Apache-2.0.
Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""

import argparse
import collections
import csv
import datetime
import html as htmlmod
import json
import os
import random
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

import learnlabels as ll

VERSION = "0.2.0"
USER_AGENT = ("tech-writing-ai-rules-learnshown/%s (+https://github.com/munimtechnologies/"
              "tech-writing-ai-rules; mv2@munimtech.com)" % VERSION)
PREREG_PATH = "census/2026-11-ms-learn-ai-shown/PREREGISTRATION.md"
LEARN = "https://learn.microsoft.com"
LOCALE = "en-us"
TARGET_REPOS = 15
MIN_LABELLED = 10
MAX_CLONES = 30
PER_STRATUM = 8
STRATA = ("A", "B", "C", "D", "U")
LABELLED = ("A", "B", "C")
DELAY = 1.0
MAX_BYTES = 3000000
GATE_LABELLED = 100
GATE_REPOS = 8
GATE_MD_PCT = 90
MIN_P = {"P1": 20, "P2": 10, "P3": 20, "P4": 20, "P5": 20, "P6": 20}
END_HEADINGS = {"next steps", "next step", "related content"}
BREAD_DIRS = {"breadcrumb", "_breadcrumb", "bread", "_bread"}
SEARCH_TOP = 5
RENDER_NAV_MS = 60000
RENDER_IDLE_MS = 15000
RENDER_SETTLE_MS = 2000

# The two pages read by hand before the pre-registration was written; never sampled.
SEEN = {("MicrosoftDocs/azure-docs", "articles/dev-box/overview-what-is-dev-box-mcp-server.md"),
        ("MicrosoftDocs/entra-docs", "docs/identity-platform/quickstart-register-app.md")}
CONTROLS = [
    ("control-positive", "MicrosoftDocs/entra-docs", "docs/identity-platform/quickstart-register-app.md",
     LEARN + "/en-us/entra/identity-platform/quickstart-register-app"),
    ("control-seen", "MicrosoftDocs/azure-docs", "articles/dev-box/overview-what-is-dev-box-mcp-server.md",
     LEARN + "/en-us/azure/dev-box/overview-what-is-dev-box-mcp-server"),
]

DISCLOSE_RE = re.compile(
    r"\b(?:created|written|generated|produced|drafted|authored|prepared)\b[^.!?]{0,80}?"
    r"\b(?:with|by|using|from)\b[^.!?]{0,40}?(?:\bAI\b|\bartificial intelligence\b)", re.I)
ALT_RE = re.compile(r"\bAI[- ](?:assisted|generated)\s+content\b", re.I)
SUBJECT_RE = re.compile(r"\b(?:article|page|content|document|documentation|topic)\b", re.I)
RAW_RE = re.compile(r"(?:assistance from|help of|generated by|created with|created by)\s+(?:the\s+)?AI\b", re.I)
META_RE = re.compile(r"<meta\b[^>]*>", re.I)
ATTR_RE = re.compile(r"([A-Za-z_:][A-Za-z0-9_:.\-]*)\s*=\s*(?:\"([^\"]*)\"|'([^']*)')")
DROP_RE = re.compile(r"<(script|style|noscript)\b[^>]*>.*?</\1\s*>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
BLOCK_RE = re.compile(r"</?(?:p|div|li|ul|ol|h[1-6]|br|tr|td|th|table|section|aside|article|main|header|"
                      r"footer|nav|blockquote|details|summary|dt|dd|form|button|figure|figcaption)\b[^>]*>", re.I)
H2_RE = re.compile(r"^ {0,3}##(?!#)[ \t]+(.+?)[ \t]*#*[ \t]*$")

PAGE_COLUMNS = ["repo", "path", "stratum", "src_key", "src_value", "src_category", "src_year",
                "url", "url_rule", "tried", "final_url", "md_status", "md_ctype", "md_served", "html_status",
                "mapped", "md_ai_key", "md_ai_value", "html_ai_key", "html_ai_value", "note_html",
                "note_html_text", "note_raw_html", "render_status", "note_rendered", "note_rendered_text",
                "note_md", "note_md_text", "src_h2", "md_h2_missing", "last_src_h2", "last_h2_missing"]
FRAME_COLUMNS = ["rank", "repo", "status", "commit", "articles", "labelled", "A", "B", "C", "D",
                 "U", "sampled", "docfx_files"]


# ---------------------------------------------------------------- strata and the draw

def stratum(f):
    """A, B, C, D or U for an article (see the module docstring); '' if not sampled."""
    if not f.get("is_article"):
        return ""
    cat = f.get("category") or ""
    if cat == "":
        return "U"
    if cat in ("ai-assisted", "ai-generated"):
        if f.get("ai_key") == "ai-usage":
            return "A" if cat == "ai-assisted" else "B"
        return "C"
    if cat == "other-ai":
        return "D"
    return ""


def strata_counts(files):
    c = collections.Counter(stratum(f) for f in files)
    return {s: c[s] for s in STRATA}


def draw(files, repo, per=PER_STRATUM, seen=SEEN):
    """Up to `per` articles from each stratum, by a seeded draw over the path-sorted pool."""
    pools = collections.defaultdict(list)
    for f in files:
        s = stratum(f)
        if s and (repo, f["path"]) not in seen:
            pools[s].append(f)
    picked = []
    for s in STRATA:
        pool = sorted(pools[s], key=lambda f: f["path"])
        if len(pool) > per:
            pool = random.Random("study8|%s|%s" % (repo, s)).sample(pool, per)
        for f in sorted(pool, key=lambda f: f["path"]):
            row = dict(f)
            row.update(repo=repo, stratum=s)
            picked.append(row)
    return picked


# ---------------------------------------------------------------- docfx.json -> URL

def clean_path(p):
    """'./cyclecloud/' -> 'cyclecloud', '.' -> '', 'a\\b' -> 'a/b'."""
    return "/".join(x for x in str(p or "").replace("\\", "/").split("/") if x not in ("", "."))


def breadcrumb_base(bp):
    """Learn base path from a docfx breadcrumb_path: '/fabric/breadcrumb/toc.json' -> 'fabric',
    '/azure/architecture/bread/toc.json' -> 'azure/architecture', '/dynamics365/ops-bc/toc.json'
    -> 'dynamics365/ops-bc'. A relative or empty path gives ''."""
    bp = str(bp or "").strip().replace("\\", "/")
    if not bp.startswith("/"):
        return ""
    segs = [s for s in bp.split("/") if s][:-1]
    if segs and segs[-1].lower() in BREAD_DIRS:
        segs = segs[:-1]
    return "/".join(segs)


def docfx_map(text):
    """{'dest': build.dest, 'bread': breadcrumb base, 'content': [(src, dest), ...]} for content
    entries that take .md files."""
    obj = ll.load_json_loose(text)
    if not isinstance(obj, dict) or not isinstance(obj.get("build"), dict):
        return None
    build = obj["build"]
    entries = []
    for c in build.get("content") or []:
        if not isinstance(c, dict):
            continue
        globs = c.get("files") or []
        if isinstance(globs, str):
            globs = [globs]
        if not any("md" in str(g).lower() or str(g).endswith("*") for g in globs):
            continue
        entries.append((clean_path(c.get("src")), clean_path(c.get("dest"))))
    gm = build.get("globalMetadata") if isinstance(build.get("globalMetadata"), dict) else {}
    return {"dest": clean_path(build.get("dest")), "bread": breadcrumb_base(gm.get("breadcrumb_path")),
            "content": entries}


def find_docfx(root):
    """{repo-relative folder ('' for the root): mapping} for every docfx.json outside dot folders."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        if "docfx.json" in filenames:
            rel = ll.norm_path(os.path.relpath(dirpath, root))
            rel = "" if rel == "." else rel
            try:
                with open(os.path.join(dirpath, "docfx.json"), "rb") as fh:
                    m = docfx_map(fh.read().decode("utf-8-sig", "replace"))
            except OSError:
                m = None
            if m:
                out[rel] = m
    return out


def _under(path, prefix):
    return prefix == "" or path == prefix or path.startswith(prefix + "/")


def _locate(path, maps):
    """(mapping, entry dest, path below the entry's src without .md) for `path`, or None."""
    path = ll.norm_path(path)
    dirs = [d for d in maps if _under(path, d) and path != d]
    if not dirs:
        return None
    d = max(dirs, key=len)
    rel = path[len(d) + 1:] if d else path
    m = maps[d]
    srcs = [(s, e) for s, e in m["content"] if _under(rel, s) and rel != s]
    if not srcs:
        return None
    src, edest = max(srcs, key=lambda se: len(se[0]))
    sub = rel[len(src) + 1:] if src else rel
    if not sub.lower().endswith(".md"):
        return None
    sub = sub[:-3]
    leaf = sub.split("/")[-1]
    if leaf.lower() == "index":
        sub = sub[:len(sub) - len(leaf)]
    return m, edest, sub


def _url(parts, sub):
    parts = [p for p in parts if p]
    if sub:
        url_path = "/".join(parts + [sub])
    else:
        url_path = "/".join(parts) + "/"
    return "%s/%s/%s" % (LEARN, LOCALE, url_path.lstrip("/"))


def page_url(path, maps):
    """0.1.0's rule: the en-us URL from build.dest / entry dest / path, or '' if none."""
    loc = _locate(path, maps)
    if not loc:
        return ""
    m, edest, sub = loc
    return _url([m["dest"], edest], sub)


def candidate_urls(path, maps):
    """[(rule, url), ...] in the order amendment 1 tries them, without repeats."""
    loc = _locate(path, maps)
    if not loc:
        return []
    m, edest, sub = loc
    bread = m.get("bread") or ""
    raw = []
    if bread:
        raw.append(("breadcrumb", _url([bread, edest], sub)))
        root = bread.split("/")[0]
        if root != bread:
            raw.append(("breadcrumb-root", _url([root, edest], sub)))
    raw.append(("docfx-dest", _url([m["dest"], edest], sub)))
    out, seen = [], set()
    for rule, u in raw:
        for r2, u2 in ((rule, u), (rule + "-lower", u.lower())):
            if u2 not in seen:
                seen.add(u2)
                out.append((r2, u2))
    return out


# ---------------------------------------------------------------- reading the two forms

def split_front(text):
    """(front matter lines or None, body after the front matter)."""
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, min(len(lines), 400)):
            if lines[i].strip() in ("---", "..."):
                return lines[1:i], "\n".join(lines[i + 1:])
    return None, text


def norm_heading(h):
    h = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", h)
    h = TAG_RE.sub("", h)
    return re.sub(r"[^0-9a-z]+", " ", h.lower()).strip()


def h2s(text):
    """Normalised level-2 ATX headings outside fenced code blocks."""
    out, fence = [], None
    for line in text.splitlines():
        s = line.lstrip()
        if s.startswith("```") or s.startswith("~~~"):
            if fence is None:
                fence = s[:3]
            elif s.startswith(fence):
                fence = None
            continue
        if fence:
            continue
        m = H2_RE.match(line)
        if m:
            h = norm_heading(m.group(1))
            if h:
                out.append(h)
    return out


def disclosure(text):
    """The first sentence that acknowledges AI's role in making the page, or ''. Paragraphs are
    split at blank lines, then into sentences at . ! or ?."""
    for para in re.split(r"\n[ \t]*\n", text or ""):
        flat = re.sub(r"\s+", " ", para).strip()
        for sent in re.split(r"(?<=[.!?])\s+", flat):
            if not sent or len(sent) > 400:
                continue
            if ALT_RE.search(sent) or (DISCLOSE_RE.search(sent) and SUBJECT_RE.search(sent)):
                return sent.strip()[:200]
    return ""


def rendered_note(text):
    """disclosure() over rendered text (document.body.innerText), each line its own paragraph."""
    return disclosure(re.sub(r"\r?\n", "\n\n", text or ""))


def is_html(text, ctype):
    return "html" in (ctype or "").lower() or "<html" in (text or "")[:3000].lower()


def md_served(status, ctype, text):
    if status != 200:
        return False
    if "markdown" in (ctype or "").lower():
        return True
    return (text or "").lstrip("﻿").startswith("---") and not is_html(text, ctype)


def read_md_copy(text):
    lines, body = split_front(text or "")
    fields = ll.parse_fields(lines) if lines is not None else collections.OrderedDict()
    key, val = ll.ai_label(fields)
    return {"ai_key": key, "ai_value": val[:60], "source_path": fields.get("source_path", ""),
            "git_url": fields.get("original_content_git_url", ""), "note": disclosure(body),
            "h2": h2s(body)}


def html_metas(text):
    metas = collections.OrderedDict()
    for tag in META_RE.findall(text or ""):
        attrs = {}
        for m in ATTR_RE.finditer(tag):
            attrs[m.group(1).lower()] = m.group(2) if m.group(2) is not None else m.group(3)
        name = attrs.get("name") or attrs.get("property")
        if name and "content" in attrs and name not in metas:
            metas[name] = htmlmod.unescape(attrs["content"])
    return metas


def visible_text(text):
    """Page text without scripts and styles; block elements become paragraph breaks."""
    t = DROP_RE.sub(" ", text or "")
    t = BLOCK_RE.sub("\n\n", t)
    return htmlmod.unescape(TAG_RE.sub(" ", t))


def read_html(text):
    metas = html_metas(text)
    key, val = ll.ai_label(metas)
    return {"ai_key": key, "ai_value": val[:60], "source_path": metas.get("source_path", ""),
            "git_url": metas.get("original_content_git_url", ""), "note": disclosure(visible_text(text)),
            "raw": bool(RAW_RE.search(text or ""))}


def mapped(path, *forms):
    """'yes' if any fetched form names this repo path as its source, 'no' if one names another
    path, 'unknown' if none names a source."""
    want = ll.norm_path(path).lower()
    named = False
    for f in forms:
        for v in (f.get("source_path"), f.get("git_url")):
            v = ll.norm_path(v or "").lower()
            if not v:
                continue
            named = True
            if v == want or v.endswith("/" + want):
                return "yes"
    return "no" if named else "unknown"


# ---------------------------------------------------------------- HTTP and rendering

def default_fetch(url, accept):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read(MAX_BYTES)
            return resp.status, resp.headers.get("Content-Type", ""), resp.geturl(), body.decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, "", url, ""
    except Exception as exc:  # network errors, timeouts
        return 0, type(exc).__name__, url, ""


def polite_fetch(fetch, url, accept, sleep):
    sleep(DELAY)
    got = fetch(url, accept)
    if got[0] in (429, 503):
        sleep(60)
        got = fetch(url, accept)
    return got


def robots_ok(fetch):
    """(function url -> bool, HTTP status) from learn.microsoft.com/robots.txt for this tool's
    agent name. An unreadable robots.txt allows everything (urllib.robotparser's behaviour for an
    empty file); its status is recorded."""
    status, _ct, _u, text = fetch(LEARN + "/robots.txt", "text/plain")
    rp = urllib.robotparser.RobotFileParser()
    rp.parse((text or "").splitlines() if status == 200 else [])
    return (lambda url: rp.can_fetch(USER_AGENT, url)), status


def make_renderer():
    """(render(url) -> (status, text), close()) with headless Chromium through Playwright.
    Raises if Playwright or its browser is missing."""
    from playwright.sync_api import sync_playwright  # only needed with --render
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    probe = browser.new_page()
    ua = probe.evaluate("navigator.userAgent")
    probe.close()
    ctx = browser.new_context(user_agent="%s %s" % (ua, USER_AGENT), locale="en-US")

    def render(url):
        page = ctx.new_page()
        try:
            resp = page.goto(url, wait_until="load", timeout=RENDER_NAV_MS)
            try:
                page.wait_for_load_state("networkidle", timeout=RENDER_IDLE_MS)
            except Exception:
                pass
            page.evaluate("window.scrollTo(0, document.body ? document.body.scrollHeight : 0)")
            page.wait_for_timeout(RENDER_SETTLE_MS)
            text = page.evaluate("document.body ? document.body.innerText : ''")
            return (resp.status if resp else 0), (text or "")
        except Exception:
            return 0, ""
        finally:
            try:
                page.close()
            except Exception:
                pass

    def close():
        for f in (ctx.close, browser.close, pw.stop):
            try:
                f()
            except Exception:
                pass

    return render, close


def first_fetch(url, fetch, sleep):
    """Fetch one candidate URL as Markdown; the answer tells us which source file it shows."""
    st, ct, final, text = polite_fetch(fetch, url, "text/markdown", sleep)
    served = md_served(st, ct, text)
    md = {"source_path": "", "git_url": ""}
    if served:
        md = read_md_copy(text)
    elif st == 200 and is_html(text, ct):
        md = read_html(text)  # still tells us the source path
    return {"status": st, "ctype": ct, "final": final, "served": served, "md": md}


def search_urls(title, fetch, sleep, allowed, top=SEARCH_TOP):
    """The first `top` en-us page URLs Learn's public search API returns for `title`."""
    title = (title or "").strip()
    if not title:
        return []
    url = "%s/api/search?search=%s&locale=%s&$top=%d" % (LEARN, urllib.parse.quote(title), LOCALE, top)
    if not allowed(url):
        return []
    st, _ct, _f, text = polite_fetch(fetch, url, "application/json", sleep)
    if st != 200:
        return []
    try:
        obj = json.loads(text)
    except ValueError:
        return []
    results = obj.get("results") if isinstance(obj, dict) else None
    out = []
    for r in results if isinstance(results, list) else []:
        u = r.get("url") if isinstance(r, dict) else None
        if isinstance(u, str) and u.startswith("%s/%s/" % (LEARN, LOCALE)):
            u = u.split("#")[0].split("?")[0]
            if u not in out:
                out.append(u)
    return out[:top]


def check_page(row, fetch, sleep, allowed, render=None):
    """Find the page's live URL and fill the live columns of one sampled page row."""
    cands = list(row.get("_cands") or [])
    if not cands and row.get("url"):
        cands = [("given", row["url"])]
    title = row.get("_title") or ""
    row.update(md_status="", md_ctype="", md_served=False, html_status="", mapped="unknown",
               md_ai_key="", md_ai_value="", html_ai_key="", html_ai_value="", note_html=False,
               note_html_text="", note_raw_html=False, note_md=False, note_md_text="", final_url="",
               md_h2_missing="", last_h2_missing="", url_rule="", tried=0, render_status="",
               note_rendered=False, note_rendered_text="")
    chosen = first = None
    tried = []
    searched = False
    i = 0
    while True:
        if i >= len(cands):
            if searched or not title:
                break
            searched = True
            known = set(u for _r, u in cands)
            for u in search_urls(title, fetch, sleep, allowed):
                if u not in known:
                    cands.append(("search", u))
            if i >= len(cands):
                break
        rule, url = cands[i]
        i += 1
        if url in tried:
            continue
        tried.append(url)
        if not allowed(url):
            if first is None:
                first = (rule, url, None)
            continue
        got = first_fetch(url, fetch, sleep)
        if first is None:
            first = (rule, url, got)
        if mapped(row["path"], got["md"]) == "yes":
            chosen = (rule, url, got)
            break
    row["tried"] = len(tried)
    pick = chosen or first
    if pick is None:
        row["mapped"] = "no url"
        return row
    rule, url, got = pick
    row.update(url=url, url_rule=rule)
    if got is None:
        row["mapped"] = "robots"
        return row
    row.update(md_status=got["status"], md_ctype=(got["ctype"] or "")[:60], final_url=got["final"])
    md = got["md"]
    if got["served"]:
        row["md_served"] = True
        row.update(md_ai_key=md["ai_key"], md_ai_value=md["ai_value"], note_md=bool(md["note"]),
                   note_md_text=md["note"])
    st2, ct2, final2, text2 = polite_fetch(fetch, url, "text/html,application/xhtml+xml", sleep)
    row["html_status"] = st2
    h = {"source_path": "", "git_url": ""}
    if st2 == 200 and is_html(text2, ct2):
        h = read_html(text2)
        row.update(html_ai_key=h["ai_key"], html_ai_value=h["ai_value"], note_html=bool(h["note"]),
                   note_html_text=h["note"], note_raw_html=h["raw"])
        row["final_url"] = row["final_url"] or final2
    row["mapped"] = mapped(row["path"], md, h)
    if render and row["mapped"] == "yes" and st2 == 200:
        sleep(DELAY)
        rst, rtext = render(url)
        note = rendered_note(rtext)
        row.update(render_status=rst, note_rendered=bool(note), note_rendered_text=note)
    src = row.get("_src_h2") or []
    if row["md_served"]:
        have = set(md.get("h2") or [])
        row["md_h2_missing"] = sum(1 for x in src if x not in have)
        if src:
            row["last_h2_missing"] = src[-1] not in have
    return row


# ---------------------------------------------------------------- summary and predictions

def pct(a, b):
    return round(100.0 * a / b, 2) if b else None


def _share(rows, test):
    return sum(1 for r in rows if test(r)), len(rows)


def summarise(pages, controls, rows, note_field="note_html"):
    """Gates and predictions. `note_field` is the acknowledgement measure for G2 and P1 to P4:
    'note_html' (served HTML, the pre-registration) or 'note_rendered' (amendment 1, --render)."""
    nf = note_field
    ok = [p for p in pages if p.get("mapped") == "yes" and p.get("html_status") == 200]
    lab = [p for p in ok if p["stratum"] in LABELLED]
    lab_repos = sorted(set(p["repo"] for p in lab))
    md_ok = [p for p in ok if p.get("md_served")]
    pos = [c for c in controls if c["stratum"] == "control-positive"]
    g1 = len(lab) >= GATE_LABELLED and len(lab_repos) >= GATE_REPOS
    g2 = bool(pos) and bool(pos[0].get(nf))
    g3 = bool(ok) and 100 * len(md_ok) >= GATE_MD_PCT * len(ok)

    def grade(name, k, n, holds, needs_html=False, needs_md=False):
        graded = g1 and n >= MIN_P[name] and (g2 or not needs_html) and (g3 or not needs_md)
        return {"k": k, "n": n, "value_pct": pct(k, n), "held": holds(k, n) if graded else None}

    preds = collections.OrderedDict()
    ab = [p for p in ok if p["stratum"] in ("A", "B")]
    k, n = _share(ab, lambda p: p.get(nf))
    preds["P1"] = grade("P1", k, n, lambda k, n: 100 * k >= 90 * n, needs_html=True)
    c = [p for p in ok if p["stratum"] == "C"]
    k, n = _share(c, lambda p: p.get(nf))
    preds["P2"] = grade("P2", k, n, lambda k, n: 100 * k <= 20 * n, needs_html=True)
    u = [p for p in ok if p["stratum"] == "U"]
    k, n = _share(u, lambda p: p.get(nf))
    preds["P3"] = grade("P3", k, n, lambda k, n: 100 * k <= 5 * n, needs_html=True)
    shown = [p for p in lab if p.get(nf) and p.get("md_served")]
    k, n = _share(shown, lambda p: p.get("note_md"))
    preds["P4"] = grade("P4", k, n, lambda k, n: 100 * k <= 20 * n, needs_html=True, needs_md=True)
    labmd = [p for p in lab if p.get("md_served")]
    k, n = _share(labmd, lambda p: bool(p.get("md_ai_key")))
    preds["P5"] = grade("P5", k, n, lambda k, n: 100 * k >= 90 * n, needs_md=True)
    ends = [p for p in md_ok if p.get("last_src_h2") in END_HEADINGS and p.get("last_h2_missing") != ""]
    k, n = _share(ends, lambda p: p.get("last_h2_missing") is True)
    preds["P6"] = grade("P6", k, n, lambda k, n: 100 * k >= 80 * n, needs_md=True)

    by_stratum = collections.OrderedDict()
    for s in STRATA:
        sp = [p for p in ok if p["stratum"] == s]
        sm = [p for p in sp if p.get("md_served")]
        by_stratum[s] = {
            "sampled": sum(1 for p in pages if p["stratum"] == s), "mapped_ok": len(sp),
            "note_html": sum(1 for p in sp if p.get("note_html")),
            "note_rendered": sum(1 for p in sp if p.get("note_rendered")),
            "note_raw_html": sum(1 for p in sp if p.get("note_raw_html")),
            "html_ai_meta": sum(1 for p in sp if p.get("html_ai_key")),
            "md_served": len(sm), "note_md": sum(1 for p in sm if p.get("note_md")),
            "md_ai_key": sum(1 for p in sm if p.get("md_ai_key")),
            "any_h2_missing": sum(1 for p in sm if (p.get("md_h2_missing") or 0) > 0),
            "last_h2_missing": sum(1 for p in sm if p.get("last_h2_missing") is True)}
    by_value = collections.OrderedDict()
    for v in ("ai-assisted", "ai-generated"):
        vp = [p for p in lab if p.get("src_category") == v]
        by_value[v] = {"pages": len(vp), "note": sum(1 for p in vp if p.get(nf))}
    keys = collections.Counter(p.get("src_key") for p in ok if p["stratum"] in ("C", "D"))
    notes = collections.Counter(p.get(nf + "_text") for p in ok if p.get(nf))
    last = collections.Counter(p.get("last_src_h2") or "(none)" for p in md_ok)
    status = collections.Counter(p.get("mapped") for p in pages)
    rules = collections.Counter(p.get("url_rule") or "(none)" for p in ok)
    return collections.OrderedDict([
        ("note_measure", nf),
        ("pages_sampled", len(pages)), ("mapped_status", dict(status)), ("mapped_ok", len(ok)),
        ("url_rules", dict(rules)),
        ("labelled_ok", len(lab)), ("labelled_repos", len(lab_repos)), ("md_served", len(md_ok)),
        ("by_stratum", by_stratum), ("by_value", by_value), ("other_keys", dict(keys)),
        ("note_texts", dict(notes.most_common(15))), ("last_src_h2", dict(last.most_common(15))),
        ("controls", [{k2: c2.get(k2) for k2 in ("stratum", "url", "url_rule", "html_status", "md_served",
                                                   "mapped", "note_html", "note_html_text", "render_status",
                                                   "note_rendered", "note_rendered_text", "note_md",
                                                   "md_ai_key", "html_ai_key", "last_h2_missing")}
                      for c2 in controls]),
        ("gates", {"G1": {"labelled_ok": len(lab), "repos": len(lab_repos), "passed": g1},
                   "G2": {"positive_control_note": g2, "measure": nf, "passed": g2},
                   "G3": {"md_served_pct": pct(len(md_ok), len(ok)), "passed": g3}}),
        ("repos_read", sum(1 for r in rows if r.get("status") == "read")),
        ("predictions", preds),
    ])


# ---------------------------------------------------------------- output

def write_csv(path, rows, columns):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in columns})


def report(meta, s):
    yn = {True: "yes", False: "no", None: "n/a"}
    out = ["# learnshown %s: does Microsoft Learn show readers that an article was made with AI? (automatic report)"
           % VERSION, "", "First pass written by the tool. The graded result is in RESULT.md.", "",
           "- Started %s, finished %s." % (meta["started"], meta.get("finished")),
           "- Pre-registration (or amendment) file first committed: %s." % (
               meta["prereg"].get("committed_at") or "not found (%s)" % meta["prereg"].get("error")),
           "- Acknowledgement measure for G2 and P1 to P4: %s." % s["note_measure"],
           "- Repos read: %d. Pages sampled: %d; mapped and fetched as HTML: %d; labelled (A-C): %d from %d repos; "
           "Markdown copy served: %d." % (s["repos_read"], s["pages_sampled"], s["mapped_ok"], s["labelled_ok"],
                                          s["labelled_repos"], s["md_served"]),
           "- Mapping: %s." % ", ".join("%s %d" % kv for kv in sorted(s["mapped_status"].items(), key=str)),
           "- URL rule of counted pages: %s." % (", ".join("%s %d" % kv for kv in sorted(s["url_rules"].items()))
                                                 or "none"),
           "- Gates: G1 %s, G2 %s, G3 %s." % tuple(yn[s["gates"][g]["passed"]] for g in ("G1", "G2", "G3")),
           "", "## Predictions (automatic; boundaries as pre-registered)", "", "| | k | n | % | held |",
           "|---|---|---|---|---|"]
    for k, p in s["predictions"].items():
        out.append("| %s | %d | %d | %s | %s |" % (k, p["k"], p["n"], p["value_pct"], yn[p["held"]]))
    out += ["", "## By stratum", "",
            "| stratum | sampled | mapped | note in served HTML | note rendered | AI meta in HTML | MD served | "
            "note in MD | AI key in MD | last h2 missing in MD |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for st, v in s["by_stratum"].items():
        out.append("| %s | %d | %d | %d | %d | %d | %d | %d | %d | %d |" % (
            st, v["sampled"], v["mapped_ok"], v["note_html"], v["note_rendered"], v["html_ai_meta"],
            v["md_served"], v["note_md"], v["md_ai_key"], v["last_h2_missing"]))
    out += ["", "## Acknowledgement sentences seen (%s)" % s["note_measure"], ""]
    out += ["- %d x \"%s\"" % (n, t) for t, n in s["note_texts"].items()] or ["- none"]
    out += ["", "## Controls", ""]
    out += ["- %s" % json.dumps(c) for c in s["controls"]]
    return "\n".join(out) + "\n"


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_text(path, limit=2000000):
    with open(path, "rb") as fh:
        return fh.read(limit).decode("utf-8-sig", "replace")


def main(argv=None, opener=None, lister=None, cloner=None, fetch=None, sleep=time.sleep, renderer=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--target", type=int, default=TARGET_REPOS)
    ap.add_argument("--max-clones", type=int, default=MAX_CLONES)
    ap.add_argument("--per-stratum", type=int, default=PER_STRATUM)
    ap.add_argument("--prereg-path", default=PREREG_PATH)
    ap.add_argument("--no-prereg-check", action="store_true")
    ap.add_argument("--wait-prereg-minutes", type=float, default=0)
    ap.add_argument("--render", action="store_true",
                    help="also load each counted page in headless Chromium (Playwright); amendment 1")
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    meta = {"version": VERSION, "learnlabels_version": ll.VERSION, "started": utcnow(),
            "settings": {"target": a.target, "max_clones": a.max_clones, "per_stratum": a.per_stratum,
                         "min_labelled": MIN_LABELLED, "since": ll.PUSHED_SINCE, "render": a.render,
                         "search_top": SEARCH_TOP}}

    def dump(obj):
        with open(os.path.join(a.out_dir, "shown.json"), "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=1, default=str)

    render = close = None
    if a.render:
        try:
            render, close = (renderer or make_renderer)()
        except Exception as exc:
            meta["error"] = "renderer: %s: %s" % (type(exc).__name__, exc)
            print("cannot start the renderer (%s); nothing was read" % meta["error"])
            dump(meta)
            return 5
    note_field = "note_rendered" if render else "note_html"

    if a.no_prereg_check:
        meta["prereg"] = {"committed_at": None, "error": "not checked"}
    else:
        meta["prereg"] = ll.wait_for_prereg(a.prereg_path, a.wait_prereg_minutes, opener, sleep)
        meta["prereg"]["path"] = a.prereg_path
        if a.wait_prereg_minutes > 0 and meta["prereg"].get("committed_at") is None:
            print("pre-registration %s not found; nothing was read" % a.prereg_path)
            dump(meta)
            if close:
                close()
            return 3
    try:
        repos = (lister or (lambda: ll.list_org(opener, sleep)))()
    except RuntimeError as exc:
        meta["error"] = str(exc)
        print("cannot list the organisation: %s" % exc)
        dump(meta)
        if close:
            close()
        return 4
    eligible, excluded = ll.build_frame(repos)
    meta.update(listed=len(repos), eligible=len(eligible), excluded=dict(excluded))
    print("listed %d repos, %d eligible" % (len(repos), len(eligible)))

    cloner = cloner or ll.git_clone
    fetch = fetch or default_fetch
    work = tempfile.mkdtemp(prefix="learnshown-")
    rows, pages = [], []
    read = clones = 0
    for rank, r in enumerate(eligible, 1):
        row = {"rank": rank, "repo": r["full_name"], "status": "not reached", "commit": ""}
        if read < a.target and clones < a.max_clones:
            clones += 1
            dest = os.path.join(work, "r%03d" % rank)
            err, commit = cloner(r["full_name"], r["default_branch"], dest)
            if err:
                row["status"] = err
            else:
                files, _docfx = ll.scan_repo(dest)
                counts = strata_counts(files)
                labelled = sum(counts[s] for s in ("A", "B", "C", "D"))
                maps = find_docfx(dest)
                row.update(counts, commit=commit, articles=sum(1 for f in files if f["is_article"]),
                           labelled=labelled, docfx_files=len(maps))
                if labelled >= MIN_LABELLED:
                    row["status"] = "read"
                    read += 1
                    picked = draw(files, r["full_name"], a.per_stratum)
                    for p in picked:
                        p["_cands"] = candidate_urls(p["path"], maps)
                        p["url"] = p["_cands"][0][1] if p["_cands"] else ""
                        p.update(src_key=p["ai_key"], src_value=p["ai_value"], src_category=p["category"],
                                 src_year=p["year"])
                        try:
                            fm, body = split_front(read_text(os.path.join(dest, p["path"])))
                        except OSError:
                            fm, body = None, ""
                        fields = ll.parse_fields(fm) if fm is not None else {}
                        p["_title"] = fields.get("title", "")
                        src = h2s(body)
                        p["_src_h2"] = src
                        p["src_h2"] = len(src)
                        p["last_src_h2"] = src[-1] if src else ""
                    pages.extend(picked)
                    row["sampled"] = len(picked)
                else:
                    row["status"] = "too few labelled"
            shutil.rmtree(dest, ignore_errors=True)
            print("%3d %-50s %-18s labelled %s sampled %s" % (rank, r["full_name"], str(row["status"])[:18],
                                                             row.get("labelled", ""), row.get("sampled", "")))
            sys.stdout.flush()
        rows.append(row)
    shutil.rmtree(work, ignore_errors=True)

    allowed, meta["robots_status"] = robots_ok(fetch)
    controls = []
    for name, repo, path, url in CONTROLS:
        controls.append(check_page({"repo": repo, "path": path, "stratum": name, "url": url}, fetch, sleep,
                                   allowed, render))
    for i, p in enumerate(pages, 1):
        check_page(p, fetch, sleep, allowed, render)
        if i % 25 == 0:
            print("checked %d of %d pages" % (i, len(pages)))
            sys.stdout.flush()
    if close:
        close()

    summary = summarise(pages, controls, rows, note_field)
    meta["finished"] = utcnow()
    meta["clones"] = clones
    write_csv(os.path.join(a.out_dir, "frame.csv"), rows, FRAME_COLUMNS)
    write_csv(os.path.join(a.out_dir, "pages.csv"), controls + pages, PAGE_COLUMNS)
    dump({"meta": meta, "summary": summary})
    text = report(meta, summary)
    with open(os.path.join(a.out_dir, "LEARNSHOWN_AUTO.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
