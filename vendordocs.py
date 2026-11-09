#!/usr/bin/env python3
# Copyright 2026 Munim, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
"""vendordocs 0.1.0: do company docs sites tell readers, people and agents, which pages were made with AI?

Study 9 of tech-writing-ai-rules. Microsoft Learn labels AI-made articles (`ai-usage`, studies 7
and 8). This tool asks whether the other company-run docs sites that developers use most do
anything like it, and how many of them already write for AI readers (llms.txt, Markdown copies).

Frame: every entry of the Stack Overflow 2025 Developer Survey's "Cloud development" list whose
docs are run by a company that sells the product or a paid tier of it (20 sites; see SITES and
the pre-registration). For each site the tool:

  1. reads robots.txt (its own User-Agent; disallowed URLs are never fetched),
  2. collects in-scope page URLs from the site's sitemaps (robots.txt Sitemap lines, then
     /sitemap.xml, <docs root>/sitemap.xml and /sitemap_index.xml; sitemap indexes are expanded
     with children whose path names "doc" first, then a seeded shuffle; at most 25 sitemap files
     or 2,000 URLs), and crawls from the docs root if that gives fewer URLs than the sample size,
  3. draws 30 pages with random.Random("study9|<site id>"),
  4. fetches each page as HTML, then with `Accept: text/markdown`, then at `<url>.md`, and
     records an AI label (a <meta> tag or a Markdown front matter key), a sentence that
     acknowledges AI's role in making the page, and whether a Markdown copy is served,
  5. checks /llms.txt and /llms-full.txt at the host root and the docs root.

Two controls test the detectors: a Microsoft Learn article whose Markdown copy carries
`ai-usage: ai-assisted`, and a Microsoft DevBlogs post that shows an "AI-assisted content" note.

No page text is kept, only matched label values and sentences (at most 200 characters).

Usage: python vendordocs.py --out-dir OUT [--wait-prereg-minutes 240] [--no-prereg-check]
Outputs: sites.csv, pages.csv, vendordocs.json, VENDORDOCS_AUTO.md.
Standard library only. Apache-2.0.
Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""

import argparse
import collections
import csv
import datetime
import gzip
import html as htmlmod
import io
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

VERSION = "0.1.0"
USER_AGENT = ("tech-writing-ai-rules-vendordocs/%s (+https://github.com/munimtechnologies/"
              "tech-writing-ai-rules; mv2@munimtech.com)" % VERSION)
REPO_API = "https://api.github.com/repos/munimtechnologies/tech-writing-ai-rules/commits"
PREREG_PATH = "census/2026-11-vendor-docs-ai-labels/PREREGISTRATION.md"
PER_SITE = 30
WANT_URLS = 2000
MAX_SITEMAPS = 25
CRAWL_PAGES = 10
DELAY = 1.0
MAX_BYTES = 3000000
MAX_SITEMAP_BYTES = 20000000
READABLE_MIN = 20
GATE_SITES = 15
ACCEPT_HTML = "text/html,application/xhtml+xml"
ACCEPT_MD = "text/markdown"
ACCEPT_XML = "application/xml,text/xml,*/*"


def _site(sid, name, so, root, hosts, path_re):
    return {"id": sid, "name": name, "so": so, "root": root, "hosts": tuple(h.lower() for h in hosts),
            "path_re": path_re}


# The frame, fixed in the pre-registration. Microsoft Azure, NuGet and MSBuild (all on
# learn.microsoft.com) are the reference studied in studies 7 and 8, not part of these 20.
SITES = [
    _site("docker", "Docker", "Docker", "https://docs.docker.com/", ["docs.docker.com"], r"^/"),
    _site("npm", "npm", "npm", "https://docs.npmjs.com/", ["docs.npmjs.com"], r"^/"),
    _site("aws", "Amazon Web Services", "Amazon Web Services (AWS)", "https://docs.aws.amazon.com/",
          ["docs.aws.amazon.com"], r"^/"),
    _site("gcloud", "Google Cloud", "Google Cloud", "https://cloud.google.com/docs",
          ["cloud.google.com", "docs.cloud.google.com"], r"/docs(?:/|$)"),
    _site("cloudflare", "Cloudflare", "Cloudflare", "https://developers.cloudflare.com/",
          ["developers.cloudflare.com"], r"^/"),
    _site("terraform", "Terraform (HashiCorp)", "Terraform", "https://developer.hashicorp.com/terraform",
          ["developer.hashicorp.com"], r"^/terraform(?:/|$)"),
    _site("firebase", "Firebase", "Firebase", "https://firebase.google.com/docs", ["firebase.google.com"],
          r"^/docs(?:/|$)"),
    _site("ansible", "Ansible", "Ansible", "https://docs.ansible.com/", ["docs.ansible.com"], r"^/"),
    _site("chocolatey", "Chocolatey", "Chocolatey", "https://docs.chocolatey.org/", ["docs.chocolatey.org"],
          r"^/"),
    _site("digitalocean", "DigitalOcean", "Digital Ocean", "https://docs.digitalocean.com/",
          ["docs.digitalocean.com"], r"^/"),
    _site("vercel", "Vercel", "Vercel", "https://vercel.com/docs", ["vercel.com"], r"^/docs(?:/|$)"),
    _site("datadog", "Datadog", "Datadog", "https://docs.datadoghq.com/", ["docs.datadoghq.com"], r"^/"),
    _site("netlify", "Netlify", "Netlify", "https://docs.netlify.com/", ["docs.netlify.com"], r"^/"),
    _site("supabase", "Supabase", "Supabase", "https://supabase.com/docs", ["supabase.com"],
          r"^/docs(?:/|$)"),
    _site("heroku", "Heroku", "Heroku", "https://devcenter.heroku.com/", ["devcenter.heroku.com"],
          r"^/articles/"),
    _site("splunk", "Splunk", "Splunk", "https://help.splunk.com/", ["help.splunk.com", "docs.splunk.com"],
          r"^/"),
    _site("newrelic", "New Relic", "New Relic", "https://docs.newrelic.com/", ["docs.newrelic.com"],
          r"^/docs/"),
    _site("railway", "Railway", "Railway", "https://docs.railway.com/", ["docs.railway.com", "docs.railway.app"],
          r"^/"),
    _site("ibmcloud", "IBM Cloud", "IBM Cloud", "https://cloud.ibm.com/docs", ["cloud.ibm.com"],
          r"^/docs(?:/|$)"),
    _site("yandex", "Yandex Cloud", "Yandex Cloud", "https://yandex.cloud/en/docs", ["yandex.cloud"],
          r"^/en/docs(?:/|$)"),
]

CONTROLS = [
    ("control-md", "https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app"),
    ("control-note", "https://devblogs.microsoft.com/performance-diagnostics/"
                     "introducing-windbg-mcp-debug-with-natural-language-grounded-in-evidence/"),
]

LOCALE_RE = re.compile(r"^(?:ja|ko|zh|fr|de|es|pt|it|ru|id|tr|ar|he|th|vi|pl|nl|sv|uk|cs|da|fi|nb|no|hu|ro|"
                       r"el|bg|hr|sk|sl|et|lv|lt|hi|bn|fa|kk|uz|cn|jp|kr|tw)(?:[-_][a-z]{2,4})?$", re.I)
SKIP_EXT = re.compile(r"\.(?:pdf|xml|json|txt|md|zip|gz|tgz|tar|png|jpe?g|gif|svg|webp|ico|csv|ya?ml|mp4|webm|"
                      r"css|js|woff2?)$", re.I)
LOC_RE = re.compile(r"<loc>\s*(?:<!\[CDATA\[)?\s*(.*?)\s*(?:\]\]>)?\s*</loc>", re.I | re.S)
HREF_RE = re.compile(r"\bhref\s*=\s*[\"']([^\"'#<>]+)", re.I)
HTML_START_RE = re.compile(r"<(?:!doctype\s+html|html[\s>])", re.I)
BLOCKED_RE = re.compile(r"_cf_chl_opt|<title>\s*Just a moment|<title>\s*Access Denied|"
                        r"_Incapsula_Resource|px-captcha|captcha-delivery", re.I)

AI_KEY_RE = re.compile(r"^(?:[a-z0-9]+[._:-])*ai[-_.]?(?:usage|generated|assisted|authored|authorship|"
                       r"disclosure|content|created)$", re.I)
AI_VALUE_RE = re.compile(r"(?<![a-z0-9])ai[- _](?:generated|assisted)(?![a-z0-9-])|trainedalgorithmicmedia", re.I)
TEXT_KEYS = {"title", "description", "keywords", "summary", "abstract", "subject", "tags", "topics", "category",
             "categories", "og:title", "og:description", "og:site_name", "twitter:title",
             "twitter:description", "application-name"}
DISCLOSE_RE = re.compile(
    r"\b(?:created|written|generated|produced|drafted|authored|prepared)\b[^.!?]{0,80}?"
    r"\b(?:with|by|using|from)\b[^.!?]{0,40}?(?:\bAI\b|\bartificial intelligence\b)", re.I)
ALT_RE = re.compile(r"\bAI[- ](?:assisted|generated)\s+content\b", re.I)
SUBJECT_RE = re.compile(r"\b(?:article|page|content|document|documentation|topic|post|guide)\b", re.I)
RAW_RE = re.compile(r"(?:assistance from|help of|generated by|created with|created by)\s+(?:the\s+)?AI\b", re.I)
RAW_LABEL_RE = re.compile(r"trainedAlgorithmicMedia", re.I)
META_RE = re.compile(r"<meta\b[^>]*>", re.I)
ATTR_RE = re.compile(r"([A-Za-z_:][A-Za-z0-9_:.\-]*)\s*=\s*(?:\"([^\"]*)\"|'([^']*)')")
DROP_RE = re.compile(r"<(script|style|noscript|template)\b[^>]*>.*?</\1\s*>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
BLOCK_RE = re.compile(r"</?(?:p|div|li|ul|ol|h[1-6]|br|tr|td|th|table|section|aside|article|main|header|"
                      r"footer|nav|blockquote|details|summary|dt|dd|form|button|figure|figcaption)\b[^>]*>", re.I)
KV_RE = re.compile(r"^([A-Za-z0-9_.\-]+)[ \t]*:(?:[ \t]+(.*))?$")

PAGE_COLUMNS = ["site", "url", "final_url", "html_status", "html_ctype", "readable", "blocked", "html_ai_key",
                "html_ai_value", "note_html", "note_html_text", "note_raw_html", "raw_label",
                "md_accept_status", "md_accept", "md_suffix_status", "md_suffix", "md_ai_key", "md_ai_value",
                "md_keys", "note_md", "note_md_text"]
SITE_COLUMNS = ["id", "name", "so", "root", "robots_status", "content_signal", "method", "sitemaps_read", "pool",
                "sampled", "readable", "blocked", "llms_txt", "llms_url", "llms_full", "md_pages",
                "md_accept_pages", "md_suffix_pages", "label_pages", "note_pages", "raw_note_pages"]


# ---------------------------------------------------------------- URLs

def base_of(url):
    try:
        p = urllib.parse.urlsplit(url or "")
    except ValueError:
        return ""
    return "%s://%s" % (p.scheme, p.netloc)


def clean_url(u):
    return htmlmod.unescape((u or "").strip()).split("#")[0]


def in_scope(url, site):
    """True for an English HTML docs page of this site, by host, path rule and file type."""
    try:
        p = urllib.parse.urlsplit((url or "").strip())
        host = (p.hostname or "").lower()
    except ValueError:
        return False
    if p.scheme not in ("http", "https") or host not in site["hosts"]:
        return False
    if p.query:
        return False
    path = p.path or "/"
    if not re.search(site["path_re"], path) or SKIP_EXT.search(path):
        return False
    segs = [s for s in path.split("/") if s][:2]
    return not any(LOCALE_RE.match(s) for s in segs)


def md_suffix_url(url):
    """The llms.txt convention's Markdown address: <path>.md ('/' -> '/index.md')."""
    p = urllib.parse.urlsplit(url)
    path = p.path.rstrip("/") or "/index"
    return urllib.parse.urlunsplit((p.scheme, p.netloc, path + ".md", "", ""))


