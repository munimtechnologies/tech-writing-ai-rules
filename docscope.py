# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Do open-source AI contribution policies say whether they cover documentation?

Usage: python docscope.py --out-dir OUT [--save-text] [--pause 0.5] [--wait-prereg-minutes 120]
                          [--frame-url URL] [--prereg-path census/2026-11-oss-docs/PREREGISTRATION.md]

The frame is every entry of policies.json at one pinned commit of the open dataset
awesome-ai-contribution-policies (data CC BY 4.0): 101 open-source projects, each with a GitHub repo and a
source link. The frame is read at run time from that commit, so it cannot drift and no URL is retyped.

For every project it reads, from the repo's default branch (raw.githubusercontent.com/<repo>/HEAD/...), the
standard places a contribution policy lives (REPO_FILES: CONTRIBUTING, AI_POLICY, AGENTS.md, the pull request
template), plus the dataset's own source link when that is not just the repo's home page, plus up to
MAX_FOLLOW links from those texts that point to an AI policy (no further hops). From every text it keeps,
word for word, each sentence that mentions AI, and flags whether it names documentation, names code, speaks
of contributions in general, and has a rule word (must, may, allow, disclose, ban ...).

A deterministic first-pass label per project comes from those flags (classify()). The study's primary
coding is done afterwards by reading the saved sentences against the rubric in the pre-registration, and
both are published.

