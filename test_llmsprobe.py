# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Offline tests for llmsprobe.py (no network). Run: python -m unittest -v test_llmsprobe"""
import csv
import json
import os
import tempfile
import unittest

import llmsprobe as L

LLMS = ("# Example project\n\n> Example docs for testing the probe tool.\n\n## Docs\n\n"
        "- [Start](https://docs.alpha.dev/start.md): first steps\n")
LINKS_ONLY = ("Docs index for the example project, the list follows here\n"
              "- [a](/a.md)\n- [b](/b.md)\n- [c](/c.md)\n")
HTML = "<!doctype html><html><head><title>Docs</title></head><body><p>Welcome to the docs.</p></body></html>"
ANUBIS = "<html><head><title>Making sure you're not a bot!</title></head><body>Anubis</body></html>"
CLOUDFLARE = "<html><head><title>Just a moment...</title></head><body></body></html>"


def resp(text, ctype="text/plain; charset=utf-8", status=200, final=None):
    return {"status": status, "tls": "verified", "final_url": final, "ctype": ctype, "length": None,
            "truncated": False, "text": text, "error": None if status == 200 else "HTTP Error %d" % status}


def missing(status=404):
    return {"status": status, "tls": "verified", "final_url": None, "ctype": "", "length": None,
            "truncated": False, "text": None, "error": "HTTP Error %d" % status}


class FakeWeb:
    """Answers by (url, accept) first, then by url; anything else is a 404."""

    def __init__(self, pages):
        self.pages, self.calls = pages, []

    def __call__(self, url, accept=L.ACCEPT_TEXT):
        self.calls.append((url, accept))
        got = self.pages.get((url, accept), self.pages.get(url))
        got = dict(got if got is not None else missing())
        if got["final_url"] is None:
            got["final_url"] = url
        return got


def noop(_seconds):
    return None


class TestCandidates(unittest.TestCase):
    def test_folder_base(self):
        self.assertEqual(L.base_dir("https://nextjs.org/docs"), "/docs/")
        self.assertEqual(L.base_dir("https://docs.python.org/3/"), "/3/")
        self.assertEqual(L.base_dir("https://sqlite.org/docs.html"), "/")
        self.assertEqual(L.base_dir("https://example.org"), "/")

    def test_candidates(self):
        c = L.candidates("https://NextJS.org/docs")
        self.assertEqual([x["url"] for x in c], ["https://nextjs.org/docs/llms.txt", "https://nextjs.org/llms.txt",
                                                  "https://nextjs.org/docs/llms-full.txt",
                                                  "https://nextjs.org/llms-full.txt"])
        self.assertEqual([x["where"] for x in c], ["dir", "root", "dir", "root"])
        root = L.candidates("https://sqlite.org/docs.html")
        self.assertEqual([x["url"] for x in root], ["https://sqlite.org/llms.txt", "https://sqlite.org/llms-full.txt"])
        self.assertEqual([x["where"] for x in root], ["root", "root"])


ROBOTS = """# test robots
User-agent: *
Disallow: /private/
Allow: /private/ok$

User-agent: GPTBot
User-agent: CCBot/1.0
Disallow: /

User-agent: ClaudeBot
Disallow: /docs/
Allow: /docs/public/
Content-Signal: search=yes, ai-train=no
"""


