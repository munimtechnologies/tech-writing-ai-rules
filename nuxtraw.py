#!/usr/bin/env python3
# nuxtraw.py 0.1.0 - Apache-2.0
# By MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
#
# Study 15 tool: on docs sites whose llms.txt sends AI agents to Nuxt Content's
# /raw/<path>.md copies, count the component tags that reach a copy empty
# (an element with no text inside, such as <partial content="x"></partial> or
# <component-props name="Button"></component-props>), and compare each copy's
# words with the words of the live page's main content.
#
# Nuxt Content's raw route (src/features/llms/runtime/server/routes/raw/
# [...slug].md.get.ts, read 2026-11-12) stringifies the page's stored body with
# minimark's 'markdown/html' format, so a component that gets its content only
# when the page is rendered (a Vue component, a partial) is printed as a tag.
#
# Standard library only. Polite: robots.txt honoured (token "nuxtraw"), one
# request at a time, one second apart, an identifying User-Agent.

import argparse
import csv
import json
import os
import random
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser

VERSION = "0.1.0"
UA = ("nuxtraw/%s (+https://github.com/munimtechnologies/tech-writing-ai-rules; "
      "MV2 of Munim, Inc., mv2@munimtech.com)" % VERSION)
ROBOTS_TOKEN = "nuxtraw"
PREREG_URL = ("https://raw.githubusercontent.com/munimtechnologies/tech-writing-ai-rules/"
              "main/census/2026-11-nuxt-raw/PREREG.md")
SAMPLE = 30
MIN_LINKS = 10      # eligibility: at least this many /raw/ links in llms.txt
MIN_READ = 10       # a site is counted if at least this many copies are read

# The frame (fixed in PREREG.md): candidate llms.txt addresses.
SITES = [
    "https://nuxt.com/llms.txt",
    "https://ui.nuxt.com/llms.txt",
    "https://content.nuxt.com/llms.txt",
    "https://hub.nuxt.com/llms.txt",
    "https://image.nuxt.com/llms.txt",
    "https://eslint.nuxt.com/llms.txt",
    "https://devtools.nuxt.com/llms.txt",
    "https://fonts.nuxt.com/llms.txt",
    "https://scripts.nuxt.com/llms.txt",
    "https://test-utils.nuxt.com/llms.txt",
    "https://nuxt.studio/llms.txt",
    "https://docus.dev/llms.txt",
    "https://i18n.nuxtjs.org/llms.txt",
    "https://color-mode.nuxtjs.org/llms.txt",
    "https://supabase.nuxtjs.org/llms.txt",
    "https://tailwindcss.nuxtjs.org/llms.txt",
    "https://nuxtseo.com/llms.txt",
    "https://unhead.unjs.io/llms.txt",
    "https://motion.vueuse.org/llms.txt",
    "https://directus.com/docs/llms.txt",
]

HTML_ELEMENTS = set("""
a abbr address area article aside audio b base bdi bdo blockquote body br button canvas
caption cite code col colgroup data datalist dd del details dfn dialog div dl dt em embed
fieldset figcaption figure footer form h1 h2 h3 h4 h5 h6 head header hgroup hr html i
iframe img input ins kbd label legend li link main map mark menu meta meter nav noscript
object ol optgroup option output p param picture pre progress q rp rt ruby s samp script
search section select slot small source span strong style sub summary sup table tbody td
template textarea tfoot th thead time title tr track u ul var video wbr svg path math
center font big tt strike
""".split())
LINK_ATTRS = {"to", "href", "src"}
TEXT_ATTRS = {"title", "label", "description", "text", "alt", "summary", "caption",
              "heading", "message"}

LINK_RE = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+)\)")
FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
INLINE_CODE_RE = re.compile(r"(`+)(?:(?!\1).)+?\1")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
OPEN_RE = re.compile(r"<([A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*)((?:\s[^<>]*?)?)(/?)>")
ATTR_RE = re.compile(r"""[:@#]?([A-Za-z_][\w:.-]*)(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'>]+))?""")
TAG_RE = re.compile(r"</?[A-Za-z][^<>\n]*>")
WORD_RE = re.compile(r"\w+")


# ---------- text analysis (offline, tested) ----------

def strip_code(text):
    """Remove fenced code blocks, inline code spans and HTML comments."""
    text = COMMENT_RE.sub(" ", text)
    out, fence = [], None
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)[0] * 3
                continue
            out.append(INLINE_CODE_RE.sub(" ", line))
        elif m and m.group(1).startswith(fence):
            fence = None
    return "\n".join(out)