def prioritise(urls, seed):
    """Sitemap URLs whose path names 'doc' first, each group in a seeded shuffle."""
    urls = list(dict.fromkeys(urls))
    rnd = random.Random(seed)
    rnd.shuffle(urls)
    return sorted(urls, key=lambda u: 0 if "doc" in urllib.parse.urlsplit(u).path.lower() else 1)


# ---------------------------------------------------------------- reading responses

def body_text(body, limit=MAX_SITEMAP_BYTES):
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
    if status != 200 or not (text or "").strip() or is_html(text, ctype):
        return False
    ct = (ctype or "").lower()
    if "markdown" in ct:
        return True
    head = text.lstrip("\ufeff \t\r\n")
    return ("text/plain" in ct or not ct) and (head.startswith("---") or head.startswith("#"))


def llms_valid(status, ctype, text):
    if status != 200 or is_html(text, ctype):
        return False
    for line in (text or "").lstrip("\ufeff").splitlines():
        if line.strip():
            return line.lstrip().startswith("# ")
    return False


def parse_sitemap(text):
    """('index' | 'urlset' | '', [loc, ...])."""
    t = text or ""
    head = t[:5000].lower()
    locs = [htmlmod.unescape(m.group(1)).strip() for m in LOC_RE.finditer(t)]
    if "<sitemapindex" in head:
        return "index", locs
    if "<urlset" in head:
        return "urlset", locs
    lines = [x.strip() for x in t.splitlines() if x.strip()]
    if lines and all(x.startswith(("http://", "https://")) for x in lines[:50]):
        return "urlset", lines
    return "", []


