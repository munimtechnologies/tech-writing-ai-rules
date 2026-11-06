# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""What do public documentation style guides say about AI? Read each guide in a frame, keep every AI sentence.

Usage: python guidescan.py --out-dir OUT [--save-text] [--pause 0.5] [--wait-prereg-minutes 240]
                           [--frame-url URL] [--prereg-path census/2026-11-style-guides/PREREGISTRATION.md]

The frame (frame.json) lists each style guide with its seed URLs and its scope: the URL prefixes that belong to
the guide. Starting from the seeds, the tool reads every HTML page whose address falls inside the scope, breadth
first, up to the guide's max_pages, following only links that stay inside the scope. A JSON table of contents
(such as Microsoft Learn's toc.json) is read for its "href" links only. robots.txt is honoured for every host
whose robots.txt can be read (status 200); query strings and fragments are dropped, so a page is read once.

From every page it keeps, word for word, each sentence that mentions AI (AI_TOKEN, AI_WORDS) and flags it:
by_ai (words about writing, drafting, generating, reviewing or tools), for_ai (words about chatbots, virtual
agents, conversational interfaces, llms.txt, AI search or retrieval), rule (must, should, never, allow ...), and
whether the page looks like a word list or glossary (term_page). These flags only help the reader; the study's
primary coding is done afterwards by reading the saved sentences against the rubric in the pre-registration.

Writes census.json, frame.csv, pages.csv, sentences.csv and GUIDESCAN_AUTO.md to --out-dir (and pages/*.txt with
--save-text). Standard library only. Made by MV2 of Munim, Inc., with AI agents working in his name. Apache-2.0.
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
import urllib.robotparser
from html.parser import HTMLParser

VERSION = "0.1.0"
USER_AGENT = ("tech-writing-ai-rules-guidescan/%s (+https://github.com/munimtechnologies/"
              "tech-writing-ai-rules)" % VERSION)
ROBOTS_AGENT = "tech-writing-ai-rules-guidescan"
REPO_API = "https://api.github.com/repos/munimtechnologies/tech-writing-ai-rules/commits"
PREREG_PATH = "census/2026-11-style-guides/PREREGISTRATION.md"
FRAME_URL = ("https://raw.githubusercontent.com/munimtechnologies/tech-writing-ai-rules/main/"
             "census/2026-11-style-guides/frame.json")
DEFAULT_MAX_PAGES = 600
UNREAD_CHARS = 1000  # a guide with less readable text than this in total is reported as unread

# "AI" is matched case-sensitively so that words such as "aim", "said", "email" or "Maine" never count.
AI_TOKEN = re.compile(r"(?<![A-Za-z0-9])A\.?Is?(?![A-Za-z0-9])")
# Machine translation is deliberately not an AI word here: writing for translation predates the question.
AI_WORDS = re.compile(
    r"artificial[\s-]+intelligence|chat\s?gpt|\bGPTs?\b|\bLLMs?\b|llms\.txt|large[\s-]+language[\s-]+models?|"
    r"\bgenerative\b|machine[\s-]+(?:generated|learning)|\bcopilot\b|\bclaude\b|\bgemini\b|\bchat\s?bots?\b|"
    r"virtual[\s-]+(?:agents?|assistants?)|conversational[\s-]+(?:AI|agents?|interfaces?|UI)|\bagentic\b|"
    r"\bneural\b|\bprompt[\s-]+engineer\w*", re.I)

BY_CUE = re.compile(
    r"\b(?:writ(?:e|es|ing|ten)|wrote|draft\w*|generat\w*|author\w*|edit(?:s|ed|ing|or|ors)?|review\w*|"
    r"proofread\w*|rewrit\w*|summari[sz]\w*|creat\w*|produc\w*|outputs?|tools?|assist\w*)\b", re.I)
FOR_CUE = re.compile(
    r"\bchat\s?bots?\b|virtual[\s-]+(?:agents?|assistants?)|\bconversational\b|llms\.txt|machine[\s-]+readable|"
    r"\bfor\s+(?:AI|LLMs?|agents|machines|models)\b|\bretriev\w*|\bRAG\b|"
    r"(?<![A-Za-z])AI[\s-]+(?:agents?|assistants?|search|answers?|overviews?)\b|\bingest\w*|\bconsum\w*|"
    r"\bcrawl\w*", re.I)
RULE_CUE = re.compile(
    r"\b(must|should|shall|may|not|never|avoid\w*|allow\w*|permit\w*|accept\w*|welcome\w*|disclos\w*|declar\w*|"
    r"ban|bans|banned|prohibit\w*|forbid\w*|reject\w*|requir\w*|responsib\w*|polic(?:y|ies)|verify|check)\b|"
    r"\b(?:can't|won't|don't|cannot)\b", re.I)
TERM_PAGE = re.compile(r"word[-_ ]?list|glossary|terminolog|term[-_]collections|usage[-_]dictionary|a-z|"
                       r"/[a-z](?:-[a-z0-9]+)?/(?:web/?)?$", re.I)

JSON_HREF = re.compile(r'"href"\s*:\s*"([^"]+)"')
BINARY = re.compile(r"\.(pdf|docx?|jpe?g|png|gif|svg|webp|zip|mp3|mp4|css|js|xml|ico|woff2?)$", re.I)

SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}
BLOCK_TAGS = {"p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "td", "th",
              "section", "article", "header", "footer", "nav", "table", "blockquote", "dd", "dt", "form",
              "main", "aside", "figcaption", "hr", "label", "option", "summary", "details", "pre"}
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[\"'“‘(\[*_`]?[A-Z0-9])")
SPACE = re.compile(r"\s+")
APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'"})


def norm(s):
    """Curly apostrophes to straight ones, for cue matching only; sentences are always kept as found."""
    return s.translate(APOSTROPHES)


def canon(url):
    """http(s) URL without query or fragment, host in lower case; None for anything else."""
    url = urllib.parse.urldefrag(url or "")[0]
    p = urllib.parse.urlsplit(url)
    if p.scheme not in ("http", "https") or not p.netloc:
        return None
    return urllib.parse.urlunsplit((p.scheme, p.netloc.lower(), p.path or "/", "", ""))


def in_scope(url, scopes):
    """True when url starts with one of the scope prefixes, or equals one apart from a trailing slash."""
    for s in scopes:
        if s and (url.startswith(s) or url.rstrip("/") == s.rstrip("/")):
            return True
    return False


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


def html_text(page):
    p = Extract()
    try:
        p.feed(page)
        p.close()
    except Exception:  # malformed HTML: keep what was parsed
        pass
    lines = [SPACE.sub(" ", line).strip() for line in "".join(p.parts).split("\n")]
    return "\n".join(line for line in lines if line), p.links


def json_links(text):
    """Every "href" value in a JSON table of contents, in order."""
    return JSON_HREF.findall(text or "")


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


def sentence_flags(sentence):
    n = norm(sentence)
    return {"by_ai": bool(BY_CUE.search(n)), "for_ai": bool(FOR_CUE.search(n)), "rule": bool(RULE_CUE.search(n))}


def ai_sentences(text, limit=800):
    found, seen = [], set()
    for s in sentences(text):
        if mentions_ai(s):
            s = s if len(s) <= limit else s[:limit] + " [...]"
            if s not in seen:
                seen.add(s)
                found.append(s)
    return found


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
    """{'status', 'tls', 'final_url', 'ctype', 'text' (decoded body or None), 'error'}.

    Redirects are followed with a fresh cookie jar per call. One unverified retry on a certificate error,
    marked as such."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "text/html,application/json,text/plain,*/*;q=0.8",
                                               "Accept-Language": "en"})
    error = None
    for tls, ctx in (("verified", ssl.create_default_context()), ("unverified", ssl._create_unverified_context())):
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
                                             urllib.request.HTTPSHandler(context=ctx))
        try:
            with opener.open(req, timeout=timeout) as resp:
                ctype = resp.headers.get("Content-Type", "")
                body = resp.read(8_000_000)
                if ctype and not any(k in ctype for k in ("html", "text", "json")):
                    return {"status": resp.status, "tls": tls, "final_url": resp.geturl(), "ctype": ctype,
                            "text": None, "error": "not text: %s" % ctype}
                return {"status": resp.status, "tls": tls, "final_url": resp.geturl(), "ctype": ctype,
                        "text": decode(body, resp.headers.get_content_charset()), "error": None}
        except urllib.error.HTTPError as e:
            return {"status": e.code, "tls": tls, "final_url": url, "ctype": "", "text": None, "error": str(e)}
        except (urllib.error.URLError, ssl.SSLError, OSError) as e:
            error = str(getattr(e, "reason", e))
            if "CERTIFICATE" not in error.upper():
                break
    return {"status": None, "tls": None, "final_url": url, "ctype": "", "text": None, "error": error}


