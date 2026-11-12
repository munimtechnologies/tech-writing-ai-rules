# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""Offline tests for docsyleak.py (study 14). No network."""

import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("docsyleak", os.path.join(HERE, "docsyleak.py"))
dl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dl)


def site(key, eligible=True, copies=10):
    return {"key": key, "url": "https://%s/" % key, "final_url": "", "status": 200,
            "docsy": eligible, "md_method": "index.md" if eligible else "none",
            "md_home_url": "", "md_ok": eligible, "eligible": eligible, "robots": "ok",
            "pool_source": "sitemap", "pool_size": 50, "sampled": 30, "copies_read": copies,
            "copies_structural": 0, "copies_docsy": 0, "median_markup_share": "", "note": ""}


def page(key, labels=(), share=0.0, structural=0, ok=True):
    return {"site": key, "ok": ok, "docsy_labels": list(labels), "markup_share": share,
            "structural_tags": structural, "labels": {lab: 1 for lab in labels}}


def fixture():
    sites = [site("a"), site("b", copies=12), site("c", copies=5), site("d", eligible=False),
             site("e")]
    pages = []
    pages += [page("a", ["docsy:alert"], 0.10, 3), page("a", ["docsy:alert"], 0.02, 3)]
    pages += [page("a") for _ in range(8)]
    pages += [page("b", ["docsy:alert", "docsy:tabpane"], 0.30, 10),
              page("b", ["docsy:tabpane"], 0.06, 5)]
    pages += [page("b") for _ in range(10)]
    pages += [page("c", ["docsy:card"], 0.5, 9) for _ in range(5)]
    pages += [page("e") for _ in range(10)]
    return sites, pages


class TestFrame(unittest.TestCase):
    def test_frame(self):
        self.assertEqual(len(dl.SITES), 27)
        self.assertEqual(len(set(dl.SITES)), 27)
        self.assertTrue(all(u.startswith("https://") and u.endswith("/") for u in dl.SITES))
        self.assertIn("https://www.docsy.dev/", dl.SITES)

    def test_checker_version_is_fixed(self):
        self.assertEqual(dl.load_leak().VERSION, dl.LEAK_VERSION)

    def test_site_key(self):
        self.assertEqual(dl.site_key("https://agones.dev/site/"), "agones-dev-site")
        self.assertEqual(dl.site_key("https://www.docsy.dev/"), "www-docsy-dev")


class TestDetection(unittest.TestCase):
    def test_alternate_link(self):
        h = ('<head><link rel="alternate" type="text/markdown" href="/index.md" title="Markdown">'
             '<link rel=stylesheet href=x.css></head>')
        self.assertEqual(dl.find_md_alternate(h, "https://www.docsy.dev/"),
                         "https://www.docsy.dev/index.md")
        h2 = "<link href='page.md' type='text/markdown' rel='alternate'>"
        self.assertEqual(dl.find_md_alternate(h2, "https://a.io/docs/"), "https://a.io/docs/page.md")
        h3 = '<link rel="alternate" type="application/rss+xml" href="/index.xml">'
        self.assertIsNone(dl.find_md_alternate(h3, "https://a.io/"))

    def test_docsy(self):
        self.assertTrue(dl.is_docsy('<body class="td-home">'))
        self.assertTrue(dl.is_docsy('<nav class="td-navbar js-navbar-scroll">'))
        self.assertFalse(dl.is_docsy('<body class="home">'))

    def test_markdown_copy(self):
        self.assertTrue(dl.is_markdown_copy(200, "text/markdown; charset=utf-8", "# T\n"))
        self.assertFalse(dl.is_markdown_copy(200, "text/html", "# T\n"))
        self.assertFalse(dl.is_markdown_copy(404, "text/markdown", "# T\n"))
        self.assertFalse(dl.is_markdown_copy(200, "text/plain", "<!DOCTYPE html><html>"))
        self.assertFalse(dl.is_markdown_copy(200, "", "  "))

    def test_md_urls(self):
        self.assertEqual(dl.md_pattern("https://www.docsy.dev/", "https://www.docsy.dev/index.md"),
                         "index")
        self.assertEqual(dl.md_pattern("https://agones.dev/site/", "https://agones.dev/site.md"),
                         "dotmd")
        self.assertEqual(dl.md_for("https://a.io/docs/x/", "index"), "https://a.io/docs/x/index.md")
        self.assertEqual(dl.md_for("https://a.io/docs/x", "index"), "https://a.io/docs/x/index.md")
        self.assertEqual(dl.md_for("https://a.io/docs/x/", "dotmd"), "https://a.io/docs/x.md")


