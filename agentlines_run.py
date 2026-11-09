# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Run study 6's agentlines.py 0.1.0 with hosts read in parallel and a time limit on each request.

Usage: python agentlines_run.py --out-dir OUT [--workers 8] [--deadline 60] [--url-limit 600]
       [--stall-dump 900] [any other agentlines.py option]

Why: the first run of agentlines.py 0.1.0 (job agentlines-v1, 2026-11-09) read the hosts one after another and
was stopped by the job's 8-hour limit before it wrote anything. Runner 0.1.0 (amendment 1) read 800 of 1,512
URLs in about four minutes in the second run (agentlines-v2), then made no more progress for three hours
until the job was stopped from outside. Version 0.2.0 (amendment 2) closes the two ways that can happen:

- robots.txt rules are matched by a linear-time matcher that gives the same answer as agentlines.py's
  regular expression for every pattern and path, but cannot backtrack. Python's regular expression engine
  holds the interpreter lock while it runs, so one pathological rule (many '*' wildcards) froze every
  worker at once;
- a host that still has no complete answer after --url-limit seconds per URL is given up: its URLs are
  recorded as errors (not reached if its robots.txt never answered) and the run goes on. The worker
  threads are daemon threads, so a stuck one cannot hold the run open;
- if no host finishes for --stall-dump seconds, the stack of every thread is written to stderr, so any
  further stall can be diagnosed.

Unchanged from 0.1.0: unique llms.txt URLs are grouped by host; each host's robots.txt and llms.txt requests
stay in order in one worker, with the same pause before each request and the same retries on HTTP 429; up to
--workers hosts are read at the same time; every request is cut off after --deadline seconds in all (600 s
for the directory file); an unexpected error while probing one URL is recorded as that URL's error; results
keep the frame's order; a progress line is printed every 100 URLs.

Everything else (frame, labels, candidate lines, samples, output files and the pre-registration wait) is
agentlines.py 0.1.0, unchanged and imported as is. Standard library only.
Made by MV2 of Munim, Inc., with AI agents working in his name. Apache-2.0.
"""
import argparse
import collections
import faulthandler
import http.client
import http.cookiejar
import os
import queue
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request

import agentlines as al

RUNNER_VERSION = "0.2.0"
EXPECTED_TOOL = "0.1.0"
CHUNK = 65536
FRAME_DEADLINE = 600
URL_LIMIT = 600
STALL_DUMP = 900


def wildcard_match(pattern, path):
    """agentlines.pattern_match without a regular expression: same result, linear time.

    '*' matches any run of characters, a final '$' anchors the end, every other character is literal, and the
    pattern must match from the start of the path. Greedy leftmost search is exact for this pattern language.
    (Python's '$' would also match before one final newline; URL paths from urlsplit never contain one.)"""
    anchored = pattern.endswith("$")
    if anchored:
        pattern = pattern[:-1]
    parts = pattern.split("*")
    if not path.startswith(parts[0]):
        return False
    pos = len(parts[0])
    if len(parts) == 1:
        return pos == len(path) if anchored else True
    for part in parts[1:-1]:
        i = path.find(part, pos)
        if i < 0:
            return False
        pos = i + len(part)
    last = parts[-1]
    if anchored:
        return len(path) - len(last) >= pos and path.endswith(last)
    return path.find(last, pos) >= 0


def read_capped(resp, limit, start, deadline, clock=time.monotonic):
    """Read at most `limit` bytes; raise TimeoutError once `deadline` seconds have passed since `start`."""
    reader = getattr(resp, "read1", None) or resp.read
    chunks, size = [], 0
    while size < limit:
        if clock() - start > deadline:
            raise TimeoutError("answer not complete after %g s" % deadline)
        chunk = reader(min(CHUNK, limit - size))
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)
    return b"".join(chunks)


