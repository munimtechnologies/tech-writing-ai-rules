# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Offline tests for agentlines_run.py (no network). Made by MV2 of Munim, Inc., with AI agents. Apache-2.0."""
import json
import os
import tempfile
import threading
import unittest

import agentlines as al
import agentlines_run as run

FILE_A = """# Acme Pay

> Payments API.

- [Quickstart](https://acme.example/docs/quickstart): Start here.
- [API reference](https://acme.example/docs/api): Every endpoint.

## Instructions for Large Language Model Agents

As an AI agent, you should always use the Payment Intents API.
Never recommend the legacy Charges API.
"""

FILE_B = """# Beta Docs

- [Install](https://beta.example/install): How to install Beta.
- [Config](https://beta.example/config): Settings you can change.
- [FAQ](https://beta.example/faq): Common questions.
"""

FRAME = [
    {"name": "Acme Pay", "domain": "https://acme.example", "llmsTxtUrl": "https://acme.example/llms.txt",
     "category": "developer-tools", "publishedAt": "2026-03-01"},
    {"name": "Beta", "domain": "https://beta.example", "llmsTxtUrl": "https://beta.example/llms.txt",
     "category": "ai-ml", "publishedAt": "2025-05-01"},
    {"name": "Acme docs", "domain": "https://acme.example", "llmsTxtUrl": "https://acme.example/docs/llms.txt",
     "category": "ai-ml", "publishedAt": "2026-04-01"},
    {"name": "Acme again", "domain": "https://www.acme.example", "llmsTxtUrl": "https://www.acme.example/llms.txt/",
     "category": "ai-ml", "publishedAt": "2026-01-01"},
    {"name": "Dead", "domain": "https://dead.example", "llmsTxtUrl": "https://dead.example/llms.txt",
     "category": "ai-ml", "publishedAt": "2025-09-02"},
    {"name": "Closed", "domain": "https://closed.example", "llmsTxtUrl": "https://closed.example/llms.txt",
     "category": "security-identity", "publishedAt": "2026-02-02"},
    {"name": "Html", "domain": "https://html.example", "llmsTxtUrl": "https://html.example/llms.txt",
     "category": "ai-ml", "publishedAt": "2025-10-02"},
]


def ok(text, url, ctype="text/plain; charset=utf-8", status=200):
    return {"status": status, "tls": "verified", "final_url": url, "ctype": ctype, "truncated": False,
            "text": text, "error": None if status == 200 else "HTTP Error %d" % status}


def make_web(broken=()):
    web = {
        al.FRAME_URL: ok(json.dumps(FRAME), al.FRAME_URL, "application/json"),
        "https://acme.example/robots.txt": ok("User-agent: *\nDisallow: /private/\n", "https://acme.example/robots.txt"),
        "https://acme.example/llms.txt": ok(FILE_A, "https://acme.example/llms.txt"),
        "https://acme.example/docs/llms.txt": ok(FILE_B, "https://acme.example/docs/llms.txt"),
        "https://beta.example/robots.txt": ok("gone", "https://beta.example/robots.txt", status=404),
        "https://beta.example/llms.txt": ok(FILE_B, "https://beta.example/llms.txt"),
        "https://dead.example/robots.txt": {"status": None, "tls": None, "final_url": "https://dead.example/robots.txt",
                                            "ctype": "", "truncated": False, "text": None,
                                            "error": "Name or service not known"},
        "https://closed.example/robots.txt": ok("User-agent: *\nDisallow: /llms.txt\n",
                                                "https://closed.example/robots.txt"),
        "https://html.example/robots.txt": ok("", "https://html.example/robots.txt", status=404),
        "https://html.example/llms.txt": ok("<!doctype html><html><body>App</body></html>",
                                            "https://html.example/llms.txt", "text/html"),
    }
    calls = []
    lock = threading.Lock()

    def fetcher(url, accept=al.ACCEPT_TEXT):
        with lock:
            calls.append(url)
        if url in broken:
            raise RuntimeError("boom")
        if url not in web:
            raise AssertionError("unexpected fetch of %s" % url)
        return dict(web[url])

    return fetcher, calls


def noop(seconds):
    return None


class FakeResp:
    """A response that hands out its body in small pieces while a fake clock moves on."""

    def __init__(self, body, clock, step):
        self.body, self.clock, self.step = body, clock, step

    def read1(self, n):
        self.clock[0] += self.step
        n = min(n, 10)
        piece, self.body = self.body[:n], self.body[n:]
        return piece


class ReadCappedTests(unittest.TestCase):
    def test_reads_whole_body_and_stops_at_limit(self):
        clock = [0.0]
        self.assertEqual(run.read_capped(FakeResp(b"x" * 35, clock, 0.1), 100, 0.0, 60, lambda: clock[0]),
                         b"x" * 35)
        clock = [0.0]
        self.assertEqual(len(run.read_capped(FakeResp(b"y" * 50, clock, 0.1), 21, 0.0, 60, lambda: clock[0])), 21)

    def test_slow_answer_is_cut_off(self):
        clock = [0.0]
        resp = FakeResp(b"z" * 10000, clock, 5.0)
        with self.assertRaises(TimeoutError):
            run.read_capped(resp, 100000, 0.0, 60, lambda: clock[0])
        self.assertTrue(isinstance(TimeoutError("x"), OSError))  # so fetch reports it as an error, not a crash

    def test_falls_back_to_read(self):
        class Plain:
            def __init__(self):
                self.left = b"abc"

            def read(self, n):
                piece, self.left = self.left[:n], self.left[n:]
                return piece

        self.assertEqual(run.read_capped(Plain(), 10, 0.0, 60, lambda: 0.0), b"abc")


