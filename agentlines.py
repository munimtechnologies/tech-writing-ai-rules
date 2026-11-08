# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""What do llms.txt files tell AI agents to do? Read every llms.txt listed in a public directory and pull out
the lines that may address an AI reader.

Usage: python agentlines.py --out-dir OUT [--pause 0.25] [--wait-prereg-minutes 240] [--frame-url URL]
                            [--prereg-path census/2026-11-llms-txt-agents/PREREGISTRATION.md]

The frame is data/websites.json of the open llms-txt-hub directory (github.com/thedaviddias/llms-txt-hub, MIT),
read at a pinned commit. Each entry gives a site's name, domain, category, listing date and llms.txt URL.
Entries are numbered W0001... in file order; entries whose llms.txt URL repeats an earlier one are kept in
frame.csv but probed once. For every unique URL the tool:

1. reads robots.txt of the URL's host once (the site is "reached" when that request gets any HTTP answer;
   a host that gives no answer at all is not asked again) and honours it for its own agent name;
2. asks for the llms.txt URL and labels the answer: valid (status 200, the same file name after redirects,
   not HTML, at least MIN_CHARS non-space characters and either a Markdown H1 in the first 50 lines or at
   least three Markdown links), html, challenge, redirected, missing, short, unstructured, robots or error;
3. in a valid file, lists CANDIDATE lines that may address an AI reader: a line naming an AI reader together
   with a directive word, a line that starts with an imperative, "you should/must" lines, override phrases
   ("ignore previous instructions", "system prompt", "do not tell the user"), level-2-or-deeper headings that
   name AI readers or instructions, and every line in the section under such a heading (up to SECTION_LINES
   non-empty lines, until a heading of the same or a higher level).

Then it draws the CODE sample (the first CODE_N valid files when sorted by sha256(SALT + "|" + url)) and the
RECALL sample (the first RECALL_N files of the CODE sample with no candidate line, in the same order), and
counts how many files hold each candidate line once it is normalised (lower case, site names replaced), so
lines shared by SHARED_MIN or more files (platform or generator templates) stand out.

