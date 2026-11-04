# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Offline tests for docscope.py (no network). Run: python -m unittest -v test_docscope"""
import csv
import json
import os
import tempfile
import unittest

import docscope

RAW = "https://raw.githubusercontent.com/o/r/HEAD/"
CONTRIB = ("Thanks for helping!\n\nAI tools are welcome for docs, but\nAI-generated code must be disclosed.\n"
           "See our [AI policy](docs/ai-use.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).\n")
AIUSE = "# AI use\n\nAll contributions made with AI must be disclosed in the PR.\n"
WEB = ("<html><body><p>We do not accept AI-generated patches.</p><p><a href=\"/ai-policy\">Our AI policy</a></p>"
       "<script>var AI=1;</script></body></html>")
FRAME = json.dumps([
    {"project": "Proj", "repo": "o/r", "stance": "neutral", "source_url": "https://github.com/o/r"},
    {"project": "Web", "repo": "", "stance": "ban", "source_url": "https://web.example/policy"}])
PAGES = {
    docscope.FRAME_URL: (FRAME, "text/plain; charset=utf-8"),
    RAW + "CONTRIBUTING.md": (CONTRIB, "text/plain; charset=utf-8"),
    RAW + "docs/ai-use.md": (AIUSE, "text/plain; charset=utf-8"),
    "https://web.example/policy": (WEB, "text/html; charset=utf-8"),
    "https://web.example/ai-policy": ("<p>No AI.</p>", "text/html"),
}


def fake_fetch(url):
    if url in PAGES:
        text, ctype = PAGES[url]
        return {"status": 200, "tls": "verified", "final_url": url, "ctype": ctype, "text": text, "error": None}
    return {"status": 404, "tls": "verified", "final_url": url, "ctype": "", "text": None,
            "error": "HTTP Error 404: Not Found"}


def opener_ok(req):
    return json.dumps([{"sha": "abc123", "commit": {"committer": {"date": "2026-11-04T16:00:00Z"}}}]).encode("utf-8")


def opener_missing(req):
    return b"[]"


def S(kind, rule, docs, code, generic):
    return {"kind": kind, "rule": bool(rule), "docs": bool(docs), "code": bool(code), "generic": bool(generic),
            "sentence": "x"}


class TextTests(unittest.TestCase):
    def test_wrapped_markdown_lines_are_joined(self):
        raw = "Use of AI\ntools must be\ndisclosed.\n\n- item one\n- item two\n  continued\n"
        self.assertEqual(docscope.md_text(raw), "Use of AI tools must be disclosed.\n- item one\n- item two continued")

    def test_comment_text_kept_and_link_text_only(self):
        raw = "See our [AI policy](docs/ai-use.md). <!-- If you used AI, say so -->"
        self.assertEqual(docscope.ai_sentences(docscope.md_text(raw)),
                         ["See our AI policy.", "If you used AI, say so"])

    def test_ai_links(self):
        raw = "See our [AI policy](docs/ai-use.md) and the [Code of Conduct](CODE_OF_CONDUCT.md). [Mail](mailto:a@b)"
        links = docscope.md_links(raw)
        self.assertEqual(links[:2], [("docs/ai-use.md", "AI policy"), ("CODE_OF_CONDUCT.md", "Code of Conduct")])
        self.assertEqual(docscope.ai_links(RAW + "CONTRIBUTING.md", links, set()), [RAW + "docs/ai-use.md"])

    def test_mentions_ai(self):
        self.assertTrue(docscope.mentions_ai("Code written with Copilot must be reviewed."))
        self.assertFalse(docscope.mentions_ai("The aim of Maine said"))


class FlagTests(unittest.TestCase):
    def test_code_rule(self):
        self.assertEqual(docscope.sentence_flags("AI-generated code must be disclosed."),
                         {"docs": False, "code": True, "generic": False, "rule": True})

    def test_docs_generic(self):
        self.assertEqual(docscope.sentence_flags("This applies to all contributions, including documentation."),
                         {"docs": True, "code": False, "generic": True, "rule": False})

    def test_code_of_conduct_is_not_code(self):
        self.assertFalse(docscope.sentence_flags("Read our Code of Conduct before using AI tools.")["code"])

    def test_pr_case_sensitive(self):
        self.assertTrue(docscope.sentence_flags("Open a PR and say if AI helped.")["generic"])
        self.assertFalse(docscope.sentence_flags("Mr. Smith uses AI.")["generic"])


class LabelTests(unittest.TestCase):
    def test_labels(self):
        P = [{"chars": 900, "kind": "repo_file"}]
        self.assertEqual(docscope.classify([{"chars": None, "kind": "repo_file"}], []), "unreachable")
        self.assertEqual(docscope.classify([{"chars": 50, "kind": "press"}], [S("press", 1, 1, 0, 0)]),
                         "unreachable")
        self.assertEqual(docscope.classify(P, []), "no_ai_text")
        self.assertEqual(docscope.classify(P, [S("press", 1, 1, 0, 0)]), "no_ai_text")
        self.assertEqual(docscope.classify(P, [S("repo_file", 0, 1, 0, 0)]), "ai_text_no_rule_cue")
        code = [S("repo_file", 1, 0, 1, 0)]
        self.assertEqual(docscope.classify(P, code), "code_only")
        self.assertEqual(docscope.classify(P, code + [S("web", 1, 0, 0, 1)]), "generic")
        self.assertEqual(docscope.classify(P, code + [S("web", 1, 0, 0, 1), S("followed", 1, 1, 0, 0)]),
                         "docs_named")
        self.assertEqual(docscope.classify(P, [S("repo_file", 1, 0, 0, 0)]), "other")