def links(text, base, site):
    out = []
    for m in HREF_RE.finditer(text or ""):
        try:
            u = clean_url(urllib.parse.urljoin(base, htmlmod.unescape(m.group(1))))
        except ValueError:
            continue
        if in_scope(u, site) and u not in out:
            out.append(u)
    return out


def meta_label(fields):
    """(key, value) of the first AI label among name -> value fields, or ('', '')."""
    for k, v in fields.items():
        if AI_KEY_RE.match(k.strip()):
            return k, str(v)[:60]
    for k, v in fields.items():
        if k.strip().lower() not in TEXT_KEYS and AI_VALUE_RE.search(str(v)):
            return k, str(v)[:60]
    return "", ""


def disclosure(text):
    """The first sentence that acknowledges AI's role in making the page, or ''."""
    for para in re.split(r"\n[ \t]*\n", text or ""):
        flat = re.sub(r"\s+", " ", para).strip()
        for sent in re.split(r"(?<=[.!?])\s+", flat):
            if not sent or len(sent) > 400:
                continue
            if ALT_RE.search(sent) or (DISCLOSE_RE.search(sent) and SUBJECT_RE.search(sent)):
                return sent.strip()[:200]
    return ""


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
    t = DROP_RE.sub(" ", text or "")
    t = BLOCK_RE.sub("\n\n", t)
    return htmlmod.unescape(TAG_RE.sub(" ", t))


