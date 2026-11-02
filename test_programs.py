# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Offline tests for programs.py (no network). Run: python -m unittest -v test_programs"""
import csv
import json
import os
import tempfile
import unittest

import programs

LISTING_MD = """# Paid Community Writer Programs

> **Status key:** ✅ Active | ⏸️ Paused
>
> *Last audited: July 2026*


## ✅ Active

- [Alpha](https://alpha.example/write) - $300 per article
  > Tutorials about Alpha.

- [Beta Docs](https://beta.example/w) (apply via email) - Up to $500 per piece
  > Guides. AI-written drafts are not accepted.


## ⏸️ Paused

- [Gamma](https://gamma.example/voices) - $650 per piece
  > Not accepting new applications.


## Resources with similar lists

- [Who Pays](https://whopays.example/) - a list
"""

ALPHA = ("<html><body><nav><a href=\"/guidelines\">Writer guidelines</a> "
         "<a href=\"https://other.example/terms\">Terms</a> <a href=\"/blog\">Blog</a></nav>"
         "<p>We pay $300 per article. Submissions must be your own work and AI-generated content will be "
         "rejected.</p></body></html>")
ALPHA_GUIDE = "<html><body><p>You may use Grammarly or other AI tools for editing.</p></body></html>"
GAMMA = ("<html><body><p>We are not accepting new applications at this time.</p><p>"
         + "Developer stories and community. " * 20 + "</p></body></html>")


def page(text, status=200, url=None):
    return {"status": status, "tls": "verified", "final_url": url, "text": text, "error": None}


PAGES = {
    programs.LISTING_URL: page(LISTING_MD),
    "https://alpha.example/write": page(ALPHA, url="https://alpha.example/write"),
    "https://alpha.example/guidelines": page(ALPHA_GUIDE, url="https://alpha.example/guidelines"),
    "https://gamma.example/voices": page(GAMMA, url="https://gamma.example/voices"),
}


def fake_fetch(url):
    if url == "https://beta.example/w":
        return {"status": 403, "tls": "verified", "final_url": url, "text": None, "error": "HTTP Error 403"}
    if url in PAGES:
        return PAGES[url]
    return {"status": 404, "tls": "verified", "final_url": url, "text": None, "error": "HTTP Error 404"}


def opener_ok(req):
    return json.dumps([{"sha": "abc123", "commit": {"committer": {"date": "2026-11-02T12:30:00Z"}}}]).encode("utf-8")


def opener_missing(req):
    return b"[]"


class ParseListing(unittest.TestCase):
    def test_sections_and_fields(self):
        got = programs.parse_listing(LISTING_MD)
        self.assertEqual([p["id"] for p in got], ["P01", "P02", "P03"])
        self.assertEqual([p["name"] for p in got], ["Alpha", "Beta Docs", "Gamma"])
        self.assertEqual([p["section"] for p in got], ["Active", "Active", "Paused"])
        self.assertEqual(got[0]["url"], "https://alpha.example/write")
        self.assertEqual(got[0]["pay"], "$300 per article")
        self.assertEqual(got[1]["pay"], "(apply via email) - Up to $500 per piece")
        self.assertEqual(got[1]["description"], "Guides. AI-written drafts are not accepted.")
        self.assertEqual(got[2]["description"], "Not accepting new applications.")


class Sentences(unittest.TestCase):
    def test_mentions_ai(self):
        self.assertTrue(programs.mentions_ai("We do not accept AI-generated content."))
        self.assertTrue(programs.mentions_ai("Drafts are checked with Originality.ai before review."))
        self.assertFalse(programs.mentions_ai("The aim of Maine said"))
        self.assertFalse(programs.mentions_ai("SAID"))

    def test_status_sentences(self):
        self.assertEqual(programs.status_sentences("We are no longer paying for articles. Read our blog."),
                         ["We are no longer paying for articles."])


class Classify(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(programs.classify([], []), ("unreachable", None))
        self.assertEqual(programs.classify([{"chars": 100}], []), ("unreadable", None))
        self.assertEqual(programs.classify([{"chars": 900}], []), ("silent", None))
        self.assertEqual(programs.classify([{"chars": 900}], ["We will not use your article to train AI models."]),
                         ("training_only", None))
        self.assertEqual(programs.classify([{"chars": 900}], ["Do not use AI tools at any stage, including editing."]),
                         ("ban", "assisted"))
        self.assertEqual(programs.classify([{"chars": 900}], ["AI-assisted drafts are welcome if you disclose them."]),
                         ("allow_or_conditional", None))


class FollowLinks(unittest.TestCase):
    def test_same_site_rules_links(self):
        links = [("/style-guide", "Style guide"), ("https://alpha.example/faq", "FAQ"),
                 ("https://beta.example/terms", "Terms"), ("/files/rules.pdf", "Guidelines PDF"),
                 ("mailto:x@y", "Contact"), ("/about", "About us")]
        follow, docs = programs.follow_links("https://www.alpha.example/write", links)
        self.assertEqual(follow, ["https://www.alpha.example/style-guide", "https://alpha.example/faq"])
        self.assertEqual(docs, ["https://www.alpha.example/files/rules.pdf"])


class Main(unittest.TestCase):
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc = programs.main(["--out-dir", tmp, "--pause", "0", "--wait-prereg-minutes", "5"],
                               fetcher=fake_fetch, opener=opener_ok, sleep=lambda s: None)
            self.assertEqual(rc, 0)
            with open(os.path.join(tmp, "census.json"), encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["prereg"]["committed_at"], "2026-11-02T12:30:00Z")
            by_id = {r["id"]: r for r in data["programs"]}
            self.assertEqual(sorted(by_id), ["P01", "P02", "P03"])
            self.assertEqual((by_id["P01"]["auto_label"], by_id["P01"]["auto_scope"]), ("ban", "generated"))
            self.assertEqual(len(by_id["P01"]["pages"]), 2)
            self.assertTrue(by_id["P01"]["pages"][1]["followed"])
            self.assertEqual(by_id["P02"]["auto_label"], "unreachable")
            self.assertEqual(by_id["P02"]["main_status"], 403)
            self.assertTrue(by_id["P02"]["listing_mentions_ai"])
            self.assertEqual(by_id["P03"]["auto_label"], "silent")
            self.assertTrue(by_id["P03"]["closed_cue"])
            self.assertFalse(by_id["P01"]["closed_cue"])
            with open(os.path.join(tmp, "sentences.csv"), newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual([r["program_id"] for r in rows], ["P01", "P01"])
            with open(os.path.join(tmp, "frame.csv"), newline="", encoding="utf-8") as fh:
                self.assertEqual(len(list(csv.DictReader(fh))), 3)
            self.assertTrue(os.path.exists(os.path.join(tmp, "status.csv")))
            self.assertTrue(os.path.exists(os.path.join(tmp, "CENSUS_AUTO.md")))

    def test_waits_then_stops_without_prereg(self):
        slept = []
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out")
            rc = programs.main(["--out-dir", out, "--pause", "0", "--wait-prereg-minutes", "1"],
                               fetcher=fake_fetch, opener=opener_missing, sleep=slept.append)
            self.assertEqual(rc, 3)
            self.assertEqual(slept, [120])
            self.assertFalse(os.path.exists(os.path.join(out, "census.json")))


if __name__ == "__main__":
    unittest.main()