class TestPool(unittest.TestCase):
    def test_sitemaps(self):
        idx = ('<?xml version="1.0"?><sitemapindex><sitemap><loc>https://a.io/en/sitemap.xml'
               '</loc></sitemap></sitemapindex>')
        self.assertEqual(dl.parse_sitemap(idx), ("index", ["https://a.io/en/sitemap.xml"]))
        us = ('<urlset><url><loc>https://a.io/a/?x=1&amp;y=2</loc></url>'
              '<url><loc> https://a.io/b/ </loc></url></urlset>')
        self.assertEqual(dl.parse_sitemap(us), ("urlset", ["https://a.io/a/?x=1&y=2",
                                                           "https://a.io/b/"]))

    def test_filter_default_language_at_root(self):
        urls = ["https://www.example.io/", "https://example.io/docs/a/",
                "https://www.example.io/docs/b", "https://www.example.io/tags/x/",
                "https://www.example.io/blog/page/2/", "https://www.example.io/fr/docs/a/",
                "https://other.io/docs/", "https://www.example.io/docs/c/?q=1"]
        self.assertEqual(dl.filter_pool(urls, "https://www.example.io/"),
                         ["https://www.example.io/", "https://www.example.io/docs/a/"])

    def test_filter_english_in_subfolder(self):
        urls = ["https://k.io/en/docs/", "https://k.io/en/blog/", "https://k.io/zh-cn/docs/",
                "https://k.io/docs-old/"]
        self.assertEqual(dl.filter_pool(urls, "https://k.io/"),
                         ["https://k.io/en/blog/", "https://k.io/en/docs/"])

    def test_filter_home_path(self):
        urls = ["https://agones.dev/site/docs/", "https://agones.dev/other/"]
        self.assertEqual(dl.filter_pool(urls, "https://agones.dev/site/"),
                         ["https://agones.dev/site/docs/"])

    def test_llms_links(self):
        text = ("- [A](https://a.io/docs/a/index.md): x\n- [B](/docs/b/index.md)\n"
                "- [C](https://b.io/c.md)\n- [D](https://a.io/d/)\n")
        self.assertEqual(dl.llms_md_links(text, "https://a.io/"),
                         ["https://a.io/docs/a/index.md", "https://a.io/docs/b/index.md"])

    def test_draw(self):
        pool = ["https://a.io/p%03d/" % i for i in range(100)]
        one = dl.draw(pool, "a-io")
        self.assertEqual(len(one), 30)
        self.assertEqual(one, dl.draw(list(reversed(pool)), "a-io"))
        self.assertTrue(set(one) <= set(pool))
        self.assertEqual(dl.draw(["b", "a"], "x"), ["a", "b"])


class TestGrade(unittest.TestCase):
    def test_grade(self):
        sites, pages = fixture()
        g = dl.grade(sites, pages)
        self.assertEqual((g["eligible"], g["counted"], g["copies"], g["docsy_copies"]), (4, 3, 32, 4))
        self.assertTrue(g["G1"])
        self.assertTrue(g["P1"])
        self.assertEqual(g["sites_with_docsy"], 2)
        self.assertTrue(g["P2"])
        self.assertEqual(g["docsy_copy_share"], 0.125)
        self.assertTrue(g["P3"])
        self.assertEqual(g["docsy_label_copies"], {"docsy:alert": 3, "docsy:tabpane": 2})
        self.assertEqual(g["top_labels"], ["docsy:alert"])
        self.assertTrue(g["P4"])
        self.assertAlmostEqual(g["median_docsy_markup_share"], 0.08)
        self.assertTrue(g["P5"])
        self.assertFalse(g["P6"])  # site e has no structural tag

    def test_gate_fails_with_two_sites(self):
        sites, pages = fixture()
        sites = [s for s in sites if s["key"] != "e"]
        g = dl.grade(sites, pages)
        self.assertEqual(g["counted"], 2)
        self.assertFalse(g["G1"])

    def test_hand_check_sample_and_labels(self):
        sites, pages = fixture()
        rows = dl.hand_check_sample(sites, pages)
        self.assertEqual(len(rows), 7)
        self.assertEqual([r["group"] for r in rows if r["site"] == "b"], ["docsy", "docsy", "none"])
        self.assertFalse(any(r["site"] == "c" for r in rows))
        labels = dl.label_rows(sites, pages)
        self.assertEqual(labels, [{"label": "docsy:alert", "sites": 2, "copies": 3, "tags": 3},
                                  {"label": "docsy:tabpane", "sites": 1, "copies": 2, "tags": 2}])

    def test_auto_md(self):
        sites, pages = fixture()
        g = dl.grade(sites, pages)
        meta = {"version": dl.VERSION, "leak_version": dl.LEAK_VERSION, "started": "s",
                "finished": "f", "requests": 1}
        text = dl.auto_md(meta, sites, g, dl.label_rows(sites, pages))
        self.assertIn("G1 (at least 3 counted sites): passed", text)
        self.assertIn("P6 (every counted site has a copy with a structural tag): failed", text)
        self.assertIn("| docsy:alert | 2 | 3 | 3 |", text)


if __name__ == "__main__":
    unittest.main()
