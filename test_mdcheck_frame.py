# SPDX-License-Identifier: Apache-2.0
"""Offline tests for mdcheck_frame.py (study 11's runner).

Run: python -m unittest -v test_mdcheck_frame

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his
name. Apache-2.0.
"""
import unittest

import mdcheck_frame as m

NETLIFY = "https://docs.netlify.com/resources/troubleshooting/fix-a-failed-deploy/"
K7_URL = ("https://docs.cloud.google.com/compute/docs/instances/sql-server/"
          "configure-failover-cluster-instance-with-multi-writer")
POPSQL = "https://devcenter.heroku.com/articles/popsql"


class FakeTool:
    """Stands in for md_copy_check: ERR gives an error, WARN a warning, INFO an info."""

    @staticmethod
    def looks_like_markdown(status, ctype, text):
        return status == 200 and bool(text)

    @staticmethod
    def check_text(text):
        found = []
        if "ERR" in text:
            found.append({"code": "component-placeholder", "severity": "error", "line": 1, "text": "ERR"})
        if "WARN" in text:
            found.append({"code": "empty-section", "severity": "warning", "line": 2, "text": "## WARN"})
        if "INFO" in text:
            found.append({"code": "dangling-lead-in", "severity": "info", "line": 3, "text": "lead-in:"})
        return found, len(text.split())


def fake_fetcher(pages):
    def fetch(url, accept):
        if url in pages:
            return 200, "text/markdown", pages[url]
        return 404, "", ""
    return fetch


def frame_rows():
    rows = [
        (NETLIFY, "a tip title then the placeholder ERR"),
        (K7_URL, "a lead-in INFO and other text"),
        (POPSQL, "The PopSQL add-on is currently in beta."),
        ("https://example.com/one", "fine words only"),
        ("https://example.com/two", "a heading WARN here"),
        ("https://example.com/three", None),
    ]
    frame, pages = [], {}
    for i, (url, text) in enumerate(rows):
        frame.append({"site": "s%d" % i, "url": url, "method": "accept", "md_url": url, "idx": i})
        if text is not None:
            pages[url] = text
    return frame, pages


class MarkerTests(unittest.TestCase):
    def test_norm_handles_markdown(self):
        self.assertTrue(m.has_marker("To help you control costs for [Agent Runners](https://x.y/z)",
                                     "control costs for Agent"))
        self.assertTrue(m.has_marker("Volumes attached to\nactive sandboxes cannot be removed",
                                     "Volumes attached to active sandboxes"))
        self.assertTrue(m.has_marker("Create a `static\\-analysis.datadog.yml` file",
                                     "static-analysis.datadog.yml"))
        self.assertTrue(m.has_marker("If you don’t plan to keep them, **create a project instead of "
                                     "selecting an existing project**.",
                                     "create a project instead of selecting an existing project"))
        self.assertFalse(m.has_marker("> **Snippet** component (self-closing)", "control costs for Agent"))

    def test_known_pages(self):
        urls = [k[2] for k in m.KNOWN]
        self.assertEqual(len(urls), 10)
        self.assertEqual(len(set(urls)), 10)
        self.assertEqual(sum(1 for k in m.KNOWN if k[1] == "trace"), 7)
        self.assertEqual(sum(1 for k in m.KNOWN if k[1] == "notrace"), 3)
        self.assertEqual(m.group_of(NETLIFY), ("K1", "trace", "control costs for Agent"))
        self.assertEqual(m.group_of("https://example.com/"), ("", "other", ""))


class FrameTests(unittest.TestCase):
    def test_read_frame_keeps_row_numbers(self):
        text = ("site,url,method,md_url,counted\n"
                "a,https://a/1,accept,https://a/1,True\n"
                "a,https://a/2,accept,https://a/2,False\n"
                "b,https://b/3,suffix,https://b/3.md,True\n")
        frame = m.read_frame(text)
        self.assertEqual([r["idx"] for r in frame], [0, 2])
        self.assertEqual(frame[1]["url"], "https://b/3")

    def test_copy_request(self):
        self.assertEqual(m.copy_request({"url": "https://b/3", "method": "suffix", "md_url": "https://b/3.md"}),
                         ("https://b/3.md", m.ACCEPT_SUFFIX))
        self.assertEqual(m.copy_request({"url": "https://a/1", "method": "accept", "md_url": "https://a/1"}),
                         ("https://a/1", m.ACCEPT_MD))