class FrameTests(unittest.TestCase):
    def test_source_kinds(self):
        k = docscope.source_kind
        self.assertEqual(k("https://github.com/apache/airflow"), ("repo_home", None))
        self.assertEqual(k("https://github.com/vercel/ai/blob/main/CONTRIBUTING.md"),
                         ("repo_file", "https://raw.githubusercontent.com/vercel/ai/main/CONTRIBUTING.md"))
        raw = "https://raw.githubusercontent.com/ghostty-org/ghostty/main/AI_POLICY.md"
        self.assertEqual(k(raw), ("repo_file", raw))
        self.assertEqual(k("https://github.com/honojs/hono/commit/d4542eeb"), ("github_page", None))
        self.assertEqual(k("https://www.theregister.com/a/5281851"), ("press", "https://www.theregister.com/a/5281851"))
        self.assertEqual(k("https://www.kubernetes.dev/docs/guide/pull-requests/#ai-guidance"),
                         ("web", "https://www.kubernetes.dev/docs/guide/pull-requests/"))
        self.assertEqual(k(""), ("none", None))

    def test_parse_frame_and_targets(self):
        rows = docscope.parse_frame(json.loads(FRAME))
        self.assertEqual([r["id"] for r in rows], ["D001", "D002"])
        self.assertEqual([r["source_kind"] for r in rows], ["repo_home", "web"])
        t = docscope.targets(rows[0])
        self.assertEqual(len(t), len(docscope.REPO_FILES))
        self.assertEqual(t[0], ("repo_file", RAW + "CONTRIBUTING.md"))
        self.assertEqual(docscope.targets(rows[1]), [("web", "https://web.example/policy")])


class CensusTests(unittest.TestCase):
    def test_census(self):
        rows = docscope.parse_frame(json.loads(FRAME))
        results, texts = docscope.census(rows, fake_fetch, pause=0)
        a, b = results
        self.assertEqual(len(a["pages"]), len(docscope.REPO_FILES) + 1)
        self.assertEqual(a["own_texts_read"], 2)
        self.assertEqual(a["followed"], [{"from": RAW + "CONTRIBUTING.md", "url": RAW + "docs/ai-use.md"}])
        self.assertEqual([s["sentence"] for s in a["ai_sentences"]], [
            "AI tools are welcome for docs, but AI-generated code must be disclosed.",
            "See our AI policy and the Code of Conduct.",
            "# AI use",
            "All contributions made with AI must be disclosed in the PR."])
        self.assertEqual(a["auto_label"], "docs_named")
        self.assertEqual(len(b["pages"]), 2)
        self.assertEqual([s["sentence"] for s in b["ai_sentences"]],
                         ["We do not accept AI-generated patches.", "Our AI policy", "No AI."])
        self.assertEqual(b["auto_label"], "code_only")

    def test_retries_rate_limit(self):
        calls, slept = [], []

        def flaky(url):
            calls.append(url)
            if len(calls) == 1:
                return {"status": 429, "tls": "verified", "final_url": url, "ctype": "", "text": None,
                        "error": "HTTP Error 429: Too Many Requests"}
            return fake_fetch(url)

        rows = docscope.parse_frame(json.loads(FRAME))[1:]
        results, _ = docscope.census(rows, flaky, pause=0, sleep=slept.append)
        self.assertEqual(slept, [60])
        self.assertTrue(results[0]["pages"][0]["retried_429"])
        self.assertFalse(results[0]["pages"][1]["retried_429"])
        self.assertEqual(results[0]["auto_label"], "code_only")

    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc = docscope.main(["--out-dir", tmp, "--pause", "0", "--wait-prereg-minutes", "5"],
                               fetcher=fake_fetch, opener=opener_ok, sleep=lambda s: None)
            self.assertEqual(rc, 0)
            with open(os.path.join(tmp, "census.json"), encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["prereg"]["committed_at"], "2026-11-04T16:00:00Z")
            self.assertEqual([p["auto_label"] for p in data["projects"]], ["docs_named", "code_only"])
            with open(os.path.join(tmp, "sentences.csv"), newline="", encoding="utf-8") as fh:
                self.assertEqual(len(list(csv.reader(fh))), 1 + 4 + 3)
            self.assertTrue(os.path.exists(os.path.join(tmp, "DOCSCOPE_AUTO.md")))
            self.assertFalse(os.path.exists(os.path.join(tmp, "pages")))

    def test_waits_then_stops_without_prereg(self):
        slept = []
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out")
            rc = docscope.main(["--out-dir", out, "--pause", "0", "--wait-prereg-minutes", "1"],
                               fetcher=fake_fetch, opener=opener_missing, sleep=slept.append)
            self.assertEqual(rc, 3)
            self.assertEqual(slept, [120])
            self.assertFalse(os.path.exists(os.path.join(out, "census.json")))


if __name__ == "__main__":
    unittest.main()