def read_html(text):
    key, val = meta_label(html_metas(text))
    return {"key": key, "value": val, "note": disclosure(visible_text(text)),
            "raw": bool(RAW_RE.search(text or "")), "raw_label": bool(RAW_LABEL_RE.search(text or ""))}


def split_front(text):
    t = (text or "").lstrip("\ufeff")
    lines = t.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, min(len(lines), 400)):
            if lines[i].strip() in ("---", "..."):
                return lines[1:i], "\n".join(lines[i + 1:])
    return [], t


def read_md(text):
    lines, body = split_front(text)
    fields = collections.OrderedDict()
    for line in lines:
        m = KV_RE.match(line)
        if m and m.group(1) not in fields:
            fields[m.group(1)] = (m.group(2) or "").strip().strip("\"'")
    key, val = meta_label(fields)
    return {"key": key, "value": val, "keys": list(fields), "note": disclosure(body)}


# ---------------------------------------------------------------- HTTP

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
    """A function base -> {'status', 'allowed', 'sitemaps', 'signals'} with a per-host cache. An
    unreadable robots.txt allows everything (RFC 9309 for 4xx; urllib for an empty file)."""
    cache = {}

    def robots_for(base):
        if base not in cache:
            st, ct, _f, body = polite_fetch(fetch, base + "/robots.txt", "text/plain", sleep)
            text = body_text(body) if st == 200 else ""
            if is_html(text, ct):
                text = ""
            rp = urllib.robotparser.RobotFileParser()
            rp.parse(text.splitlines())
            sitemaps, signals = [], []
            for line in text.splitlines():
                s = line.strip()
                low = s.lower()
                if low.startswith("sitemap:"):
                    sitemaps.append(s.split(":", 1)[1].strip())
                elif low.startswith("content-signal:"):
                    signals.append(s.split(":", 1)[1].strip())
            cache[base] = {"status": st, "allowed": (lambda u, rp=rp: rp.can_fetch(USER_AGENT, u)),
                           "sitemaps": sitemaps, "signals": signals}
        return cache[base]
    return robots_for