class Robots:
    """robots.txt per host, read once. A host whose robots.txt is not readable with status 200 is not limited."""

    def __init__(self):
        self.cache = {}

    def allowed(self, url, get):
        p = urllib.parse.urlsplit(url)
        key = "%s://%s" % (p.scheme, p.netloc)
        if key not in self.cache:
            got = get(key + "/robots.txt")
            parser = None
            if got["status"] == 200 and got["text"] is not None:
                parser = urllib.robotparser.RobotFileParser()
                parser.parse(got["text"].splitlines())
                parser.modified()  # can_fetch() refuses everything until the parser is marked as read
            self.cache[key] = {"status": got["status"], "parser": parser}
        parser = self.cache[key]["parser"]
        return True if parser is None else parser.can_fetch(ROBOTS_AGENT, url)


def guide_label(chars, n_sentences):
    if chars < UNREAD_CHARS:
        return "unread"
    return "ai_text" if n_sentences else "no_ai_text"


def crawl(guide, get, robots):
    """Read one guide. Returns (result dict, {text_key: text})."""
    scopes = [c for c in (canon(s) for s in guide["scopes"]) if c]
    queue, seen = [], set()
    for s in guide["seeds"]:
        c = canon(s)
        if c and c not in seen:
            seen.add(c)
            queue.append(c)
    pages, texts, sents, done = [], {}, [], set()
    fetched, i = 0, 0
    while i < len(queue) and fetched < guide["max_pages"]:
        url = queue[i]
        i += 1
        entry = {"url": url, "final_url": None, "status": None, "error": None, "kind": None, "chars": None,
                 "text_key": None, "term_page": bool(TERM_PAGE.search(urllib.parse.urlsplit(url).path))}
        if not robots.allowed(url, get):
            entry.update(kind="robots", error="robots.txt disallows")
            pages.append(entry)
            continue
        got = get(url)
        fetched += 1
        final = canon(got.get("final_url") or url) or url
        entry.update(final_url=final, status=got["status"], error=got["error"],
                     term_page=bool(TERM_PAGE.search(urllib.parse.urlsplit(final).path)))
        if got["text"] is None:
            entry["kind"] = "no_text"
        elif final != url and not in_scope(final, scopes):
            entry["kind"] = "redirect_out"
        elif final in done:
            entry["kind"] = "duplicate"
        else:
            done.add(final)
            seen.add(final)
            ctype = (got.get("ctype") or "").lower()
            if "json" in ctype or urllib.parse.urlsplit(final).path.endswith(".json"):
                entry["kind"] = "toc"
                links = json_links(got["text"])
            else:
                text, pairs = html_text(got["text"])
                links = [h for h, _ in pairs]
                key = "%s-%04d" % (guide["id"], len(pages))
                entry.update(kind="page", chars=len(text), text_key=key)
                texts[key] = text
                for s in ai_sentences(text):
                    d = {"page": final, "term_page": entry["term_page"], "sentence": s}
                    d.update(sentence_flags(s))
                    sents.append(d)
            for href in links:
                if not href or href.startswith(("mailto:", "tel:", "javascript:")):
                    continue
                u = canon(urllib.parse.urljoin(final, href))
                if not u or u in seen or BINARY.search(urllib.parse.urlsplit(u).path):
                    continue
                if in_scope(u, scopes):
                    seen.add(u)
                    queue.append(u)
        pages.append(entry)
    unique, seen_s = [], set()
    for s in sents:
        if s["sentence"] not in seen_s:
            seen_s.add(s["sentence"])
            unique.append(s)
    chars = sum(p["chars"] for p in pages if p["kind"] == "page")
    result = {"id": guide["id"], "guide": guide["guide"], "publisher": guide["publisher"], "group": guide["group"],
              "lists": guide["lists"], "seeds": guide["seeds"], "scopes": guide["scopes"],
              "max_pages": guide["max_pages"], "fetched": fetched,
              "pages_read": sum(1 for p in pages if p["kind"] == "page"), "chars": chars,
              "cap_hit": i < len(queue), "pages": pages, "ai_sentences": unique,
              "auto_label": guide_label(chars, len(unique))}
    return result, texts