class TestRobots(unittest.TestCase):
    def setUp(self):
        self.r = L.RobotsFile(ROBOTS)

    def test_named_groups(self):
        self.assertFalse(self.r.allowed("GPTBot", "/docs/"))
        self.assertFalse(self.r.allowed("CCBot", "/anything"))
        self.assertFalse(self.r.allowed("ClaudeBot", "/docs/x"))
        self.assertTrue(self.r.allowed("ClaudeBot", "/docs/public/a"))
        self.assertTrue(self.r.allowed("ClaudeBot", "/other"))
        self.assertTrue(self.r.allowed("GPTBot", "/robots.txt"))

    def test_star_group_and_longest_match(self):
        self.assertFalse(self.r.allowed(L.GENERIC_AGENT, "/private/x"))
        self.assertTrue(self.r.allowed(L.GENERIC_AGENT, "/private/ok"))
        self.assertFalse(self.r.allowed(L.GENERIC_AGENT, "/private/ok/more"))
        self.assertTrue(self.r.allowed(L.GENERIC_AGENT, "/docs/"))
        # an agent with no group of its own falls back to "*"
        self.assertTrue(self.r.allowed("PerplexityBot", "/docs/"))

    def test_signals_and_patterns(self):
        self.assertEqual(self.r.signals, ["search=yes, ai-train=no"])
        self.assertTrue(L.pattern_match("/*.pdf$", "/a/b.pdf"))
        self.assertFalse(L.pattern_match("/*.pdf$", "/a/b.pdf?x=1"))
        self.assertTrue(L.pattern_match("/a", "/abc"))

    def test_no_rules_allows(self):
        self.assertTrue(L.RobotsFile("").allowed("GPTBot", "/"))
        self.assertTrue(L.RobotsFile("User-agent: *\nDisallow:\n").allowed("GPTBot", "/x"))

    def test_ai_answer(self):
        web = FakeWeb({"https://a.org/robots.txt": resp(ROBOTS),
                       "https://b.org/robots.txt": resp(HTML, "text/html")})
        robots = L.Robots(lambda u, a=L.ACCEPT_TEXT: web(u, a))
        blocked, generic, signals, status = robots.ai_answer("https://a.org/docs/")
        self.assertEqual(blocked, ["GPTBot", "ClaudeBot", "CCBot"])
        self.assertTrue(generic)
        self.assertEqual(signals, ["search=yes, ai-train=no"])
        self.assertEqual(status, 200)
        self.assertEqual(robots.ai_answer("https://b.org/"), (None, None, [], 200))   # HTML robots: unknown
        self.assertEqual(robots.ai_answer("https://c.org/"), ([], True, [], 404))     # no robots.txt
        self.assertFalse(robots.allowed("https://a.org/private/x"))
        self.assertTrue(robots.allowed("https://c.org/private/x"))
        self.assertEqual(sum(1 for u, _ in web.calls if u.endswith("/robots.txt")), 3)  # read once per host


class TestClassify(unittest.TestCase):
    def c(self, got, name="llms.txt", url="https://x.org/llms.txt"):
        got = dict(got)
        if got["final_url"] is None:
            got["final_url"] = url
        return L.classify(got, name)

    def test_labels(self):
        self.assertEqual(self.c(resp(LLMS)), "valid")
        self.assertEqual(self.c(resp(LINKS_ONLY)), "valid")
        self.assertEqual(self.c(resp(LLMS), "llms-full.txt", "https://x.org/llms-full.txt"), "valid")
        self.assertEqual(self.c(resp(HTML, "text/html")), "html")
        self.assertEqual(self.c(resp(HTML, "")), "html")
        self.assertEqual(self.c(resp(ANUBIS, "text/html")), "challenge")
        self.assertEqual(self.c(resp(CLOUDFLARE, "text/html", status=403)), "challenge")
        self.assertEqual(self.c(resp(HTML, "text/html", final="https://x.org/")), "redirected")
        self.assertEqual(self.c(resp(LLMS, final="https://x.org/llms-full.txt")), "redirected")
        self.assertEqual(self.c(missing()), "missing")
        self.assertEqual(self.c(dict(missing(), status=None)), "error")
        self.assertEqual(self.c(resp("# Hi\n")), "short")
        self.assertEqual(self.c(resp("Plain text with no heading at all. " * 5)), "unstructured")
        self.assertEqual(self.c(resp("## Only a second-level heading here\n" + "words " * 20)), "unstructured")

    def test_facts(self):
        f = L.file_facts("\n\n" + LLMS)
        self.assertTrue(f["spec_h1"])
        self.assertEqual(f["links"], 1)
        self.assertEqual(f["first_line"], "# Example project")
        self.assertFalse(L.file_facts(LINKS_ONLY)["spec_h1"])

    def test_markdown_negotiation(self):
        self.assertTrue(L.md_negotiated(resp(LLMS, "text/markdown; charset=utf-8")))
        self.assertFalse(L.md_negotiated(resp(HTML, "text/html")))
        self.assertFalse(L.md_negotiated(resp(HTML, "text/markdown")))
        self.assertFalse(L.md_negotiated(missing()))

    def test_challenge_needs_html_and_a_short_page(self):
        self.assertFalse(L.is_challenge("We use Anubis to stop scrapers.", "text/plain"))
        self.assertFalse(L.is_challenge("<html>" + "Anubis " + "x" * L.CHALLENGE_MAX_CHARS + "</html>", "text/html"))
        self.assertTrue(L.is_challenge(ANUBIS, "text/html"))


