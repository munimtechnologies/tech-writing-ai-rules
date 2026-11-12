#!/usr/bin/env python3
# rawcopy_scan.py 0.1.0 - Apache-2.0
# By MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
#
# Compare the Markdown copies a docs site's llms.txt links to (Nuxt Content's
# /raw/<path>.md route) with a second Markdown copy of the same page
# (<path>.md, the same address without the /raw segment), and count component
# tags that reach the raw copy empty (for example <partial content="x"></partial>,
# whose text the web page shows but the copy does not).
#
# Standard library only. Reads public pages politely (one request at a time,
# a pause between requests, an identifying User-Agent).

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

VERSION = "0.1.0"
UA = ("rawcopy_scan/%s (+https://github.com/munimtechnologies/tech-writing-ai-rules; "
      "MV2 of Munim, Inc., mv2@munimtech.com)" % VERSION)

LINK_RE = re.compile(r"\[([^\]]*)\]\((https?://[^)\s]+)\)")
FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
# <partial ...> ... </partial>, shortest match, across lines
PARTIAL_RE = re.compile(r"<partial\b([^>]*)>(.*?)</partial\s*>", re.S | re.I)
ATTR_CONTENT_RE = re.compile(r"""\bcontent\s*=\s*["']([^"']+)["']""")
# opening tag of a custom element (name contains a hyphen) or a known MDC component
KNOWN_COMPONENTS = {"partial", "callout", "card", "tabs", "tab", "steps", "badge",
                    "icon", "note", "tip", "warning", "caution"}
OPEN_TAG_RE = re.compile(r"<([A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*)\b[^>]*?>")
WORD_RE = re.compile(r"[A-Za-z0-9_]+")
TAG_RE = re.compile(r"<[^>\n]+>")


def strip_fences(text):
    """Return the text with fenced code blocks removed (fence lines included)."""
    out = []
    fence = None
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)[0] * 3
                continue
            out.append(line)
        else:
            if m and m.group(1).startswith(fence):
                fence = None
            continue
    return "\n".join(out)


def partials(text):
    """List of (name, empty) for every <partial> element outside code fences."""
    body = strip_fences(text)
    found = []
    for m in PARTIAL_RE.finditer(body):
        am = ATTR_CONTENT_RE.search(m.group(1))
        name = am.group(1) if am else ""
        found.append((name, m.group(2).strip() == ""))
    return found


def component_tags(text):
    """Count opening tags of components (hyphenated custom elements or known MDC names)."""
    body = strip_fences(text)
    counts = {}
    for m in OPEN_TAG_RE.finditer(body):
        name = m.group(1).lower()
        if "-" in name or name in KNOWN_COMPONENTS:
            counts[name] = counts.get(name, 0) + 1
    return counts


def word_count(text):
    body = TAG_RE.sub(" ", strip_fences(text))
    return len(WORD_RE.findall(body))


def raw_links(llms_txt, domain=None):
    """Unique links in llms.txt whose path contains /raw/ and ends in .md, in order."""
    seen = []
    for _title, url in LINK_RE.findall(llms_txt):
        if "/raw/" in url and url.split("?")[0].split("#")[0].endswith(".md"):
            if domain and not url.startswith(domain):
                continue
            if url not in seen:
                seen.append(url)
    return seen


def twin_url(raw_url):
    """The same page's address without the /raw segment (first occurrence)."""
    return raw_url.replace("/raw/", "/", 1)


def fetch(url, timeout=30):
    """Return (status, content_type, text). Never raises for HTTP errors."""
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "text/markdown, text/plain;q=0.9, */*;q=0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
            return r.status, r.headers.get("Content-Type", ""), data.decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", "") if e.headers else "", ""
    except Exception as e:  # network error
        return 0, "error: %s" % type(e).__name__, ""


def looks_html(ctype, text):
    head = text.lstrip()[:200].lower()
    return "text/html" in (ctype or "").lower() or head.startswith("<!doctype html") or head.startswith("<html")


def analyse_pair(raw_text, twin_text):
    rp = partials(raw_text)
    tp = partials(twin_text)
    rc = component_tags(raw_text)
    return {
        "raw_words": word_count(raw_text),
        "twin_words": word_count(twin_text),
        "raw_partials": len(rp),
        "raw_empty_partials": sum(1 for _, e in rp if e),
        "raw_empty_partial_names": ";".join(sorted({n for n, e in rp if e})),
        "twin_partial_tags": len(tp),
        "raw_component_tags": sum(rc.values()),
        "raw_component_names": ";".join("%s:%d" % kv for kv in sorted(rc.items())),
    }