# ---------------------------------------------------------------- per site

def sitemap_candidates(site, robots_sitemaps):
    base = base_of(site["root"])
    out = list(robots_sitemaps) + [base + "/sitemap.xml", site["root"].rstrip("/") + "/sitemap.xml",
                                   base + "/sitemap_index.xml"]
    return list(dict.fromkeys(out))


def collect_urls(site, fetch, sleep, robots_for, min_pool=PER_SITE, want=WANT_URLS, max_docs=MAX_SITEMAPS):
    """(set of in-scope URLs, method, sitemap files read, log)."""
    rb = robots_for(base_of(site["root"]))
    queue = prioritise(sitemap_candidates(site, rb["sitemaps"]), "study9|%s|start" % site["id"])
    seen, urls, log = set(), set(), []
    read = 0
    while queue and read < max_docs and len(urls) < want:
        sm = queue.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        if not robots_for(base_of(sm))["allowed"](sm):
            log.append([sm, "robots"])
            continue
        st, _ct, _f, body = polite_fetch(fetch, sm, ACCEPT_XML, sleep, MAX_SITEMAP_BYTES)
        read += 1
        if st != 200:
            log.append([sm, st])
            continue
        kind, locs = parse_sitemap(body_text(body))
        log.append([sm, kind or "not a sitemap", len(locs)])
        if kind == "index":
            queue.extend(prioritise([u for u in locs if u not in seen], "study9|%s|%s" % (site["id"], sm)))
        elif kind == "urlset":
            for u in locs:
                u = clean_url(u)
                if in_scope(u, site):
                    urls.add(u)
    method = "sitemap"
    if len(urls) < min_pool:
        method = "sitemap+crawl" if urls else "crawl"
        found = []
        if robots_for(base_of(site["root"]))["allowed"](site["root"]):
            st, ct, final, body = polite_fetch(fetch, site["root"], ACCEPT_HTML, sleep)
            text = body_text(body)
            if st == 200 and is_html(text, ct):
                found = links(text, final or site["root"], site)
        urls.update(found)
        more = sorted(found)
        random.Random("study9|%s|crawl" % site["id"]).shuffle(more)
        for u in more[:CRAWL_PAGES]:
            if not robots_for(base_of(u))["allowed"](u):
                continue
            st, ct, final, body = polite_fetch(fetch, u, ACCEPT_HTML, sleep)
            text = body_text(body)
            if st == 200 and is_html(text, ct):
                urls.update(links(text, final or u, site))
        log.append(["crawl", len(urls)])
    return urls, method, read, log


def draw(urls, site, n=PER_SITE):
    pool = sorted(urls)
    if len(pool) > n:
        pool = random.Random("study9|%s" % site["id"]).sample(pool, n)
    return sorted(pool)