These lines are only candidates. Whether a file gives AI readers directives, and of which kinds, is decided
by reading, as the pre-registration says. Writes frame.csv, probes.csv, candidates.csv, coding_template.csv,
recall_heads.json, census.json and AGENTLINES_AUTO.md to --out-dir.
Standard library only. Made by MV2 of Munim, Inc., with AI agents working in his name. Apache-2.0.
"""
import argparse
import collections
import csv
import hashlib
import http.client
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

VERSION = "0.1.0"
USER_AGENT = ("tech-writing-ai-rules-agentlines/%s (+https://github.com/munimtechnologies/"
              "tech-writing-ai-rules)" % VERSION)
ROBOTS_AGENT = "tech-writing-ai-rules-agentlines"
REPO_API = "https://api.github.com/repos/munimtechnologies/tech-writing-ai-rules/commits"
PREREG_PATH = "census/2026-11-llms-txt-agents/PREREGISTRATION.md"
FRAME_SHA = "e4068608664a9349ddfcf3b51b3724849b51dd76"
FRAME_URL = "https://raw.githubusercontent.com/thedaviddias/llms-txt-hub/%s/data/websites.json" % FRAME_SHA
SALT = "study6"
CODE_N = 200
RECALL_N = 20
SHARED_MIN = 3
MAX_BYTES = 2_000_000
FRAME_MAX_BYTES = 30_000_000
HEAD_CHARS = 4000
MIN_CHARS = 50
MAX_LINE = 600
MAX_CANDIDATES = 80
SECTION_LINES = 30
TIMEOUT = 15

H1 = re.compile(r"^#[ \t]+\S")
HEADING = re.compile(r"^(#{1,6})[ \t]+(.*)$")
MD_LINK = re.compile(r"\]\([^)\s]+\)")
CHALLENGE = re.compile(r"anubis|making sure you(?:'|\u2019)re not a bot|just a moment\.\.\.|cf-chl|"
                       r"challenge-platform|checking your browser|proof[- ]of[- ]work", re.I)
CHALLENGE_MAX_CHARS = 60000

ADDRESSEE = re.compile(
    r"\b(?:AI|LLMs?|large language models?|language models?|assistants?|agents?|chat ?bots?|"
    r"ChatGPT|Claude|Gemini|Copilot|Cursor|Perplexity|Grok|crawlers?|answer engines?|generative engines?)\b",
    re.I)
DIRECTIVE = re.compile(
    r"\b(?:should|must|shall|please|always|never|do not|don't|avoid|recommend\w*|cite|citing|attribut\w*|"
    r"link (?:to|back)|ignore|disregard|make sure|ensure|instead of|"
    r"when (?:a )?(?:users?|someone|people|asked|answering|responding|recommending)|"
    r"if (?:a |the )?(?:users?|someone|people) asks?|(?:are|is) (?:not )?(?:allowed|permitted|encouraged)|"
    r"may not|may only|only use|prefer (?:this|these|our|the official))\b", re.I)
IMPERATIVE = re.compile(
    r"^[\W_]*(?:always|never|do not|don't|please|ignore|avoid|make sure|ensure|"
    r"when (?:answering|responding|recommending|asked|citing|summari[sz]ing|referencing|discussing|"
    r"generating|writing (?:about|code))|if (?:a |the )?users? (?:asks?|wants?|needs?))\b", re.I)
YOU = re.compile(r"\byou (?:should|must|shall|are to|may not|must not|should not|need to|are (?:an?|the) "
                 r"(?:AI|assistant|agent|helpful|expert))\b", re.I)
OVERRIDE = re.compile(
    r"ignore (?:all |any |the |your )?(?:previous|prior|above|earlier|other|preceding) (?:instructions|prompts|"
    r"directions|rules)|disregard (?:all |any |the |your )?(?:previous|prior|above|earlier|other)|system prompt|"
    r"you are now\b|new instructions|(?:do not|don't|never) (?:tell|inform|mention (?:this |it )?to|reveal (?:this )?to)"
    r" the user|without (?:telling|informing) the user", re.I)
HEADING_CUE = re.compile(
    r"\b(?:AI|LLMs?|language models?|agents?|assistants?|chat ?bots?|crawlers?|instructions?|guidelines?|"
    r"rules|citations?|attribution|usage polic(?:y|ies)|notes? for|how to (?:cite|use this))\b", re.I)
WORD = re.compile(r"[^a-z0-9]+")

CHARSET_ALIASES = {"shift_jis": "cp932", "euc-kr": "cp949", "gb2312": "gb18030", "gbk": "gb18030"}
ACCEPT_TEXT = "text/plain,text/markdown;q=0.9,text/html;q=0.8,*/*;q=0.5"
CATEGORIES_CODE = ("directive", "cite", "promote", "source", "usage", "action", "limit", "override", "other")


def decode(body, header_charset=None):
    for cs in (header_charset, "utf-8"):
        if not cs:
            continue
        cs = CHARSET_ALIASES.get(cs.lower(), cs.lower())
        try:
            return body.decode(cs)
        except (LookupError, UnicodeDecodeError):
            pass
    return body.decode("utf-8", errors="replace")


def fetch(url, accept=ACCEPT_TEXT, timeout=TIMEOUT, max_bytes=MAX_BYTES):
    """{'status', 'tls', 'final_url', 'ctype', 'truncated', 'text', 'error'}; one unverified retry on a
    certificate error, marked as such. The body of an error answer is kept (up to 200 kB)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept, "Accept-Language": "en"})
    error = None
    for tls, ctx in (("verified", ssl.create_default_context()), ("unverified", ssl._create_unverified_context())):
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
                                             urllib.request.HTTPSHandler(context=ctx))
        try:
            with opener.open(req, timeout=timeout) as resp:
                body = resp.read(max_bytes + 1)
                return {"status": resp.status, "tls": tls, "final_url": resp.geturl(),
                        "ctype": resp.headers.get("Content-Type", ""), "truncated": len(body) > max_bytes,
                        "text": decode(body[:max_bytes], resp.headers.get_content_charset()), "error": None}
        except urllib.error.HTTPError as e:
            body = b""
            try:
                body = e.read(200_000)
            except Exception:
                pass
            headers = e.headers if e.headers is not None else {}
            return {"status": e.code, "tls": tls, "final_url": e.geturl() or url,
                    "ctype": headers.get("Content-Type", "") or "", "truncated": False,
                    "text": decode(body) if body else None, "error": str(e)}
        except (urllib.error.URLError, ssl.SSLError, OSError, ValueError, http.client.HTTPException) as e:
            error = str(getattr(e, "reason", e)) or type(e).__name__
            if "CERTIFICATE" not in error.upper():
                break
        except Exception as e:  # anything else from one site must not stop the census
            error = "%s: %s" % (type(e).__name__, e)
            break
    return {"status": None, "tls": None, "final_url": url, "ctype": "", "truncated": False, "text": None,
            "error": error}