FIELDS = ["raw_url", "raw_status", "twin_url", "twin_status", "twin_is_html",
          "raw_words", "twin_words", "raw_partials", "raw_empty_partials",
          "raw_empty_partial_names", "twin_partial_tags", "raw_component_tags",
          "raw_component_names"]


def summarise(rows, llms_url, llms_status, extra_status):
    ok = [r for r in rows if r["raw_status"] == 200]
    pairs = [r for r in ok if r["twin_status"] == 200 and not r["twin_is_html"]]
    with_empty = [r for r in ok if r["raw_empty_partials"] > 0]
    names = {}
    for r in with_empty:
        for n in r["raw_empty_partial_names"].split(";"):
            if n:
                names[n] = names.get(n, 0) + 1
    words_lost = [r["twin_words"] - r["raw_words"] for r in pairs if r["raw_empty_partials"] > 0]
    return {
        "tool": "rawcopy_scan", "version": VERSION,
        "llms_txt": llms_url, "llms_txt_status": llms_status,
        "other_status": extra_status,
        "raw_links": len(rows),
        "raw_ok": len(ok),
        "twin_markdown_ok": len(pairs),
        "pages_with_empty_partial": len(with_empty),
        "empty_partials_total": sum(r["raw_empty_partials"] for r in ok),
        "pages_by_partial_name": dict(sorted(names.items(), key=lambda kv: (-kv[1], kv[0]))),
        "twins_with_partial_tags": sum(1 for r in pairs if r["twin_partial_tags"] > 0),
        "median_words_missing_where_empty": (sorted(words_lost)[len(words_lost) // 2]
                                             if words_lost else None),
        "pages_with_component_tags": sum(1 for r in ok if r["raw_component_tags"] > 0),
    }


def render_md(s):
    lines = ["# rawcopy_scan %s summary (automatic, not hand-checked)" % s["version"], "",
             "- llms.txt: %s (HTTP %s)" % (s["llms_txt"], s["llms_txt_status"]),
             "- /raw/ links in llms.txt: %d; fetched OK: %d; Markdown twin fetched OK: %d"
             % (s["raw_links"], s["raw_ok"], s["twin_markdown_ok"]),
             "- raw copies with at least one empty <partial>: %d (empty partials in all: %d)"
             % (s["pages_with_empty_partial"], s["empty_partials_total"]),
             "- twins that still contain <partial> tags: %d" % s["twins_with_partial_tags"],
             "- median words missing (twin minus raw) where a partial is empty: %s"
             % s["median_words_missing_where_empty"],
             "- raw copies with component tags: %d" % s["pages_with_component_tags"], "",
             "## Pages per empty partial", ""]
    for n, c in s["pages_by_partial_name"].items():
        lines.append("- `%s`: %d" % (n, c))
    lines += ["", "## Other addresses", ""]
    for u, st in s["other_status"].items():
        lines.append("- %s: HTTP %s" % (u, st))
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Compare /raw/ Markdown copies with their .md twins.")
    ap.add_argument("--llms", default="https://directus.com/docs/llms.txt")
    ap.add_argument("--also", action="append", default=[],
                    help="extra address to record the HTTP status of (repeatable)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--delay", type=float, default=0.5)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--version", action="version", version="rawcopy_scan " + VERSION)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    st, ct, llms = fetch(a.llms)
    with open(os.path.join(a.out_dir, "llms.txt"), "w", encoding="utf-8") as f:
        f.write(llms)
    if st != 200 or not llms:
        print("error: llms.txt HTTP %s" % st, file=sys.stderr)
        return 3
    links = raw_links(llms)
    if a.limit:
        links = links[:a.limit]
    print("rawcopy_scan %s: %d /raw/ links" % (VERSION, len(links)))
    rows = []
    for i, u in enumerate(links, 1):
        rs, _rct, rt = fetch(u)
        time.sleep(a.delay)
        tu = twin_url(u)
        ts, tct, tt = fetch(tu)
        time.sleep(a.delay)
        twin_html = looks_html(tct, tt)
        row = {"raw_url": u, "raw_status": rs, "twin_url": tu, "twin_status": ts,
               "twin_is_html": twin_html}
        row.update(analyse_pair(rt, "" if twin_html else tt))
        rows.append(row)
        if i % 25 == 0:
            print("  %d/%d" % (i, len(links)))
    extra = {}
    for u in a.also:
        extra[u] = fetch(u)[0]
        time.sleep(a.delay)
    with open(os.path.join(a.out_dir, "pages.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    s = summarise(rows, a.llms, st, extra)
    with open(os.path.join(a.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)
    md = render_md(s)
    with open(os.path.join(a.out_dir, "RAWCOPY_AUTO.md"), "w", encoding="utf-8") as f:
        f.write(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