def check_llms(site, fetch, sleep, robots_for):
    base = base_of(site["root"])
    out = {"llms_txt": False, "llms_url": "", "llms_full": False}
    for name, key in (("llms.txt", "llms_txt"), ("llms-full.txt", "llms_full")):
        for u in dict.fromkeys([base + "/" + name, site["root"].rstrip("/") + "/" + name]):
            if not robots_for(base_of(u))["allowed"](u):
                continue
            st, ct, _f, body = polite_fetch(fetch, u, "text/plain,text/markdown", sleep)
            if llms_valid(st, ct, body_text(body)):
                out[key] = True
                if key == "llms_txt":
                    out["llms_url"] = u
                break
    return out


def check_page(url, fetch, sleep, robots_for, site_id=""):
    row = {c: "" for c in PAGE_COLUMNS}
    row.update(site=site_id, url=url, readable=False, blocked=False, note_html=False, note_raw_html=False,
               raw_label=False, md_accept=False, md_suffix=False, note_md=False)
    if not robots_for(base_of(url))["allowed"](url):
        row["html_status"] = "robots"
        return row
    st, ct, final, body = polite_fetch(fetch, url, ACCEPT_HTML, sleep)
    text = body_text(body, MAX_BYTES)
    row.update(html_status=st, html_ctype=(ct or "")[:60], final_url=final)
    if blocked(st, text):
        row["blocked"] = True
    elif st == 200 and is_html(text, ct):
        row["readable"] = True
        h = read_html(text)
        row.update(html_ai_key=h["key"], html_ai_value=h["value"], note_html=bool(h["note"]),
                   note_html_text=h["note"], note_raw_html=h["raw"], raw_label=h["raw_label"])
    copies = []
    st2, ct2, _f2, body2 = polite_fetch(fetch, url, ACCEPT_MD, sleep)
    t2 = body_text(body2, MAX_BYTES)
    row["md_accept_status"] = st2
    if md_ok(st2, ct2, t2):
        row["md_accept"] = True
        copies.append(t2)
    murl = md_suffix_url(url)
    if robots_for(base_of(murl))["allowed"](murl):
        st3, ct3, _f3, body3 = polite_fetch(fetch, murl, ACCEPT_MD, sleep)
        t3 = body_text(body3, MAX_BYTES)
        row["md_suffix_status"] = st3
        if md_ok(st3, ct3, t3):
            row["md_suffix"] = True
            copies.append(t3)
    else:
        row["md_suffix_status"] = "robots"
    for c in copies:
        m = read_md(c)
        if not row["md_ai_key"] and m["key"]:
            row.update(md_ai_key=m["key"], md_ai_value=m["value"])
        if not row["md_keys"]:
            row["md_keys"] = " ".join(m["keys"][:30])
        if m["note"] and not row["note_md"]:
            row.update(note_md=True, note_md_text=m["note"])
    return row


def site_row(site, rb, method, read, pool, pages, llms):
    rp = [p for p in pages if p["readable"]]
    return {"id": site["id"], "name": site["name"], "so": site["so"], "root": site["root"],
            "robots_status": rb["status"], "content_signal": " | ".join(rb["signals"])[:200], "method": method,
            "sitemaps_read": read, "pool": pool, "sampled": len(pages), "readable": len(rp),
            "blocked": sum(1 for p in pages if p["blocked"]), "llms_txt": llms["llms_txt"],
            "llms_url": llms["llms_url"], "llms_full": llms["llms_full"],
            "md_pages": sum(1 for p in rp if p["md_accept"] or p["md_suffix"]),
            "md_accept_pages": sum(1 for p in rp if p["md_accept"]),
            "md_suffix_pages": sum(1 for p in rp if p["md_suffix"]),
            "label_pages": sum(1 for p in rp if p["html_ai_key"] or p["md_ai_key"]),
            "note_pages": sum(1 for p in rp if p["note_html"] or p["note_md"]),
            "raw_note_pages": sum(1 for p in rp if p["note_raw_html"])}


# ---------------------------------------------------------------- summary and predictions

def pct(a, b):
    return round(100.0 * a / b, 2) if b else None


