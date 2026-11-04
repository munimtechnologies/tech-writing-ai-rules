# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Census of what paid technical-writing programs' own pages say about AI.

Usage: python programs.py --out-dir OUT [--save-text] [--pause 1.0] [--wait-prereg-minutes 90]
                          [--listing-url URL] [--prereg-path census/2026-11/PREREGISTRATION.md]

The frame is every program bullet in the "Active" and "Paused" sections of one pinned commit of the
community list malgamves/CommunityWriterPrograms (MIT). The list is parsed at run time from that commit, so
the frame cannot drift and no URL is retyped by hand.

For every program it fetches the listed page and up to MAX_FOLLOW same-site links whose text or path looks
like guidelines, FAQ, terms, policies, a style guide or a contributor page. From the visible text it keeps,
word for word, every sentence that mentions AI (the capitalised token "AI", artificial intelligence,
ChatGPT, LLM, generative, AI-detection tools and similar) and every sentence about the program's status or
pay (paused, closed, not accepting, "$300 per article"...).

A deterministic first-pass label is given to each program (classify()); the census's primary coding is done
afterwards by reading the saved sentences against the rubric in the pre-registration, and both are
published.

Writes census.json, sentences.csv, status.csv, frame.csv and CENSUS_AUTO.md to --out-dir (and pages/*.txt
with --save-text). Standard library only. Made by MV2 of Munim, Inc., with AI agents working in his name.
Apache-2.0.

0.1.1 (see CHANGELOG.md): curly apostrophes are matched like straight ones; status cues also catch "not
looking for new writers" and "positions filled"; each page records whether it redirected to a home page or
elsewhere; the detector flag no longer fires on AI sentences about detecting fraud, and a separate flag
records whether a detection tool is named.
"""
import argparse
import csv
import http.cookiejar
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

VERSION = "0.1.1"
USER_AGENT = ("tech-writing-ai-rules-census/%s (+https://github.com/munimtechnologies/"
              "tech-writing-ai-rules)" % VERSION)
REPO_API = "https://api.github.com/repos/munimtechnologies/tech-writing-ai-rules/commits"
LISTING_SHA = "0338535184058ff7099b819679f65ff82dfe30a6"
LISTING_URL = ("https://raw.githubusercontent.com/malgamves/CommunityWriterPrograms/%s/README.md"
               % LISTING_SHA)
MAX_FOLLOW = 5
MIN_CHARS = 500  # a program whose pages all have less visible text than this is "unreadable"

# "AI" is matched case-sensitively so that words such as "aim", "said" or "Maine" never count.
AI_TOKEN = re.compile(r"(?<![A-Za-z0-9])A\.?Is?(?![A-Za-z0-9])")
AI_WORDS = re.compile(
    r"artificial[\s-]+intelligence|chat\s?gpt|\bLLMs?\b|large[\s-]+language[\s-]+models?|\bgenerative\b|"
    r"machine[\s-]+generated|computer[\s-]+generated|\bchat\s?bots?\b|\bgrammarly\b|\bcopilot\b|"
    r"\bclaude\b|\bgemini\b|\bmidjourney\b|text[\s-]+generat\w*|originality\.ai|\bgptzero\b|"
    r"\bcopyleaks\b|\bzerogpt\b", re.I)

BAN_CUE = re.compile(
    r"\b(not|no|never|nor|prohibit\w*|ban|bans|banned|disqualif\w*|ineligible|cannot|can't|won't|don't|"
    r"forbid\w*|reject\w*|exclud\w*|refuse\w*)\b|"
    r"must be (?:\w+ )?(?:your own|original|human)|human[\s-]+(?:written|authored|created|made)|"
    r"written by (?:a )?human|entirely human", re.I)
ASSIST_CUE = re.compile(r"assist\w*|aided|\bany (?:use|form|kind)|\btools?\b|in any (?:way|form|part)|"
                        r"partial\w*|\bedit\w*|grammar|spell", re.I)
ALLOW_CUE = re.compile(r"\b(allow\w*|permit\w*|welcome\w*|may use|can use|accept\w*|disclos\w*|declar\w*|"
                       r"acknowledg\w*)\b", re.I)
TRAIN_CUE = re.compile(r"\btrain(?:s|ing|ed)?\b|\bscrap\w*|\bdatasets?\b|\bmachine learning\b", re.I)

# 0.1.1: a named AI-writing detector (or "AI detector", "AI detection tool"). Recorded as names_detector_tool.
DETECTOR_TOOL = re.compile(
    r"originality\.ai|\bgptzero\b|\bcopyleaks\b|\bzerogpt\b|\bturnitin\b|"
    r"\bAI[\s-]+(?:content[\s-]+|text[\s-]+|writing[\s-]+)?detect(?:or|ors|ion)[\s-]+"
    r"(?:tools?|software|services?|checkers?)\b|"
    r"\bAI[\s-]+detectors?\b", re.I)
# 0.1.1: detection of AI writing, named tool or not. 0.1.0 matched any "detect" word, so an AI sentence
# such as "we use AI to detect fraud" in a privacy policy counted.
DETECTOR_CUE = re.compile(
    DETECTOR_TOOL.pattern + r"|"
    r"\bAI[\s-]+(?:content[\s-]+|text[\s-]+|writing[\s-]+)?detect\w*|"
    r"\bdetect\w*\s+(?:\w+[\s-]+){0,3}?(?:AI|machine)[\s-]+"
    r"(?:generated|written|assisted|drafts?|content|text|writing)\b|"
    r"\bdetect\w*\s+(?:the\s+)?(?:use of\s+)?(?:AI|ChatGPT|LLMs?|generative AI)\b", re.I)

CLOSED_CUE = re.compile(
    r"\bnot (?:currently |presently |actively )?(?:accepting|taking|open)\b|"
    r"\bnot (?:currently |presently |actively )?(?:looking for|hiring|seeking) (?:new |more |any )?"
    r"(?:writers|authors|contributors|submissions|guest posts|articles)\b|"
    r"\bno longer (?:accept\w*|pay\w*|tak\w*|runn?\w*|open|available|offer\w*)|"
    r"\bpositions? (?:are |have been )?filled\b|"
    r"\b(?:paused|on hold|suspended|discontinued|closed)\b", re.I)
PAY_CUE = re.compile(r"[$€£]\s?\d|\bUSD\b|\bper (?:article|post|piece|tutorial|word)\b|"
                     r"\bhonorari(?:um|a)\b|\bpaid\b|\bpay(?:s|ment|ments|out|outs)?\b", re.I)

FOLLOW_TEXT = re.compile(r"\b(guidelines?|faqs?|terms|polic(?:y|ies)|style guide|editorial|contribut\w*|"
                         r"write for us|submissions?|submit|pitch|apply|authors?)\b", re.I)
FOLLOW_PATH = re.compile(r"guideline|faq|terms|polic|style|editorial|contribut|write-for|submi|pitch|apply|"
                         r"author", re.I)
BINARY = re.compile(r"\.(pdf|docx?|jpe?g|png|gif|zip|mp3|mp4)$", re.I)

SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}
BLOCK_TAGS = {"p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "td", "th",
              "section", "article", "header", "footer", "nav", "table", "blockquote", "dd", "dt", "form",
              "main", "aside", "figcaption", "hr", "label", "option", "summary", "details"}
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[\"'“‘(\[]?[A-Z0-9])")
SPACE = re.compile(r"\s+")

ENTRY = re.compile(r"^- \[(?P<name>[^\]]+)\]\((?P<url>[^)\s]+)\)(?P<rest>.*)$")
HEADING = re.compile(r"^##\s+(?P<title>.*?)\s*$")

APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'"})


def norm(s):
    """Curly apostrophes to straight ones, for cue matching only; sentences are always kept as found."""
    return s.translate(APOSTROPHES)


def parse_listing(md):
    """Program bullets in the 'Active' and 'Paused' sections of the list, in file order.

    Returns dicts: id (P01, P02, ...), name, url, section ('Active' or 'Paused'), pay (text after the
    link, leading ' - ' removed) and description (the blockquote lines that follow, joined)."""
    out, section = [], None
    for raw in md.splitlines():
        line = raw.rstrip()
        h = HEADING.match(line)
        if h:
            title = h.group("title")
            section = "Active" if "Active" in title else "Paused" if "Paused" in title else None
            continue
        if section is None:
            continue
        m = ENTRY.match(line)
        if m:
            rest = m.group("rest").strip()
            if rest.startswith("- "):
                rest = rest[2:]
            elif rest.startswith("-"):
                rest = rest[1:].strip()
            out.append({"id": "P%02d" % (len(out) + 1), "name": m.group("name").strip(),
                        "url": m.group("url"), "section": section, "pay": rest, "description": ""})
            continue
        s = line.strip()
        if out and s.startswith(">") and out[-1]["section"] == section:
            text = s.lstrip(">").strip()
            if text:
                out[-1]["description"] = (out[-1]["description"] + " " + text).strip()
    return out


class Extract(HTMLParser):
    """Visible text with line breaks at block elements, plus every link (href, anchor text)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.links = [], []
        self.skip = 0
        self.href, self.anchor = None, []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip += 1
        if tag in BLOCK_TAGS:
            self.parts.append("\n")
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.anchor = []

    def handle_startendtag(self, tag, attrs):
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self.skip:
            self.skip -= 1
        if tag in BLOCK_TAGS:
            self.parts.append("\n")
        if tag == "a" and self.href is not None:
            self.links.append((self.href, SPACE.sub(" ", "".join(self.anchor)).strip()))
            self.href = None

    def handle_data(self, data):
        if self.skip:
            return
        self.parts.append(data)
        if self.href is not None:
            self.anchor.append(data)


def extract(page):
    p = Extract()
    try:
        p.feed(page)
        p.close()
    except Exception:  # malformed HTML: keep what was parsed
        pass
    lines = [SPACE.sub(" ", line).strip() for line in "".join(p.parts).split("\n")]
    return "\n".join(line for line in lines if line), p.links


def sentences(text):
    out = []
    for line in text.split("\n"):
        for s in SENTENCE_END.split(line):
            s = s.strip()
            if s:
                out.append(s)
    return out


def mentions_ai(sentence):
    return bool(AI_TOKEN.search(sentence) or AI_WORDS.search(sentence))


def matching_sentences(text, test, limit=800, most=None):
    found, seen = [], set()
    for s in sentences(text):
        if test(s):
            s = s if len(s) <= limit else s[:limit] + " [...]"
            if s not in seen:
                seen.add(s)
                found.append(s)
                if most is not None and len(found) >= most:
                    break
    return found


def ai_sentences(text, limit=800):
    return matching_sentences(text, mentions_ai, limit)


def is_closed(sentence):
    return bool(CLOSED_CUE.search(norm(sentence)))


def status_sentences(text, limit=400, most=30):
    return matching_sentences(text, lambda s: bool(is_closed(s) or PAY_CUE.search(s)), limit, most)


def host(url):
    h = urllib.parse.urlsplit(url).hostname or ""
    return h[4:] if h.startswith("www.") else h


def redirect_kind(listed, final):
    """'' if the final URL is the listed page (scheme, 'www.' and a trailing slash ignored); 'home' if it is
    a home page while the listed page is not; 'elsewhere' for any other move (another path or site)."""
    if not final:
        return ""
    pa = urllib.parse.urlsplit(listed).path.rstrip("/")
    pb = urllib.parse.urlsplit(final).path.rstrip("/")
    if host(listed) == host(final) and pa == pb:
        return ""
    if pb == "" and pa != "":
        return "home"
    return "elsewhere"


def follow_links(base_url, links, limit=MAX_FOLLOW):
    """Same-site links that look like guidelines/FAQ/terms/policies, in page order. Returns (follow, docs)."""
    follow, docs, seen = [], [], {urllib.parse.urldefrag(base_url)[0]}
    for href, text in links:
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        url = urllib.parse.urldefrag(urllib.parse.urljoin(base_url, href))[0]
        if not url.startswith(("http://", "https://")) or host(url) != host(base_url) or url in seen:
            continue
        path = urllib.parse.urlsplit(url).path
        if not (FOLLOW_TEXT.search(text or "") or FOLLOW_PATH.search(path)):
            continue
        seen.add(url)
        if BINARY.search(path):
            docs.append(url)
        elif len(follow) < limit:
            follow.append(url)
    return follow, docs


def classify(pages, sents):
    """Deterministic first-pass label. pages: list of dicts with 'chars'; sents: AI sentences found.

    unreachable  no page could be read          unreadable  every page read has < MIN_CHARS visible chars
    silent       no AI sentence                 training_only  AI sentences only about training/scraping
    ban          an AI sentence (not about training) has a prohibition cue; scope 'assisted' if a banning
                 sentence also mentions assistance, tools, editing or any use, else 'generated'
    allow_or_conditional  no ban cue, but an allow/disclose cue     other_mention  anything else

    Cues are matched on norm(sentence), so "can’t" counts like "can't" (0.1.1)."""
    read = [p for p in pages if p.get("chars") is not None]
    if not read:
        return "unreachable", None
    if not sents:
        if all(p["chars"] < MIN_CHARS for p in read):
            return "unreadable", None
        return "silent", None
    rule = [norm(s) for s in sents if not TRAIN_CUE.search(s)]
    if not rule:
        return "training_only", None
    bans = [s for s in rule if BAN_CUE.search(s)]
    if bans:
        return "ban", "assisted" if any(ASSIST_CUE.search(s) for s in bans) else "generated"
    if any(ALLOW_CUE.search(s) for s in rule):
        return "allow_or_conditional", None
    return "other_mention", None


CHARSET_ALIASES = {"shift_jis": "cp932", "euc-kr": "cp949", "gb2312": "gb18030", "gbk": "gb18030"}
META_CHARSET = re.compile(rb"""<meta[^>]+charset\s*=\s*["']?([A-Za-z0-9_.:-]+)""", re.I)


def decode(body, header_charset=None):
    m = META_CHARSET.search(body[:8192])
    for cs in (header_charset, m.group(1).decode("ascii") if m else None, "utf-8"):
        if not cs:
            continue
        cs = CHARSET_ALIASES.get(cs.lower(), cs.lower())
        try:
            return body.decode(cs)
        except (LookupError, UnicodeDecodeError):
            pass
    return body.decode("utf-8", errors="replace")


def fetch(url, timeout=45):
    """{'status', 'tls', 'final_url', 'text' (decoded HTML or None), 'error'}.

    Redirects (301/302/303/307/308) are followed with a fresh cookie jar per call, so a site that sets a
    cookie and redirects back to itself does not loop. One unverified retry on a certificate error, marked
    as such."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                                               "Accept-Language": "en"})
    error = None
    for tls, ctx in (("verified", ssl.create_default_context()), ("unverified", ssl._create_unverified_context())):
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
                                             urllib.request.HTTPSHandler(context=ctx))
        try:
            with opener.open(req, timeout=timeout) as resp:
                ctype = resp.headers.get("Content-Type", "")
                body = resp.read(5_000_000)
                if ctype and "html" not in ctype and "text" not in ctype:
                    return {"status": resp.status, "tls": tls, "final_url": resp.geturl(), "text": None,
                            "error": "not html: %s" % ctype}
                return {"status": resp.status, "tls": tls, "final_url": resp.geturl(),
                        "text": decode(body, resp.headers.get_content_charset()), "error": None}
        except urllib.error.HTTPError as e:
            return {"status": e.code, "tls": tls, "final_url": url, "text": None, "error": str(e)}
        except (urllib.error.URLError, ssl.SSLError, OSError) as e:
            error = str(getattr(e, "reason", e))
            if "CERTIFICATE" not in error.upper():
                break
    return {"status": None, "tls": None, "final_url": url, "text": None, "error": error}


def census(programs, fetcher=fetch, pause=1.0):
    results, texts = [], {}
    calls = [0]

    def get(url):
        if calls[0] and pause:
            time.sleep(pause)
        calls[0] += 1
        return fetcher(url)

    for row in programs:
        pages, sents, stat, docs, done = [], [], [], [], set()
        queue = [row["url"]]
        while queue:
            url = queue.pop(0)
            if url in done:
                continue
            done.add(url)
            got = get(url)
            entry = {"url": url, "final_url": got["final_url"], "status": got["status"], "tls": got["tls"],
                     "error": got["error"], "chars": None, "followed": url != row["url"],
                     "redirect": redirect_kind(url, got["final_url"])}
            if got["text"] is not None:
                text, links = extract(got["text"])
                entry["chars"] = len(text)
                texts["%s-%d" % (row["id"], len(pages))] = text
                for s in ai_sentences(text):
                    sents.append({"page": url, "sentence": s})
                for s in status_sentences(text):
                    stat.append({"page": url, "sentence": s})
                if url == row["url"]:
                    more, d = follow_links(got["final_url"] or url, links)
                    docs += d
                    queue += [u for u in more if u not in done]
            pages.append(entry)
        unique, seen = [], set()
        for s in sents:
            if s["sentence"] not in seen:
                seen.add(s["sentence"])
                unique.append(s)
        stat_unique, seen = [], set()
        for s in stat:
            if s["sentence"] not in seen:
                seen.add(s["sentence"])
                stat_unique.append(s)
        label, scope = classify(pages, [s["sentence"] for s in unique])
        results.append({"id": row["id"], "name": row["name"], "url": row["url"], "section": row["section"],
                        "pay_listed": row["pay"], "listing_mentions_ai": mentions_ai(row["description"]),
                        "main_status": pages[0]["status"] if pages else None,
                        "main_redirect": pages[0]["redirect"] if pages else "",
                        "pages": pages, "documents_not_read": docs, "ai_sentences": unique,
                        "status_sentences": stat_unique, "auto_label": label, "auto_scope": scope,
                        "mentions_training": any(TRAIN_CUE.search(s["sentence"]) for s in unique),
                        "mentions_detector": any(DETECTOR_CUE.search(s["sentence"]) for s in unique),
                        "names_detector_tool": any(DETECTOR_TOOL.search(s["sentence"]) for s in unique),
                        "closed_cue": any(is_closed(s["sentence"]) for s in stat_unique)})
    return results, texts


def prereg_commit(path, opener=None):
    """Date of the first commit that added the pre-registration (None if not on main yet)."""
    url = REPO_API + "?" + urllib.parse.urlencode({"path": path, "per_page": 100})
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    try:
        data = json.loads((opener or (lambda r: urllib.request.urlopen(r, timeout=60).read()))(req))
    except Exception as exc:
        return {"committed_at": None, "error": type(exc).__name__}
    if not isinstance(data, list):
        return {"committed_at": None, "error": "unexpected API answer"}
    if not data:
        return {"committed_at": None, "error": "no commit touches %s yet" % path}
    first = data[-1]
    return {"committed_at": first["commit"]["committer"]["date"], "sha": first["sha"], "error": None}


def wait_for_prereg(path, minutes, opener=None, sleep=time.sleep, every=120):
    """Poll until the pre-registration is on main or `minutes` have passed."""
    prereg = prereg_commit(path, opener)
    waited = 0
    while prereg.get("committed_at") is None and waited < minutes * 60:
        sleep(every)
        waited += every
        prereg = prereg_commit(path, opener)
    prereg["waited_seconds"] = waited
    return prereg


def report(results, started, finished, prereg, listing_url):
    labels = ["ban", "allow_or_conditional", "other_mention", "training_only", "silent", "unreadable",
              "unreachable"]
    counts = {k: sum(1 for r in results if r["auto_label"] == k) for k in labels}
    lines = ["# Paid technical-writing programs' AI rules: automatic first pass", "",
             "programs.py %s. Frame: %d programs from %s. Pages fetched %s to %s UTC. "
             "Pre-registration first committed: %s." % (
                 VERSION, len(results), listing_url, started, finished,
                 prereg.get("committed_at") or "not found (%s)" % prereg.get("error")),
             "", "This is the deterministic first pass, not the census's primary coding (see the "
             "pre-registration). Every AI sentence is in sentences.csv and every status or pay sentence in "
             "status.csv, word for word.", "",
             "| Auto label | Programs |", "|---|---|"]
    lines += ["| %s | %d |" % (k, counts[k]) for k in labels]
    bans = [r for r in results if r["auto_label"] == "ban"]
    lines += ["", "Ban scope (auto): assisted %d, generated only %d." % (
        sum(1 for r in bans if r["auto_scope"] == "assisted"), sum(1 for r in bans if r["auto_scope"] == "generated")),
        "Programs whose AI sentences mention detecting AI writing: %d (naming a detection tool: %d)." % (
            sum(1 for r in results if r["mentions_detector"]),
            sum(1 for r in results if r["names_detector_tool"])),
        "Programs with a closed/paused cue in a status sentence: %d." % sum(1 for r in results if r["closed_cue"]),
        "Listed pages that redirect to a home page: %d; elsewhere: %d." % (
            sum(1 for r in results if r["main_redirect"] == "home"),
            sum(1 for r in results if r["main_redirect"] == "elsewhere")),
        "", "| id | program | listed as | main page HTTP | redirect | auto label | scope | pages read | "
        "AI sentences | detector | closed cue |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        read = sum(1 for p in r["pages"] if p["chars"] is not None)
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %d/%d | %d | %s | %s |" % (
            r["id"], r["name"].replace("|", "/"), r["section"], r["main_status"], r["main_redirect"],
            r["auto_label"], r["auto_scope"] or "", read, len(r["pages"]), len(r["ai_sentences"]),
            "tool" if r["names_detector_tool"] else "yes" if r["mentions_detector"] else "",
            "yes" if r["closed_cue"] else ""))
    lines += ["", "Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0, code Apache-2.0.",
              ""]
    return "\n".join(lines)


def main(argv=None, fetcher=fetch, opener=None, sleep=time.sleep):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--listing-url", default=LISTING_URL)
    ap.add_argument("--save-text", action="store_true")
    ap.add_argument("--pause", type=float, default=1.0)
    ap.add_argument("--prereg-path", default="census/2026-11/PREREGISTRATION.md")
    ap.add_argument("--no-prereg-check", action="store_true")
    ap.add_argument("--wait-prereg-minutes", type=float, default=0)
    a = ap.parse_args(argv)
    if a.no_prereg_check:
        prereg = {"committed_at": None, "error": "not checked"}
    else:
        prereg = wait_for_prereg(a.prereg_path, a.wait_prereg_minutes, opener, sleep)
        if a.wait_prereg_minutes > 0 and prereg.get("committed_at") is None:
            print("pre-registration %s not on main after %s minutes (%s); nothing fetched"
                  % (a.prereg_path, a.wait_prereg_minutes, prereg.get("error")))
            return 3
    got = fetcher(a.listing_url)
    if got["text"] is None:
        print("listing could not be read: %s %s" % (got["status"], got["error"]))
        return 2
    programs = parse_listing(got["text"])
    if not programs:
        print("no programs parsed from the listing")
        return 2
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    results, texts = census(programs, fetcher, a.pause)
    finished = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "census.json"), "w", encoding="utf-8") as fh:
        json.dump({"version": VERSION, "listing_url": a.listing_url, "started": started, "finished": finished,
                   "prereg": prereg, "programs": results}, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out_dir, "frame.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "name", "url", "section", "pay_listed", "description"])
        for p in programs:
            w.writerow([p["id"], p["name"], p["url"], p["section"], p["pay"], p["description"]])
    with open(os.path.join(a.out_dir, "sentences.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["program_id", "page", "sentence"])
        for r in results:
            for s in r["ai_sentences"]:
                w.writerow([r["id"], s["page"], s["sentence"]])
    with open(os.path.join(a.out_dir, "status.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["program_id", "page", "sentence"])
        for r in results:
            for s in r["status_sentences"]:
                w.writerow([r["id"], s["page"], s["sentence"]])
    text = report(results, started, finished, prereg, a.listing_url)
    with open(os.path.join(a.out_dir, "CENSUS_AUTO.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    if a.save_text:
        os.makedirs(os.path.join(a.out_dir, "pages"), exist_ok=True)
        for key, t in texts.items():
            with open(os.path.join(a.out_dir, "pages", key + ".txt"), "w", encoding="utf-8") as fh:
                fh.write(t)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
