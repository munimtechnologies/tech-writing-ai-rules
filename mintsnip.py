#!/usr/bin/env python3
# mintsnip.py 0.1.0 - Apache-2.0
# By MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
#
# Study 16 tool: do the Markdown copies that Mintlify docs sites serve to AI
# agents (<page>.md) carry the content of <Snippet file="..."/> tags, as
# Mintlify's Markdown-export page says they do, or the bare tag?
#
# Mintlify, "Markdown export" (read 2026-11-12): "Snippets render the content of
# the imported file, not the tag such as <Snippet file="path/to/snippet.mdx" />."
# and "If a referenced snippet file isn't found, the Markdown export includes the
# tag."  On docs.mem0.ai (2026-11-12) the .md copy of /open-source/python-quickstart
# keeps <Snippet file="get-help.mdx" /> although docs/_snippets/get-help.mdx exists
# in mem0ai/mem0 and search-engine copies of the HTML page show its text.
#
# For each site in the frame: clone the docs repo (sparse, .mdx/.md/docs.json
# only), find pages that use <Snippet file="..."> and where each file resolves
# (snippets/, _snippets/, docs root, page folder), map pages to live URLs through
# the site's own llms.txt, then read each page's .md copy and its HTML page and
# check whether the snippet's text, or the bare tag, reaches each.
#
# Standard library + git. Polite: robots.txt honoured (token "mintsnip"), one
# request at a time, a delay between requests, an identifying User-Agent.

import argparse
import csv
import html as htmlmod
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser

VERSION = "0.1.0"
UA = ("mintsnip/%s (+https://github.com/munimtechnologies/tech-writing-ai-rules; "
      "MV2 of Munim, Inc., mv2@munimtech.com)" % VERSION)
ROBOTS_TOKEN = "mintsnip"
PREREG_URL = ("https://raw.githubusercontent.com/munimtechnologies/tech-writing-ai-rules/"
              "main/census/2026-11-mintlify-snippets/PREREG.md")
SAMPLE = 15         # pages with a <Snippet file> tag read per site (seeded sample)
CONTROL = 4         # pages with an import-style snippet read per site
SEED = "study16"

# The frame (fixed in PREREG.md): open-source Mintlify docs repos, the folder that
# holds docs.json ("" = repo root), and the live docs base URL.
SITES = [
    ("mem0ai/mem0", "docs", "https://docs.mem0.ai"),
    ("crewAIInc/crewAI", "docs", "https://docs.crewai.com"),
    ("browser-use/browser-use", "docs", "https://docs.browser-use.com"),
    ("Infisical/infisical", "docs", "https://infisical.com/docs"),
    ("triggerdotdev/trigger.dev", "docs", "https://trigger.dev/docs"),
    ("ollama/ollama", "docs", "https://docs.ollama.com"),
    ("mintlify/docs", "", "https://www.mintlify.com/docs"),
    ("pipecat-ai/docs", "", "https://docs.pipecat.ai"),
    ("Helicone/helicone", "docs", "https://docs.helicone.ai"),
    ("novuhq/docs", "", "https://docs.novu.co"),
    ("firecrawl/firecrawl-docs", "", "https://docs.firecrawl.dev"),
    ("langgenius/dify-docs", "", "https://docs.dify.ai"),
    ("cline/cline", "docs", "https://docs.cline.bot"),
    ("continuedev/continue", "docs", "https://docs.continue.dev"),
    ("supermemoryai/supermemory", "apps/docs", "https://supermemory.ai/docs"),
    ("agno-agi/docs", "", "https://docs.agno.com"),
    ("formbricks/formbricks", "docs", "https://formbricks.com/docs"),
    ("Unstructured-IO/docs", "", "https://docs.unstructured.io"),
    ("Portkey-AI/docs-core", "", "https://portkey.ai/docs"),
    ("lmnr-ai/docs", "", "https://docs.lmnr.ai"),
    ("AgentOps-AI/agentops", "docs", "https://docs.agentops.ai"),
    ("openlit/openlit", "docs", "https://docs.openlit.io"),
]

