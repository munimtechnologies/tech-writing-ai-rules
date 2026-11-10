# Copyright 2026 Munim, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
"""Offline tests for learnshown.py (study 8). No network and no browser: the cloner, lister,
fetcher and renderer are fakes. Run: python -m unittest -v test_learnshown"""

import csv
import json
import os
import shutil
import tempfile
import unittest

import learnshown as ls

ENTRA_NOTE = "The author created this article with assistance from AI."
L = ls.LEARN


def art(path, key="", value="", is_article=True):
    cat = ls.ll.category(key, value)
    return {"path": path, "is_article": is_article, "ai_key": key, "ai_value": value, "category": cat,
            "year": 2026, "include": False}


class StrataTest(unittest.TestCase):
    def test_stratum(self):
        self.assertEqual(ls.stratum(art("a.md", "ai-usage", "ai-assisted")), "A")
        self.assertEqual(ls.stratum(art("a.md", "ai-usage", "AI-Generated")), "B")
        self.assertEqual(ls.stratum(art("a.md", "ms.ai-usage", "ai-generated")), "C")
        self.assertEqual(ls.stratum(art("a.md", "ai.usage", "ai-assisted")), "C")
        self.assertEqual(ls.stratum(art("a.md", "ai-usage", "ai-gen-docs")), "D")
        self.assertEqual(ls.stratum(art("a.md")), "U")
        self.assertEqual(ls.stratum(art("a.md", "ai-usage", "human-only")), "")
        self.assertEqual(ls.stratum(art("a.md", is_article=False)), "")

    def test_draw_is_seeded_capped_and_skips_seen(self):
        repo = "MicrosoftDocs/entra-docs"
        seen = "docs/identity-platform/quickstart-register-app.md"
        files = [art("docs/a%02d.md" % i, "ai-usage", "ai-assisted") for i in range(20)]
        files.append(art(seen, "ai-usage", "ai-assisted"))
        files += [art("docs/u%d.md" % i) for i in range(3)]
        one = ls.draw(files, repo)
        two = ls.draw(list(reversed(files)), repo)
        self.assertEqual([p["path"] for p in one], [p["path"] for p in two])
        a = [p for p in one if p["stratum"] == "A"]
        self.assertEqual(len(a), ls.PER_STRATUM)
        self.assertNotIn(seen, [p["path"] for p in one])
        self.assertEqual(len([p for p in one if p["stratum"] == "U"]), 3)
        self.assertTrue(all(p["repo"] == repo for p in one))


