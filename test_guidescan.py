# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Offline tests for guidescan.py (no network). Run: python -m unittest -v test_guidescan"""
import json
import os
import tempfile
import unittest

import guidescan as g

PAD = "<p>" + "Plain words for readers. " * 50 + "</p>"


def page(html, ctype="text/html; charset=utf-8", final=None, status=200):
    return {"status": status, "tls": "verified", "final_url": final, "ctype": ctype, "text": html, "error": None}


def missing(status=404):
    return {"status": status, "tls": "verified", "final_url": None, "ctype": "", "text": None,
            "error": "HTTP Error %d" % status}


class FakeWeb:
    def __init__(self, pages):
        self.pages, self.calls = pages, []

    def __call__(self, url):
        self.calls.append(url)
        got = self.pages.get(url)
        if got is None:
            got = missing()
        got = dict(got)
        if got["final_url"] is None:
            got["final_url"] = url
        return got


def noop(_seconds):
    return None


ROOT = "https://docs.example.com/style/"
WORDS = "https://docs.example.com/style/word-list"
ROBOTS = "https://docs.example.com/robots.txt"
SEED_HTML = ('<html><body><h1>Style</h1>' + PAD + '<a href="word-list">Word list</a> <a href="/other/">Other</a> '
             '<a href="guide.pdf">PDF</a> <a href="#top">Top</a> <a href="private">Private</a> '
             '<a href="https://elsewhere.example.org/style/x">X</a></body></html>')
WORDS_HTML = ("<p>AI: spell out artificial intelligence on first mention. Do not use AI as a verb.</p>"
              "<p>Apple: a fruit.</p>")


def guide(**kw):
    d = {"id": "G01", "guide": "Test guide", "publisher": "Example", "group": "COMPANY", "lists": "wtd",
         "seeds": [ROOT], "scopes": [ROOT], "max_pages": 10}
    d.update(kw)
    return d


class TestUrls(unittest.TestCase):
    def test_canon(self):
        self.assertEqual(g.canon("https://Example.COM/a/b?x=1#frag"), "https://example.com/a/b")
        self.assertEqual(g.canon("https://example.com"), "https://example.com/")
        self.assertIsNone(g.canon("mailto:someone@example.com"))
        self.assertIsNone(g.canon(""))

    def test_in_scope(self):
        scopes = [g.canon("https://developers.google.com/style/")]
        self.assertTrue(g.in_scope("https://developers.google.com/style", scopes))
        self.assertTrue(g.in_scope("https://developers.google.com/style/word-list", scopes))
        self.assertFalse(g.in_scope("https://developers.google.com/styleguide", scopes))
        self.assertFalse(g.in_scope("https://developers.google.com/", scopes))

    def test_json_links(self):
        toc = '{"items": [{"href": "welcome/", "toc_title": "W", "children": [{"href" : "a-z/a"}]}]}'
        self.assertEqual(g.json_links(toc), ["welcome/", "a-z/a"])


class TestSentences(unittest.TestCase):
    def test_mentions_ai(self):
        for s in ("Spell out artificial intelligence (AI) on first use.", "Don't paste output from ChatGPT.",
                  "Use machine learning as a noun.", "Publish an llms.txt file.", "AI-generated drafts need review.",
                  "Write prompts for the chatbot."):
            self.assertTrue(g.mentions_ai(s), s)
        for s in ("We said it was the main aim.", "Maine is a state.", "Use the email address field.",
                  "Write for machine translation."):
            self.assertFalse(g.mentions_ai(s), s)

    def test_flags(self):
        by = g.sentence_flags("If you use AI tools to draft content, you must review the output.")
        self.assertEqual(by, {"by_ai": True, "for_ai": False, "rule": True})
        fo = g.sentence_flags("Write responses that a chatbot can read aloud.")
        self.assertTrue(fo["for_ai"])
        self.assertFalse(fo["rule"])

    def test_split(self):
        self.assertEqual(g.ai_sentences("AI: spell it out. Do not use AI as a verb. Apples are red."),
                         ["AI: spell it out.", "Do not use AI as a verb."])