# ---------------------------------------------------------------- robots.txt (RFC 9309 / Google-style matching)

def pattern_match(pattern, path):
    anchored = pattern.endswith("$")
    if anchored:
        pattern = pattern[:-1]
    rx = "".join(".*" if c == "*" else re.escape(c) for c in pattern)
    return re.match(rx + ("$" if anchored else ""), path, re.S) is not None


class RobotsFile:
    def __init__(self, text):
        self.groups = []
        cur, last_was_agent = None, False
        for raw in (text or "").splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key, val = key.strip().lower(), val.strip()
            if key in ("user-agent", "useragent"):
                if cur is None or not last_was_agent:
                    cur = {"agents": [], "rules": []}
                    self.groups.append(cur)
                cur["agents"].append(val.split("/")[0].strip().lower())
                last_was_agent = True
            elif key in ("allow", "disallow"):
                last_was_agent = False
                if cur is not None:
                    cur["rules"].append((key == "allow", val))

    def allowed(self, agent, path):
        a = agent.lower()
        own = [g for g in self.groups if a in g["agents"]]
        chosen = own or [g for g in self.groups if "*" in g["agents"]]
        best = None
        for allow, pat in (r for g in chosen for r in g["rules"]):
            if not pat or not pattern_match(pat, path):
                continue
            if best is None or len(pat) > best[0] or (len(pat) == best[0] and allow):
                best = (len(pat), allow)
        return True if best is None else best[1]


def url_path(url):
    p = urllib.parse.urlsplit(url)
    return (p.path or "/") + ("?" + p.query if p.query else "")


def host_key(url):
    p = urllib.parse.urlsplit(url)
    return "%s://%s" % (p.scheme.lower(), p.netloc.lower())


def is_html(text, ctype=""):
    return "html" in (ctype or "").lower() or (text or "").lstrip()[:1] == "<"


def is_challenge(text, ctype=""):
    return bool(text) and is_html(text, ctype) and len(text) < CHALLENGE_MAX_CHARS and bool(CHALLENGE.search(text))


class Robots:
    """robots.txt per host, read once. Status 200 with a non-HTML body is parsed; any other HTTP answer limits
    nothing. No HTTP answer at all marks the host as not reached."""

    def __init__(self, get):
        self.get, self.cache = get, {}

    def entry(self, url):
        key = host_key(url)
        if key not in self.cache:
            got = self.get(key + "/robots.txt")
            parsed = None
            if got["status"] == 200 and got["text"] is not None and not is_html(got["text"], got["ctype"]):
                parsed = RobotsFile(got["text"])
            self.cache[key] = {"status": got["status"], "parsed": parsed, "error": got.get("error")}
        return self.cache[key]

    def allowed(self, url):
        parsed = self.entry(url)["parsed"]
        return True if parsed is None else parsed.allowed(ROBOTS_AGENT, url_path(url))