class MappingTest(unittest.TestCase):
    AZURE = json.dumps({"build": {"dest": "azure", "content": [
        {"files": ["**/*.md", "**/*.yml"], "src": "articles", "dest": "."},
        {"files": ["**/*.md"], "src": "articles/cyclecloud", "dest": "./cyclecloud/"},
        {"files": ["**/*.png"], "src": "articles"}]}})
    # Shapes of real docfx.json files read on 2026-11-10 (fabric-docs, dynamics-365-unified-operations-public).
    FABRIC = json.dumps({"build": {"dest": "fabric-docs", "content": [
        {"files": ["**/*.md", "**/*.yml"], "src": "./"}],
        "globalMetadata": {"breadcrumb_path": "/fabric/breadcrumb/toc.json"}}})
    D365 = json.dumps({"build": {"dest": "d365F-O", "content": [{"files": ["**/*.md"]}],
                                 "globalMetadata": {"breadcrumb_path": "/dynamics365/ops-bc/toc.json"}}})

    def test_docfx_map(self):
        m = ls.docfx_map(self.AZURE)
        self.assertEqual(m["dest"], "azure")
        self.assertEqual(m["bread"], "")
        self.assertEqual(m["content"], [("articles", ""), ("articles/cyclecloud", "cyclecloud")])
        self.assertIsNone(ls.docfx_map("not json"))
        self.assertIsNone(ls.docfx_map(json.dumps({"metadata": []})))
        self.assertEqual(ls.docfx_map(self.FABRIC)["bread"], "fabric")

    def test_breadcrumb_base(self):
        self.assertEqual(ls.breadcrumb_base("/fabric/breadcrumb/toc.json"), "fabric")
        self.assertEqual(ls.breadcrumb_base("/azure/cloud-adoption-framework/_bread/toc.json"),
                         "azure/cloud-adoption-framework")
        self.assertEqual(ls.breadcrumb_base("/azure/architecture/bread/toc.json"), "azure/architecture")
        self.assertEqual(ls.breadcrumb_base("/visualstudio/_breadcrumb/toc.json"), "visualstudio")
        self.assertEqual(ls.breadcrumb_base("/dynamics365/ops-bc/toc.json"), "dynamics365/ops-bc")
        self.assertEqual(ls.breadcrumb_base("breadcrumb/toc.yml"), "")
        self.assertEqual(ls.breadcrumb_base(None), "")

    def test_page_url_azure_layout(self):
        maps = {"": ls.docfx_map(self.AZURE)}
        self.assertEqual(ls.page_url("articles/dev-box/overview-what-is-dev-box-mcp-server.md", maps),
                         "https://learn.microsoft.com/en-us/azure/dev-box/overview-what-is-dev-box-mcp-server")
        self.assertEqual(ls.page_url("articles/cyclecloud/how-to/a.md", maps),
                         "https://learn.microsoft.com/en-us/azure/cyclecloud/how-to/a")
        self.assertEqual(ls.page_url("articles/dev-box/index.md", maps),
                         "https://learn.microsoft.com/en-us/azure/dev-box/")
        self.assertEqual(ls.page_url("media/x.md", maps), "")

    def test_page_url_entra_layout(self):
        maps = {"docs": ls.docfx_map(json.dumps({"build": {"dest": "entra", "content": [{"files": ["**/*.md"]}]}}))}
        self.assertEqual(ls.page_url("docs/identity-platform/quickstart-register-app.md", maps),
                         "https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app")
        self.assertEqual(ls.page_url("README.md", maps), "")
        self.assertEqual(ls.page_url("docs/x.md", {}), "")

    def test_candidates_fabric(self):
        maps = {"docs": ls.docfx_map(self.FABRIC)}
        self.assertEqual(ls.candidate_urls("docs/admin/map-settings.md", maps), [
            ("breadcrumb", L + "/en-us/fabric/admin/map-settings"),
            ("docfx-dest", L + "/en-us/fabric-docs/admin/map-settings")])
        self.assertEqual(ls.candidate_urls("README.md", maps), [])

    def test_candidates_root_segment_and_lower_case(self):
        maps = {"articles": ls.docfx_map(self.D365)}
        self.assertEqual(ls.candidate_urls("articles/human-resources/Payroll-API.md", maps), [
            ("breadcrumb", L + "/en-us/dynamics365/ops-bc/human-resources/Payroll-API"),
            ("breadcrumb-lower", L + "/en-us/dynamics365/ops-bc/human-resources/payroll-api"),
            ("breadcrumb-root", L + "/en-us/dynamics365/human-resources/Payroll-API"),
            ("breadcrumb-root-lower", L + "/en-us/dynamics365/human-resources/payroll-api"),
            ("docfx-dest", L + "/en-us/d365F-O/human-resources/Payroll-API"),
            ("docfx-dest-lower", L + "/en-us/d365f-o/human-resources/payroll-api")])

    def test_candidates_keep_entry_dest(self):
        azure = json.loads(self.AZURE)
        azure["build"]["globalMetadata"] = {"breadcrumb_path": "/azure/bread/toc.json"}
        maps = {"": ls.docfx_map(json.dumps(azure))}
        self.assertEqual(ls.candidate_urls("articles/cyclecloud/how-to/a.md", maps),
                         [("breadcrumb", L + "/en-us/azure/cyclecloud/how-to/a")])

    def test_clean_path(self):
        self.assertEqual(ls.clean_path("./cyclecloud/"), "cyclecloud")
        self.assertEqual(ls.clean_path("."), "")
        self.assertEqual(ls.clean_path("a\\b"), "a/b")