class TestCrawl(unittest.TestCase):
    def test_scope_links_and_sentences(self):
        web = FakeWeb({ROBOTS: missing(404), ROOT: page(SEED_HTML), WORDS: page(WORDS_HTML)})
        results, texts = g.census([guide()], web, pause=0, sleep=noop)
        r = results[0]
        self.assertEqual(web.calls, [ROBOTS, ROOT, WORDS, "https://docs.example.com/style/private"])
        self.assertEqual(r["fetched"], 3)
        self.assertEqual(r["pages_read"], 2)
        self.assertFalse(r["cap_hit"])
        self.assertEqual([s["sentence"] for s in r["ai_sentences"]],
                         ["AI: spell out artificial intelligence on first mention.", "Do not use AI as a verb."])
        self.assertTrue(all(s["term_page"] for s in r["ai_sentences"]))
        self.assertEqual(r["auto_label"], "ai_text")
        self.assertEqual(len(texts), 2)
        kinds = [p["kind"] for p in r["pages"]]
        self.assertEqual(kinds, ["page", "page", "no_text"])

    def test_robots(self):
        rules = page("User-agent: *\nDisallow: /style/private\n", ctype="text/plain")
        web = FakeWeb({ROBOTS: rules, ROOT: page(SEED_HTML), WORDS: page(WORDS_HTML)})
        r = g.census([guide()], web, pause=0, sleep=noop)[0][0]
        self.assertNotIn("https://docs.example.com/style/private", web.calls)
        self.assertEqual([p["kind"] for p in r["pages"]], ["page", "page", "robots"])
        self.assertEqual(r["fetched"], 2)

    def test_cap(self):
        web = FakeWeb({ROBOTS: missing(404), ROOT: page(SEED_HTML), WORDS: page(WORDS_HTML)})
        r = g.census([guide(max_pages=1)], web, pause=0, sleep=noop)[0][0]
        self.assertEqual(r["fetched"], 1)
        self.assertTrue(r["cap_hit"])
        self.assertEqual(r["auto_label"], "no_ai_text")

    def test_unread_and_redirect_out(self):
        web = FakeWeb({ROBOTS: missing(404), ROOT: missing(403)})
        r = g.census([guide()], web, pause=0, sleep=noop)[0][0]
        self.assertEqual(r["auto_label"], "unread")
        self.assertEqual(r["pages"][0]["kind"], "no_text")
        web = FakeWeb({ROBOTS: missing(404), ROOT: page(SEED_HTML, final="https://docs.example.com/home")})
        r = g.census([guide()], web, pause=0, sleep=noop)[0][0]
        self.assertEqual(r["pages"][0]["kind"], "redirect_out")
        self.assertEqual(r["auto_label"], "unread")

    def test_json_toc(self):
        toc_url = "https://docs.example.com/style/toc.json"
        web = FakeWeb({ROBOTS: missing(404), toc_url: page('{"items": [{"href": "word-list"}]}',
                                                           ctype="application/json"),
                       WORDS: page(WORDS_HTML + PAD)})
        r = g.census([guide(seeds=[toc_url])], web, pause=0, sleep=noop)[0][0]
        self.assertEqual([p["kind"] for p in r["pages"]], ["toc", "page"])
        self.assertEqual(len(r["ai_sentences"]), 2)

    def test_parse_frame(self):
        rows = g.parse_frame({"guides": [guide(max_pages=None)]})
        self.assertEqual(rows[0]["max_pages"], g.DEFAULT_MAX_PAGES)
        with self.assertRaises(ValueError):
            g.parse_frame({"guides": [{"id": "G02", "seeds": []}]})


class TestMain(unittest.TestCase):
    def test_wait_prereg(self):
        answers = [b"[]", json.dumps([{"sha": "abc", "commit": {"committer": {"date": "2026-11-07T00:00:00Z"}}}])
                   .encode("utf-8")]
        got = g.wait_for_prereg("x.md", 10, opener=lambda req: answers.pop(0), sleep=noop)
        self.assertEqual(got["committed_at"], "2026-11-07T00:00:00Z")
        self.assertEqual(got["waited_seconds"], 120)

    def test_wait_prereg_gives_up(self):
        out = os.devnull
        code = g.main(["--out-dir", out, "--wait-prereg-minutes", "4"], fetcher=FakeWeb({}),
                      opener=lambda req: b"[]", sleep=noop)
        self.assertEqual(code, 3)

    def test_end_to_end(self):
        frame_url = "https://raw.example.com/frame.json"
        web = FakeWeb({frame_url: page(json.dumps({"guides": [guide()]}), ctype="text/plain"),
                       ROBOTS: missing(404), ROOT: page(SEED_HTML), WORDS: page(WORDS_HTML)})
        commits = json.dumps([{"sha": "abc", "commit": {"committer": {"date": "2026-11-07T00:00:00Z"}}}])
        with tempfile.TemporaryDirectory() as d:
            code = g.main(["--out-dir", d, "--save-text", "--pause", "0", "--frame-url", frame_url],
                          fetcher=web, opener=lambda req: commits.encode("utf-8"), sleep=noop)
            self.assertEqual(code, 0)
            for name in ("census.json", "frame.csv", "pages.csv", "sentences.csv", "GUIDESCAN_AUTO.md"):
                self.assertTrue(os.path.exists(os.path.join(d, name)), name)
            self.assertEqual(len(os.listdir(os.path.join(d, "pages"))), 2)
            with open(os.path.join(d, "sentences.csv"), encoding="utf-8") as fh:
                self.assertEqual(len(fh.read().strip().splitlines()), 3)
            with open(os.path.join(d, "census.json"), encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["prereg"]["committed_at"], "2026-11-07T00:00:00Z")
            self.assertEqual(data["guides"][0]["auto_label"], "ai_text")


if __name__ == "__main__":
    unittest.main()
