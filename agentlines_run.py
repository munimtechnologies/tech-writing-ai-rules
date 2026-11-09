# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Run study 6's agentlines.py 0.1.0 with hosts read in parallel and a time limit on each request.

Usage: python agentlines_run.py --out-dir OUT [--workers 8] [--deadline 60] [any other agentlines.py option]

Why: the first run of agentlines.py 0.1.0 (job agentlines-v1, 2026-11-09) read the hosts one after another and
was stopped by the job's 8-hour limit before it wrote anything. A slow server can hold one request far longer
than the 15 s socket timeout, because that timeout applies to each read, not to the whole answer.

This runner changes only how requests are scheduled, never what is asked or how answers are labelled:

- unique llms.txt URLs are grouped by host (scheme and host, as agentlines.host_key). Each host's robots.txt
  and llms.txt requests stay in order in one worker, with the same pause before each request and the same
  retries on HTTP 429. Up to --workers hosts are read at the same time;
- every request is cut off after --deadline seconds in all (600 s for the directory file itself). A cut-off
  answer is an error with no HTTP status, as a timeout already was in 0.1.0;
- an unexpected error while probing one URL is recorded as that URL's error instead of stopping the run;
- results keep the frame's order, so the samples, counts and files are what a one-by-one run would give for
  the same answers;
- a progress line is printed every 100 URLs.

Everything else (frame, labels, candidate lines, samples, output files and the pre-registration wait) is
agentlines.py 0.1.0, unchanged and imported as is. Standard library only.
Made by MV2 of Munim, Inc., with AI agents working in his name. Apache-2.0.
"""
import argparse
import collections
import concurrent.futures
import http.client
import http.cookiejar
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request

import agentlines as al

RUNNER_VERSION = "0.1.0"
EXPECTED_TOOL = "0.1.0"
CHUNK = 65536
FRAME_DEADLINE = 600


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


def census(rows, fetcher, pause=0.25, sleep=time.sleep, workers=8, log=print):
    """agentlines.census with hosts read in parallel. Returns (results in frame order, requests made)."""
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
        r = {"id": row["id"], "url": url, "status": None, "final_url": "", "ctype": "", "kind": "error",
             "chars": 0, "truncated": False, "spec_h1": False, "links": 0, "reached": False, "error": "",
             "candidates": [], "head": ""}
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

    todo = [row for row in rows if not row["dup_of"] and row["key"]]
    groups = collections.OrderedDict()
    for row in todo:
        groups.setdefault(al.host_key(row["llms_url"]), []).append(row)
    done = {}
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = [pool.submit(lambda g: [probe(row) for row in g], g) for g in groups.values()]
        for fut in concurrent.futures.as_completed(futures):
            before = len(done)
            for r in fut.result():
                done[r["id"]] = r
            if log and len(done) // 100 > before // 100:
                log("progress: %d of %d URLs (%d hosts), %d requests, %.0f s"
                    % (len(done), len(todo), len(groups), calls[0], time.monotonic() - started))
                sys.stdout.flush()
    return [done[row["id"]] for row in todo], calls[0]


def main(argv=None, fetcher=None, opener=None, sleep=time.sleep):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], add_help=False)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--deadline", type=float, default=60)
    own, rest = ap.parse_known_args(argv)
    if al.VERSION != EXPECTED_TOOL:
        print("agentlines.py is %s, this runner is for %s" % (al.VERSION, EXPECTED_TOOL))
        return 5
    if own.workers < 1 or own.deadline <= 0:
        print("--workers must be at least 1 and --deadline above 0")
        return 2
    saved = (al.census, al.fetch, al.VERSION)

    def parallel(rows, f, pause, slp):
        return census(rows, f, pause, slp, workers=own.workers)

    al.census = parallel
    if fetcher is None:
        al.fetch = make_fetch(own.deadline)
    al.VERSION = "%s, run by agentlines_run.py %s (%d workers, %g s per request)" % (
        EXPECTED_TOOL, RUNNER_VERSION, own.workers, own.deadline)
    try:
        return al.main(rest, fetcher=fetcher, opener=opener, sleep=sleep)
    finally:
        al.census, al.fetch, al.VERSION = saved


if __name__ == "__main__":
    sys.exit(main())