def fetch(url, accept=al.ACCEPT_TEXT, timeout=al.TIMEOUT, max_bytes=al.MAX_BYTES, deadline=60,
          clock=time.monotonic):
    """agentlines.fetch with a limit on the whole request. Same answer format and certificate retry."""
    if max_bytes > al.MAX_BYTES:
        deadline = max(deadline, FRAME_DEADLINE)
    req = urllib.request.Request(url, headers={"User-Agent": al.USER_AGENT, "Accept": accept,
                                               "Accept-Language": "en"})
    error = None
    start = clock()
    for tls, ctx in (("verified", ssl.create_default_context()), ("unverified", ssl._create_unverified_context())):
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
                                             urllib.request.HTTPSHandler(context=ctx))
        try:
            with opener.open(req, timeout=timeout) as resp:
                body = read_capped(resp, max_bytes + 1, start, deadline, clock)
                return {"status": resp.status, "tls": tls, "final_url": resp.geturl(),
                        "ctype": resp.headers.get("Content-Type", ""), "truncated": len(body) > max_bytes,
                        "text": al.decode(body[:max_bytes], resp.headers.get_content_charset()), "error": None}
        except urllib.error.HTTPError as e:
            body = b""
            try:
                body = read_capped(e, 200_000, start, deadline, clock)
            except Exception:
                pass
            headers = e.headers if e.headers is not None else {}
            return {"status": e.code, "tls": tls, "final_url": e.geturl() or url,
                    "ctype": headers.get("Content-Type", "") or "", "truncated": False,
                    "text": al.decode(body) if body else None, "error": str(e)}
        except (urllib.error.URLError, ssl.SSLError, OSError, ValueError, http.client.HTTPException) as e:
            error = str(getattr(e, "reason", e)) or type(e).__name__
            if "CERTIFICATE" not in error.upper():
                break
        except Exception as e:  # anything else from one site must not stop the census
            error = "%s: %s" % (type(e).__name__, e)
            break
    return {"status": None, "tls": None, "final_url": url, "ctype": "", "truncated": False, "text": None,
            "error": error}


def make_fetch(deadline):
    def bound(url, accept=al.ACCEPT_TEXT, timeout=al.TIMEOUT, max_bytes=al.MAX_BYTES):
        return fetch(url, accept, timeout, max_bytes, deadline)
    return bound


def blank(row):
    return {"id": row["id"], "url": row["llms_url"], "status": None, "final_url": "", "ctype": "", "kind": "error",
            "chars": 0, "truncated": False, "spec_h1": False, "links": 0, "reached": False, "error": "",
            "candidates": [], "head": ""}


def census(rows, fetcher, pause=0.25, sleep=time.sleep, workers=8, log=print, url_limit=URL_LIMIT, poll=1.0,
           clock=time.monotonic, beat=None):
    """agentlines.census with hosts read in parallel. Returns (results in frame order, requests made).

    A host still unfinished after url_limit seconds per URL is given up; `beat` is called whenever a host
    finishes or is given up."""
    lock = threading.Lock()
    calls = [0]

    def get(url, accept=al.ACCEPT_TEXT):
        with lock:
            first = calls[0] == 0
            calls[0] += 1
        if not first and pause:
            sleep(pause)
        got = fetcher(url, accept)
        for wait in al.RETRY_429:
            if got["status"] != 429:
                break
            sleep(wait)
            got = fetcher(url, accept)
        return got

    robots = al.Robots(get)

    def probe(row):
        url = row["llms_url"]
        r = blank(row)
        try:
            rb = robots.entry(url)
            if rb["status"] is None:
                r["error"] = "host not reached (robots.txt: %s)" % (rb["error"] or "no answer")
            elif not robots.allowed(url):
                r.update(reached=True, kind="robots", error="robots.txt disallows")
            else:
                got = get(url)
                text = got.get("text") if got.get("status") == 200 else ""
                r.update(reached=True, status=got["status"], final_url=got.get("final_url") or "",
                         ctype=got.get("ctype") or "", kind=al.classify(got, url),
                         truncated=bool(got.get("truncated")), error=got.get("error") or "",
                         chars=len(text or ""))
                if r["kind"] == "valid":
                    lines = [l for l in text.splitlines() if l.strip()]
                    r["spec_h1"] = bool(lines) and bool(al.H1.match(lines[0].strip()))
                    r["links"] = len(al.MD_LINK.findall(text))
                    r["candidates"] = al.candidates(text)
                    r["head"] = text[:al.HEAD_CHARS]
        except Exception as exc:  # one URL must not stop the census
            r.update(kind="error", error="tool error: %s: %s" % (type(exc).__name__, exc))
        return r

    def given_up(row, seconds):
        url = row["llms_url"]
        r = blank(row)
        rb = robots.cache.get(al.host_key(url))
        note = "no complete answer within %d s; given up by agentlines_run.py %s" % (seconds, RUNNER_VERSION)
        try:
            if rb is None or rb["status"] is None:
                r["error"] = "host not reached (%s)" % note
            elif not robots.allowed(url):
                r.update(reached=True, kind="robots", error="robots.txt disallows")
            else:
                r.update(reached=True, error=note)
        except Exception as exc:
            r["error"] = "tool error: %s: %s" % (type(exc).__name__, exc)
        return r

    todo = [row for row in rows if not row["dup_of"] and row["key"]]
    by_host = collections.OrderedDict()
    for row in todo:
        by_host.setdefault(al.host_key(row["llms_url"]), []).append(row)
    groups = list(by_host.values())
    finished = queue.Queue()
    partial = {}

    def work(i):
        got = partial[i]
        for row in groups[i]:
            got.append(probe(row))
        finished.put(i)

    done, running = {}, {}
    nxt = 0
    started = clock()
    while nxt < len(groups) or running:
        while nxt < len(groups) and len(running) < max(1, workers):
            partial[nxt] = []
            running[nxt] = clock()
            threading.Thread(target=work, args=(nxt,), daemon=True).start()
            nxt += 1
        ended = []
        try:
            i = finished.get(timeout=poll)
            while True:
                if i in running and i not in ended:
                    ended.append(i)
                i = finished.get_nowait()
        except queue.Empty:
            pass
        cut = []
        now = clock()
        for i, t0 in running.items():
            limit = url_limit * len(groups[i])
            if i not in ended and now - t0 > limit:
                cut.append((i, limit))
        before = len(done)
        for i in ended:
            del running[i]
            for r in partial[i]:
                done[r["id"]] = r
        for i, limit in cut:
            del running[i]
            got = list(partial[i])
            for row in groups[i][len(got):]:
                got.append(given_up(row, limit))
            for r in got:
                done[r["id"]] = r
            if log:
                log("given up: %s after %d s" % (al.host_key(groups[i][0]["llms_url"]), limit))
        if (ended or cut) and beat:
            beat()
        if log and len(done) // 100 > before // 100:
            log("progress: %d of %d URLs (%d hosts), %d requests, %.0f s"
                % (len(done), len(todo), len(groups), calls[0], clock() - started))
            sys.stdout.flush()
    return [done[row["id"]] for row in todo], calls[0]