def summarise(sites, pages, controls, readable_min=READABLE_MIN, gate_sites=GATE_SITES):
    rs = [s for s in sites if s["readable"] >= readable_min]
    ids = set(s["id"] for s in rs)
    rp = [p for p in pages if p["readable"] and p["site"] in ids]
    ctl = {c["control"]: c for c in controls}
    g1 = len(rs) >= gate_sites
    g2 = bool(ctl.get("control-md", {}).get("md_ai_key"))
    g3 = bool(ctl.get("control-note", {}).get("note_html"))

    def grade(k, n, ok, holds):
        return {"k": k, "n": n, "value_pct": pct(k, n), "held": holds(k, n) if ok else None}

    preds = collections.OrderedDict()
    preds["P1"] = grade(sum(1 for s in rs if s["label_pages"]), len(rs), g1 and g2, lambda k, n: k <= 2)
    preds["P2"] = grade(sum(1 for s in rs if s["note_pages"]), len(rs), g1 and g3, lambda k, n: k <= 2)
    k = sum(1 for p in rp if p["html_ai_key"] or p["md_ai_key"] or p["note_html"] or p["note_md"])
    preds["P3"] = grade(k, len(rp), g1 and g2 and g3, lambda k, n: 100 * k <= n)
    preds["P4"] = grade(sum(1 for s in sites if s["llms_txt"]), len(sites), len(sites) >= gate_sites,
                        lambda k, n: k >= 10)
    preds["P5"] = grade(sum(1 for s in rs if 2 * s["md_pages"] >= s["readable"]), len(rs), g1,
                        lambda k, n: k >= 6)
    preds["P6"] = {"k": None, "n": len(sites), "value_pct": None, "held": None, "note": "graded by hand"}

    keys = collections.Counter()
    for s_id in sorted(set(p["site"] for p in pages)):
        site_keys = set()
        for p in pages:
            if p["site"] == s_id and p["md_keys"]:
                site_keys.update(p["md_keys"].split())
        keys.update(site_keys)
    labels = collections.Counter("%s=%s" % (p["html_ai_key"] or p["md_ai_key"], p["html_ai_value"] or p["md_ai_value"])
                                 for p in pages if p["html_ai_key"] or p["md_ai_key"])
    notes = collections.Counter(p["note_html_text"] or p["note_md_text"] for p in pages
                                if p["note_html"] or p["note_md"])
    return collections.OrderedDict([
        ("sites", len(sites)), ("readable_sites", len(rs)), ("pages_sampled", len(pages)),
        ("pages_readable", sum(1 for p in pages if p["readable"])), ("pages_counted", len(rp)),
        ("gates", {"G1": {"readable_sites": len(rs), "passed": g1}, "G2": {"passed": g2}, "G3": {"passed": g3}}),
        ("predictions", preds),
        ("md_header_keys_by_sites", dict(keys.most_common(30))),
        ("labels", dict(labels.most_common(20))), ("note_texts", dict(notes.most_common(30))),
        ("controls", controls),
    ])


# ---------------------------------------------------------------- output

def write_csv(path, rows, columns):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in columns})