# ---------------------------------------------------------------- frame

def norm_url(url):
    p = urllib.parse.urlsplit((url or "").strip())
    host = p.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return "%s%s%s" % (host, p.path.rstrip("/") or "/", "?" + p.query if p.query else "")


def parse_frame(data):
    if isinstance(data, dict):
        data = data.get("websites") or data.get("items") or data.get("data")
    if not isinstance(data, list):
        raise ValueError("websites.json is not a list of entries")
    rows, first = [], {}
    for i, e in enumerate(data, 1):
        if not isinstance(e, dict):
            raise ValueError("entry %d is not an object" % i)
        url = (e.get("llmsTxtUrl") or "").strip()
        key = norm_url(url) if url.lower().startswith(("http://", "https://")) else ""
        row = {"id": "W%04d" % i, "name": (e.get("name") or "").strip(), "domain": (e.get("domain") or "").strip(),
               "llms_url": url, "full_url": (e.get("llmsFullTxtUrl") or "").strip(),
               "category": (e.get("category") or "").strip(), "published": (e.get("publishedAt") or "").strip(),
               "key": key, "dup_of": ""}
        if key:
            if key in first:
                row["dup_of"] = first[key]
            else:
                first[key] = row["id"]
        rows.append(row)
    return rows


def year(published):
    m = re.match(r"(\d{4})", published or "")
    return m.group(1) if m else ""


# ---------------------------------------------------------------- labels and candidates

def classify(got, url):
    text, status = got.get("text"), got.get("status")
    if status is None:
        return "error"
    if is_challenge(text, got.get("ctype")):
        return "challenge"
    if status != 200:
        return "missing"
    want = urllib.parse.urlsplit(url).path.rsplit("/", 1)[-1].lower()
    final = urllib.parse.urlsplit(got.get("final_url") or url).path.rsplit("/", 1)[-1].lower()
    if final != want:
        return "redirected"
    if text is None:
        return "error"
    if is_html(text, got.get("ctype")):
        return "html"
    if len("".join(text.split())) < MIN_CHARS:
        return "short"
    lines = text.splitlines()
    if any(H1.match(line) for line in lines[:50]) or len(MD_LINK.findall(text)) >= 3:
        return "valid"
    return "unstructured"


def line_cues(line):
    cues = []
    if OVERRIDE.search(line):
        cues.append("override")
    if ADDRESSEE.search(line) and DIRECTIVE.search(line):
        cues.append("addressee+directive")
    if IMPERATIVE.search(line):
        cues.append("imperative")
    if YOU.search(line):
        cues.append("you")
    return cues