class DisclosureTest(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(ls.disclosure("Note\n\n%s Learn more" % ENTRA_NOTE), ENTRA_NOTE)
        self.assertTrue(ls.disclosure("AI-assisted content. This article was partially created with the help of AI."))
        self.assertTrue(ls.disclosure("This article was generated by AI and reviewed by an author."))

    def test_negative(self):
        for text in [
            "The Microsoft Dev Box Model Context Protocol (MCP) Server is an open-source integration layer "
            "that connects AI agents with Microsoft Dev Box services.",
            "Ready to enhance your development workflow with AI-powered Dev Box management?",
            "AI Disclaimer\n\nPrevious Versions\n\nBlog",
            "Ask Learn is an AI assistant that can answer questions, clarify concepts, and define terms "
            "using trusted Microsoft documentation.",
            "Use Azure OpenAI to generate content for your app.",
        ]:
            self.assertEqual(ls.disclosure(text), "", text)

    def test_long_run_is_skipped(self):
        self.assertEqual(ls.disclosure("x " * 300 + ENTRA_NOTE.replace(".", "")), "")

    def test_rendered_lines_are_paragraphs(self):
        text = "Grant admin consent\n" + "Select the permissions you need " * 20 + "\nNote\n" + ENTRA_NOTE + \
               "\nLearn more\nFeedback\nAI Disclaimer"
        self.assertEqual(ls.rendered_note(text), ENTRA_NOTE)
        self.assertEqual(ls.rendered_note("Feedback\r\nAI Disclaimer\r\nPrevious Versions"), "")
        self.assertEqual(ls.rendered_note(None), "")


class FormsTest(unittest.TestCase):
    HTML = ('<!DOCTYPE html><html><head><meta name="ms.ai-usage" content="ai-generated">'
            '<meta content="https://github.com/MicrosoftDocs/azure-docs-pr/blob/live/articles/dev-box/x.md" '
            'name="original_content_git_url" />'
            '<script>var s = "created with the help of AI";</script></head><body><main><h1>X</h1>'
            '<p>Body text.</p><ul><li>Link one</li><li>Link two</li></ul><div class="alert"><p>Note</p>'
            '<p>The author created this article with assistance from AI. <a href="/x">Learn more</a></p></div>'
            '</main><footer><a href="/ai">AI Disclaimer</a></footer></body></html>')

    def test_read_html(self):
        h = ls.read_html(self.HTML)
        self.assertEqual((h["ai_key"], h["ai_value"]), ("ms.ai-usage", "ai-generated"))
        self.assertTrue(h["git_url"].endswith("articles/dev-box/x.md"))
        self.assertEqual(h["note"], ENTRA_NOTE)
        self.assertTrue(h["raw"])

    def test_note_only_in_script_is_not_visible(self):
        page = '<html><body><script>t = "The author created this article with assistance from AI.";</script><p>Hi.</p></body></html>'
        h = ls.read_html(page)
        self.assertEqual(h["note"], "")
        self.assertTrue(h["raw"])

    def test_read_md_copy(self):
        text = ("---\nlayout: Conceptual\ntitle: How to Register an App\nai-usage: ai-assisted\n"
                "source_path: docs/identity-platform/quickstart-register-app.md\n---\n\n# How to\n\nIntro.\n\n"
                "## Prerequisites\n\n- An account.\n\n```bash\n## not a heading\n```\n\n"
                "## Grant admin consent (external tenants only)\n\n1. Select **API permissions**.\n")
        m = ls.read_md_copy(text)
        self.assertEqual((m["ai_key"], m["ai_value"]), ("ai-usage", "ai-assisted"))
        self.assertEqual(m["source_path"], "docs/identity-platform/quickstart-register-app.md")
        self.assertEqual(m["h2"], ["prerequisites", "grant admin consent external tenants only"])
        self.assertEqual(m["note"], "")

    def test_h2s(self):
        self.assertEqual(ls.h2s("## [Next steps](x.md)\n### Deeper\n##Bad\n  ## Related content ##\n"),
                         ["next steps", "related content"])

    def test_md_served(self):
        self.assertTrue(ls.md_served(200, "text/markdown; charset=utf-8", "# x"))
        self.assertTrue(ls.md_served(200, "", "---\ntitle: x\n---\n"))
        self.assertFalse(ls.md_served(200, "text/html", "<!DOCTYPE html><html>"))
        self.assertFalse(ls.md_served(404, "text/markdown", ""))

    def test_mapped(self):
        p = "articles/dev-box/x.md"
        self.assertEqual(ls.mapped(p, {"source_path": "articles/dev-box/x.md"}), "yes")
        self.assertEqual(ls.mapped(p, {"git_url": "https://github.com/MicrosoftDocs/azure-docs-pr/blob/live/Articles/dev-box/x.md"}), "yes")
        self.assertEqual(ls.mapped(p, {"source_path": "articles/other.md"}, {}), "no")
        self.assertEqual(ls.mapped(p, {"source_path": ""}, {"git_url": ""}), "unknown")


class CheckPageTest(unittest.TestCase):
    """Candidates are tried in order; Learn search by title is the last resort."""

    @staticmethod
    def fetch(url, accept):
        if url.startswith(L + "/api/search?"):
            assert "search=X%20page" in url and "$top=5" in url, url
            return 200, "application/json", url, json.dumps({"results": [
                {"url": L + "/en-us/other/y"}, {"url": L + "/en-us/b/x#frag"}, {"url": "https://example.com/z"}]})
        if url == L + "/en-us/b/x":
            if accept == "text/markdown":
                return 200, "text/markdown", url, "---\ntitle: X\nai-usage: ai-assisted\nsource_path: pa/x.md\n---\n# X\n"
            return 200, "text/html", url, ('<html><head><meta name="ai-usage" content="ai-assisted"></head>'
                                           '<body><p>Hi.</p></body></html>')
        if url == L + "/en-us/other/y" and accept == "text/markdown":
            return 200, "text/markdown", url, "---\ntitle: Y\nsource_path: other/y.md\n---\n# Y\n"
        return 404, "", url, ""

    @staticmethod
    def render(url):
        return 200, "X\nNote\n%s\nLearn more\nAI Disclaimer" % ENTRA_NOTE

    def row(self):
        return {"repo": "R", "path": "pa/x.md", "stratum": "A", "_title": "X page",
                "_cands": [("breadcrumb", L + "/en-us/a/x")]}

    def test_search_fallback_and_render(self):
        r = ls.check_page(self.row(), self.fetch, lambda s: None, lambda u: True, self.render)
        self.assertEqual((r["url"], r["url_rule"], r["mapped"], r["tried"]), (L + "/en-us/b/x", "search", "yes", 3))
        self.assertTrue(r["md_served"])
        self.assertEqual(r["md_ai_key"], "ai-usage")
        self.assertEqual(r["html_ai_key"], "ai-usage")
        self.assertFalse(r["note_html"])
        self.assertTrue(r["note_rendered"])
        self.assertEqual(r["note_rendered_text"], ENTRA_NOTE)
        self.assertEqual(r["render_status"], 200)

    def test_no_candidate_confirms(self):
        row = self.row()
        row["_title"] = ""
        r = ls.check_page(row, self.fetch, lambda s: None, lambda u: True, self.render)
        self.assertEqual((r["url"], r["url_rule"], r["mapped"], r["tried"]), (L + "/en-us/a/x", "breadcrumb", "unknown", 1))
        self.assertEqual(r["html_status"], 404)
        self.assertEqual(r["render_status"], "")
        self.assertFalse(r["note_rendered"])

    def test_robots_blocks_everything(self):
        r = ls.check_page(self.row(), self.fetch, lambda s: None, lambda u: False)
        self.assertEqual(r["mapped"], "robots")
        self.assertEqual(r["url"], L + "/en-us/a/x")


def page(repo, st, note=False, md_key="ai-usage", last="", missing=""):
    return {"repo": repo, "path": "p.md", "stratum": st, "mapped": "yes", "html_status": 200, "md_served": True,
            "note_html": note, "note_md": False, "md_ai_key": md_key, "src_category": "ai-assisted",
            "src_key": "ai-usage", "note_html_text": ENTRA_NOTE if note else "", "last_src_h2": last,
            "last_h2_missing": missing, "md_h2_missing": 1 if missing is True else 0}


class SummaryTest(unittest.TestCase):
    def build(self, a_notes=90, pos_note=True):
        pages = []
        for r in range(10):
            for i in range(10):
                pages.append(page("R%d" % r, "A", note=(r * 10 + i) < a_notes))
        for i in range(10):
            pages.append(page("R0", "C", note=i < 2))
        for i in range(20):
            pages.append(page("R1", "U", note=i < 1, md_key="", last="next steps", missing=i < 16))
        lab = [p for p in pages if p["stratum"] in ("A", "C")]
        for p in lab[99:]:
            p["md_ai_key"] = ""
        controls = [{"stratum": "control-positive", "note_html": pos_note}]
        return ls.summarise(pages, controls, [{"status": "read"}] * 10)

    def test_boundaries_hold(self):
        s = self.build()
        self.assertTrue(s["gates"]["G1"]["passed"])
        self.assertTrue(s["gates"]["G2"]["passed"])
        self.assertTrue(s["gates"]["G3"]["passed"])
        p = s["predictions"]
        self.assertEqual((p["P1"]["k"], p["P1"]["n"], p["P1"]["held"]), (90, 100, True))
        self.assertEqual((p["P2"]["k"], p["P2"]["n"], p["P2"]["held"]), (2, 10, True))
        self.assertEqual((p["P3"]["k"], p["P3"]["n"], p["P3"]["held"]), (1, 20, True))
        self.assertEqual((p["P4"]["k"], p["P4"]["n"], p["P4"]["held"]), (0, 92, True))
        self.assertEqual((p["P5"]["k"], p["P5"]["n"], p["P5"]["held"]), (99, 110, True))
        self.assertEqual((p["P6"]["k"], p["P6"]["n"], p["P6"]["held"]), (16, 20, True))

    def test_one_below_fails(self):
        self.assertFalse(self.build(a_notes=89)["predictions"]["P1"]["held"])

    def test_failed_control_ungrades_html_predictions(self):
        p = self.build(pos_note=False)["predictions"]
        for k in ("P1", "P2", "P3", "P4"):
            self.assertIsNone(p[k]["held"], k)
        self.assertTrue(p["P5"]["held"])
        self.assertTrue(p["P6"]["held"])

    def test_rendered_measure(self):
        pages = []
        for r in range(10):
            for i in range(10):
                p = page("R%d" % r, "A")
                p["note_rendered"] = (r * 10 + i) < 90
                p["note_rendered_text"] = ENTRA_NOTE if p["note_rendered"] else ""
                pages.append(p)
        controls = [{"stratum": "control-positive", "note_html": False, "note_rendered": True}]
        rows = [{"status": "read"}] * 10
        s = ls.summarise(pages, controls, rows, "note_rendered")
        self.assertEqual(s["note_measure"], "note_rendered")
        self.assertTrue(s["gates"]["G2"]["passed"])
        self.assertEqual((s["predictions"]["P1"]["k"], s["predictions"]["P1"]["held"]), (90, True))
        self.assertEqual(s["note_texts"], {ENTRA_NOTE: 90})
        self.assertEqual(s["by_stratum"]["A"]["note_rendered"], 90)
        served = ls.summarise(pages, controls, rows)
        self.assertFalse(served["gates"]["G2"]["passed"])
        self.assertIsNone(served["predictions"]["P1"]["held"])


class MainTest(unittest.TestCase):
    REPOS = [{"full_name": "MicrosoftDocs/demo-one", "size": 200, "default_branch": "main",
              "pushed_at": "2026-10-01T00:00:00Z", "visibility": "public"},
             {"full_name": "MicrosoftDocs/demo-two", "size": 100, "default_branch": "main",
              "pushed_at": "2026-10-01T00:00:00Z", "visibility": "public"},
             {"full_name": "MicrosoftDocs/demo-old", "size": 900, "default_branch": "main",
              "pushed_at": "2025-01-01T00:00:00Z", "visibility": "public"}]

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    @staticmethod
    def cloner(full_name, branch, dest):
        docs = os.path.join(dest, "docs")
        os.makedirs(docs)
        with open(os.path.join(docs, "docfx.json"), "w", encoding="utf-8") as fh:
            json.dump({"build": {"dest": "demo", "content": [{"files": ["**/*.md"]}]}}, fh)
        body = "# T\n\n## Prerequisites\n\nText.\n\n## Next steps\n\n- link\n"
        for i in range(12):
            with open(os.path.join(docs, "a%02d.md" % i), "w", encoding="utf-8", newline="\n") as fh:
                fh.write("---\ntitle: A%d\nai-usage: ai-assisted\nms.date: 05/14/2026\n---\n%s" % (i, body))
        for i in range(3):
            with open(os.path.join(docs, "u%02d.md" % i), "w", encoding="utf-8", newline="\n") as fh:
                fh.write("---\ntitle: U%d\nms.date: 05/14/2024\n---\n%s" % (i, body))
        return None, "abc123"

    @staticmethod
    def fetch(url, accept):
        base = ls.LEARN + "/en-us/demo/"
        if url == ls.LEARN + "/robots.txt":
            return 200, "text/plain", url, "User-agent: *\nDisallow: /*/answers/accounts/\n"
        if not url.startswith(base):
            return 404, "", url, ""
        sub = url[len(base):]
        path = "docs/%s.md" % sub
        labelled = sub.startswith("a")
        if accept == "text/markdown":
            return 200, "text/markdown; charset=utf-8", url, (
                "---\ntitle: X\n%ssource_path: %s\n---\n# X\n\n## Prerequisites\n\nText.\n"
                % ("ai-usage: ai-assisted\n" if labelled else "", path))
        return 200, "text/html; charset=utf-8", url, (
            '<html><head><meta name="original_content_git_url" content="https://github.com/MicrosoftDocs/demo-pr/'
            'blob/live/%s"></head><body><main><h2>Prerequisites</h2><p>Text.</p>%s</main></body></html>'
            % (path, "<div><p>%s</p></div>" % ENTRA_NOTE if labelled else ""))

    def run_main(self, extra=(), renderer=None):
        out = os.path.join(self.tmp, "out")
        rc = ls.main(["--out-dir", out, "--no-prereg-check"] + list(extra), lister=lambda: self.REPOS,
                     cloner=self.cloner, fetch=self.fetch, sleep=lambda s: None, renderer=renderer)
        return rc, out

    def test_end_to_end(self):
        rc, out = self.run_main()
        self.assertEqual(rc, 0)
        with open(os.path.join(out, "shown.json"), encoding="utf-8") as fh:
            s = json.load(fh)["summary"]
        self.assertEqual(s["pages_sampled"], 22)
        self.assertEqual(s["mapped_ok"], 22)
        self.assertEqual(s["repos_read"], 2)
        self.assertEqual(s["url_rules"], {"docfx-dest": 22})
        self.assertEqual(s["note_measure"], "note_html")
        a = s["by_stratum"]["A"]
        self.assertEqual((a["sampled"], a["note_html"], a["md_ai_key"], a["note_md"], a["last_h2_missing"]),
                         (16, 16, 16, 0, 16))
        self.assertEqual(s["by_stratum"]["U"]["note_html"], 0)
        self.assertFalse(s["gates"]["G1"]["passed"])
        self.assertIsNone(s["predictions"]["P1"]["held"])
        self.assertEqual(s["controls"][0]["html_status"], 404)
        with open(os.path.join(out, "pages.csv"), encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 24)
        self.assertEqual(rows[2]["url"], "https://learn.microsoft.com/en-us/demo/" + rows[2]["path"][5:-3])
        self.assertEqual(rows[2]["url_rule"], "docfx-dest")
        self.assertTrue(os.path.exists(os.path.join(out, "LEARNSHOWN_AUTO.md")))
        self.assertTrue(os.path.exists(os.path.join(out, "frame.csv")))

    def test_end_to_end_rendered(self):
        seen = []

        def render(url):
            seen.append(url)
            return 200, ("Body\n" + ENTRA_NOTE) if "/demo/a" in url else "Body"

        closed = []
        rc, out = self.run_main(["--render"], renderer=lambda: (render, lambda: closed.append(1)))
        self.assertEqual(rc, 0)
        with open(os.path.join(out, "shown.json"), encoding="utf-8") as fh:
            s = json.load(fh)["summary"]
        self.assertEqual(s["note_measure"], "note_rendered")
        self.assertEqual(s["by_stratum"]["A"]["note_rendered"], 16)
        self.assertEqual(s["by_stratum"]["U"]["note_rendered"], 0)
        self.assertEqual(len(seen), 22)
        self.assertEqual(closed, [1])
        self.assertFalse(s["gates"]["G2"]["passed"])

    def test_render_unavailable_stops_before_reading(self):
        def broken():
            raise ImportError("No module named 'playwright'")

        rc, out = self.run_main(["--render"], renderer=broken)
        self.assertEqual(rc, 5)
        with open(os.path.join(out, "shown.json"), encoding="utf-8") as fh:
            meta = json.load(fh)
        self.assertIn("playwright", meta["error"])
        self.assertFalse(os.path.exists(os.path.join(out, "pages.csv")))


if __name__ == "__main__":
    unittest.main()
