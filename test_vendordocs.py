# Copyright 2026 Munim, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
"""Offline tests for vendordocs.py (study 9). No network: every fetch is a fake."""

import json
import os
import shutil
import tempfile
import unittest

import vendordocs as vd

EX = vd._site("ex", "Example", "Example", "https://docs.example.com/", ["docs.example.com"], r"^/")
VER = vd._site("ver", "Vercel-like", "V", "https://v.example.com/docs", ["v.example.com"], r"^/docs(?:/|$)")


class Fake(object):
    """url -> (status, content type, body); a (url, accept) key wins over a url key."""

    def __init__(self, table):
        self.table = table
        self.calls = []

    def __call__(self, url, accept, limit=vd.MAX_BYTES):
        self.calls.append((url, accept))
        got = self.table.get((url, accept), self.table.get(url))
        if got is None:
            return 404, "", url, b""
        st, ct, body = got
        return st, ct, url, body.encode("utf-8") if isinstance(body, str) else body


def nosleep(_s):
    return None


def pg(site, **kw):
    row = {c: "" for c in vd.PAGE_COLUMNS}
    row.update(site=site, readable=True, blocked=False, note_html=False, note_md=False, md_accept=False,
               md_suffix=False)
    row.update(kw)
    return row


def srow(sid, readable, label=0, note=0, llms=False, md=0):
    return {"id": sid, "readable": readable, "label_pages": label, "note_pages": note, "llms_txt": llms,
            "md_pages": md}


ROBOTS = ("User-agent: *\nDisallow: /secret\nSitemap: https://docs.example.com/sm.xml\n"
          "Content-Signal: ai-train=no\n")
PAGE_A = ('<html><head><meta name="ai-usage" content="ai-assisted"></head><body><p>Intro.</p>'
          '<p>This page was written with the help of AI tools.</p></body></html>')
MD_A = "---\ntitle: A\nai-usage: ai-assisted\n---\n# A\n\nText.\n"
PAGE_PLAIN = "<!DOCTYPE html><html><body><p>Plain page.</p></body></html>"
DEVBLOGS = ("<html><body><div>AI-assisted content. This article was partially created with the help of AI."
            "</div><p>Body.</p></body></html>")


class TestUrls(unittest.TestCase):
    def test_in_scope(self):
        self.assertTrue(vd.in_scope("https://docs.example.com/get-started/", EX))
        self.assertTrue(vd.in_scope("https://docs.example.com/en-us/a", EX))
        self.assertFalse(vd.in_scope("https://docs.example.com/ja/get-started/", EX))
        self.assertFalse(vd.in_scope("https://docs.example.com/a?x=1", EX))
        self.assertFalse(vd.in_scope("https://docs.example.com/guide.pdf", EX))
        self.assertFalse(vd.in_scope("https://other.example.com/a", EX))
        self.assertTrue(vd.in_scope("https://v.example.com/docs/functions", VER))
        self.assertTrue(vd.in_scope("https://v.example.com/docs", VER))
        self.assertFalse(vd.in_scope("https://v.example.com/pricing", VER))
        gcloud = [s for s in vd.SITES if s["id"] == "gcloud"][0]
        self.assertTrue(vd.in_scope("https://cloud.google.com/go/docs/setup", gcloud))
        self.assertFalse(vd.in_scope("https://cloud.google.com/products/compute", gcloud))

    def test_frame(self):
        self.assertEqual(len(vd.SITES), 20)
        self.assertEqual(len(set(s["id"] for s in vd.SITES)), 20)
        for s in vd.SITES:
            self.assertTrue(vd.in_scope(s["root"].rstrip("/") + "/x", s) or s["id"] in ("heroku", "newrelic"),
                            s["id"])

    def test_md_suffix_url(self):
        self.assertEqual(vd.md_suffix_url("https://d.example.com/a/b/"), "https://d.example.com/a/b.md")
        self.assertEqual(vd.md_suffix_url("https://d.example.com/x.html"), "https://d.example.com/x.html.md")
        self.assertEqual(vd.md_suffix_url("https://d.example.com/"), "https://d.example.com/index.md")
        self.assertEqual(vd.md_suffix_url("https://d.example.com/a?q=1#f"), "https://d.example.com/a.md")

    def test_parse_sitemap(self):
        idx = ('<?xml version="1.0"?><sitemapindex xmlns="x"><sitemap><loc>https://x/a.xml</loc></sitemap>'
               '<sitemap><loc> https://x/b.xml?x=1&amp;y=2 </loc></sitemap></sitemapindex>')
        self.assertEqual(vd.parse_sitemap(idx), ("index", ["https://x/a.xml", "https://x/b.xml?x=1&y=2"]))
        cdata = "<urlset><url><loc><![CDATA[https://x/p]]></loc></url></urlset>"
        self.assertEqual(vd.parse_sitemap(cdata), ("urlset", ["https://x/p"]))
        self.assertEqual(vd.parse_sitemap("https://x/1\nhttps://x/2\n"), ("urlset", ["https://x/1", "https://x/2"]))
        self.assertEqual(vd.parse_sitemap("<html><body>no</body></html>"), ("", []))