FRAME = {"projects": [
    {"id": "D001", "project": "Alpha", "stance": "neutral", "group": "OPEN", "bases": ["https://docs.alpha.dev/"],
     "policy_url": "https://alpha.dev/policy"},
    {"id": "D002", "project": "Beta", "stance": "ban", "group": "BAN", "bases": ["https://beta.org/docs/"]},
    {"id": "D003", "project": "Gamma", "stance": "restricted", "group": "RESTRICTED",
     "bases": ["https://gamma.org/wiki/Main"]},
    {"id": "D004", "project": "Delta", "stance": "neutral", "group": "OPEN", "bases": ["https://delta.io/docs"]},
    {"id": "D005", "project": "Eps", "stance": "encouraged", "group": "OPEN", "bases": ["https://eps.dev/"]},
]}


def fake_web():
    return FakeWeb({
        "https://docs.alpha.dev/": resp(HTML, "text/html"),
        ("https://docs.alpha.dev/", L.ACCEPT_MD): resp(LLMS, "text/markdown"),
        "https://docs.alpha.dev/llms.txt": resp(LLMS),
        "https://docs.alpha.dev/llms-full.txt": resp(LLMS + "\nFull text of every page.\n"),
        "https://alpha.dev/policy": resp("We publish llms.txt and llms-full.txt for readers."),
        "https://beta.org/robots.txt": resp("User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nDisallow: /admin/\n"),
        "https://beta.org/docs/": resp(HTML, "text/html"),
        "https://gamma.org/wiki/Main": resp(ANUBIS, "text/html"),
        "https://delta.io/robots.txt": resp(HTML, "text/html"),
        "https://delta.io/docs": resp(HTML, "text/html"),
        "https://delta.io/docs/llms.txt": resp(HTML, "text/html"),
        "https://delta.io/llms.txt": resp(HTML, "text/html", final="https://delta.io/"),
        "https://eps.dev/robots.txt": resp("User-agent: tech-writing-ai-rules-llmsprobe\nDisallow: /llms-full.txt\n"),
        "https://eps.dev/": resp(HTML, "text/html"),
        "https://eps.dev/llms.txt": resp(LINKS_ONLY),
        "https://eps.dev/llms-full.txt": resp(LLMS),
        "https://example.org/frame.json": resp(json.dumps(FRAME), "application/json"),
    })