def candidates(text):
    """Lines of a file that may address an AI reader: [{'line', 'text', 'cues', 'section'}]."""
    out, section, level, left = [], "", 0, 0
    for n, raw in enumerate((text or "").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        h = HEADING.match(line)
        if h:
            lv = len(h.group(1))
            if section and lv <= level:
                section, level, left = "", 0, 0
            # A level-1 heading is the file's title (often the site's name), so it never opens a section.
            if lv > 1 and HEADING_CUE.search(h.group(2)) and (ADDRESSEE.search(h.group(2)) or not section):
                cues = ["heading"] + line_cues(line)
                out.append({"line": n, "text": line[:MAX_LINE], "cues": cues, "section": h.group(2)[:200]})
                section, level, left = h.group(2)[:200], lv, SECTION_LINES
                continue
        cues = line_cues(line)
        in_section = bool(section) and left > 0
        if in_section:
            left -= 1
            cues = cues + ["section"]
        if cues:
            out.append({"line": n, "text": line[:MAX_LINE], "cues": cues, "section": section if in_section else ""})
    return out


def norm_line(text, site_words):
    t = text.lower()
    for w in site_words:
        if w and len(w) >= 3:
            t = t.replace(w, " site ")
    return WORD.sub(" ", t).strip()


def site_words(row, final_url=""):
    words = set()
    for u in (row.get("domain"), row.get("llms_url"), final_url):
        host = urllib.parse.urlsplit(u or "").netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        if host:
            words.add(host)
            labels = host.split(".")
            core = labels[-2] if len(labels) >= 2 else labels[0]  # docs.stripe.com -> stripe
            if len(labels) >= 3 and len(labels[-2]) <= 3 and len(labels[-1]) <= 3:
                core = labels[-3]  # shop.example.co.uk -> example
            words.add(core)
    if row.get("name"):
        words.add(row["name"].lower())
    return sorted(words, key=len, reverse=True)


# ---------------------------------------------------------------- census

RETRY_429 = (30, 60)


def census(rows, fetcher=fetch, pause=0.25, sleep=time.sleep):
    calls = [0]

    def get(url, accept=ACCEPT_TEXT):
        if calls[0] and pause:
            sleep(pause)
        calls[0] += 1
        got = fetcher(url, accept)
        for wait in RETRY_429:
            if got["status"] != 429:
                break
            sleep(wait)
            got = fetcher(url, accept)
        return got

    robots = Robots(get)
    results = []
    for row in rows:
        if row["dup_of"] or not row["key"]:
            continue
        url = row["llms_url"]
        r = {"id": row["id"], "url": url, "status": None, "final_url": "", "ctype": "", "kind": "error",
             "chars": 0, "truncated": False, "spec_h1": False, "links": 0, "reached": False, "error": "",
             "candidates": [], "head": ""}
        rb = robots.entry(url)
        if rb["status"] is None:
            r["error"] = "host not reached (robots.txt: %s)" % (rb["error"] or "no answer")
        elif not robots.allowed(url):
            r.update(reached=True, kind="robots", error="robots.txt disallows")
        else:
            got = get(url)
            text = got.get("text") if got.get("status") == 200 else ""
            r.update(reached=True, status=got["status"], final_url=got.get("final_url") or "",
                     ctype=got.get("ctype") or "", kind=classify(got, url), truncated=bool(got.get("truncated")),
                     error=got.get("error") or "", chars=len(text or ""))
            if r["kind"] == "valid":
                lines = [l for l in text.splitlines() if l.strip()]
                r["spec_h1"] = bool(lines) and bool(H1.match(lines[0].strip()))
                r["links"] = len(MD_LINK.findall(text))
                r["candidates"] = candidates(text)
                r["head"] = text[:HEAD_CHARS]
        results.append(r)
    return results, calls[0]


def sample_order(url):
    return hashlib.sha256((SALT + "|" + norm_url(url)).encode("utf-8")).hexdigest()


def draw_samples(results, code_n=CODE_N, recall_n=RECALL_N):
    valid = sorted((r for r in results if r["kind"] == "valid"), key=lambda r: sample_order(r["url"]))
    code = valid[:code_n]
    recall = [r for r in code if not r["candidates"]][:recall_n]
    return [r["id"] for r in code], [r["id"] for r in recall]


def shared_counts(results, rows_by_id):
    """({normalised candidate line: number of distinct files holding it}, {id: site words}).
    Lines under 20 characters once normalised are not counted."""
    words = {r["id"]: site_words(rows_by_id[r["id"]], r["final_url"]) for r in results}
    seen = collections.defaultdict(set)
    for r in results:
        for c in r["candidates"]:
            key = norm_line(c["text"], words[r["id"]])
            if len(key) >= 20:
                seen[key].add(r["id"])
    return {k: len(v) for k, v in seen.items()}, words


# ---------------------------------------------------------------- pre-registration check and report

def prereg_commit(path, opener=None):
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


def wait_for_prereg(path, minutes, opener=None, sleep=time.sleep, every=300):
    prereg = prereg_commit(path, opener)
    waited = 0
    while prereg.get("committed_at") is None and waited < minutes * 60:
        sleep(every)
        waited += every
        prereg = prereg_commit(path, opener)
    prereg["waited_seconds"] = waited
    return prereg


def summarise(rows, results, code_ids, shared):
    by_id = {r["id"]: r for r in rows}
    groups = collections.OrderedDict()

    def add(name, r):
        g = groups.setdefault(name, collections.Counter())
        g["unique"] += 1
        g["reached"] += r["reached"]
        g["valid"] += r["kind"] == "valid"
        g["candidate"] += bool(r["candidates"])
        g["heading"] += any("heading" in c["cues"] for c in r["candidates"])
        g["override"] += any("override" in c["cues"] for c in r["candidates"])

    for r in results:
        add("ALL", r)
    for r in sorted(results, key=lambda x: by_id[x["id"]]["category"]):
        add("category " + (by_id[r["id"]]["category"] or "(none)"), r)
    for r in sorted(results, key=lambda x: year(by_id[x["id"]]["published"])):
        add("listed " + (year(by_id[r["id"]]["published"]) or "(no date)"), r)
    code = [r for r in results if r["id"] in set(code_ids)]
    for r in code:
        add("CODE sample", r)
    kinds = collections.Counter(r["kind"] for r in results)
    top_shared = sorted(((n, k) for k, n in shared.items() if n >= SHARED_MIN), reverse=True)[:25]
    return groups, kinds, top_shared


def report(rows, results, code_ids, recall_ids, shared, meta):
    groups, kinds, top_shared = summarise(rows, results, code_ids, shared)
    dups = sum(1 for r in rows if r["dup_of"])
    nourl = sum(1 for r in rows if not r["key"])
    lines = ["# What do llms.txt files tell AI agents to do? Automatic counts", "",
             "agentlines.py %s. Frame: %d entries of llms-txt-hub data/websites.json at commit %s "
             "(%d repeat an earlier llms.txt URL, %d have no http(s) URL), so %d unique URLs. Fetched %s to %s "
             "UTC (%d requests). Pre-registration first committed: %s." % (
                 VERSION, len(rows), meta["frame_sha"], dups, nourl, len(results), meta["started"],
                 meta["finished"], meta["requests"],
                 meta["prereg"].get("committed_at") or "not found (%s)" % meta["prereg"].get("error")),
             "", "Candidate lines are not directives: the pre-registered hand coding decides that.", "",
             "Labels: " + ", ".join("%s %d" % (k, n) for k, n in sorted(kinds.items())), "",
             "| Group | Unique URLs | Reached | Valid llms.txt | With a candidate line | With an AI heading | "
             "With an override phrase |", "|---|---|---|---|---|---|---|"]
    for name, g in groups.items():
        lines.append("| %s | %d | %d | %d | %d | %d | %d |" % (name, g["unique"], g["reached"], g["valid"],
                                                                g["candidate"], g["heading"], g["override"]))
    lines += ["", "CODE sample: %d files. RECALL sample: %d files." % (len(code_ids), len(recall_ids)), "",
              "## Candidate lines shared by %d or more files (normalised; site names replaced by 'site')" % SHARED_MIN,
              "", "| Files | Line |", "|---|---|"]
    for n, k in top_shared:
        lines.append("| %d | %s |" % (n, k[:200].replace("|", "/")))
    lines += ["", "Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0, code Apache-2.0. "
              "Frame: llms-txt-hub by David Dias (MIT).", ""]
    return "\n".join(lines)


def write_outputs(out_dir, rows, results, code_ids, recall_ids, shared, words, meta, text):
    os.makedirs(out_dir, exist_ok=True)
    by_id = {r["id"]: r for r in rows}
    code_set, recall_set = set(code_ids), set(recall_ids)
    with open(os.path.join(out_dir, "frame.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "name", "domain", "llms_url", "llms_full_url", "category", "published", "dup_of"])
        for r in rows:
            w.writerow([r["id"], r["name"], r["domain"], r["llms_url"], r["full_url"], r["category"],
                        r["published"], r["dup_of"]])
    with open(os.path.join(out_dir, "probes.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "url", "reached", "status", "final_url", "ctype", "kind", "chars", "truncated",
                    "spec_h1", "links", "candidates", "ai_heading", "override", "code_sample", "recall_sample",
                    "error"])
        for r in results:
            w.writerow([r["id"], r["url"], int(r["reached"]), r["status"] or "", r["final_url"], r["ctype"],
                        r["kind"], r["chars"], int(r["truncated"]), int(r["spec_h1"]), r["links"],
                        len(r["candidates"]), int(any("heading" in c["cues"] for c in r["candidates"])),
                        int(any("override" in c["cues"] for c in r["candidates"])), int(r["id"] in code_set),
                        int(r["id"] in recall_set), r["error"][:300]])
    with open(os.path.join(out_dir, "candidates.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "code_sample", "line", "cues", "section", "shared_files", "text"])
        for r in results:
            for c in r["candidates"][:MAX_CANDIDATES]:
                w.writerow([r["id"], int(r["id"] in code_set), c["line"], " ".join(c["cues"]), c["section"],
                            shared.get(norm_line(c["text"], words[r["id"]]), 1), c["text"]])
    with open(os.path.join(out_dir, "coding_template.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["order", "id", "url", "category", "published", "candidates", "recall_sample"]
                   + list(CATEGORIES_CODE) + ["template", "quote", "note"])
        for i, rid in enumerate(code_ids, 1):
            r = next(x for x in results if x["id"] == rid)
            w.writerow([i, rid, r["url"], by_id[rid]["category"], by_id[rid]["published"], len(r["candidates"]),
                        int(rid in recall_set)] + [""] * (len(CATEGORIES_CODE) + 3))
    with open(os.path.join(out_dir, "recall_heads.json"), "w", encoding="utf-8") as fh:
        json.dump([{"id": r["id"], "url": r["url"], "head": r["head"]} for r in results if r["id"] in recall_set],
                  fh, ensure_ascii=False, indent=1)
    slim = [{k: v for k, v in r.items() if k != "head"} for r in results]
    with open(os.path.join(out_dir, "census.json"), "w", encoding="utf-8") as fh:
        json.dump(dict(meta, code_sample=code_ids, recall_sample=recall_ids, results=slim), fh,
                  ensure_ascii=False, indent=1)
    with open(os.path.join(out_dir, "AGENTLINES_AUTO.md"), "w", encoding="utf-8") as fh:
        fh.write(text)


def main(argv=None, fetcher=None, opener=None, sleep=time.sleep):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--frame-url", default=FRAME_URL)
    ap.add_argument("--pause", type=float, default=0.25)
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
    if fetcher is None:
        fetcher = fetch
        got = fetch(a.frame_url, ACCEPT_TEXT, 90, FRAME_MAX_BYTES)
    else:
        got = fetcher(a.frame_url, ACCEPT_TEXT)
    if got["text"] is None or got["status"] != 200 or got.get("truncated"):
        print("frame could not be read in full: %s %s" % (got["status"], got["error"]))
        return 2
    raw = got["text"]
    try:
        rows = parse_frame(json.loads(raw))
    except (ValueError, TypeError) as exc:
        print("frame is not a websites list: %s" % exc)
        return 2
    if not rows:
        print("no entries in the frame")
        return 2
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    results, calls = census(rows, fetcher, a.pause, sleep)
    finished = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    code_ids, recall_ids = draw_samples(results)
    by_id = {r["id"]: r for r in rows}
    shared, words = shared_counts(results, by_id)
    meta = {"version": VERSION, "frame_url": a.frame_url, "frame_sha": FRAME_SHA if FRAME_SHA in a.frame_url else "",
            "frame_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(), "started": started,
            "finished": finished, "requests": calls, "prereg": prereg, "salt": SALT, "code_n": CODE_N,
            "recall_n": RECALL_N}
    text = report(rows, results, code_ids, recall_ids, shared, meta)
    write_outputs(a.out_dir, rows, results, code_ids, recall_ids, shared, words, meta, text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