RETRY_429 = (60, 120, 240)  # seconds to wait before each retry of a rate-limited (HTTP 429) fetch


def census(guides, fetcher=fetch, pause=0.5, sleep=time.sleep):
    calls = [0]

    def get(url):
        if calls[0] and pause:
            sleep(pause)
        calls[0] += 1
        got = fetcher(url)
        for wait in RETRY_429:
            if got["status"] != 429:
                break
            sleep(wait)
            got = fetcher(url)
        return got

    robots = Robots()
    results, texts = [], {}
    for g in guides:
        r, t = crawl(g, get, robots)
        results.append(r)
        texts.update(t)
    return results, texts


def parse_frame(data):
    """frame.json ({"guides": [...]} or a bare list) as rows with id, guide, publisher, group, lists, seeds,
    scopes, max_pages."""
    guides = data.get("guides") if isinstance(data, dict) else data
    if not isinstance(guides, list):
        raise ValueError("no guides list")
    rows = []
    for e in guides:
        if not e.get("id") or not e.get("seeds") or not e.get("scopes"):
            raise ValueError("a guide entry lacks id, seeds or scopes")
        rows.append({"id": e["id"], "guide": e.get("guide", ""), "publisher": e.get("publisher", ""),
                     "group": e.get("group", ""), "lists": e.get("lists", ""), "seeds": list(e["seeds"]),
                     "scopes": list(e["scopes"]), "max_pages": int(e.get("max_pages") or DEFAULT_MAX_PAGES)})
    return rows


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