Writes census.json, frame.csv, sentences.csv and DOCSCOPE_AUTO.md to --out-dir (and pages/*.txt with
--save-text). Standard library only. Made by MV2 of Munim, Inc., with AI agents working in his name.
Apache-2.0.
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

VERSION = "0.1.0"
USER_AGENT = ("tech-writing-ai-rules-docscope/%s (+https://github.com/munimtechnologies/"
              "tech-writing-ai-rules)" % VERSION)
REPO_API = "https://api.github.com/repos/munimtechnologies/tech-writing-ai-rules/commits"
PREREG_PATH = "census/2026-11-oss-docs/PREREGISTRATION.md"
FRAME_SHA = "6cd258e96c3772a624f07fcf7f7a0b3867eaeabd"
FRAME_URL = ("https://raw.githubusercontent.com/ahmad-punch/awesome-ai-contribution-policies/%s/policies.json"
             % FRAME_SHA)
RAW = "https://raw.githubusercontent.com/%s/HEAD/%s"
REPO_FILES = ("CONTRIBUTING.md", ".github/CONTRIBUTING.md", "docs/CONTRIBUTING.md", "CONTRIBUTING.rst",
              "AI_POLICY.md", ".github/AI_POLICY.md", "AGENTS.md",
              ".github/pull_request_template.md", ".github/PULL_REQUEST_TEMPLATE.md")
MAX_FOLLOW = 4
PRESS_HOSTS = ("theregister.com", "infoq.com")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

# "AI" is matched case-sensitively so that words such as "aim", "said" or "Maine" never count.
AI_TOKEN = re.compile(r"(?<![A-Za-z0-9])A\.?Is?(?![A-Za-z0-9])")
AI_WORDS = re.compile(
    r"artificial[\s-]+intelligence|chat\s?gpt|\bLLMs?\b|large[\s-]+language[\s-]+models?|\bgenerative\b|"
    r"machine[\s-]+generated|\bcopilot\b|\bclaude\b|\bgemini\b|\bcodex\b|coding[\s-]+(?:assistants?|agents?)|"
    r"\bagentic\b|vibe[\s-]?cod\w*", re.I)

DOCS_CUE = re.compile(
    r"\bdoc(?:s|umentation|umenting|string|strings)?\b|\bREADMEs?\b|\btutorials?\b|"
    r"\btranslat(?:e|es|ed|ing|ion|ions|or|ors)\b|\blocali[sz]ations?\b|\btypos?\b|\bchangelogs?\b|"
    r"\bwebsite\b|\bmanuals?\b|\bman[\s-]?pages?\b", re.I)
CODE_CUE = re.compile(r"\bcode\b(?!\s+of\s+conduct)|\bcodebase\b|\bpatch(?:es|sets?)?\b|\bimplementations?\b",
                      re.I)
GENERIC_CUE = re.compile(r"\bcontribut\w*|\bpull[\s-]+requests?\b|\bmerge[\s-]+requests?\b|\bchanges?\b|"
                         r"\bsubmi(?:t|ts|tted|tting|ssion|ssions)\b|\bcommits?\b|\bcontent\b", re.I)
GENERIC_CS = re.compile(r"\b(?:PRs?|MRs?)\b")  # case-sensitive, so "Mr." never counts
RULE_CUE = re.compile(
    r"\b(must|should|shall|may|not|never|allow\w*|permit\w*|accept\w*|welcome\w*|disclos\w*|declar\w*|"
    r"ban|bans|banned|prohibit\w*|forbid\w*|reject\w*|declin\w*|requir\w*|responsib\w*|polic(?:y|ies))\b|"
    r"\b(?:can't|won't|don't|cannot)\b", re.I)

# Links worth one hop: they point to an AI policy by their URL or their link text.
FOLLOW_AI = re.compile(
    r"(?<![A-Za-z])ai[-_ ]?(?:polic|tool|contribut|usage|use\b|coding|assist|guidance)|AIToolPolicy|"
    r"coding[-_ ]assistants|llm[-_ ]?polic|use[-_ ]of[-_ ](?:ai|llms?|generative)|"
    r"generative[-_ ]ai[-_ ]?(?:polic|contribut|guid)", re.I)
BINARY = re.compile(r"\.(pdf|docx?|jpe?g|png|gif|svg|zip|mp3|mp4)$", re.I)
TEXT_PATH = re.compile(r"\.(md|markdown|rst|txt)$", re.I)

GH_HOME = re.compile(r"^https?://github\.com/[^/]+/[^/#?]+/?$")
GH_BLOB = re.compile(r"^https?://github\.com/([^/]+)/([^/]+)/blob/([^#?]+)")

SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}
BLOCK_TAGS = {"p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "td", "th",
              "section", "article", "header", "footer", "nav", "table", "blockquote", "dd", "dt", "form",
              "main", "aside", "figcaption", "hr", "label", "option", "summary", "details", "pre"}
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[\"'“‘(\[*_`]?[A-Z0-9])")
SPACE = re.compile(r"\s+")
MD_LINK = re.compile(r"!?\[([^\]]*)\]\(<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\)")
BARE_URL = re.compile(r"https?://[^\s)>\]\"'`]+")
BREAK_LINE = re.compile(r"^\s*(?:[-*+]\s|\d+[.)]\s|#{1,6}\s|\||>|```|\.\.\s|[=\-~^`]{3,}\s*$)")

APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'"})


def norm(s):
    """Curly apostrophes to straight ones, for cue matching only; sentences are always kept as found."""
    return s.translate(APOSTROPHES)


def host(url):
    h = urllib.parse.urlsplit(url).hostname or ""
    return h[4:] if h.startswith("www.") else h


def to_raw(url):
    """A github.com .../blob/<ref>/<path> link as its raw.githubusercontent.com address; others unchanged."""
    m = GH_BLOB.match(url)
    return "https://raw.githubusercontent.com/%s/%s/%s" % m.groups() if m else url


def source_kind(url):
    """(kind, url to fetch or None). Kinds: none, repo_home (covered by REPO_FILES), repo_file, github_page
    (a commit or other github.com page: not read), press (read, but not the project's own text), web."""
    if not url:
        return "none", None
    url = urllib.parse.urldefrag(url)[0]
    if GH_HOME.match(url):
        return "repo_home", None
    if GH_BLOB.match(url) or host(url) == "raw.githubusercontent.com":
        return "repo_file", to_raw(url)
    if host(url) == "github.com":
        return "github_page", None
    h = host(url)
    if any(h == p or h.endswith("." + p) for p in PRESS_HOSTS):
        return "press", url
    return "web", url


def parse_frame(data):
    """policies.json entries in file order as rows: id (D001...), project, repo, stance, source_url,
    source_kind, fetch_url."""
    rows = []
    for e in data:
        kind, fetch_url = source_kind(e.get("source_url") or "")
        rows.append({"id": "D%03d" % (len(rows) + 1), "project": e.get("project", ""),
                     "repo": e.get("repo", "") or "", "stance": e.get("stance", ""),
                     "source_url": e.get("source_url", "") or "", "source_kind": kind, "fetch_url": fetch_url})
    return rows


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


def md_links(raw):
    out = [(m.group(2), m.group(1)) for m in MD_LINK.finditer(raw)]
    linked = {u for u, _ in out}
    out += [(u.rstrip(".,;:"), "") for u in BARE_URL.findall(raw) if u.rstrip(".,;:") not in linked]
    return out


def md_text(raw):
    """Markdown/reST/plain text as one line per paragraph, list item, heading or table row.

    Hard-wrapped lines are joined, so a sentence that spans lines is kept whole. Link syntax keeps only the
    link text; HTML comment markers are dropped but their text is kept (pull request templates put their
    instructions in comments)."""
    s = raw.replace("\r\n", "\n").replace("<!--", " ").replace("-->", " ")
    s = MD_LINK.sub(lambda m: m.group(1), s)
    out = []
    for line in s.split("\n"):
        t = SPACE.sub(" ", line).strip()
        if not t:
            out.append("")
        elif not out or out[-1] == "" or BREAK_LINE.match(line):
            out.append(t)
        else:
            out[-1] = out[-1] + " " + t
    return "\n".join(x for x in out if x)


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
    return {"docs": bool(DOCS_CUE.search(n)), "code": bool(CODE_CUE.search(n)),
            "generic": bool(GENERIC_CUE.search(n) or GENERIC_CS.search(n)), "rule": bool(RULE_CUE.search(n))}


def ai_sentences(text, limit=800):
    found, seen = [], set()
    for s in sentences(text):
        if mentions_ai(s):
            s = s if len(s) <= limit else s[:limit] + " [...]"
            if s not in seen:
                seen.add(s)
                found.append(s)
    return found


def ai_links(base, links, seen, limit=MAX_FOLLOW):
    """Links (absolute, github blob links as raw) whose URL or text points to an AI policy, in order."""
    out = []
    for href, text in links:
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        url = to_raw(urllib.parse.urldefrag(urllib.parse.urljoin(base, href))[0])
        if not url.startswith(("http://", "https://")) or url in seen:
            continue
        if BINARY.search(urllib.parse.urlsplit(url).path):
            continue
        if not (FOLLOW_AI.search(url) or FOLLOW_AI.search(text or "")):
            continue
        seen.add(url)
        out.append(url)
        if len(out) >= limit:
            break
    return out


def classify(pages, sents):
    """Deterministic first-pass label from the project's own texts (press pages never count).

    unreachable          no own text could be read     no_ai_text   no AI sentence in the own texts
    ai_text_no_rule_cue  AI sentences, none with a rule word
    docs_named           a rule-word AI sentence names documentation
    generic              rule-word AI sentences speak of contributions/PRs/changes, none names documentation
    code_only            rule-word AI sentences name code or patches only
    other                rule-word AI sentences with none of those cues"""
    read = [p for p in pages if p.get("chars") is not None and p.get("kind") != "press"]
    if not read:
        return "unreachable"
    own = [s for s in sents if s.get("kind") != "press"]
    if not own:
        return "no_ai_text"
    rules = [s for s in own if s["rule"]]
    if not rules:
        return "ai_text_no_rule_cue"
    if any(s["docs"] for s in rules):
        return "docs_named"
    if any(s["generic"] for s in rules):
        return "generic"
    if any(s["code"] for s in rules):
        return "code_only"
    return "other"


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
                                               "Accept": "text/html,text/plain,text/markdown,*/*;q=0.8",
                                               "Accept-Language": "en"})
    error = None
    for tls, ctx in (("verified", ssl.create_default_context()), ("unverified", ssl._create_unverified_context())):
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
                                             urllib.request.HTTPSHandler(context=ctx))
        try:
            with opener.open(req, timeout=timeout) as resp:
                ctype = resp.headers.get("Content-Type", "")
                body = resp.read(5_000_000)
                if ctype and not any(k in ctype for k in ("html", "text", "json", "markdown")):
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


