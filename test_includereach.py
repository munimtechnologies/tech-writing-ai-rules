# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""Offline tests for includereach.py (study 13). No network: clones, pages and the renderer are
fakes. Run: python -m unittest -v test_includereach"""

import csv
import json
import os
import shutil
import tempfile
import unittest

import includereach as ir
import learnlabels as ll
import learnshown as ls

NOTE = "The author created this article with assistance from AI."
CONTROL_URL = ls.CONTROLS[0][3]
CONTROL_PATH = ls.CONTROLS[0][2]


class IncludeRefTest(unittest.TestCase):
    def test_targets(self):
        text = ("Intro\n[!INCLUDE [Prereqs](includes/a.md)]\n"
                "[!include[](../shared/b.md)]\n"
                "> [!INCLUDE [c](~/includes/c.md \"title\")]\n"
                "[!INCLUDE [again](includes/a.md)]\n"
                "[link](includes/d.md) is not an include\n")
        self.assertEqual(ir.include_targets(text), ["includes/a.md", "../shared/b.md", "~/includes/c.md"])

    def test_resolve(self):
        self.assertEqual(ir.resolve("docs/x/a.md", "includes/i.md"), "docs/x/includes/i.md")
        self.assertEqual(ir.resolve("docs/x/a.md", "../includes/i.md#part"), "docs/includes/i.md")
        self.assertEqual(ir.resolve("docs/x/a.md", "./i.md?tabs=y"), "docs/x/i.md")
        self.assertEqual(ir.resolve("docs/x/a.md", "~/includes/i.md", ["", "docs"]), "docs/includes/i.md")
        self.assertEqual(ir.resolve("a.md", "~/includes/i.md", [""]), "includes/i.md")
        self.assertEqual(ir.resolve("a.md", "/includes/i.md"), "includes/i.md")
        self.assertEqual(ir.resolve("a.md", "../../outside.md"), "")
        self.assertEqual(ir.resolve("a.md", "https://example.com/i.md"), "")

    def test_docset_root(self):
        self.assertEqual(ir.docset_root("docs/x/a.md", ["", "docs", "docs/x"]), "docs/x")
        self.assertEqual(ir.docset_root("other/a.md", ["", "docs"]), "")
        self.assertEqual(ir.docset_root("other/a.md", ["docs"]), "")

    def test_graph_and_reach(self):
        texts = {"a.md": "[!INCLUDE [x](inc/One.md)]", "inc/one.md": "[!INCLUDE [y](two.md)]",
                 "inc/two.md": "[!INCLUDE [z](one.md)]", "b.md": "no includes"}
        g = ir.build_graph(texts)
        self.assertEqual(g["a.md"], ["inc/one.md"])
        self.assertEqual(g["inc/one.md"], ["inc/two.md"])
        self.assertEqual(g["b.md"], [])
        self.assertEqual(ir.reached("a.md", g), {"inc/one.md": 1, "inc/two.md": 2})
        self.assertEqual(ir.reached("a.md", g, max_depth=1), {"inc/one.md": 1})
        self.assertEqual(ir.reached("b.md", g), {})


def describe(path, front, body=""):
    return ll.describe_file(path, "---\n%s---\n%s" % (front, body))


class HostTest(unittest.TestCase):
    def files_graph(self):
        files = [
            describe("docs/includes/ai.md", "author: x\nai-usage: ai-assisted\n"),
            describe("docs/includes/plain.md", "author: x\n"),
            describe("docs/h0.md", "title: H0\n"),
            describe("docs/h1.md", "title: H1\nai-usage: ai-generated\n"),
            describe("docs/hx.md", "title: HX\nms.ai-usage: ai-assisted\n"),
            describe("docs/none.md", "title: None\n"),
        ]
        graph = {"docs/h0.md": ["docs/includes/ai.md"], "docs/h1.md": ["docs/includes/ai.md"],
                 "docs/hx.md": ["docs/includes/ai.md"], "docs/none.md": ["docs/includes/plain.md"],
                 "docs/includes/ai.md": [], "docs/includes/plain.md": []}
        return files, graph

    def test_groups(self):
        files, graph = self.files_graph()
        hosts = ir.find_hosts("o/r", files, graph)
        self.assertEqual([(h["path"], h["group"]) for h in hosts],
                         [("docs/h0.md", "H0"), ("docs/h1.md", "H1"), ("docs/hx.md", "HX")])
        self.assertEqual(hosts[0]["include_values"], "ai-assisted=1")
        self.assertEqual(hosts[0]["first_include"], "docs/includes/ai.md")
        self.assertEqual(hosts[0]["depth"], 1)
        labelled, used = ir.labelled_used(files, graph)
        self.assertEqual(labelled, ["docs/includes/ai.md"])
        self.assertEqual(used, {"docs/includes/ai.md"})

    def test_draw_is_seeded_and_capped(self):
        hosts = [{"repo": "o/r", "path": "p%02d.md" % i, "group": "H0"} for i in range(30)]
        hosts += [{"repo": "o/r", "path": "q%02d.md" % i, "group": "H1"} for i in range(3)]
        hosts += [{"repo": "o/other", "path": "z.md", "group": "H0"}]
        a = ir.draw_hosts(hosts, "o/r")
        b = ir.draw_hosts(hosts, "o/r")
        self.assertEqual(a, b)
        self.assertEqual(sum(1 for h in a if h["group"] == "H0"), ir.PER_H0)
        self.assertEqual(sum(1 for h in a if h["group"] == "H1"), 3)
        self.assertNotIn("z.md", [h["path"] for h in a])


class SummaryTest(unittest.TestCase):
    @staticmethod
    def page(group, note, md_key=""):
        return {"repo": "o/r", "group": group, "mapped": "yes", "html_status": 200, "render_status": 200,
                "note_rendered": note, "note_rendered_text": NOTE if note else "", "md_served": True,
                "md_ai_key": md_key}

    def summary(self, h0_notes, h1_notes=8, control=True):
        pages = [self.page("H0", i < h0_notes) for i in range(20)]
        pages += [self.page("H1", i < h1_notes, "ai-usage") for i in range(8)]
        controls = [{"stratum": "control-positive", "note_rendered": control}]
        return ir.summarise([], pages, controls, [{"repo": "o/r", "status": "read"}])

    def test_boundaries(self):
        s = self.summary(1)
        self.assertTrue(s["gates"]["G1"]["passed"])
        self.assertTrue(s["gates"]["G2"]["passed"])
        self.assertEqual((s["predictions"]["P1"]["k"], s["predictions"]["P1"]["n"]), (1, 20))
        self.assertTrue(s["predictions"]["P1"]["held"])
        self.assertTrue(s["predictions"]["P2"]["held"])
        self.assertTrue(s["predictions"]["P3"]["held"])
        self.assertFalse(self.summary(2)["predictions"]["P1"]["held"])
        self.assertFalse(self.summary(0, h1_notes=7)["predictions"]["P2"]["held"])

    def test_failed_control_leaves_note_predictions_ungraded(self):
        s = self.summary(0, control=False)
        self.assertFalse(s["gates"]["G1"]["passed"])
        self.assertIsNone(s["predictions"]["P1"]["held"])
        self.assertIsNone(s["predictions"]["P2"]["held"])
        self.assertTrue(s["predictions"]["P3"]["held"])

    def test_unrendered_pages_not_counted(self):
        pages = [dict(self.page("H0", False), render_status=0) for _ in range(20)]
        s = ir.summarise([], pages, [{"stratum": "control-positive", "note_rendered": True}],
                         [{"repo": "o/r", "status": "read"}])
        self.assertEqual(s["H0_counted"], 0)
        self.assertFalse(s["gates"]["G2"]["passed"])
        self.assertIsNone(s["predictions"]["P1"]["held"])


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


class EndToEndTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    @staticmethod
    def cloner(full_name, branch, dest):
        d = os.path.join(dest, "docs")
        write(os.path.join(d, "docfx.json"),
              json.dumps({"build": {"dest": "demo", "content": [{"files": ["**/*.md"]}]}}))
        write(os.path.join(d, "includes", "ai-inc.md"), "---\nauthor: x\nai-usage: ai-assisted\n---\nShared.\n")
        write(os.path.join(d, "includes", "wrap.md"), "---\nauthor: x\n---\n[!INCLUDE [x](ai-inc.md)]\n")
        write(os.path.join(d, "includes", "plain.md"), "---\nauthor: x\n---\nPlain.\n")
        write(os.path.join(d, "h0a.md"), "---\ntitle: A\n---\n# A\n\n[!INCLUDE [a](includes/ai-inc.md)]\n")
        write(os.path.join(d, "h0b.md"), "---\ntitle: B\n---\n# B\n\n[!INCLUDE[w](~/includes/wrap.md)]\n")
        write(os.path.join(d, "h1.md"),
              "---\ntitle: C\nai-usage: ai-generated\n---\n# C\n\n[!include[](./includes/AI-INC.md)]\n")
        write(os.path.join(d, "hx.md"), "---\ntitle: D\nms.ai-usage: ai-assisted\n---\n[!INCLUDE [a](includes/ai-inc.md)]\n")
        write(os.path.join(d, "none.md"), "---\ntitle: E\n---\n[!INCLUDE [p](includes/plain.md)]\n")
        return None, "abc123"

    @staticmethod
    def fetch(url, accept):
        if url == ls.LEARN + "/robots.txt":
            return 200, "text/plain", url, "User-agent: *\nDisallow: /*/answers/accounts/\n"
        if url == CONTROL_URL:
            path, labelled = CONTROL_PATH, True
        elif url.startswith(ls.LEARN + "/en-us/demo/"):
            sub = url[len(ls.LEARN + "/en-us/demo/"):]
            path, labelled = "docs/%s.md" % sub, sub == "h1"
        else:
            return 404, "", url, ""
        if accept == "text/markdown":
            return 200, "text/markdown; charset=utf-8", url, (
                "---\ntitle: X\n%ssource_path: %s\n---\n# X\n\nText.\n" % ("ai-usage: ai-assisted\n" if labelled else "", path))
        return 200, "text/html; charset=utf-8", url, (
            '<html><head><meta name="source_path" content="%s"></head><body><p>Text.</p></body></html>' % path)

    @staticmethod
    def render(url):
        if url == CONTROL_URL or url.endswith("/demo/h1"):
            return 200, "Body\n" + NOTE
        return 200, "Body"

    def test_end_to_end(self):
        out = os.path.join(self.tmp, "out")
        closed = []
        rc = ir.main(["--out-dir", out, "--no-prereg-check", "--render", "--repos", "demo/one"],
                     cloner=self.cloner, fetch=self.fetch, sleep=lambda s: None,
                     renderer=lambda: (self.render, lambda: closed.append(1)))
        self.assertEqual(rc, 0)
        self.assertEqual(closed, [1])
        with open(os.path.join(out, "includereach.json"), encoding="utf-8") as fh:
            s = json.load(fh)["summary"]
        self.assertEqual(s["hosts"], 4)
        self.assertEqual(s["hosts_by_group"], {"H0": 2, "H1": 1, "HX": 1})
        self.assertEqual(s["pages_sampled"], 3)
        self.assertEqual((s["H0_counted"], s["H1_counted"]), (2, 1))
        r = s["by_repo"]["demo/one"]
        self.assertEqual((r["labelled_includes"], r["labelled_includes_used"], r["H0_note"], r["H1_note"]),
                         (1, 1, 0, 1))
        self.assertTrue(s["gates"]["G1"]["passed"])
        self.assertFalse(s["gates"]["G2"]["passed"])
        self.assertIsNone(s["predictions"]["P1"]["held"])
        with open(os.path.join(out, "hosts.csv"), encoding="utf-8") as fh:
            hosts = {row["path"]: row for row in csv.DictReader(fh)}
        self.assertEqual(hosts["docs/h0b.md"]["depth"], "2")
        self.assertEqual(hosts["docs/h0b.md"]["first_include"], "docs/includes/ai-inc.md")
        self.assertNotIn("docs/none.md", hosts)
        with open(os.path.join(out, "pages.csv"), encoding="utf-8") as fh:
            pages = list(csv.DictReader(fh))
        self.assertEqual([p["path"] for p in pages], ["docs/h0a.md", "docs/h0b.md", "docs/h1.md"])
        self.assertEqual([p["mapped"] for p in pages], ["yes", "yes", "yes"])
        self.assertEqual(pages[0]["url"], ls.LEARN + "/en-us/demo/h0a")
        self.assertTrue(os.path.exists(os.path.join(out, "INCLUDEREACH_AUTO.md")))

    def test_renderer_missing_stops(self):
        def broken():
            raise ImportError("No module named 'playwright'")
        out = os.path.join(self.tmp, "out")
        rc = ir.main(["--out-dir", out, "--no-prereg-check", "--render", "--repos", "demo/one"],
                     cloner=self.cloner, fetch=self.fetch, sleep=lambda s: None, renderer=broken)
        self.assertEqual(rc, 5)
        self.assertFalse(os.path.exists(os.path.join(out, "hosts.csv")))


if __name__ == "__main__":
    unittest.main()
