# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Do projects with AI contribution rules serve their documentation to AI readers? Probe each docs base.

Usage: python llmsprobe.py --out-dir OUT [--pause 0.5] [--wait-prereg-minutes 240]
                           [--frame-url URL] [--prereg-path census/2026-11-llms-txt/PREREGISTRATION.md]

The frame (frame.json) lists each project with its group (BAN, RESTRICTED or OPEN, from the stance an open
dataset gives its AI contribution policy), one or more documentation base URLs and the policy page that was
coded in study 2. For every base the tool:

1. reads the base page (it is "reached" when any HTTP status comes back) and notes a bot challenge page;
2. asks for the base page again with "Accept: text/markdown" and notes whether Markdown comes back;
3. reads robots.txt of the host the base page finally lands on and records which of the named AI crawlers in
   AI_AGENTS may not fetch the base page while an agent without a group of its own may (Google-style
   matching: the most specific group, the longest matching rule, Allow wins a tie), plus any Content-Signal line;
4. asks for llms.txt and llms-full.txt in the base's own folder and at the host root, and labels each answer:
   valid (status 200, the same file name after redirects, not HTML, at least MIN_CHARS characters and either a
   Markdown H1 in the first 50 lines or at least three Markdown links), html, challenge, redirected, missing,
   short, unstructured or error.

It also counts mentions of llms.txt / llms-full.txt on each project's policy page. robots.txt is honoured for
every fetch the tool makes, for its own agent name. These labels are the study's measurement; every valid file
and every status-200 answer that was not valid is then checked by reading, as the pre-registration says.

Writes census.json, frame.csv, bases.csv, probes.csv, projects.csv and LLMSPROBE_AUTO.md to --out-dir.
Standard library only. Made by MV2 of Munim, Inc., with AI agents working in his name. Apache-2.0.
"""
import argparse
import csv
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
USER_AGENT = ("tech-writing-ai-rules-llmsprobe/%s (+https://github.com/munimtechnologies/"
              "tech-writing-ai-rules)" % VERSION)
ROBOTS_AGENT = "tech-writing-ai-rules-llmsprobe"
GENERIC_AGENT = "no-group-of-its-own"  # a made-up agent name, so it always falls back to the "*" group
REPO_API = "https://api.github.com/repos/munimtechnologies/tech-writing-ai-rules/commits"
PREREG_PATH = "census/2026-11-llms-txt/PREREGISTRATION.md"
FRAME_URL = ("https://raw.githubusercontent.com/munimtechnologies/tech-writing-ai-rules/main/"
             "census/2026-11-llms-txt/frame.json")
FILES = ("llms.txt", "llms-full.txt")
GROUPS = ("BAN", "RESTRICTED", "OPEN")
MAX_BYTES = 2_000_000  # llms-full.txt files can be tens of MB; the first 2 MB are enough to label one
HEAD_CHARS = 2000
MIN_CHARS = 50
# Named AI crawlers and AI fetchers, fixed in the pre-registration.
AI_AGENTS = ("GPTBot", "ChatGPT-User", "OAI-SearchBot", "ClaudeBot", "Claude-User", "Claude-SearchBot",
             "anthropic-ai", "CCBot", "Google-Extended", "PerplexityBot", "Perplexity-User", "Bytespider",
             "Applebot-Extended", "meta-externalagent", "Amazonbot", "cohere-ai", "Diffbot", "Omgilibot",
             "Timpibot", "YouBot")

H1 = re.compile(r"^#[ \t]+\S")
MD_LINK = re.compile(r"\]\([^)\s]+\)")
LLMS_MENTION = re.compile(r"llms(?:-full)?\.txt", re.I)
CHALLENGE = re.compile(r"anubis|making sure you(?:'|\u2019)re not a bot|just a moment\.\.\.|cf-chl|"
                       r"challenge-platform|checking your browser|proof[- ]of[- ]work", re.I)
CHALLENGE_MAX_CHARS = 60000  # challenge pages are small; a long docs page that names Anubis is not one

CHARSET_ALIASES = {"shift_jis": "cp932", "euc-kr": "cp949", "gb2312": "gb18030", "gbk": "gb18030"}
META_CHARSET = re.compile(rb"""<meta[^>]+charset\s*=\s*["']?([A-Za-z0-9_.:-]+)""", re.I)
ACCEPT_TEXT = "text/plain,text/markdown;q=0.9,text/html;q=0.8,*/*;q=0.5"
ACCEPT_HTML = "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"
ACCEPT_MD = "text/markdown"


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