def is_plain(url, ctype):
    """Markdown, reST or plain text rather than HTML."""
    if "html" in (ctype or "").lower():
        return False
    return bool(TEXT_PATH.search(urllib.parse.urlsplit(url).path)) or "text/plain" in (ctype or "").lower() \
        or host(url) == "raw.githubusercontent.com"


def targets(row):
    out = []
    if REPO_RE.match(row["repo"]):
        out += [("repo_file", RAW % (row["repo"], p)) for p in REPO_FILES]
    if row["fetch_url"] and row["fetch_url"] not in [u for _, u in out]:
        out.append((row["source_kind"], row["fetch_url"]))
    return out


RETRY_429 = (60, 120, 240)  # seconds to wait before each retry of a rate-limited (HTTP 429) fetch


def census(rows, fetcher=fetch, pause=0.5, sleep=time.sleep):
    results, texts = [], {}
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
            got["retried_429"] = True
        return got

    for row in rows:
        pages, sents, links_found = [], [], []
        todo = targets(row)
        seen = {u for _, u in todo}
        i = 0
        while i < len(todo):
            kind, url = todo[i]
            i += 1
            got = get(url)
            entry = {"url": url, "kind": kind, "final_url": got["final_url"], "status": got["status"],
                     "tls": got["tls"], "error": got["error"], "chars": None,
                     "retried_429": bool(got.get("retried_429"))}
            if got["text"] is not None:
                if is_plain(got["final_url"] or url, got.get("ctype")):
                    text, links = md_text(got["text"]), md_links(got["text"])
                else:
                    text, links = html_text(got["text"])
                entry["chars"] = len(text)
                texts["%s-%02d" % (row["id"], len(pages))] = text
                for s in ai_sentences(text):
                    d = {"page": url, "kind": kind, "sentence": s}
                    d.update(sentence_flags(s))
                    sents.append(d)
                if kind in ("repo_file", "web"):
                    budget = MAX_FOLLOW - sum(1 for k, _ in todo if k == "followed")
                    if budget > 0:
                        for u in ai_links(got["final_url"] or url, links, seen, budget):
                            todo.append(("followed", u))
                            links_found.append({"from": url, "url": u})
            pages.append(entry)
        unique, seen_s = [], set()
        for s in sents:
            if s["sentence"] not in seen_s:
                seen_s.add(s["sentence"])
                unique.append(s)
        own_read = [p for p in pages if p["chars"] is not None and p["kind"] != "press"]
        results.append({"id": row["id"], "project": row["project"], "repo": row["repo"], "stance": row["stance"],
                        "source_url": row["source_url"], "source_kind": row["source_kind"], "pages": pages,
                        "own_texts_read": len(own_read), "followed": links_found, "ai_sentences": unique,
                        "auto_label": classify(pages, unique)})
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