class TestCensus(unittest.TestCase):
    def run_census(self):
        web = fake_web()
        results, calls = L.census(L.parse_frame(FRAME), web, pause=0, sleep=noop)
        return {r["id"]: r for r in results}, web, calls

    def test_project_labels(self):
        r, web, calls = self.run_census()
        self.assertEqual(calls, len(web.calls))
        a = r["D001"]
        self.assertTrue(a["serves_llms"] and a["serves_full"] and a["spec_h1"] and a["md_negotiated"])
        self.assertIs(a["ai_block"], False)
        self.assertFalse(a["refuses_ai_readers"])
        self.assertEqual(a["policy_mentions_llms"], 2)
        self.assertEqual(a["valid_urls"], ["https://docs.alpha.dev/llms.txt", "https://docs.alpha.dev/llms-full.txt"])
        b = r["D002"]
        self.assertFalse(b["serves_any"])
        self.assertIs(b["ai_block"], True)
        self.assertEqual(b["ai_blocked_agents"], ["GPTBot"])
        self.assertTrue(b["refuses_ai_readers"])
        self.assertIsNone(b["policy_mentions_llms"])
        g = r["D003"]
        self.assertTrue(g["challenge"] and g["refuses_ai_readers"] and g["reached"])
        self.assertEqual(g["bases"][0]["base_kind"], "challenge")
        d = r["D004"]
        self.assertFalse(d["serves_any"])
        self.assertIsNone(d["ai_block"])
        self.assertEqual([f["kind"] for f in d["bases"][0]["files"]], ["html", "redirected", "missing", "missing"])
        e = r["D005"]
        self.assertTrue(e["serves_llms"])
        self.assertFalse(e["serves_full"])
        self.assertFalse(e["spec_h1"])
        self.assertEqual([f["kind"] for f in e["bases"][0]["files"]], ["valid", "robots"])
        self.assertNotIn(("https://eps.dev/llms-full.txt", L.ACCEPT_TEXT), web.calls)

    def test_predictions(self):
        r, _, _ = self.run_census()
        p = L.predictions(list(r.values()))
        self.assertFalse(p["G1"]["held"])
        self.assertEqual(p["P1"]["value"], "2 of 5")
        self.assertFalse(p["P1"]["held"])
        self.assertTrue(p["P2"]["held"])
        self.assertTrue(p["P3"]["held"])
        self.assertEqual(p["P4"]["value"], "1 of 2")
        self.assertTrue(p["P4"]["held"])
        self.assertTrue(p["P5"]["held"])

    def test_retry_429(self):
        answers = [missing(429), resp(LLMS)]
        waits = []

        def fetcher(url, accept=L.ACCEPT_TEXT):
            got = dict(answers.pop(0) if answers else missing())
            got["final_url"] = url
            return got

        frame = L.parse_frame({"projects": [{"id": "D9", "group": "OPEN", "bases": ["https://z.org/"]}]})
        L.census(frame, fetcher, pause=0, sleep=waits.append)
        self.assertEqual(waits, [60])

    def test_parse_frame_rejects_bad_group(self):
        with self.assertRaises(ValueError):
            L.parse_frame({"projects": [{"id": "X", "group": "MAYBE", "bases": ["https://x.org/"]}]})


class TestMain(unittest.TestCase):
    def test_outputs(self):
        web = fake_web()
        with tempfile.TemporaryDirectory() as d:
            code = L.main(["--out-dir", d, "--frame-url", "https://example.org/frame.json", "--no-prereg-check",
                           "--pause", "0"], fetcher=web, sleep=noop)
            self.assertEqual(code, 0)
            for name in ("census.json", "frame.csv", "bases.csv", "probes.csv", "projects.csv", "LLMSPROBE_AUTO.md"):
                self.assertTrue(os.path.exists(os.path.join(d, name)), name)
            with open(os.path.join(d, "projects.csv"), encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 5)
            self.assertEqual(rows[1]["ai_block"], "yes")
            self.assertEqual(rows[3]["ai_block"], "?")
            with open(os.path.join(d, "LLMSPROBE_AUTO.md"), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("| BAN | 1 | 1 | 0 |", text)
            self.assertIn("| ALL | 5 | 5 | 2 |", text)
            with open(os.path.join(d, "census.json"), encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["version"], L.VERSION)
            self.assertIn("P5", data["predictions_auto"])

    def test_waits_for_prereg(self):
        web = fake_web()
        code = L.main(["--out-dir", "unused", "--wait-prereg-minutes", "1"], fetcher=web,
                      opener=lambda req: b"[]", sleep=noop)
        self.assertEqual(code, 3)
        self.assertEqual(web.calls, [])

    def test_prereg_commit(self):
        commits = [{"sha": "b", "commit": {"committer": {"date": "2026-11-08T03:00:00Z"}}},
                   {"sha": "a", "commit": {"committer": {"date": "2026-11-08T02:50:00Z"}}}]
        got = L.prereg_commit(L.PREREG_PATH, opener=lambda req: json.dumps(commits).encode())
        self.assertEqual(got["committed_at"], "2026-11-08T02:50:00Z")
        self.assertEqual(got["sha"], "a")


if __name__ == "__main__":
    unittest.main()