class MeasureAndGradeTests(unittest.TestCase):
    def setUp(self):
        frame, pages = frame_rows()
        self.results, self.findings = m.measure(frame, FakeTool, None, fake_fetcher(pages), None, 0)

    def test_measure(self):
        r = {x["url"]: x for x in self.results}
        self.assertEqual(len(self.results), 6)
        self.assertEqual(len(self.findings), 3)
        self.assertTrue(r[NETLIFY]["flagged"])
        self.assertIs(r[NETLIFY]["marker_present"], False)
        self.assertEqual(r[NETLIFY]["known_id"], "K1")
        self.assertFalse(r[K7_URL]["flagged"])
        self.assertEqual(r[K7_URL]["infos"], 1)
        self.assertIs(r[POPSQL]["marker_present"], True)
        self.assertEqual(r["https://example.com/two"]["codes"], "empty-section")
        self.assertFalse(r["https://example.com/three"]["got_copy"])
        self.assertEqual(r["https://example.com/three"]["status"], 404)

    def test_grade(self):
        g = m.grade(self.results, self.findings)
        self.assertEqual(g["gates"]["G1"], {"copies": 5, "frame": 6, "passed": False})
        p = g["predictions"]
        self.assertEqual(p["P1"]["still_broken"], ["K1", "K7"])
        self.assertEqual(p["P1"]["caught"], ["K1"])
        self.assertTrue(p["P1"]["held"])
        self.assertTrue(p["P2"]["held"])
        self.assertEqual(p["P3"]["fixed"], ["N1"])
        self.assertIsNone(p["P3"]["held"])
        self.assertEqual((p["P4"]["flagged"], p["P4"]["others"]), (1, 2))
        self.assertFalse(p["P4"]["held"])
        self.assertEqual(p["P5"]["pages_by_warning_code"], {"empty-section": 1})
        self.assertTrue(p["P5"]["held"])
        self.assertEqual(p["P7"]["error_pages"], 0)
        self.assertTrue(p["P7"]["held"])
        self.assertIn("https://example.com/three", g["descriptive"]["no_copy"])

    def test_sample_and_auto(self):
        sample = m.draw_sample(self.results)
        self.assertEqual([(s["why"], s["url"]) for s in sample],
                         [("warning-sample", "https://example.com/two")])
        self.assertEqual(m.draw_sample(self.results), sample)
        meta = {"version": m.VERSION, "tool_version": "0.1.0", "tool_sha256": "0" * 64,
                "read_started": "t0", "finished": "t1"}
        text = m.auto_md(meta, m.grade(self.results, self.findings))
        self.assertIn("G1: 5 of 6 pages have a copy (FAILED)", text)
        self.assertIn("P7: 0 other pages with an error: held.", text)


class HtmlTests(unittest.TestCase):
    def test_html_to_text_and_context(self):
        page = ("<h3>401: Not authorized</h3><p>Body text here</p>"
                "<script>var a = '<h3>';</script><p>Next &amp; last</p>")
        text = m.html_to_text(page)
        self.assertIn("401: Not authorized\nBody text here", text)
        self.assertIn("Next & last", text)
        self.assertNotIn("var a", text)
        self.assertTrue(m.context_after(text, m.heading_text("### 401: Not authorized")).startswith("Body text here"))
        self.assertEqual(m.context_after(text, "Not on the page"), "")

    def test_heading_text(self):
        self.assertEqual(m.heading_text("## Overview{% #overview %}"), "Overview")
        self.assertEqual(m.heading_text("### [Project setup](#setup) ###"), "Project setup")
        self.assertEqual(m.heading_text("#### `sbx volume rm`"), "sbx volume rm")

    def test_contexts_skip_info(self):
        findings = [{"idx": 4, "code": "empty-section", "severity": "warning", "line": 2, "text": "## Usage"},
                    {"idx": 4, "code": "dangling-lead-in", "severity": "info", "line": 3, "text": "x:"}]
        sample = [{"why": "warning-sample", "site": "s", "idx": 4, "url": "https://example.com/two"}]

        def fetch(url, accept):
            return 200, "text/html", "<h2>Usage</h2><p>Run it.</p>"
        rows = m.fetch_contexts(sample, findings, None, None, 0, fetch)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["html_context"], "Run it.")
        self.assertTrue(rows[0]["html_ok"])


if __name__ == "__main__":
    unittest.main()
