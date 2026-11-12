#!/usr/bin/env python3
# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""docsyleak: study 14's census tool. How much shortcode HTML do Docsy sites'
Markdown copies for AI agents carry?

Frame: the 26 sites on www.docsy.dev/examples/ (read 2026-11-12) plus
www.docsy.dev itself (see census/2026-11-docsy-md-html/PREREG.md). For each
site it reads the home page, decides whether the site is built with Docsy and
serves Markdown copies, collects page URLs from the sitemap (or llms.txt),
draws a seeded sample of 30 pages, fetches each page's Markdown copy and runs
md_html_leak.py 0.1.0 unchanged on it. robots.txt is honoured and requests are
one second apart. It waits until the pre-registration is on `main`.

Outputs: sites.csv, pages.csv, labels.csv, hand_check_sample.csv,
docsyleak.json, DOCSYLEAK_AUTO.md, and copies/ (the fetched copies, for the
hand check; not republished).

    python docsyleak.py --out-dir out
"""

import argparse
import csv
import html
import importlib.util
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

VERSION = "0.1.0"
LEAK_VERSION = "0.1.0"
PREREG_URL = ("https://raw.githubusercontent.com/munimtechnologies/tech-writing-ai-rules/main/"
              "census/2026-11-docsy-md-html/PREREG.md")
UA_TOKEN = "docsyleak"
USER_AGENT = ("docsyleak/%s (+https://github.com/munimtechnologies/tech-writing-ai-rules; "
              "mv2@munimtech.com)" % VERSION)
PAGES_PER_SITE = 30
MIN_COPIES = 10
SEED_PREFIX = "study14:"

# www.docsy.dev/examples/ as read on 2026-11-12, in page order, then docsy.dev.
SITES = [
    "https://example.docsy.dev/",
    "https://cncf-docsy-starter.netlify.app/",
    "https://docs.agilebase.co.uk/",
    "https://agones.dev/site/",
    "https://parquet.apache.org/",
    "https://www.cloudwego.io/",
    "https://etcd.io/",
    "https://fission.io/",
    "https://fluxcd.io/",
    "https://graphviz.org/",
    "https://www.grpc.io/",
    "https://jvmperf.net/",
    "https://www.kubeflow.org/",
    "https://docs.layer5.io/",
    "https://www.navidrome.org/",
    "https://opentelemetry.io/",
    "https://protobuf.dev/",
    "https://www.selenium.dev/",
    "https://gchq.github.io/stroom-docs/",
    "https://tekton.dev/",
    "https://ds-docs.y.org/",
    "https://airflow.apache.org/",
    "https://mostlydocs.netlify.app/",
    "https://kubernetes.io/",
    "https://xltdoc.xceptance.com/",
    "https://docs.dapr.io/",
    "https://www.docsy.dev/",
]

DOCSY_RE = re.compile(
    r'class="[^"]*\btd-(?:home|section|page|navbar|main|outer|sidebar|content|default)\b')
LINK_TAG_RE = re.compile(r"<link\b[^>]*>", re.I)
ATTR_RE = re.compile(r"""([A-Za-z_:][-\w:.]*)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""")
LOC_RE = re.compile(r"<loc>\s*(.*?)\s*</loc>", re.S | re.I)
MD_LINK_RE = re.compile(r"\]\(\s*<?([^)\s>]+?\.md)>?(?:\s+\"[^\"]*\")?\s*\)")
LANG_CODES = {
    "ar", "bg", "bn", "ca", "cs", "da", "de", "el", "es", "et", "fa", "fi", "fr", "he", "hi",
    "hr", "hu", "id", "it", "ja", "ko", "lt", "lv", "ms", "nl", "no", "pl", "pt", "pt-br",
    "ro", "ru", "sk", "sl", "sr", "sv", "ta", "th", "tr", "uk", "vi", "zh", "zh-cn", "zh-hans",
    "zh-hant", "zh-tw",
}
SKIP_SEGMENTS = {"tags", "categories", "search", "authors", "author"}


def find(relpath):
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, relpath)
    if os.path.isfile(p):
        return p
    base = os.path.basename(relpath)
    for root, _dirs, files in os.walk(here):
        if base in files:
            return os.path.join(root, base)
    raise FileNotFoundError(relpath)


def load_leak():
    path = find(os.path.join("skills", "md-html-leak-check", "scripts", "md_html_leak.py"))
    spec = importlib.util.spec_from_file_location("md_html_leak", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------- pure helpers (tested offline) ----------

def site_key(url):
    p = urllib.parse.urlsplit(url)
    raw = (p.netloc + p.path).lower()
    return re.sub(r"[^a-z0-9]+", "-", raw).strip("-")


def host_of(url):
    h = urllib.parse.urlsplit(url).netloc.lower()
    return h[4:] if h.startswith("www.") else h


def find_md_alternate(page_html, base_url):
    """Return the absolute URL of <link rel="alternate" type="text/markdown">, or None."""
    for tag in LINK_TAG_RE.findall(page_html):
        attrs = {}
        for m in ATTR_RE.finditer(tag):
            val = m.group(2) if m.group(2) is not None else (
                m.group(3) if m.group(3) is not None else m.group(4))
            attrs[m.group(1).lower()] = html.unescape(val)
        rel = attrs.get("rel", "").lower().split()
        if "alternate" in rel and "text/markdown" in attrs.get("type", "").lower() \
                and attrs.get("href"):
            return urllib.parse.urljoin(base_url, attrs["href"])
    return None


def is_docsy(page_html):
    return bool(DOCSY_RE.search(page_html))


def looks_like_html(text):
    head = text.lstrip()[:300].lower()
    return head.startswith("<!doctype html") or head.startswith("<html")


def is_markdown_copy(status, ctype, text):
    if status != 200 or not text.strip():
        return False
    if "html" in (ctype or "").lower():
        return False
    return not looks_like_html(text)


def md_pattern(home_url, md_url):
    """'index' for <page>/index.md copies (Docsy's), 'dotmd' for <page>.md."""
    if home_url.rstrip("/") != home_url.split("://", 1)[0] + "://" + host_of_raw(home_url) \
            and md_url == home_url.rstrip("/") + ".md":
        return "dotmd"
    return "index"


def host_of_raw(url):
    return urllib.parse.urlsplit(url).netloc


def md_for(page_url, pattern):
    if pattern == "dotmd":
        return page_url.rstrip("/") + ".md"
    if page_url.endswith("/"):
        return page_url + "index.md"
    return page_url + "/index.md"


def parse_sitemap(text):
    kind = "index" if re.search(r"<sitemapindex\b", text, re.I) else "urlset"
    return kind, [html.unescape(x) for x in LOC_RE.findall(text)]


def filter_pool(urls, home_url):
    """Page URLs on the site, under its home path, in its default language."""
    home = urllib.parse.urlsplit(home_url)
    base_path = home.path if home.path.endswith("/") else home.path + "/"
    keep = []
    for u in urls:
        p = urllib.parse.urlsplit(u.strip())
        if p.scheme not in ("http", "https") or host_of(u) != host_of(home_url):
            continue
        if p.query or not p.path.endswith("/") or not p.path.startswith(base_path):
            continue
        segs = [s for s in p.path[len(base_path):].split("/") if s]
        if any(s.lower() in SKIP_SEGMENTS for s in segs):
            continue
        if any(segs[i].lower() == "page" and segs[i + 1].isdigit() for i in range(len(segs) - 1)):
            continue
        keep.append((urllib.parse.urlunsplit((home.scheme, home.netloc, p.path, "", "")), segs))
    en = sum(1 for _, segs in keep if segs and segs[0].lower() == "en")
    if keep and en * 2 >= len(keep):
        chosen = [u for u, segs in keep if segs and segs[0].lower() == "en"]
    else:
        chosen = [u for u, segs in keep if not (segs and segs[0].lower() in LANG_CODES)]
    return sorted(set(chosen))


def llms_md_links(text, base_url):
    out = []
    for m in MD_LINK_RE.finditer(text):
        u = urllib.parse.urljoin(base_url, m.group(1))
        if host_of(u) == host_of(base_url):
            out.append(u)
    return sorted(set(out))


def draw(pool, key, k=PAGES_PER_SITE):
    pool = sorted(set(pool))
    if len(pool) <= k:
        return pool
    return random.Random(SEED_PREFIX + key).sample(pool, k)


def grade(sites, pages):
    """Compute the gate and predictions exactly as pre-registered."""
    eligible = [s for s in sites if s["eligible"]]
    counted = [s for s in eligible if s["copies_read"] >= MIN_COPIES]
    ckeys = {s["key"] for s in counted}
    cpages = [p for p in pages if p["site"] in ckeys and p["ok"]]
    docsy_pages = [p for p in cpages if p["docsy_labels"]]
    res = {"eligible": len(eligible), "counted": len(counted), "copies": len(cpages),
           "docsy_copies": len(docsy_pages)}
    res["G1"] = len(counted) >= 3
    res["P1"] = len(eligible) <= 10
    with_docsy = sum(1 for s in counted
                     if any(p["docsy_labels"] for p in cpages if p["site"] == s["key"]))
    res["sites_with_docsy"] = with_docsy
    res["P2"] = bool(counted) and with_docsy * 2 >= len(counted)
    res["docsy_copy_share"] = round(len(docsy_pages) / len(cpages), 4) if cpages else None
    res["P3"] = bool(cpages) and len(docsy_pages) / len(cpages) >= 0.10
    per_label = {}
    for p in docsy_pages:
        for lab in p["docsy_labels"]:
            per_label[lab] = per_label.get(lab, 0) + 1
    res["docsy_label_copies"] = dict(sorted(per_label.items()))
    top = max(per_label.values()) if per_label else 0
    res["top_labels"] = sorted(l for l, n in per_label.items() if n == top and top > 0)
    res["P4"] = "docsy:alert" in res["top_labels"]
    shares = [p["markup_share"] for p in docsy_pages]
    res["median_docsy_markup_share"] = round(statistics.median(shares), 4) if shares else None
    res["P5"] = bool(shares) and statistics.median(shares) >= 0.05
    res["P6"] = bool(counted) and all(
        any(p["structural_tags"] > 0 for p in cpages if p["site"] == s["key"]) for s in counted)
    return res


def hand_check_sample(sites, pages):
    """Per counted site: the first 2 copies (sample order) with Docsy labels, and the first without."""
    rows = []
    for s in sites:
        if not (s["eligible"] and s["copies_read"] >= MIN_COPIES):
            continue
        ok = [p for p in pages if p["site"] == s["key"] and p["ok"]]
        rows += [dict(p, group="docsy") for p in [p for p in ok if p["docsy_labels"]][:2]]
        rows += [dict(p, group="none") for p in [p for p in ok if not p["docsy_labels"]][:1]]
    return rows


# ---------- network ----------

class Fetcher:
    def __init__(self, delay=1.0, timeout=30):
        self.delay = delay
        self.timeout = timeout
        self.last = 0.0
        self.robots = {}
        self.requests = 0

    def _wait(self):
        gap = time.monotonic() - self.last
        if gap < self.delay:
            time.sleep(self.delay - gap)
        self.last = time.monotonic()

    def get(self, url, accept="text/html,*/*;q=0.5", max_bytes=5_000_000):
        self._wait()
        self.requests += 1
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read(max_bytes)
                return {"status": resp.status, "url": resp.geturl(),
                        "ctype": resp.headers.get("Content-Type", ""),
                        "text": body.decode("utf-8", errors="replace"), "error": ""}
        except urllib.error.HTTPError as exc:
            return {"status": exc.code, "url": url, "ctype": "", "text": "", "error": "http"}
        except Exception as exc:  # timeouts, TLS, resets
            return {"status": 0, "url": url, "ctype": "", "text": "",
                    "error": type(exc).__name__}

    def allowed(self, url):
        p = urllib.parse.urlsplit(url)
        origin = "%s://%s" % (p.scheme, p.netloc)
        if origin not in self.robots:
            r = self.get(origin + "/robots.txt", accept="text/plain,*/*;q=0.5")
            if r["status"] == 200:
                rp = urllib.robotparser.RobotFileParser()
                rp.parse(r["text"].splitlines())
                rp.modified()  # can_fetch() refuses everything if it thinks robots.txt was never read
                self.robots[origin] = ("ok", rp)
            elif 400 <= r["status"] < 500:
                self.robots[origin] = ("4xx-allow", None)
            else:
                self.robots[origin] = ("error-disallow", None)
        state, rp = self.robots[origin]
        if state == "4xx-allow":
            return True
        if state == "error-disallow":
            return False
        return rp.can_fetch(UA_TOKEN, url)

    def robots_state(self, url):
        p = urllib.parse.urlsplit(url)
        return self.robots.get("%s://%s" % (p.scheme, p.netloc), ("unread", None))[0]


def collect_pool(f, home):
    tried = []
    origin = "%s://%s/" % tuple(urllib.parse.urlsplit(home)[:2])
    for sm in [urllib.parse.urljoin(home, "sitemap.xml"), urllib.parse.urljoin(origin, "sitemap.xml")]:
        if sm in tried or not f.allowed(sm):
            continue
        tried.append(sm)
        r = f.get(sm, accept="application/xml,text/xml,*/*;q=0.5")
        if r["status"] != 200:
            continue
        kind, locs = parse_sitemap(r["text"])
        if kind == "index":
            children = sorted(locs, key=lambda u: (not u.startswith(home), u))[:30]
            locs = []
            for c in children:
                if not f.allowed(c):
                    continue
                rc = f.get(c, accept="application/xml,text/xml,*/*;q=0.5")
                if rc["status"] == 200:
                    locs += parse_sitemap(rc["text"])[1]
        pool = filter_pool(locs, home)
        if pool:
            return "sitemap", pool
    return "none", []


def run_site(f, leak, url, out_dir, log):
    key = site_key(url)
    s = {"key": key, "url": url, "final_url": "", "status": 0, "docsy": False,
         "md_method": "none", "md_home_url": "", "md_ok": False, "eligible": False,
         "robots": "", "pool_source": "none", "pool_size": 0, "sampled": 0,
         "copies_read": 0, "copies_structural": 0, "copies_docsy": 0,
         "median_markup_share": "", "note": ""}
    pages = []
    if not f.allowed(url):
        s["robots"] = f.robots_state(url)
        s["note"] = "home page disallowed by robots.txt"
        return s, pages
    r = f.get(url)
    s["robots"] = f.robots_state(url)
    s["status"], s["final_url"] = r["status"], r["url"]
    if r["status"] != 200:
        s["note"] = "home page not readable (%s %s)" % (r["status"], r["error"])
        return s, pages
    home = r["url"]
    s["docsy"] = is_docsy(r["text"])
    alt = find_md_alternate(r["text"], home)
    candidates = [("alternate-link", alt)] if alt else []
    candidates.append(("index.md", md_for(home, "index")))
    for method, md_url in candidates:
        if not f.allowed(md_url):
            continue
        rm = f.get(md_url, accept="text/markdown,text/plain;q=0.9,*/*;q=0.1")
        if is_markdown_copy(rm["status"], rm["ctype"], rm["text"]):
            s["md_method"], s["md_home_url"], s["md_ok"] = method, md_url, True
            break
    s["eligible"] = s["docsy"] and s["md_ok"]
    if not s["eligible"]:
        return s, pages
    pattern = md_pattern(home, s["md_home_url"])
    source, pool = collect_pool(f, home)
    if not pool:
        rl = f.get(urllib.parse.urljoin(home, "llms.txt"), accept="text/plain,*/*;q=0.5")
        if rl["status"] == 200 and not looks_like_html(rl["text"]):
            pool = llms_md_links(rl["text"], home)
            source = "llms.txt" if pool else "none"
        pattern = "direct" if pool else pattern
    s["pool_source"], s["pool_size"] = source, len(pool)
    picks = draw(pool, key)
    s["sampled"] = len(picks)
    os.makedirs(os.path.join(out_dir, "copies", key), exist_ok=True)
    for i, page in enumerate(picks):
        md_url = page if pattern == "direct" else md_for(page, pattern)
        row = {"site": key, "n": i, "page_url": page, "md_url": md_url, "status": 0,
               "ctype": "", "ok": False, "chars": 0, "text_chars": 0, "tags": 0,
               "structural_tags": 0, "markup_chars": 0, "markup_share": 0.0,
               "docsy_labels": [], "source_labels": [], "labels": {}, "example": ""}
        if not f.allowed(md_url):
            row["ctype"] = "robots-disallowed"
            pages.append(row)
            continue
        rm = f.get(md_url, accept="text/markdown,text/plain;q=0.9,*/*;q=0.1")
        row["status"], row["ctype"] = rm["status"], rm["ctype"]
        if is_markdown_copy(rm["status"], rm["ctype"], rm["text"]):
            res = leak.scan(rm["text"])
            row.update({"ok": True, "chars": res["chars"], "text_chars": res["text_chars"],
                        "tags": res["tags"], "structural_tags": res["structural_tags"],
                        "markup_chars": res["markup_chars"], "markup_share": res["markup_share"],
                        "docsy_labels": res["docsy_labels"], "source_labels": res["source_labels"],
                        "labels": {k: v["tags"] for k, v in res["labels"].items()},
                        "example": res["examples"][0] if res["examples"] else ""})
            with open(os.path.join(out_dir, "copies", key, "%02d.md" % i), "w",
                      encoding="utf-8") as fh:
                fh.write(rm["text"])
        pages.append(row)
    ok = [p for p in pages if p["ok"]]
    s["copies_read"] = len(ok)
    s["copies_structural"] = sum(1 for p in ok if p["structural_tags"])
    s["copies_docsy"] = sum(1 for p in ok if p["docsy_labels"])
    if ok:
        s["median_markup_share"] = round(statistics.median(p["markup_share"] for p in ok), 4)
    log("%s: %d of %d copies read, %d with Docsy shortcode markup"
        % (key, len(ok), len(picks), s["copies_docsy"]))
    return s, pages


# ---------- output ----------

SITE_FIELDS = ["key", "url", "final_url", "status", "docsy", "md_method", "md_home_url", "md_ok",
               "eligible", "robots", "pool_source", "pool_size", "sampled", "copies_read",
               "copies_structural", "copies_docsy", "median_markup_share", "note"]
PAGE_FIELDS = ["site", "n", "page_url", "md_url", "status", "ctype", "ok", "chars", "text_chars",
               "tags", "structural_tags", "markup_chars", "markup_share", "docsy_labels",
               "source_labels", "labels", "example"]


def page_csv_row(p):
    row = dict(p)
    row["docsy_labels"] = ";".join(p["docsy_labels"])
    row["source_labels"] = ";".join(p["source_labels"])
    row["labels"] = json.dumps(p["labels"], sort_keys=True)
    return row


def write_csv(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def label_rows(sites, pages):
    counted = {s["key"] for s in sites if s["eligible"] and s["copies_read"] >= MIN_COPIES}
    agg = {}
    for p in pages:
        if p["site"] not in counted or not p["ok"]:
            continue
        for lab, n in p["labels"].items():
            e = agg.setdefault(lab, {"label": lab, "sites": set(), "copies": 0, "tags": 0})
            e["sites"].add(p["site"])
            e["copies"] += 1
            e["tags"] += n
    rows = []
    for lab in sorted(agg):
        e = agg[lab]
        rows.append({"label": lab, "sites": len(e["sites"]), "copies": e["copies"],
                     "tags": e["tags"]})
    return rows


def auto_md(meta, sites, grades, labels):
    yn = lambda b: "held" if b else "failed"
    out = ["# docsyleak first-pass output (study 14)", "",
           "Tool %s with md_html_leak %s; run %s to %s UTC; %d requests."
           % (meta["version"], meta["leak_version"], meta["started"], meta["finished"],
              meta["requests"]), "",
           "This is the tool's own output, before any hand check. RESULT.md grades the study.", "",
           "| site | Docsy | Markdown copy | pool | read | structural | Docsy markup | median share |",
           "|---|---|---|---|---|---|---|---|"]
    for s in sites:
        out.append("| %s | %s | %s | %s %s | %s | %s | %s | %s |" % (
            s["key"], "yes" if s["docsy"] else "no",
            s["md_method"] if s["md_ok"] else "no", s["pool_source"], s["pool_size"],
            s["copies_read"], s["copies_structural"], s["copies_docsy"],
            s["median_markup_share"]))
    out += ["", "## Gate and predictions (computed, before the hand check)", "",
            "- Eligible sites: %d; counted (at least %d copies read): %d; copies: %d; "
            "with Docsy shortcode markup: %d"
            % (grades["eligible"], MIN_COPIES, grades["counted"], grades["copies"],
               grades["docsy_copies"]),
            "- G1 (at least 3 counted sites): %s" % ("passed" if grades["G1"] else "failed"),
            "- P1 (at most 10 of 27 sites eligible): %s" % yn(grades["P1"]),
            "- P2 (at least half of counted sites have a copy with Docsy markup; %d): %s"
            % (grades["sites_with_docsy"], yn(grades["P2"])),
            "- P3 (at least 10%% of copies hold Docsy markup; %s): %s"
            % (grades["docsy_copy_share"], yn(grades["P3"])),
            "- P4 (docsy:alert is on the most copies; top %s): %s"
            % (", ".join(grades["top_labels"]) or "none", yn(grades["P4"])),
            "- P5 (median markup share of Docsy-markup copies at least 5%%; %s): %s"
            % (grades["median_docsy_markup_share"], yn(grades["P5"])),
            "- P6 (every counted site has a copy with a structural tag): %s" % yn(grades["P6"]),
            "", "## Sources of markup in counted copies", "",
            "| label | sites | copies | tags |", "|---|---|---|---|"]
    for r in labels:
        out.append("| %s | %d | %d | %d |" % (r["label"], r["sites"], r["copies"], r["tags"]))
    if not grades["G1"]:
        out += ["", "G1 failed: per the pre-registration, P2 to P6 are reported as description, "
                    "not graded."]
    return "\n".join(out) + "\n"


def prereg_on_main(f):
    r = f.get(PREREG_URL, accept="text/plain,*/*;q=0.5")
    return r["status"] == 200 and "Study 14" in r["text"]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Study 14: shortcode HTML in Docsy sites' Markdown copies.")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--no-prereg-check", action="store_true")
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--sites", nargs="*", help="override the frame (for trials only)")
    args = ap.parse_args(argv)
    leak = load_leak()
    if leak.VERSION != LEAK_VERSION:
        print("md_html_leak is %s, the pre-registration fixes %s" % (leak.VERSION, LEAK_VERSION),
              file=sys.stderr)
        return 3
    os.makedirs(args.out_dir, exist_ok=True)
    f = Fetcher(delay=args.delay)
    if not args.no_prereg_check and not prereg_on_main(f):
        print("the pre-registration is not on main yet; nothing was read", file=sys.stderr)
        return 3
    started = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    sites, pages = [], []
    log = lambda msg: print(msg, flush=True)
    for url in (args.sites or SITES):
        try:
            s, p = run_site(f, leak, url, args.out_dir, log)
        except Exception as exc:  # one site must not stop the census
            s = {k: "" for k in SITE_FIELDS}
            s.update({"key": site_key(url), "url": url, "docsy": False, "md_ok": False,
                      "eligible": False, "copies_read": 0, "copies_structural": 0,
                      "copies_docsy": 0, "pool_size": 0, "sampled": 0,
                      "note": "error: %s" % type(exc).__name__})
            p = []
        sites.append(s)
        pages += p
        if not s["eligible"]:
            log("%s: not eligible (Docsy %s, Markdown copy %s) %s"
                % (s["key"], s["docsy"], s["md_ok"], s["note"]))
    finished = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    grades = grade(sites, pages)
    labels = label_rows(sites, pages)
    meta = {"tool": "docsyleak", "version": VERSION, "leak_version": leak.VERSION,
            "started": started, "finished": finished, "requests": f.requests,
            "frame_size": len(args.sites or SITES), "pages_per_site": PAGES_PER_SITE}
    write_csv(os.path.join(args.out_dir, "sites.csv"), SITE_FIELDS, sites)
    write_csv(os.path.join(args.out_dir, "pages.csv"), PAGE_FIELDS, [page_csv_row(p) for p in pages])
    write_csv(os.path.join(args.out_dir, "labels.csv"), ["label", "sites", "copies", "tags"], labels)
    write_csv(os.path.join(args.out_dir, "hand_check_sample.csv"), ["group"] + PAGE_FIELDS,
              [page_csv_row(p) for p in hand_check_sample(sites, pages)])
    with open(os.path.join(args.out_dir, "docsyleak.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "grades": grades, "sites": sites, "labels": labels}, fh,
                  indent=2, ensure_ascii=False)
    with open(os.path.join(args.out_dir, "DOCSYLEAK_AUTO.md"), "w", encoding="utf-8") as fh:
        fh.write(auto_md(meta, sites, grades, labels))
    log("done: %d eligible, %d counted, %d copies" % (grades["eligible"], grades["counted"],
                                                     grades["copies"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