SNIPPET_RE = re.compile(r"""<Snippet\s+file\s*=\s*["']([^"']+)["']""")
IMPORT_RE = re.compile(r"""^\s*import\s+([A-Z]\w*)\s+from\s+["']([^"']+\.mdx?)["']\s*;?\s*$""", re.M)
FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.S)
TAG_ANY_RE = re.compile(r"<[^<>]*>", re.S)
MDLINK_RE = re.compile(r"!?\[([^\]]*)\]\(([^)\s]*)\)")
HREF_RE = re.compile(r"""href\s*=\s*["'](https?://[^"']+)["']""")
LINK_RE = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+)\)")
BARE_URL_RE = re.compile(r"(?<![(\[])\bhttps?://[^\s)<>\]]+")
MIN_NEEDLE = 15


# ---------- source analysis (offline, tested) ----------

def code_free(text):
    """Text with fenced code blocks and HTML comments removed (to find tags)."""
    text = COMMENT_RE.sub(" ", text)
    out, fence = [], None
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)[0] * 3
                continue
            out.append(line)
        elif m and m.group(1).startswith(fence):
            fence = None
    return "\n".join(out)


def snippet_tags(src):
    """Unique file= values of <Snippet file="..."> tags outside code, in order."""
    seen, out = set(), []
    for f in SNIPPET_RE.findall(code_free(src)):
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def import_snippets(src):
    """(name, path) for default imports of .md/.mdx files that the page uses as <Name."""
    body = code_free(src)
    out = []
    for name, path in IMPORT_RE.findall(body):
        if re.search(r"<%s[\s/>]" % re.escape(name), body):
            out.append((name, path))
    return out


def resolve(file_attr, docs_root, page_dir, exists=os.path.isfile):
    """Where Mintlify would find a <Snippet file>: (location label, path or None).

    Bare names are tried in snippets/, then _snippets/, then the docs root, then
    the page's folder; '/x' is root-relative; './x' and '../x' are page-relative."""
    if "{" in file_attr or "}" in file_attr:
        return "variable", None
    f = file_attr.strip()
    if f.startswith("/"):
        cands = [os.path.join(docs_root, f.lstrip("/"))]
    elif f.startswith("./") or f.startswith("../"):
        cands = [os.path.join(page_dir, f)]
    else:
        cands = [os.path.join(docs_root, "snippets", f), os.path.join(docs_root, "_snippets", f),
                 os.path.join(docs_root, f), os.path.join(page_dir, f)]
    for p in cands:
        p = os.path.normpath(p)
        if exists(p):
            return location_label(p, docs_root), p
    return "missing", None


def location_label(path, docs_root):
    """Which folder a resolved snippet file sits in, relative to the docs root."""
    rel = os.path.relpath(path, docs_root).replace("\\", "/")
    first = rel.split("/", 1)[0] if "/" in rel else ""
    if first in ("snippets", "_snippets"):
        return first
    return "other"


def resolve_import(path, docs_root, page_dir, exists=os.path.isfile):
    if path.startswith("/"):
        p = os.path.normpath(os.path.join(docs_root, path.lstrip("/")))
    else:
        p = os.path.normpath(os.path.join(page_dir, path))
    return p if exists(p) else None


def needles(snippet_src, n_text=3, n_url=2):
    """Distinctive strings of a snippet that should appear wherever it is rendered:
    the longest plain-text fragments (>= 15 chars, no braces) and absolute hrefs."""
    src = FRONTMATTER_RE.sub("", snippet_src)
    src = COMMENT_RE.sub(" ", src)
    urls = []
    for u in HREF_RE.findall(src) + [m.group(2) for m in MDLINK_RE.finditer(src)]:
        if u.startswith("http") and u not in urls:
            urls.append(u)
    lines = []
    for line in src.splitlines():
        if re.match(r"^\s*(import|export)\s", line) or FENCE_RE.match(line):
            continue
        lines.append(line)
    text = "\n".join(lines)
    text = TAG_ANY_RE.sub("\x00", text)
    text = MDLINK_RE.sub(lambda m: "\x00" + m.group(1) + "\x00", text)
    text = re.sub(r"\*\*|__|`", "\x00", text)
    frags = []
    for line in text.split("\n"):
        line = re.sub(r"^\s*(#+|>+|[-*+]|\d+[.)])\s+", "", line)
        for part in line.split("\x00"):
            part = " ".join(part.split()).strip(" :.,;")
            if len(part) >= MIN_NEEDLE and "{" not in part and "}" not in part and part not in frags:
                frags.append(part)
    frags.sort(key=lambda s: (-len(s), s))
    return frags[:n_text] + urls[:n_url]