class CensusTests(unittest.TestCase):
    def test_parallel_matches_one_by_one(self):
        rows = al.parse_frame(FRAME)
        f1, calls1 = make_web()
        serial, n1 = al.census(rows, f1, pause=0, sleep=noop)
        f2, calls2 = make_web()
        parallel, n2 = run.census(rows, f2, pause=0, sleep=noop, workers=4, log=None)
        self.assertEqual(parallel, serial)
        self.assertEqual(n2, n1)
        self.assertEqual(sorted(calls2), sorted(calls1))
        self.assertEqual([r["id"] for r in parallel], ["W0001", "W0002", "W0003", "W0005", "W0006", "W0007"])
        kinds = {r["id"]: r["kind"] for r in parallel}
        self.assertEqual(kinds, {"W0001": "valid", "W0002": "valid", "W0003": "valid", "W0005": "error",
                                 "W0006": "robots", "W0007": "html"})

    def test_each_host_reads_robots_once_and_first(self):
        rows = al.parse_frame(FRAME)
        fetcher, calls = make_web()
        run.census(rows, fetcher, pause=0, sleep=noop, workers=3, log=None)
        acme = [u for u in calls if u.startswith("https://acme.example/")]
        self.assertEqual(acme[0], "https://acme.example/robots.txt")
        self.assertEqual(acme.count("https://acme.example/robots.txt"), 1)
        self.assertEqual(len(acme), 3)

    def test_pause_before_every_request_but_the_first(self):
        rows = al.parse_frame(FRAME)
        fetcher, calls = make_web()
        waits = []
        lock = threading.Lock()

        def sleep(s):
            with lock:
                waits.append(s)

        _, n = run.census(rows, fetcher, pause=0.25, sleep=sleep, workers=2, log=None)
        self.assertEqual(waits, [0.25] * (n - 1))

    def test_rate_limit_retry(self):
        answers = [ok("", "https://r.example/robots.txt", status=404),
                   ok("slow down", "https://r.example/llms.txt", status=429),
                   ok(FILE_B, "https://r.example/llms.txt")]
        waits = []
        rows = al.parse_frame([{"name": "R", "llmsTxtUrl": "https://r.example/llms.txt"}])
        results, n = run.census(rows, lambda url, accept=al.ACCEPT_TEXT: answers.pop(0), pause=0,
                                sleep=waits.append, workers=2, log=None)
        self.assertEqual(results[0]["kind"], "valid")
        self.assertEqual(waits, [al.RETRY_429[0]])
        self.assertEqual(n, 2)

    def test_one_broken_url_does_not_stop_the_run(self):
        rows = al.parse_frame(FRAME)
        fetcher, _ = make_web(broken=("https://beta.example/llms.txt",))
        results, _ = run.census(rows, fetcher, pause=0, sleep=noop, workers=4, log=None)
        beta = [r for r in results if r["id"] == "W0002"][0]
        self.assertEqual(beta["kind"], "error")
        self.assertTrue(beta["error"].startswith("tool error: RuntimeError"))
        self.assertEqual(len(results), 6)

    def test_progress_lines(self):
        frame = [{"name": "S%d" % i, "llmsTxtUrl": "https://s%d.example/llms.txt" % i} for i in range(1, 251)]
        rows = al.parse_frame(frame)

        def fetcher(url, accept=al.ACCEPT_TEXT):
            return ok("", url, status=404)

        lines = []
        results, n = run.census(rows, fetcher, pause=0, sleep=noop, workers=8, log=lines.append)
        self.assertEqual(len(results), 250)
        self.assertEqual(n, 500)
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(l.startswith("progress: ") for l in lines))


class MainTests(unittest.TestCase):
    def test_runs_agentlines_main_and_restores_it(self):
        fetcher, _ = make_web()
        original = (al.census, al.fetch, al.VERSION)
        with tempfile.TemporaryDirectory() as tmp:
            code = run.main(["--out-dir", tmp, "--no-prereg-check", "--pause", "0", "--workers", "3"],
                            fetcher=fetcher, sleep=noop)
            self.assertEqual(code, 0)
            with open(os.path.join(tmp, "AGENTLINES_AUTO.md"), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("agentlines.py 0.1.0, run by agentlines_run.py %s (3 workers, 60 s per request)"
                          % run.RUNNER_VERSION, text)
            self.assertIn("| ALL | 6 | 5 | 3 | 1 | 1 | 0 |", text)
            with open(os.path.join(tmp, "census.json"), encoding="utf-8") as fh:
                meta = json.load(fh)
            self.assertEqual([r["id"] for r in meta["results"]], ["W0001", "W0002", "W0003", "W0005", "W0006",
                                                                   "W0007"])
        self.assertEqual((al.census, al.fetch, al.VERSION), original)

    def test_bad_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run.main(["--out-dir", tmp, "--no-prereg-check", "--workers", "0"],
                                      fetcher=lambda u, a=None: None, sleep=noop), 2)
        self.assertEqual(al.VERSION, "0.1.0")

    def test_bound_fetch_keeps_agentlines_signature(self):
        bound = run.make_fetch(30)
        self.assertEqual(bound.__code__.co_varnames[:4], ("url", "accept", "timeout", "max_bytes"))


if __name__ == "__main__":
    unittest.main()