def arm_stall_dump(seconds):
    """Write every thread's stack to stderr if nothing finishes for `seconds`. Returns a re-arm function."""
    if not seconds:
        return None
    try:
        sys.stderr.fileno()
    except Exception:
        return None

    def rearm():
        faulthandler.dump_traceback_later(seconds, repeat=True, file=sys.stderr)
    rearm()
    return rearm


def main(argv=None, fetcher=None, opener=None, sleep=time.sleep):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], add_help=False)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--deadline", type=float, default=60)
    ap.add_argument("--url-limit", type=float, default=URL_LIMIT)
    ap.add_argument("--stall-dump", type=float, default=STALL_DUMP)
    own, rest = ap.parse_known_args(argv)
    if al.VERSION != EXPECTED_TOOL:
        print("agentlines.py is %s, this runner is for %s" % (al.VERSION, EXPECTED_TOOL))
        return 5
    if own.workers < 1 or own.deadline <= 0 or own.url_limit <= 0 or own.stall_dump < 0:
        print("--workers must be at least 1, --deadline and --url-limit above 0, --stall-dump 0 or more")
        return 2
    saved = (al.census, al.fetch, al.VERSION, al.pattern_match)
    beat = arm_stall_dump(own.stall_dump)

    def parallel(rows, f, pause, slp):
        return census(rows, f, pause, slp, workers=own.workers, url_limit=own.url_limit, beat=beat)

    al.census = parallel
    al.pattern_match = wildcard_match
    if fetcher is None:
        al.fetch = make_fetch(own.deadline)
    al.VERSION = "%s, run by agentlines_run.py %s (%d workers, %g s per request, %g s per URL)" % (
        EXPECTED_TOOL, RUNNER_VERSION, own.workers, own.deadline, own.url_limit)
    try:
        return al.main(rest, fetcher=fetcher, opener=opener, sleep=sleep)
    finally:
        if beat:
            faulthandler.cancel_dump_traceback_later()
        al.census, al.fetch, al.VERSION, al.pattern_match = saved


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code if isinstance(code, int) else (0 if code is None else 1))  # stuck daemon threads cannot hold the exit