def fetch(url, accept=ACCEPT_TEXT, timeout=45):
    """{'status', 'tls', 'final_url', 'ctype', 'length', 'truncated', 'text', 'error'}.

    Redirects are followed with a fresh cookie jar per call. The body of an error answer is kept too (up to
    200 kB), so a challenge page sent with status 403 or 503 can be recognised. One unverified retry on a
    certificate error, marked as such."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept, "Accept-Language": "en"})
    error = None
    for tls, ctx in (("verified", ssl.create_default_context()), ("unverified", ssl._create_unverified_context())):
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
                                             urllib.request.HTTPSHandler(context=ctx))
        try:
            with opener.open(req, timeout=timeout) as resp:
                body = resp.read(MAX_BYTES + 1)
                return {"status": resp.status, "tls": tls, "final_url": resp.geturl(),
                        "ctype": resp.headers.get("Content-Type", ""), "length": resp.headers.get("Content-Length"),
                        "truncated": len(body) > MAX_BYTES,
                        "text": decode(body[:MAX_BYTES], resp.headers.get_content_charset()), "error": None}
        except urllib.error.HTTPError as e:
            body = b""
            try:
                body = e.read(200_000)
            except Exception:
                pass
            headers = e.headers if e.headers is not None else {}
            return {"status": e.code, "tls": tls, "final_url": e.geturl() or url,
                    "ctype": headers.get("Content-Type", "") or "", "length": headers.get("Content-Length"),
                    "truncated": False, "text": decode(body) if body else None, "error": str(e)}
        except (urllib.error.URLError, ssl.SSLError, OSError, ValueError, http.client.HTTPException) as e:
            error = str(getattr(e, "reason", e)) or type(e).__name__
            if "CERTIFICATE" not in error.upper():
                break
        except Exception as e:  # anything else from one site must not stop the census
            error = "%s: %s" % (type(e).__name__, e)
            break
    return {"status": None, "tls": None, "final_url": url, "ctype": "", "length": None, "truncated": False,
            "text": None, "error": error}


# ---------------------------------------------------------------- robots.txt (RFC 9309 / Google-style matching)

def pattern_match(pattern, path):
    anchored = pattern.endswith("$")
    if anchored:
        pattern = pattern[:-1]
    rx = "".join(".*" if c == "*" else re.escape(c) for c in pattern)
    return re.match(rx + ("$" if anchored else ""), path, re.S) is not None


class RobotsFile:
    """A parsed robots.txt. Groups are runs of User-agent lines followed by their rules."""

    def __init__(self, text):
        self.groups, self.signals = [], []
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
            elif key == "content-signal":
                self.signals.append(val)

    def rules_for(self, agent):
        a = agent.lower()
        own = [g for g in self.groups if a in g["agents"]]
        chosen = own or [g for g in self.groups if "*" in g["agents"]]
        return [r for g in chosen for r in g["rules"]]

    def allowed(self, agent, path):
        if path == "/robots.txt":
            return True
        best = None
        for allow, pat in self.rules_for(agent):
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
    return "%s://%s" % (p.scheme, p.netloc.lower())


def is_html(text, ctype=""):
    return "html" in (ctype or "").lower() or (text or "").lstrip()[:1] == "<"


def is_challenge(text, ctype=""):
    return bool(text) and is_html(text, ctype) and len(text) < CHALLENGE_MAX_CHARS and bool(CHALLENGE.search(text))


class Robots:
    """robots.txt per host, read once. status 200 with a non-HTML body is parsed; any other answer means the
    host is not limited for the tool's own fetches, and its AI-crawler answer is recorded as unknown, except
    status 404 / 410 (no robots.txt), which blocks nothing."""

    def __init__(self, get):
        self.get, self.cache = get, {}

    def entry(self, url):
        key = host_key(url)
        if key not in self.cache:
            got = self.get(key + "/robots.txt", ACCEPT_TEXT)
            parsed = None
            if got["status"] == 200 and got["text"] is not None and not is_html(got["text"], got["ctype"]):
                parsed = RobotsFile(got["text"])
            self.cache[key] = {"host": key, "status": got["status"], "parsed": parsed,
                               "challenge": is_challenge(got["text"], got["ctype"])}
        return self.cache[key]

    def allowed(self, url):
        parsed = self.entry(url)["parsed"]
        return True if parsed is None else parsed.allowed(ROBOTS_AGENT, url_path(url))

    def ai_answer(self, url):
        """(ai_blocked list or None if unknown, generic_allowed or None, content signals, robots status)."""
        e = self.entry(url)
        if e["parsed"] is None:
            if e["status"] in (404, 410):
                return [], True, [], e["status"]
            return None, None, [], e["status"]
        path = url_path(url)
        blocked = [a for a in AI_AGENTS if not e["parsed"].allowed(a, path)]
        return blocked, e["parsed"].allowed(GENERIC_AGENT, path), list(e["parsed"].signals), e["status"]


# ---------------------------------------------------------------- llms.txt probes

def base_dir(base):
    """The folder a base URL stands for: itself when it ends in '/', its parent when its last segment looks like
    a file (has a dot), else itself plus '/'."""
    p = urllib.parse.urlsplit(base)
    path = p.path or "/"
    if not path.endswith("/"):
        last = path.rsplit("/", 1)[-1]
        path = path[: len(path) - len(last)] if "." in last else path + "/"
    return path


def candidates(base):
    p = urllib.parse.urlsplit(base)
    folder = base_dir(base)
    out = []
    for name in FILES:
        for where, d in (("dir", folder), ("root", "/")):
            if where == "root" and folder == "/":
                continue
            url = urllib.parse.urlunsplit((p.scheme, p.netloc.lower(), d + name, "", ""))
            out.append({"file": name, "where": "root" if d == "/" else where, "url": url})
    return out


def classify(got, name):
    """Label one answer to a request for llms.txt or llms-full.txt (see the module docstring)."""
    text, status = got.get("text"), got.get("status")
    if status is None:
        return "error"
    if is_challenge(text, got.get("ctype")):
        return "challenge"
    if status != 200:
        return "missing"
    final = urllib.parse.urlsplit(got.get("final_url") or "").path.rsplit("/", 1)[-1]
    if final != name:
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


def file_facts(text):
    lines = [l for l in (text or "").splitlines() if l.strip()]
    first = lines[0].strip() if lines else ""
    return {"spec_h1": bool(H1.match(first)), "links": len(MD_LINK.findall(text or "")),
            "first_line": first[:200], "chars": len(text or "")}


def md_negotiated(got):
    return (got.get("status") == 200 and "markdown" in (got.get("ctype") or "").lower()
            and not (got.get("text") or "").lstrip().startswith("<"))


def probe_base(base, get, robots):
    entry = {"base": base}
    if robots.allowed(base):
        page = get(base, ACCEPT_HTML)
        md = get(base, ACCEPT_MD)
    else:
        page = {"status": None, "final_url": base, "ctype": "", "text": None, "error": "robots.txt disallows"}
        md = dict(page)
    final = page.get("final_url") or base
    if page.get("status") is None:
        kind = "error"
    elif is_challenge(page.get("text"), page.get("ctype")):
        kind = "challenge"
    elif page["status"] == 200:
        kind = "page"
    else:
        kind = "missing"
    blocked, generic, signals, rstatus = robots.ai_answer(final)
    entry.update(base_status=page.get("status"), base_final=final, base_kind=kind, base_error=page.get("error"),
                 md_status=md.get("status"), md_ctype=md.get("ctype") or "", md_negotiated=md_negotiated(md),
                 robots_host=host_key(final), robots_status=rstatus, ai_blocked=blocked, generic_allowed=generic,
                 content_signal=signals)
    files = []
    for c in candidates(base):
        f = dict(c)
        if not robots.allowed(c["url"]):
            f.update(status=None, final_url=None, ctype="", kind="robots", truncated=False, length=None,
                     error="robots.txt disallows", head="")
            f.update(file_facts(""))
        else:
            got = get(c["url"], ACCEPT_TEXT)
            f.update(status=got["status"], final_url=got.get("final_url"), ctype=got.get("ctype") or "",
                     kind=classify(got, c["file"]), truncated=bool(got.get("truncated")), length=got.get("length"),
                     error=got.get("error"))
            text = got.get("text") if got.get("status") == 200 else ""
            f.update(file_facts(text))
            f["head"] = (text or "")[:HEAD_CHARS]
        files.append(f)
    entry["files"] = files
    return entry


def project_summary(p, bases, policy):
    files = [f for b in bases for f in b["files"]]
    valid = [f for f in files if f["kind"] == "valid"]
    known = [b for b in bases if b["ai_blocked"] is not None]
    ai_block = None
    if known:
        ai_block = any(b["ai_blocked"] and b["generic_allowed"] for b in known)
    challenge = any(b["base_kind"] == "challenge" for b in bases) or any(f["kind"] == "challenge" for f in files)
    return {"id": p["id"], "project": p["project"], "group": p["group"], "stance": p["stance"],
            "reached": any(b["base_status"] is not None for b in bases) or any(f["status"] is not None for f in files),
            "serves_llms": any(f["file"] == "llms.txt" for f in valid),
            "serves_full": any(f["file"] == "llms-full.txt" for f in valid),
            "serves_any": bool(valid),
            "spec_h1": any(f["spec_h1"] for f in valid),
            "md_negotiated": any(b["md_negotiated"] for b in bases),
            "ai_block": ai_block, "challenge": challenge,
            "refuses_ai_readers": bool(ai_block) or challenge,
            "ai_blocked_agents": sorted({a for b in bases for a in (b["ai_blocked"] or [])}),
            "content_signal": sorted({s for b in bases for s in b["content_signal"]}),
            "valid_urls": [f["url"] for f in valid],
            "policy_url": p.get("policy_url") or "", "policy_status": policy.get("status"),
            "policy_mentions_llms": policy.get("mentions")}


RETRY_429 = (60, 120, 240)  # seconds to wait before each retry of a rate-limited (HTTP 429) fetch


def census(projects, fetcher=fetch, pause=0.5, sleep=time.sleep):
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
    for p in projects:
        bases = [probe_base(b, get, robots) for b in p["bases"]]
        policy = {"status": None, "mentions": None}
        if p.get("policy_url"):
            if robots.allowed(p["policy_url"]):
                got = get(p["policy_url"], ACCEPT_TEXT)
                policy = {"status": got["status"],
                          "mentions": len(LLMS_MENTION.findall(got["text"] or "")) if got["status"] == 200 else None}
            else:
                policy = {"status": "robots", "mentions": None}
        r = project_summary(p, bases, policy)
        r["bases"] = bases
        results.append(r)
    return results, calls[0]


def parse_frame(data):
    projects = data.get("projects") if isinstance(data, dict) else data
    if not isinstance(projects, list):
        raise ValueError("no projects list")
    rows = []
    for e in projects:
        if not e.get("id") or not e.get("bases") or e.get("group") not in GROUPS:
            raise ValueError("a project entry lacks id, bases or a known group")
        rows.append({"id": e["id"], "project": e.get("project", ""), "stance": e.get("stance", ""),
                     "group": e["group"], "scope": e.get("scope", ""), "bases": list(e["bases"]),
                     "policy_url": e.get("policy_url", ""), "note": e.get("note", "")})
    return rows


# ---------------------------------------------------------------- pre-registration check and report

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


def wait_for_prereg(path, minutes, opener=None, sleep=time.sleep, every=300):
    prereg = prereg_commit(path, opener)
    waited = 0
    while prereg.get("committed_at") is None and waited < minutes * 60:
        sleep(every)
        waited += every
        prereg = prereg_commit(path, opener)
    prereg["waited_seconds"] = waited
    return prereg


def share(rows, key):
    return (sum(1 for r in rows if r[key]) / len(rows)) if rows else 0.0


def predictions(results):
    """The pre-registered gate and predictions, computed from the automatic labels (before the hand check)."""
    n = len(results)
    reached = sum(1 for r in results if r["reached"])
    closed = [r for r in results if r["group"] in ("BAN", "RESTRICTED")]
    open_ = [r for r in results if r["group"] == "OPEN"]
    serving = [r for r in results if r["serves_any"]]
    k = len(serving)
    out = {"G1": {"text": "at least 50 of the 56 projects reached", "value": "%d of %d" % (reached, n),
                  "held": reached >= 50}}
    out["P1"] = {"text": "14 to 33 of the 56 projects serve a valid llms.txt or llms-full.txt",
                 "value": "%d of %d" % (k, n), "held": 14 <= k <= 33}
    c = sum(1 for r in closed if r["serves_any"])
    out["P2"] = {"text": "at most 1 of the 10 BAN or RESTRICTED projects serves one",
                 "value": "%d of %d" % (c, len(closed)), "held": c <= 1}
    gap = share(open_, "serves_any") - share(closed, "serves_any")
    out["P3"] = {"text": "OPEN share minus BAN+RESTRICTED share is at least 25 points",
                 "value": "%.1f points" % (100 * gap), "held": gap >= 0.25}
    full = sum(1 for r in serving if r["serves_full"])
    out["P4"] = {"text": "at least half of the serving projects also serve llms-full.txt",
                 "value": "%d of %d" % (full, k), "held": bool(k) and 2 * full >= k}
    rc, ro = share(closed, "refuses_ai_readers"), share(open_, "refuses_ai_readers")
    out["P5"] = {"text": "BAN+RESTRICTED share refusing AI readers is higher than the OPEN share",
                 "value": "%.1f%% vs %.1f%%" % (100 * rc, 100 * ro), "held": rc > ro}
    return out


def yn(v):
    return "?" if v is None else ("yes" if v else "no")


def report(results, started, finished, prereg, frame_url, calls):
    lines = ["# Do projects with AI contribution rules serve their docs to AI readers? Automatic labels", "",
             "llmsprobe.py %s. Frame: %d projects from %s. Fetched %s to %s UTC (%d requests). "
             "Pre-registration first committed: %s." % (
                 VERSION, len(results), frame_url, started, finished, calls,
                 prereg.get("committed_at") or "not found (%s)" % prereg.get("error")),
             "", "These are the tool's labels before the hand check the pre-registration asks for.", "",
             "| Group | Projects | Reached | Serve llms.txt or llms-full.txt | llms.txt | llms-full.txt | "
             "Markdown on request | robots.txt blocks a named AI crawler | Bot challenge | Refuses AI readers |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for g in GROUPS + ("ALL",):
        rows = [r for r in results if g == "ALL" or r["group"] == g]
        lines.append("| %s | %d | %d | %d | %d | %d | %d | %d (%d unknown) | %d | %d |" % (
            g, len(rows), sum(r["reached"] for r in rows), sum(r["serves_any"] for r in rows),
            sum(r["serves_llms"] for r in rows), sum(r["serves_full"] for r in rows),
            sum(r["md_negotiated"] for r in rows), sum(1 for r in rows if r["ai_block"]),
            sum(1 for r in rows if r["ai_block"] is None), sum(r["challenge"] for r in rows),
            sum(r["refuses_ai_readers"] for r in rows)))
    lines += ["", "## Gate and predictions (automatic labels)", "", "| | Prediction | Value | Held |",
              "|---|---|---|---|"]
    for key, v in predictions(results).items():
        lines.append("| %s | %s | %s | %s |" % (key, v["text"], v["value"], yn(v["held"])))
    lines += ["", "## Projects", "", "| id | project | group | reached | llms.txt | llms-full.txt | H1 first | "
              "Markdown | AI crawlers blocked | challenge | policy mentions llms.txt |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["id"], r["project"].replace("|", "/"), r["group"], yn(r["reached"]), yn(r["serves_llms"]),
            yn(r["serves_full"]), yn(r["spec_h1"]) if r["serves_any"] else "",
            yn(r["md_negotiated"]), "?" if r["ai_block"] is None else (", ".join(r["ai_blocked_agents"]) or "none"),
            yn(r["challenge"]), "" if r["policy_mentions_llms"] is None else r["policy_mentions_llms"]))
    lines += ["", "Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0, code Apache-2.0.",
              ""]
    return "\n".join(lines)


def write_outputs(out_dir, rows, results, meta, text):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "census.json"), "w", encoding="utf-8") as fh:
        json.dump(dict(meta, projects=results), fh, ensure_ascii=False, indent=1)
    with open(os.path.join(out_dir, "frame.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "project", "stance", "group", "scope", "bases", "policy_url", "note"])
        for r in rows:
            w.writerow([r["id"], r["project"], r["stance"], r["group"], r["scope"], " ".join(r["bases"]),
                        r["policy_url"], r["note"]])
    with open(os.path.join(out_dir, "bases.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "base", "base_status", "base_final", "base_kind", "md_status", "md_ctype", "md_negotiated",
                    "robots_host", "robots_status", "generic_allowed", "ai_blocked", "content_signal", "base_error"])
        for r in results:
            for b in r["bases"]:
                w.writerow([r["id"], b["base"], b["base_status"] or "", b["base_final"], b["base_kind"],
                            b["md_status"] or "", b["md_ctype"], int(b["md_negotiated"]), b["robots_host"],
                            b["robots_status"] or "", yn(b["generic_allowed"]),
                            "?" if b["ai_blocked"] is None else " ".join(b["ai_blocked"]),
                            " | ".join(b["content_signal"]), b["base_error"] or ""])
    with open(os.path.join(out_dir, "probes.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "base", "file", "where", "url", "status", "final_url", "ctype", "kind", "chars",
                    "truncated", "length", "spec_h1", "links", "first_line", "error"])
        for r in results:
            for b in r["bases"]:
                for f in b["files"]:
                    w.writerow([r["id"], b["base"], f["file"], f["where"], f["url"], f["status"] or "",
                                f["final_url"] or "", f["ctype"], f["kind"], f["chars"], int(f["truncated"]),
                                f["length"] or "", int(f["spec_h1"]), f["links"], f["first_line"], f["error"] or ""])
    with open(os.path.join(out_dir, "projects.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        keys = ["id", "project", "group", "stance", "reached", "serves_any", "serves_llms", "serves_full", "spec_h1",
                "md_negotiated", "ai_block", "challenge", "refuses_ai_readers", "ai_blocked_agents",
                "content_signal", "valid_urls", "policy_url", "policy_status", "policy_mentions_llms"]
        w.writerow(keys)
        for r in results:
            row = []
            for k in keys:
                v = r[k]
                if isinstance(v, bool) or v is None:
                    v = yn(v)
                elif isinstance(v, list):
                    v = " ".join(v)
                row.append(v)
            w.writerow(row)
    with open(os.path.join(out_dir, "LLMSPROBE_AUTO.md"), "w", encoding="utf-8") as fh:
        fh.write(text)


def main(argv=None, fetcher=fetch, opener=None, sleep=time.sleep):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--frame-url", default=FRAME_URL)
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
    got = fetcher(a.frame_url, ACCEPT_TEXT)
    if got["text"] is None or got["status"] != 200:
        print("frame could not be read: %s %s" % (got["status"], got["error"]))
        return 2
    try:
        rows = parse_frame(json.loads(got["text"]))
    except (ValueError, TypeError, AttributeError) as exc:
        print("frame is not a projects list: %s" % exc)
        return 2
    if not rows:
        print("no projects in the frame")
        return 2
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    results, calls = census(rows, fetcher, a.pause, sleep)
    finished = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    meta = {"version": VERSION, "frame_url": a.frame_url, "started": started, "finished": finished,
            "prereg": prereg, "requests": calls, "ai_agents": list(AI_AGENTS),
            "predictions_auto": predictions(results)}
    text = report(results, started, finished, prereg, a.frame_url, calls)
    write_outputs(a.out_dir, rows, results, meta, text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