def is_component(name):
    n = name.lower()
    return "-" in n or n not in HTML_ELEMENTS


def attr_names(attrs):
    return sorted({m.group(1).lower() for m in ATTR_RE.finditer(attrs or "")})


def components(text):
    """Every component element outside code: dicts with name, attrs, empty.

    An element is empty if it is self-closing or nothing but whitespace and
    tags stands between its opening tag and its matching closing tag (same
    name, nesting counted)."""
    body = strip_code(text)
    found = []
    for m in OPEN_RE.finditer(body):
        name = m.group(1).lower()
        if not is_component(name):
            continue
        attrs = attr_names(m.group(2))
        if m.group(3) == "/":
            found.append({"name": name, "attrs": attrs, "empty": True})
            continue
        inner = _inner(body, m.end(), name)
        if inner is None:          # no closing tag: treat as a wrapper, not empty
            found.append({"name": name, "attrs": attrs, "empty": False})
            continue
        text_inside = TAG_RE.sub(" ", inner).strip()
        found.append({"name": name, "attrs": attrs, "empty": text_inside == ""})
    return found


def _inner(body, start, name):
    pat = re.compile(r"<(/?)%s(?:\s[^<>]*?)?(/?)>" % re.escape(name), re.I)
    depth = 1
    for m in pat.finditer(body, start):
        if m.group(1) == "/":
            depth -= 1
            if depth == 0:
                return body[start:m.start()]
        elif m.group(2) != "/":
            depth += 1
    return None


def kind_of(comp):
    """What an empty tag still carries: link, text, or nothing readable."""
    a = set(comp["attrs"])
    if a & TEXT_ATTRS:
        return "text-attr"
    if a & LINK_ATTRS:
        return "link-attr"
    return "bare"


def md_words(text):
    """Words of a Markdown copy: comments and tags removed, code kept."""
    return len(WORD_RE.findall(TAG_RE.sub(" ", COMMENT_RE.sub(" ", text))))