class TestDetectors(unittest.TestCase):
    def test_meta_label(self):
        self.assertEqual(vd.meta_label({"description": "Use AI-generated content in your app",
                                        "ms.ai-usage": "ai-generated"}), ("ms.ai-usage", "ai-generated"))
        self.assertEqual(vd.meta_label({"description": "Use AI-generated content", "tags": "ai-generated"}),
                         ("", ""))
        self.assertEqual(vd.meta_label({"generator": "Hugo", "x-content-origin": "AI-generated"}),
                         ("x-content-origin", "AI-generated"))
        self.assertEqual(vd.meta_label({"robots": "ai-generated-images"}), ("", ""))
        self.assertEqual(vd.meta_label({"openai-usage": "x"}), ("", ""))

    def test_disclosure(self):
        text = ("AI-assisted content. This article was partially created with the help of AI. "
                "An author reviewed and revised the content as needed.")
        self.assertEqual(vd.disclosure(text), "AI-assisted content.")
        self.assertEqual(vd.disclosure("Firebase lets you build AI features. Generate text with Gemini."), "")

    def test_read_html(self):
        page = ('<html><head><meta name="ms.ai-usage" content="ai-assisted">'
                '<meta property="og:description" content="AI-generated content demo"></head><body>'
                '<script>var s="generated by AI";</script><div class="note">AI-assisted content. This article '
                'was partially created with the help of AI.</div></body></html>')
        h = vd.read_html(page)
        self.assertEqual((h["key"], h["value"]), ("ms.ai-usage", "ai-assisted"))
        self.assertEqual(h["note"], "AI-assisted content.")
        self.assertTrue(h["raw"])
        self.assertFalse(h["raw_label"])

    def test_markdown(self):
        md = "---\ntitle: Register an app\nai-usage: ai-assisted\nsource_path: docs/x.md\n---\n# Register\n\nText.\n"
        self.assertTrue(vd.md_ok(200, "text/markdown; charset=utf-8", md))
        m = vd.read_md(md)
        self.assertEqual((m["key"], m["value"]), ("ai-usage", "ai-assisted"))
        self.assertEqual(m["keys"], ["title", "ai-usage", "source_path"])
        self.assertEqual(m["note"], "")
        self.assertFalse(vd.md_ok(200, "text/html", "<html>"))
        self.assertTrue(vd.md_ok(200, "text/plain", "# Title\nx"))
        self.assertFalse(vd.md_ok(200, "text/plain", "Not found"))
        self.assertFalse(vd.md_ok(404, "text/markdown", md))
        self.assertFalse(vd.md_ok(200, "", "<!DOCTYPE html><html>"))

    def test_llms_valid(self):
        self.assertTrue(vd.llms_valid(200, "text/plain", "# Docs\n> x"))
        self.assertTrue(vd.llms_valid(200, "text/plain", "\n\n# Docs"))
        self.assertFalse(vd.llms_valid(200, "text/html", "# Docs"))
        self.assertFalse(vd.llms_valid(200, "text/plain", "User-agent: *"))
        self.assertFalse(vd.llms_valid(404, "text/plain", "# Docs"))

    def test_blocked(self):
        self.assertTrue(vd.blocked(403, ""))
        self.assertTrue(vd.blocked(200, "<html><head><title>Just a moment...</title></head></html>"))
        self.assertFalse(vd.blocked(200, PAGE_PLAIN))