def report(meta, s, sites):
    yn = {True: "yes", False: "no", None: "n/a"}
    out = ["# vendordocs %s: do company docs sites tell readers which pages were made with AI? (automatic report)"
           % VERSION, "", "First pass written by the tool. The graded result is in RESULT.md.", "",
           "- Started %s, finished %s." % (meta["started"], meta.get("finished")),
           "- Pre-registration first committed: %s." % (meta["prereg"].get("committed_at")
                                                       or "not found (%s)" % meta["prereg"].get("error")),
           "- Sites: %d; readable (at least %d pages): %d. Pages sampled %d, readable %d, counted %d." % (
               s["sites"], READABLE_MIN, s["readable_sites"], s["pages_sampled"], s["pages_readable"],
               s["pages_counted"]),
           "- Gates: G1 %s, G2 %s, G3 %s." % tuple(yn[s["gates"][g]["passed"]] for g in ("G1", "G2", "G3")),
           "", "## Predictions (automatic, before the hand check)", "", "| | k | n | % | held |",
           "|---|---|---|---|---|"]
    for k, p in s["predictions"].items():
        out.append("| %s | %s | %s | %s | %s |" % (k, p["k"], p["n"], p["value_pct"], yn[p["held"]]))
    out += ["", "## Sites", "",
            "| site | method | pool | sampled | readable | blocked | llms.txt | MD copy | AI label | AI note |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for r in sites:
        out.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["name"], r["method"], r["pool"], r["sampled"], r["readable"], r["blocked"], yn[bool(r["llms_txt"])],
            r["md_pages"], r["label_pages"], r["note_pages"]))
    out += ["", "## AI labels found", ""]
    out += ["- %d x %s" % (n, t) for t, n in s["labels"].items()] or ["- none"]
    out += ["", "## Acknowledgement sentences found (to be hand-checked)", ""]
    out += ["- %d x \"%s\"" % (n, t) for t, n in s["note_texts"].items()] or ["- none"]
    out += ["", "## Controls", ""]
    out += ["- %s" % json.dumps({k: c.get(k) for k in ("control", "url", "html_status", "readable", "md_accept",
                                                      "md_ai_key", "note_html", "note_html_text")})
            for c in s["controls"]]
    return "\n".join(out) + "\n"


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


def main(argv=None, fetch=None, sleep=time.sleep, opener=None, sites=None, controls=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--per-site", type=int, default=PER_SITE)
    ap.add_argument("--prereg-path", default=PREREG_PATH)
    ap.add_argument("--no-prereg-check", action="store_true")
    ap.add_argument("--wait-prereg-minutes", type=float, default=0)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    sites = SITES if sites is None else sites
    controls = CONTROLS if controls is None else controls
    meta = {"version": VERSION, "started": utcnow(), "settings": {"per_site": a.per_site, "want_urls": WANT_URLS,
                                                                  "max_sitemaps": MAX_SITEMAPS}}

    def dump(obj):
        with open(os.path.join(a.out_dir, "vendordocs.json"), "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=1, default=str)

    if a.no_prereg_check:
        meta["prereg"] = {"committed_at": None, "error": "not checked"}
    else:
        meta["prereg"] = wait_for_prereg(a.prereg_path, a.wait_prereg_minutes, opener, sleep)
        if a.wait_prereg_minutes > 0 and meta["prereg"].get("committed_at") is None:
            print("pre-registration %s not found; nothing was read" % a.prereg_path)
            dump(meta)
            return 3

    fetch = fetch or default_fetch
    robots_for = make_robots(fetch, sleep)
    site_rows, pages, logs = [], [], {}
    for site in sites:
        urls, method, read, log = collect_urls(site, fetch, sleep, robots_for, min_pool=a.per_site)
        picked = draw(urls, site, a.per_site)
        llms = check_llms(site, fetch, sleep, robots_for)
        sp = [check_page(u, fetch, sleep, robots_for, site["id"]) for u in picked]
        pages.extend(sp)
        row = site_row(site, robots_for(base_of(site["root"])), method, read, len(urls), sp, llms)
        site_rows.append(row)
        logs[site["id"]] = log[:40]
        print("%-14s %-13s pool %5d sampled %2d readable %2d md %2d label %2d note %2d llms %s" % (
            site["id"], method, len(urls), len(sp), row["readable"], row["md_pages"], row["label_pages"],
            row["note_pages"], row["llms_txt"]))
        sys.stdout.flush()
    ctl_rows = []
    for name, url in controls:
        c = check_page(url, fetch, sleep, robots_for, name)
        c["control"] = name
        ctl_rows.append(c)

    summary = summarise(site_rows, pages, ctl_rows)
    meta["finished"] = utcnow()
    write_csv(os.path.join(a.out_dir, "sites.csv"), site_rows, SITE_COLUMNS)
    write_csv(os.path.join(a.out_dir, "pages.csv"), ctl_rows + pages, ["control"] + PAGE_COLUMNS)
    dump({"meta": meta, "summary": summary, "sites": site_rows, "sitemap_logs": logs})
    text = report(meta, summary, site_rows)
    with open(os.path.join(a.out_dir, "VENDORDOCS_AUTO.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