class PageText(HTMLParser):
    """Visible text of <main>/<article> (or the whole body if neither exists)."""
    SKIP = {"script", "style", "nav", "header", "footer", "aside", "template", "noscript"}
    KEEP = {"main", "article"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = self.keep = 0
        self.kept, self.all = [], []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in self.KEEP:
            self.keep += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag in self.KEEP:
            self.keep = max(0, self.keep - 1)

    def handle_data(self, data):
        if self.skip:
            return
        self.all.append(data)
        if self.keep:
            self.kept.append(data)

    def text(self):
        return " ".join(self.kept if self.kept else self.all)


def page_words(html):
    p = PageText()
    p.feed(html)
    p.close()
    return len(WORD_RE.findall(p.text()))


def raw_links(llms_text, llms_url):
    """Unique same-host links whose path contains /raw/ and ends in .md (sorted)."""
    host = urllib.parse.urlsplit(llms_url).netloc
    out = set()
    for url in LINK_RE.findall(llms_text):
        url = url.split("#", 1)[0].split("?", 1)[0]
        p = urllib.parse.urlsplit(url)
        if p.netloc == host and "/raw/" in p.path and p.path.endswith(".md"):
            out.add(url)
    return sorted(out)


def page_url(raw_url):
    """Live page for a /raw/ copy: drop the first /raw segment and .md; index -> folder."""
    p = urllib.parse.urlsplit(raw_url)
    path = p.path.replace("/raw/", "/", 1)[: -len(".md")]
    if path.endswith("/index"):
        path = path[: -len("index")]
    return urllib.parse.urlunsplit((p.scheme, p.netloc, path or "/", "", ""))


def sample(links, key, n=SAMPLE):
    if len(links) <= n:
        return list(links)
    return sorted(random.Random("study15:" + key).sample(links, n))


def site_key(llms_url):
    p = urllib.parse.urlsplit(llms_url)
    return p.netloc + p.path.rsplit("/", 1)[0]


def looks_html(ctype, text):
    head = text.lstrip()[:200].lower()
    return "html" in (ctype or "").lower() or head.startswith("<!doctype html") or head.startswith("<html")


def analyse(raw_text, html_text):
    comps = components(raw_text)
    empties = [c for c in comps if c["empty"]]
    mw = md_words(raw_text)
    pw = page_words(html_text) if html_text else 0
    return {
        "md_words": mw,
        "page_words": pw,
        "ratio": round(mw / pw, 3) if pw else "",
        "component_tags": len(comps),
        "empty_tags": len(empties),
        "empty_bare": sum(1 for c in empties if kind_of(c) == "bare"),
        "empty_names": ";".join(sorted({c["name"] for c in empties})),
        "first_empty": (("<%s %s>" % (empties[0]["name"], " ".join(empties[0]["attrs"]))).strip()
                        if empties else ""),
        "_empties": empties,
    }


# ---------- grading (offline, tested) ----------

def grade(sites, pages):
    """sites: rows with key, counted (bool). pages: rows with key, read (bool), empty_tags, ratio."""
    counted = [s["key"] for s in sites if s["counted"]]
    read = [p for p in pages if p["read"] and p["key"] in counted]
    by = {k: [p for p in read if p["key"] == k] for k in counted}
    with_empty = lambda rows: [p for p in rows if int(p["empty_tags"]) > 0]
    g1 = len(counted) >= 4
    res = {"counted_sites": len(counted), "copies_read": len(read), "G1": g1}
    if not read:
        return res
    share = {k: len(with_empty(v)) / len(v) for k, v in by.items() if v}
    pooled = len(with_empty(read)) / len(read)
    ratios_e = [float(p["ratio"]) for p in with_empty(read) if p["ratio"] != ""]
    ratios_n = [float(p["ratio"]) for p in read if int(p["empty_tags"]) == 0 and p["ratio"] != ""]
    med = {k: statistics.median([float(p["ratio"]) for p in v if p["ratio"] != ""])
           for k, v in by.items() if any(p["ratio"] != "" for p in v)}
    res.update({
        "share_with_empty_by_site": {k: round(v, 3) for k, v in sorted(share.items())},
        "pooled_share_with_empty": round(pooled, 3),
        "median_ratio_with_empty": round(statistics.median(ratios_e), 3) if ratios_e else None,
        "median_ratio_without_empty": round(statistics.median(ratios_n), 3) if ratios_n else None,
        "median_ratio_by_site": {k: round(v, 3) for k, v in sorted(med.items())},
        "P1": sum(1 for v in share.values() if v > 0) * 2 >= len(counted),
        "P2": pooled >= 0.15,
        "P3": sum(1 for k, v in share.items() if v >= 0.10 and not k.startswith("directus.com")) >= 2,
        "P4": (bool(ratios_e) and bool(ratios_n)
               and statistics.median(ratios_e) < statistics.median(ratios_n)),
        "P5": all(v >= 0.5 for v in med.values()),
    })
    if not g1:
        for k in ("P1", "P2", "P3", "P4", "P5"):
            res[k] = "not graded (G1 failed): " + str(res[k])
    return res


# ---------- network ----------

def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "text/markdown, text/html;q=0.9, */*;q=0.5"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, (e.headers.get("Content-Type", "") if e.headers else ""), ""
    except Exception as e:
        return 0, "error: %s" % type(e).__name__, ""


class Robots:
    def __init__(self, delay):
        self.cache, self.delay = {}, delay

    def allowed(self, url):
        p = urllib.parse.urlsplit(url)
        base = "%s://%s" % (p.scheme, p.netloc)
        if base not in self.cache:
            st, _ct, txt = fetch(base + "/robots.txt")
            time.sleep(self.delay)
            rp = urllib.robotparser.RobotFileParser()
            if st == 200:
                rp.parse(txt.splitlines())
            elif 400 <= st < 500:
                rp.parse([])            # no robots.txt: all allowed
            else:
                rp.parse(["User-agent: *", "Disallow: /"])   # unreachable: stay out
            self.cache[base] = rp
        return self.cache[base].can_fetch(ROBOTS_TOKEN, url)


SITE_FIELDS = ["key", "llms_url", "llms_status", "raw_links", "eligible", "sampled", "read", "counted"]
PAGE_FIELDS = ["key", "raw_url", "raw_status", "raw_is_html", "page_url", "page_status", "read",
               "md_words", "page_words", "ratio", "component_tags", "empty_tags", "empty_bare",
               "empty_names", "first_empty"]


def run(out_dir, delay, check_prereg=True, sites=None):
    os.makedirs(out_dir, exist_ok=True)
    if check_prereg:
        st, _ct, txt = fetch(PREREG_URL)
        if st != 200 or "Study 15" not in txt:
            print("error: PREREG.md is not on main (HTTP %s); not reading any site" % st, file=sys.stderr)
            return 4
    robots = Robots(delay)
    site_rows, page_rows, tag_rows = [], [], {}
    for llms_url in (sites or SITES):
        key = site_key(llms_url)
        row = {"key": key, "llms_url": llms_url, "llms_status": "", "raw_links": 0,
               "eligible": False, "sampled": 0, "read": 0, "counted": False}
        if not robots.allowed(llms_url):
            row["llms_status"] = "robots-disallowed"
            site_rows.append(row)
            continue
        st, ct, txt = fetch(llms_url)
        time.sleep(delay)
        row["llms_status"] = st
        links = raw_links(txt, llms_url) if st == 200 and not looks_html(ct, txt) else []
        row["raw_links"] = len(links)
        row["eligible"] = len(links) >= MIN_LINKS
        if row["eligible"]:
            chosen = sample(links, key)
            row["sampled"] = len(chosen)
            for u in chosen:
                pr = {"key": key, "raw_url": u, "page_url": page_url(u), "read": False}
                if not (robots.allowed(u) and robots.allowed(pr["page_url"])):
                    pr["raw_status"] = "robots-disallowed"
                    page_rows.append(pr)
                    continue
                rs, rct, rt = fetch(u)
                time.sleep(delay)
                ps, _pct, pt = fetch(pr["page_url"])
                time.sleep(delay)
                pr.update({"raw_status": rs, "raw_is_html": looks_html(rct, rt), "page_status": ps})
                if rs == 200 and rt.strip() and not pr["raw_is_html"]:
                    a = analyse(rt, pt if ps == 200 else "")
                    for c in a.pop("_empties"):
                        t = tag_rows.setdefault((key, c["name"], kind_of(c)),
                                                {"key": key, "tag": c["name"], "kind": kind_of(c),
                                                 "copies": set(), "count": 0,
                                                 "attrs": set()})
                        t["copies"].add(u)
                        t["count"] += 1
                        t["attrs"].update(c["attrs"])
                    pr.update(a)
                    pr["read"] = True
                    row["read"] += 1
                page_rows.append(pr)
        row["counted"] = row["read"] >= MIN_READ
        site_rows.append(row)
        print("%-28s llms=%s raw_links=%d read=%d" % (key, row["llms_status"], len(links), row["read"]))

    with open(os.path.join(out_dir, "sites.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SITE_FIELDS)
        w.writeheader()
        w.writerows(site_rows)
    with open(os.path.join(out_dir, "pages.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=PAGE_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(page_rows)
    with open(os.path.join(out_dir, "tags.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["key", "tag", "kind", "copies", "count", "attrs"])
        for t in sorted(tag_rows.values(), key=lambda t: (t["key"], -len(t["copies"]), t["tag"])):
            w.writerow([t["key"], t["tag"], t["kind"], len(t["copies"]), t["count"],
                        ";".join(sorted(t["attrs"]))])
    # hand check: per counted site, first two copies with an empty tag and first without
    hc = []
    for s in site_rows:
        if not s["counted"]:
            continue
        rows = [p for p in page_rows if p["key"] == s["key"] and p["read"]]
        hc += [p for p in rows if p["empty_tags"] > 0][:2] + [p for p in rows if p["empty_tags"] == 0][:1]
    with open(os.path.join(out_dir, "hand_check_sample.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=PAGE_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(hc)
    g = grade(site_rows, page_rows)
    with open(os.path.join(out_dir, "nuxtraw.json"), "w", encoding="utf-8") as f:
        json.dump({"tool": "nuxtraw", "version": VERSION, "grade": g}, f, indent=2)
    lines = ["# nuxtraw %s (automatic, not hand-checked)" % VERSION, ""]
    lines += ["- %s: %s" % (k, v) for k, v in g.items()]
    lines.append("")
    with open(os.path.join(out_dir, "NUXTRAW_AUTO.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Study 15: empty component tags in Nuxt Content /raw/ copies.")
    ap.add_argument("--out-dir")
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--version", action="version", version="nuxtraw " + VERSION)
    a = ap.parse_args(argv)
    if not a.out_dir:
        ap.error("--out-dir is required")
    return run(a.out_dir, a.delay)


if __name__ == "__main__":
    sys.exit(main())