class TestCollect(unittest.TestCase):
    def test_robots(self):
        fake = Fake({"https://docs.example.com/robots.txt": (200, "text/plain", ROBOTS)})
        robots_for = vd.make_robots(fake, nosleep)
        rb = robots_for("https://docs.example.com")
        self.assertTrue(rb["allowed"]("https://docs.example.com/a"))
        self.assertFalse(rb["allowed"]("https://docs.example.com/secret/c"))
        self.assertEqual(rb["sitemaps"], ["https://docs.example.com/sm.xml"])
        self.assertEqual(rb["signals"], ["ai-train=no"])
        robots_for("https://docs.example.com")
        self.assertEqual(len(fake.calls), 1)

    def test_sitemap_index(self):
        fake = Fake({
            "https://docs.example.com/robots.txt": (200, "text/plain", ROBOTS),
            "https://docs.example.com/sm.xml": (200, "application/xml", '<sitemapindex><sitemap><loc>'
                                                "https://docs.example.com/docs-1.xml</loc></sitemap></sitemapindex>"),
            "https://docs.example.com/docs-1.xml": (200, "application/xml", (
                "<urlset><url><loc>https://docs.example.com/a</loc></url>"
                "<url><loc>https://docs.example.com/b#x</loc></url>"
                "<url><loc>https://docs.example.com/ja/a</loc></url>"
                "<url><loc>https://other.com/z</loc></url>"
                "<url><loc>https://docs.example.com/secret/c</loc></url></urlset>")),
        })
        urls, method, read, _log = vd.collect_urls(EX, fake, nosleep, vd.make_robots(fake, nosleep), min_pool=3)
        self.assertEqual(urls, {"https://docs.example.com/a", "https://docs.example.com/b",
                                "https://docs.example.com/secret/c"})
        self.assertEqual(method, "sitemap")
        self.assertEqual(read, 4)

    def test_crawl_fallback(self):
        fake = Fake({
            "https://docs.example.com/": (200, "text/html", '<html><body><a href="/x">x</a><a href="y/">y</a>'
                                          '<a href="https://other.com/q">q</a><a href="/x#frag">x2</a></body></html>'),
            "https://docs.example.com/x": (200, "text/html", '<html><a href="/z">z</a></html>'),
        })
        urls, method, read, _log = vd.collect_urls(EX, fake, nosleep, vd.make_robots(fake, nosleep), min_pool=30)
        self.assertEqual(urls, {"https://docs.example.com/x", "https://docs.example.com/y/",
                                "https://docs.example.com/z"})
        self.assertEqual(method, "crawl")
        # EX's docs root is the host root, so "<host>/sitemap.xml" and "<docs root>/sitemap.xml" are the
        # same URL and are tried once: two distinct sitemap files are read (both 404), not three.
        self.assertEqual(read, 2)
        tried = [u for u, _a in fake.calls if u.endswith(".xml")]
        self.assertEqual(sorted(tried), ["https://docs.example.com/sitemap.xml",
                                         "https://docs.example.com/sitemap_index.xml"])

    def test_draw(self):
        urls = set("https://docs.example.com/p%02d" % i for i in range(50))
        a = vd.draw(urls, EX, 30)
        self.assertEqual(len(a), 30)
        self.assertEqual(a, sorted(a))
        self.assertEqual(a, vd.draw(urls, EX, 30))
        self.assertTrue(set(a) <= urls)
        self.assertEqual(vd.draw(set(list(urls)[:5]), EX, 30), sorted(list(urls)[:5]))