LABELS = ["docs_named", "generic", "code_only", "other", "ai_text_no_rule_cue", "no_ai_text", "unreachable"]


def report(results, started, finished, prereg, frame_url):
    counts = {k: sum(1 for r in results if r["auto_label"] == k) for k in LABELS}
    lines = ["# Do AI contribution policies cover documentation? Automatic first pass", "",
             "docscope.py %s. Frame: %d projects from %s. Texts fetched %s to %s UTC. "
             "Pre-registration first committed: %s." % (
                 VERSION, len(results), frame_url, started, finished,
                 prereg.get("committed_at") or "not found (%s)" % prereg.get("error")),
             "", "This is the deterministic first pass, not the study's primary coding (see the "
             "pre-registration). Every AI sentence is in sentences.csv with its flags, word for word.", "",
             "| Auto label | Projects |", "|---|---|"]
    lines += ["| %s | %d |" % (k, counts[k]) for k in LABELS]
    lines += ["", "| id | project | dataset stance | own texts read | followed | AI sentences | rule-word | "
              "docs | auto label |", "|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        s = r["ai_sentences"]
        lines.append("| %s | %s | %s | %d | %d | %d | %d | %d | %s |" % (
            r["id"], r["project"].replace("|", "/"), r["stance"], r["own_texts_read"], len(r["followed"]),
            len(s), sum(1 for x in s if x["rule"]), sum(1 for x in s if x["rule"] and x["docs"]),
            r["auto_label"]))
    lines += ["", "Frame: awesome-ai-contribution-policies (data CC BY 4.0), commit %s." % FRAME_SHA,
              "Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0, code Apache-2.0.", ""]
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
        print("frame is not a policies.json array: %s" % exc)
        return 2
    if not rows:
        print("no projects in the frame")
        return 2
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    results, texts = census(rows, fetcher, a.pause, sleep)
    finished = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "census.json"), "w", encoding="utf-8") as fh:
        json.dump({"version": VERSION, "frame_url": a.frame_url, "started": started, "finished": finished,
                   "prereg": prereg, "projects": results}, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out_dir, "frame.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "project", "repo", "stance", "source_url", "source_kind"])
        for r in rows:
            w.writerow([r["id"], r["project"], r["repo"], r["stance"], r["source_url"], r["source_kind"]])
    with open(os.path.join(a.out_dir, "sentences.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["project_id", "project", "page", "kind", "rule", "docs", "code", "generic", "sentence"])
        for r in results:
            for s in r["ai_sentences"]:
                w.writerow([r["id"], r["project"], s["page"], s["kind"], int(s["rule"]), int(s["docs"]),
                            int(s["code"]), int(s["generic"]), s["sentence"]])
    text = report(results, started, finished, prereg, a.frame_url)
    with open(os.path.join(a.out_dir, "DOCSCOPE_AUTO.md"), "w", encoding="utf-8") as fh:
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