def norm(s):
    s = htmlmod.unescape(s)
    s = (s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"')
         .replace("\u201d", '"').replace("\u00a0", " ").replace("\u2014", "-").replace("\u2013", "-"))
    s = re.sub(r"[*_`\\]", "", s)
    return " ".join(s.lower().split())


def contains_any(hay_norm, ndl):
    return any(norm(x) in hay_norm for x in ndl if norm(x))


def tag_kept(md, file_attr):
    base = re.escape(os.path.basename(file_attr))
    return re.search(r"""<Snippet\s+file\s*=\s*["'][^"']*%s["']""" % base, md) is not None


class Visible(HTMLParser):
    """Visible text of an HTML page plus every a[href] value (scripts/styles skipped)."""
    SKIP = {"script", "style", "template", "noscript"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag == "a":
            for k, v in attrs:
                if k == "href" and v:
                    self.parts.append(" %s " % v)

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def html_text(html):
    p = Visible()
    p.feed(html)
    p.close()
    return " ".join(p.parts)


# ---------- URL mapping (offline, tested) ----------

def page_slug(rel_path):
    """docs-relative file path -> Mintlify page slug (no extension; index -> folder)."""
    s = rel_path.replace("\\", "/")
    s = re.sub(r"\.mdx?$", "", s)
    if s == "index":
        return ""
    if s.endswith("/index"):
        s = s[: -len("/index")]
    return s


def llms_urls(llms_text):
    out = []
    for u in LINK_RE.findall(llms_text) + BARE_URL_RE.findall(llms_text):
        u = u.split("#", 1)[0].split("?", 1)[0].rstrip(".,;")
        if u.endswith(".md"):
            u = u[: -len(".md")]
        u = u.rstrip("/")
        if u not in out:
            out.append(u)
    return out


def map_slug(slug, urls, base):
    """The llms.txt URL for a page slug: same host as base and path exactly
    <base path>/<slug>. None if llms.txt does not list the page."""
    if not slug:
        return None
    b = urllib.parse.urlsplit(base)
    want = b.path.rstrip("/") + "/" + slug
    for u in urls:
        p = urllib.parse.urlsplit(u)
        if p.netloc == b.netloc and p.path == want:
            return u
    return None


def sample(items, key, n):
    items = sorted(items)
    if len(items) <= n:
        return items
    return sorted(random.Random("%s:%s" % (SEED, key)).sample(items, n))


def classify(kept, md_has, has_needles):
    if kept:
        return "tag-kept"
    if not has_needles:
        return "no-text"
    return "expanded" if md_has else "lost"


# ---------- grading (offline, tested) ----------

def _share(rows, pred):
    return (sum(1 for r in rows if pred(r)) / len(rows)) if rows else None


def grade(sites, inst, controls):
    """sites: rows with repo, counted. inst: per (page, tag) rows with repo, loc,
    status, has_needles, html_has. controls: rows with read, has_needles, md_has."""
    counted = [s["repo"] for s in sites if s["counted"]]
    g1 = len(counted) >= 3
    inst = [r for r in inst if r["repo"] in counted]
    res = {"counted_sites": len(counted), "instances": len(inst), "G1": g1}
    by_loc = {}
    for r in inst:
        by_loc.setdefault(r["loc"], []).append(r)
    res["tag_kept_share_by_location"] = {
        k: {"n": len(v), "tag_kept": round(_share(v, lambda r: r["status"] == "tag-kept"), 3)}
        for k, v in sorted(by_loc.items())}
    mem = [r for r in inst if r["repo"] == "mem0ai/mem0" and r["loc"] == "_snippets" and r["has_needles"]]
    und = [r for r in by_loc.get("_snippets", []) if r["has_needles"] or r["status"] == "tag-kept"]
    snp = [r for r in by_loc.get("snippets", []) if r["has_needles"] or r["status"] == "tag-kept"]
    ctl = [c for c in controls if c["read"] and c["has_needles"]]
    res_ = [r for r in inst if r["loc"] not in ("missing", "variable") and r["has_needles"]]

    def verdict(rows, minimum, test):
        if len(rows) < minimum:
            return "too few (%d < %d)" % (len(rows), minimum)
        return test(rows)

    res["P1"] = verdict(mem, 5, lambda rows: (
        _share(rows, lambda r: r["status"] == "tag-kept") >= 0.9
        and _share(rows, lambda r: r["html_has"]) >= 0.9))
    res["P2"] = verdict(und, 10, lambda rows: _share(rows, lambda r: r["status"] == "tag-kept") >= 0.8)
    res["P3"] = verdict(snp, 10, lambda rows: _share(rows, lambda r: r["status"] == "tag-kept") <= 0.2)
    res["P4"] = verdict(ctl, 5, lambda rows: _share(rows, lambda r: r["md_has"]) >= 0.8)
    res["P5"] = verdict(res_, 10, lambda rows: _share(rows, lambda r: r["html_has"]) >= 0.8)
    res["n"] = {"P1": len(mem), "P2": len(und), "P3": len(snp), "P4": len(ctl), "P5": len(res_)}
    if not g1:
        for k in ("P1", "P2", "P3", "P4", "P5"):
            res[k] = "not graded (G1 failed): " + str(res[k])
    return res


# ---------- network and repos ----------

def fetch(url, accept, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, (e.headers.get("Content-Type", "") if e.headers else ""), ""
    except Exception as e:
        return 0, "error: %s" % type(e).__name__, ""


def looks_html(ctype, text):
    head = text.lstrip()[:300].lower()
    return "text/html" in (ctype or "").lower() or head.startswith("<!doctype html") or head.startswith("<html")


class Robots:
    def __init__(self, delay):
        self.cache, self.delay = {}, delay

    def allowed(self, url):
        p = urllib.parse.urlsplit(url)
        base = "%s://%s" % (p.scheme, p.netloc)
        if base not in self.cache:
            st, _ct, txt = fetch(base + "/robots.txt", "text/plain")
            time.sleep(self.delay)
            rp = urllib.robotparser.RobotFileParser()
            if st == 200:
                rp.parse(txt.splitlines())
            elif 400 <= st < 500:
                rp.parse([])
            else:
                rp.parse(["User-agent: *", "Disallow: /"])
            self.cache[base] = rp
        return self.cache[base].can_fetch(ROBOTS_TOKEN, url)


def git(args, timeout=900):
    try:
        r = subprocess.run(["git"] + args, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stderr or "")[-300:]
    except Exception as e:
        return 1, "%s" % type(e).__name__


def clone(repo, dest):
    url = "https://github.com/%s.git" % repo
    rc, err = git(["clone", "--depth", "1", "--filter=blob:none", "--sparse", "--quiet", url, dest])
    if rc == 0:
        rc, err = git(["-C", dest, "sparse-checkout", "set", "--no-cone",
                       "*.mdx", "*.md", "docs.json", "mint.json"])
        if rc == 0:
            return "sparse"
    subprocess.run(["rm", "-rf", dest])
    rc, err = git(["clone", "--depth", "1", "--quiet", url, dest])
    return "full" if rc == 0 else "failed: " + err.replace("\n", " ")


def find_docs_root(repo_dir, hint):
    for name in ("docs.json", "mint.json"):
        if os.path.isfile(os.path.join(repo_dir, hint, name)):
            return os.path.join(repo_dir, hint)
    best = None
    for d, dirs, files in os.walk(repo_dir):
        dirs[:] = [x for x in dirs if x not in (".git", "node_modules")]
        if "docs.json" in files or "mint.json" in files:
            depth = d.count(os.sep)
            if best is None or depth < best[0]:
                best = (depth, d)
    return best[1] if best else None


def mdx_pages(docs_root):
    out = []
    for d, dirs, files in os.walk(docs_root):
        dirs[:] = [x for x in dirs if x not in (".git", "node_modules", "snippets", "_snippets")]
        for f in files:
            if f.endswith(".mdx") or f.endswith(".md"):
                rel = os.path.relpath(os.path.join(d, f), docs_root).replace("\\", "/")
                if rel.upper() in ("README.MD", "AGENTS.MD", "CLAUDE.MD", "CONTRIBUTING.MD", "LICENSE.MD"):
                    continue
                out.append(rel)
    return sorted(out)


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def excerpt(text, pattern, width=400):
    i = text.find(pattern) if pattern else -1
    if i < 0:
        return text[:width]
    return text[max(0, i - width // 2): i + width // 2]


SITE_FIELDS = ["repo", "base", "clone", "docs_root", "pages", "pages_with_tag", "pages_with_import",
               "llms_status", "llms_urls", "mapped_tag_pages", "sampled", "read", "counted", "note"]
INST_FIELDS = ["repo", "page", "url", "file", "loc", "has_needles", "md_status", "md_is_html",
               "html_status", "status", "md_has", "html_has", "needle"]
CTRL_FIELDS = ["repo", "page", "url", "import", "path", "read", "has_needles", "md_has", "html_has", "needle"]


def run(out_dir, delay, work_dir, check_prereg=True, sites=None):
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(work_dir, exist_ok=True)
    hc_dir = os.path.join(out_dir, "handcheck")
    os.makedirs(hc_dir, exist_ok=True)
    if check_prereg:
        st, _ct, txt = fetch(PREREG_URL, "text/plain")
        if st != 200 or "Study 16" not in txt:
            print("error: PREREG.md is not on main (HTTP %s); not reading any site" % st, file=sys.stderr)
            return 4
    robots = Robots(delay)
    site_rows, inst_rows, ctrl_rows = [], [], []
    hc_n = 0
    for repo, hint, base in (sites or SITES):
        row = {k: "" for k in SITE_FIELDS}
        row.update({"repo": repo, "base": base, "read": 0, "sampled": 0, "counted": False})
        site_rows.append(row)
        dest = os.path.join(work_dir, repo.replace("/", "__"))
        row["clone"] = clone(repo, dest)
        if row["clone"].startswith("failed"):
            print("%-28s clone failed" % repo)
            continue
        root = find_docs_root(dest, hint)
        if not root:
            row["note"] = "no docs.json or mint.json"
            continue
        row["docs_root"] = os.path.relpath(root, dest).replace("\\", "/")
        pages = mdx_pages(root)
        row["pages"] = len(pages)
        with_tag, with_imp = {}, {}
        for rel in pages:
            src = read(os.path.join(root, rel))
            t = snippet_tags(src)
            if t:
                with_tag[rel] = t
            im = import_snippets(src)
            if im:
                with_imp[rel] = im
        row["pages_with_tag"], row["pages_with_import"] = len(with_tag), len(with_imp)
        llms = base.rstrip("/") + "/llms.txt"
        if not robots.allowed(llms):
            row["llms_status"] = "robots-disallowed"
            continue
        st, ct, txt = fetch(llms, "text/plain, text/markdown")
        time.sleep(delay)
        row["llms_status"] = st
        urls = llms_urls(txt) if st == 200 and not looks_html(ct, txt) else []
        row["llms_urls"] = len(urls)
        mapped = {rel: map_slug(page_slug(rel), urls, base) for rel in with_tag}
        mapped = {k: v for k, v in mapped.items() if v}
        row["mapped_tag_pages"] = len(mapped)
        chosen = sample(list(mapped), repo, SAMPLE)
        row["sampled"] = len(chosen)
        for rel in chosen:
            url = mapped[rel]
            if not robots.allowed(url):
                continue
            ms, mct, md = fetch(url + ".md", "text/markdown, text/plain;q=0.9")
            time.sleep(delay)
            hs, _hct, hp = fetch(url, "text/html")
            time.sleep(delay)
            md_ok = ms == 200 and md.strip() != "" and not looks_html(mct, md)
            if md_ok:
                row["read"] += 1
            md_n = norm(md) if md_ok else ""
            ht_n = norm(html_text(hp)) if hs == 200 else ""
            page_dir = os.path.dirname(os.path.join(root, rel))
            for f in with_tag[rel]:
                loc, path = resolve(f, root, page_dir)
                nd = needles(read(path)) if path else []
                kept = md_ok and tag_kept(md, f)
                md_has = bool(md_n) and contains_any(md_n, nd)
                r = {"repo": repo, "page": rel, "url": url, "file": f, "loc": loc,
                     "has_needles": bool(nd), "md_status": ms, "md_is_html": looks_html(mct, md),
                     "html_status": hs, "md_has": md_has,
                     "html_has": bool(ht_n) and contains_any(ht_n, nd),
                     "status": classify(kept, md_has, bool(nd)) if md_ok else "md-unread",
                     "needle": nd[0] if nd else ""}
                if md_ok:
                    inst_rows.append(r)
                if md_ok and hc_n < 40:
                    hc_n += 1
                    with open(os.path.join(hc_dir, "%02d.txt" % hc_n), "w", encoding="utf-8") as fh:
                        fh.write("repo: %s\npage: %s\nurl: %s.md\nfile: %s (%s)\nstatus: %s md_has=%s html_has=%s\n"
                                 "needles: %s\n\n--- .md excerpt ---\n%s\n\n--- HTML text excerpt ---\n%s\n"
                                 % (repo, rel, url, f, loc, r["status"], md_has, r["html_has"],
                                    json.dumps(nd), excerpt(md, "<Snippet" if kept else (nd[0] if nd else "")),
                                    excerpt(" ".join(html_text(hp).split()), nd[0] if nd else "")))
        # controls: import-style snippets
        cmap = {rel: map_slug(page_slug(rel), urls, base) for rel in with_imp}
        cmap = {k: v for k, v in cmap.items() if v}
        for rel in sample(list(cmap), repo + ":control", CONTROL):
            url = cmap[rel]
            if not robots.allowed(url):
                continue
            ms, mct, md = fetch(url + ".md", "text/markdown, text/plain;q=0.9")
            time.sleep(delay)
            hs, _hct, hp = fetch(url, "text/html")
            time.sleep(delay)
            md_ok = ms == 200 and md.strip() != "" and not looks_html(mct, md)
            page_dir = os.path.dirname(os.path.join(root, rel))
            name, ipath = with_imp[rel][0]
            p = resolve_import(ipath, root, page_dir)
            nd = needles(read(p)) if p else []
            ctrl_rows.append({"repo": repo, "page": rel, "url": url, "import": name, "path": ipath,
                              "read": md_ok, "has_needles": bool(nd),
                              "md_has": md_ok and contains_any(norm(md), nd),
                              "html_has": hs == 200 and contains_any(norm(html_text(hp)), nd),
                              "needle": nd[0] if nd else ""})
        row["counted"] = any(r["repo"] == repo and r["loc"] not in ("missing", "variable") for r in inst_rows)
        print("%-28s clone=%s tag_pages=%s mapped=%s read=%s counted=%s"
              % (repo, row["clone"], row["pages_with_tag"], row["mapped_tag_pages"], row["read"], row["counted"]))
        subprocess.run(["rm", "-rf", dest])

    for name, fields, rows in (("sites.csv", SITE_FIELDS, site_rows),
                               ("instances.csv", INST_FIELDS, inst_rows),
                               ("controls.csv", CTRL_FIELDS, ctrl_rows)):
        with open(os.path.join(out_dir, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    g = grade(site_rows, inst_rows, ctrl_rows)
    with open(os.path.join(out_dir, "mintsnip.json"), "w", encoding="utf-8") as f:
        json.dump({"tool": "mintsnip", "version": VERSION, "grade": g}, f, indent=2)
    lines = ["# mintsnip %s (automatic, not hand-checked)" % VERSION, ""]
    lines += ["- %s: %s" % (k, v) for k, v in g.items()]
    lines.append("")
    with open(os.path.join(out_dir, "MINTSNIP_AUTO.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Study 16: <Snippet file> tags in Mintlify Markdown copies.")
    ap.add_argument("--out-dir")
    ap.add_argument("--work-dir", default="/tmp/mintsnip-repos")
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--version", action="version", version="mintsnip " + VERSION)
    a = ap.parse_args(argv)
    if not a.out_dir:
        ap.error("--out-dir is required")
    return run(a.out_dir, a.delay, a.work_dir)


if __name__ == "__main__":
    sys.exit(main())