class TestSummary(unittest.TestCase):
    def test_predictions(self):
        sites = [srow("a", 2, label=1, llms=True, md=2), srow("b", 2)]
        pages = [pg("a", html_ai_key="ai-usage", html_ai_value="ai-assisted"), pg("a"), pg("b"), pg("b")]
        controls = [{"control": "control-md", "md_ai_key": "ai-usage"}, {"control": "control-note", "note_html": True}]
        s = vd.summarise(sites, pages, controls, readable_min=1, gate_sites=2)
        p = s["predictions"]
        self.assertEqual((p["P1"]["k"], p["P1"]["n"], p["P1"]["held"]), (1, 2, True))
        self.assertEqual((p["P2"]["k"], p["P2"]["held"]), (0, True))
        self.assertEqual((p["P3"]["k"], p["P3"]["n"], p["P3"]["held"]), (1, 4, False))
        self.assertEqual((p["P4"]["k"], p["P4"]["held"]), (1, False))
        self.assertEqual((p["P5"]["k"], p["P5"]["held"]), (1, False))
        self.assertIsNone(p["P6"]["held"])
        self.assertEqual(s["labels"], {"ai-usage=ai-assisted": 1})
        controls[0]["md_ai_key"] = ""
        s = vd.summarise(sites, pages, controls, readable_min=1, gate_sites=2)
        self.assertIsNone(s["predictions"]["P1"]["held"])
        self.assertIsNone(s["predictions"]["P3"]["held"])

    def test_prereg(self):
        ok = vd.prereg_commit("x", lambda req: b'[{"sha": "abc", "commit": {"committer": {"date": "2026-11-09T06:00:00Z"}}}]')
        self.assertEqual(ok["committed_at"], "2026-11-09T06:00:00Z")
        none = vd.wait_for_prereg("x", 0, lambda req: b"[]", nosleep)
        self.assertIsNone(none["committed_at"])
        self.assertEqual(none["waited_seconds"], 0)


class TestMain(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp(prefix="vendordocs-test-")

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def test_end_to_end(self):
        fake = Fake({
            "https://docs.example.com/robots.txt": (200, "text/plain", ROBOTS),
            "https://docs.example.com/sm.xml": (200, "application/xml", (
                "<urlset><url><loc>https://docs.example.com/a</loc></url>"
                "<url><loc>https://docs.example.com/b</loc></url>"
                "<url><loc>https://docs.example.com/secret/c</loc></url></urlset>")),
            "https://docs.example.com/a": (200, "text/html; charset=utf-8", PAGE_A),
            ("https://docs.example.com/a", "text/markdown"): (200, "text/markdown", MD_A),
            "https://docs.example.com/b": (200, "text/html", PAGE_PLAIN),
            "https://docs.example.com/b.md": (200, "text/plain", "# B\nPlain.\n"),
            "https://docs.example.com/llms.txt": (200, "text/plain", "# Example docs\n> x\n"),
            "https://learn.example.com/c1": (200, "text/html", PAGE_PLAIN),
            ("https://learn.example.com/c1", "text/markdown"): (200, "text/markdown", MD_A),
            "https://blog.example.com/c2": (200, "text/html", DEVBLOGS),
        })
        controls = [("control-md", "https://learn.example.com/c1"), ("control-note", "https://blog.example.com/c2")]
        rc = vd.main(["--out-dir", self.out, "--no-prereg-check", "--per-site", "3"], fetch=fake, sleep=nosleep,
                     sites=[EX], controls=controls)
        self.assertEqual(rc, 0)
        for name in ("sites.csv", "pages.csv", "vendordocs.json", "VENDORDOCS_AUTO.md"):
            self.assertTrue(os.path.exists(os.path.join(self.out, name)), name)
        with open(os.path.join(self.out, "vendordocs.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        row = data["sites"][0]
        self.assertEqual((row["pool"], row["sampled"], row["readable"], row["method"]), (3, 3, 2, "sitemap"))
        self.assertEqual((row["md_pages"], row["md_accept_pages"], row["md_suffix_pages"]), (2, 1, 1))
        self.assertEqual((row["label_pages"], row["note_pages"], row["llms_txt"], row["llms_full"]), (1, 1, True, False))
        self.assertEqual((row["robots_status"], row["content_signal"]), (200, "ai-train=no"))
        g = data["summary"]["gates"]
        self.assertEqual((g["G1"]["passed"], g["G2"]["passed"], g["G3"]["passed"]), (False, True, True))
        self.assertIsNone(data["summary"]["predictions"]["P1"]["held"])
        self.assertNotIn(("https://docs.example.com/secret/c", vd.ACCEPT_HTML), fake.calls)


if __name__ == "__main__":
    unittest.main()