LABELS = ["ai_text", "no_ai_text", "unread"]


def report(results, started, finished, prereg, frame_url):
    counts = {k: sum(1 for r in results if r["auto_label"] == k) for k in LABELS}
    lines = ["# What do documentation style guides say about AI? Automatic first pass", "",
             "guidescan.py %s. Frame: %d guides from %s. Pages fetched %s to %s UTC. "
             "Pre-registration first committed: %s." % (
                 VERSION, len(results), frame_url, started, finished,
                 prereg.get("committed_at") or "not found (%s)" % prereg.get("error")),
             "", "This is the deterministic first pass, not the study's primary coding (see the "
             "pre-registration). Every AI sentence is in sentences.csv with its flags, word for word.", "",
             "| Auto label | Guides |", "|---|---|"]
    lines += ["| %s | %d |" % (k, counts[k]) for k in LABELS]
    lines += ["", "| id | guide | group | fetched | pages read | chars | cap hit | AI sentences | by_ai+rule | "
              "for_ai | on term pages | auto label |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        s = r["ai_sentences"]
        lines.append("| %s | %s | %s | %d | %d | %d | %s | %d | %d | %d | %d | %s |" % (
            r["id"], r["guide"].replace("|", "/"), r["group"], r["fetched"], r["pages_read"], r["chars"],
            "yes" if r["cap_hit"] else "no", len(s), sum(1 for x in s if x["by_ai"] and x["rule"]),
            sum(1 for x in s if x["for_ai"]), sum(1 for x in s if x["term_page"]), r["auto_label"]))
    lines += ["", "Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0, code Apache-2.0.",
              ""]
    return "\n".join(lines)


def main(argv=None, fetcher=fetch, opener=None, sleep=time.sleep):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--frame-url", default=FRAME_URL)
    ap.add_argument("--save-text", action="store_true")
    ap.add_argument("--pause", type=float, default=0.5)
    ap.add_argument("--prereg-path", default=PREREG_PATH)
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
    got = fetcher(a.frame_url)
    if got["text"] is None:
        print("frame could not be read: %s %s" % (got["status"], got["error"]))
        return 2
    try:
        rows = parse_frame(json.loads(got["text"]))
    except (ValueError, TypeError, AttributeError) as exc:
        print("frame is not a guides list: %s" % exc)
        return 2
    if not rows:
        print("no guides in the frame")
        return 2
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    results, texts = census(rows, fetcher, a.pause, sleep)
    finished = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "census.json"), "w", encoding="utf-8") as fh:
        json.dump({"version": VERSION, "frame_url": a.frame_url, "started": started, "finished": finished,
                   "prereg": prereg, "guides": results}, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out_dir, "frame.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "guide", "publisher", "group", "lists", "seeds", "scopes", "max_pages"])
        for r in rows:
            w.writerow([r["id"], r["guide"], r["publisher"], r["group"], r["lists"], " ".join(r["seeds"]),
                        " ".join(r["scopes"]), r["max_pages"]])
    with open(os.path.join(a.out_dir, "pages.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["guide_id", "text_key", "url", "final_url", "status", "kind", "chars", "term_page", "error"])
        for r in results:
            for p in r["pages"]:
                w.writerow([r["id"], p["text_key"] or "", p["url"], p["final_url"] or "", p["status"] or "",
                            p["kind"], "" if p["chars"] is None else p["chars"], int(p["term_page"]),
                            p["error"] or ""])
    with open(os.path.join(a.out_dir, "sentences.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["guide_id", "guide", "page", "term_page", "rule", "by_ai", "for_ai", "sentence"])
        for r in results:
            for s in r["ai_sentences"]:
                w.writerow([r["id"], r["guide"], s["page"], int(s["term_page"]), int(s["rule"]), int(s["by_ai"]),
                            int(s["for_ai"]), s["sentence"]])
    text = report(results, started, finished, prereg, a.frame_url)
    with open(os.path.join(a.out_dir, "GUIDESCAN_AUTO.md"), "w", encoding="utf-8") as fh:
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
