# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""Offline tests for the hugo-md-layout-check skill (skills/hugo-md-layout-check).

The fixture is modelled on the layout shapes found in docker/docs on 2026-11-12
(custom layouts built from data files, front matter lists and child pages, with
and without a Markdown template), written fresh here.
"""

import importlib.util
import io
import json
import os
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR_REL = os.path.join("skills", "hugo-md-layout-check")


def find(relpath):
    p = os.path.join(HERE, relpath)
    if os.path.isfile(p):
        return p
    base = os.path.basename(relpath)
    for root, _dirs, files in os.walk(HERE):
        if base in files:
            return os.path.join(root, base)
    raise FileNotFoundError(relpath)


SCRIPT = find(os.path.join(SKILL_DIR_REL, "scripts", "hugo_layout_check.py"))
SKILL_MD = find(os.path.join(SKILL_DIR_REL, "SKILL.md"))
_spec = importlib.util.spec_from_file_location("hugo_layout_check", SCRIPT)
hl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hl)

FIXTURE = {
    "layouts/baseof.html": '<html><body>{{ block "main" . }}{{ .Content }}{{ end }}</body></html>\n',
    "layouts/single.html": '{{ define "main" }}<h1>{{ .Title }}</h1>{{ .Content }}{{ end }}\n',
    "layouts/single.markdown.md": "# {{ .Title }}\n\n{{ .RenderShortcodes }}\n",
    "layouts/list.html": '{{ define "main" }}{{ .Content }}{{ end }}\n',
    "layouts/list.markdown.md": "# {{ .Title }}\n\n{{ .RenderShortcodes }}\n",
    "layouts/home.html": '{{ define "main" }}{{ .Content }}{{ end }}\n',
    "layouts/home.markdown.md": "# {{ .Title }}\n",
    "layouts/home.llms.txt": "# Docs\n",
    "layouts/home.metadata.json": "{}\n",
    "layouts/404.html": "<h1>Not found</h1>\n",
    "layouts/sitemap.xml": "<urlset></urlset>\n",
    "layouts/security-announcements.rss.xml": "<rss></rss>\n",
    "layouts/cli.html": "{{ $d := index hugo.Data.cli .Params.datafile }}{{ $d.usage }}\n",
    "layouts/cli.markdown.md": "# {{ .Title }}\n{{ $d := index hugo.Data.cli .Params.datafile }}{{ $d.usage }}\n",
    "layouts/sbx-cli.html": ("{{ $data := index hugo.Data.sbx_cli .Params.datafile }}"
                             "<p>{{ $data.synopsis }}</p>{{ range .Pages }}<tr>{{ .Title }}</tr>{{ end }}\n"),
    "layouts/glossary.html": ("{{ with .Content }}{{ . }}{{ end }}<table>"
                              "{{ range $term, $def := hugo.Data.glossary }}<tr><td>{{ $term }}</td></tr>"
                              "{{ end }}</table>\n"),
    "layouts/get-started.html": ('{{ define "main" }}<h1>Get started</h1>{{ range .Params.installs }}'
                                 '<a href="{{ .link }}">{{ .title }}</a>{{ end }}{{ end }}\n'),
    "layouts/wide.html": '{{ define "right" }}{{ end }}\n',
    "layouts/page.featured.html": ('{{ define "main" }}{{ with .Params.hero }}<img src="{{ . }}">'
                                   '{{ end }}{{ .Content }}{{ end }}\n'),
    "layouts/unused-thing.html": "{{ .Content }}\n",
    "layouts/page.de.html": "{{ .Content }}\n",
    "layouts/tagged.html": '{{ partial "tags.html" . }}{{ .Content }}\n',
    "layouts/guides/series.html": ('{{ partial "meta.html" . }}<ol>{{ range .Pages }}'
                                   '<li>{{ .LinkTitle }}</li>{{ end }}</ol>\n'),
    "layouts/_partials/tags.html": "{{ range .Params.tags }}<span>{{ . }}</span>{{ end }}\n",
    "layouts/_partials/meta.html": "<div></div>\n",
    "layouts/_shortcodes/note.html": "{{ .Inner }}\n",
    "layouts/_markup/render-link.html": "<a></a>\n",
    "layouts/partials/old.html": "{{ .Content }}\n",
    "hugo.yaml": ("outputs:\n  page: [html, markdown]\n  section: [html, markdown]\n"
                  "cascade:\n  - target:\n      path: /reference/cli/sbx/**\n    layout: sbx-cli\n"),
    "content/reference/glossary.md": "---\ntitle: Glossary\nlayout: glossary\n---\n\n<!-- data file -->\n",
    "content/get-started/_index.md": '+++\ntitle = "Get started"\nlayout = "get-started"\n+++\n',
    "content/manuals/wide-page.md": '---\ntitle: Wide\nlayout: "wide"   # full width\n---\nBody text.\n',
    "content/blog/featured.md": '{\n  "title": "Featured",\n  "layout": "featured"\n}\nBody\n',
    "content/guides/_content.gotmpl": ('{{ $.AddPage (dict "kind" "section" "path" "intro" '
                                       '"layout" "series" "title" "Intro") }}\n'),
    "content/notes/body-mentions.md": "---\ntitle: Notes\n---\n\nlayout: unused-thing\n",
    "content/docs/tagged.md": "---\ntitle: T\nlayout: tagged\n---\n",
}


def write_tree(root, files):
    for rel, text in files.items():
        path = os.path.join(root, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)


class ParseTemplate(unittest.TestCase):
    def p(self, name, **kw):
        return hl.parse_template(name, **kw)

    def test_custom_layouts(self):
        t = self.p("sbx-cli.html")
        self.assertEqual((t["layout"], t["format"]), ("sbx-cli", "html"))
        t = self.p("cli.markdown.md")
        self.assertEqual((t["layout"], t["format"]), ("cli", "markdown"))
        t = self.p("page.featured.html")
        self.assertEqual((t["kind"], t["layout"], t["format"]), ("page", "featured", "html"))
        t = self.p("page._layout_my-layout_.html")
        self.assertEqual(t["layout"], "my-layout")

    def test_generic_and_other_formats(self):
        t = self.p("single.markdown.md")
        self.assertEqual((t["standard"], t["layout"], t["format"]), ("single", None, "markdown"))
        self.assertEqual(self.p("single.md")["format"], "markdown")
        t = self.p("home.metadata.json")
        self.assertEqual((t["kind"], t["layout"], t["format"]), ("home", None, "metadata"))
        t = self.p("list._outputformat_rss_.xml")
        self.assertEqual((t["standard"], t["format"], t["layout"]), ("list", "rss", None))
        t = self.p("security-announcements.rss.xml")
        self.assertEqual((t["layout"], t["format"]), ("security-announcements", "rss"))
        self.assertEqual(self.p("home.llms.txt")["format"], "llms")

    def test_language(self):
        t = self.p("page.de.html")
        self.assertEqual((t["language"], t["layout"]), ("de", None))
        t = self.p("page.de.html", languages={"en"})
        self.assertEqual(t["layout"], "de")
        self.assertIsNone(self.p("README"))

    def test_directory_kept(self):
        t = self.p(os.path.join("guides", "series.html"))
        self.assertEqual((t["dir"], t["layout"]), ("guides", "series"))


class Project(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hlc-")
        write_tree(self.tmp, FIXTURE)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def by_code(self, report):
        out = {}
        for f in report["findings"]:
            out.setdefault(f["code"], []).append(f["layout"])
        return out

    def test_findings(self):
        r = hl.check_project(self.tmp)
        got = self.by_code(r)
        self.assertEqual(got.get("layout-loses-content"), ["get-started", "glossary", "sbx-cli", "series"])
        self.assertEqual(got.get("layout-no-markdown"), ["featured", "tagged", "wide"])
        self.assertEqual(got.get("unused-layout"), ["unused-thing"])
        self.assertNotIn("no-markdown-output", got)
        self.assertEqual(r["counts"], {"error": 4, "warning": 3, "info": 1})
        flagged = {f["layout"] for f in r["findings"]}
        self.assertNotIn("cli", flagged)
        for skipped in ("note", "render-link", "old", "tags", "meta", "de", "metadata"):
            self.assertNotIn(skipped, {e["layout"] for e in r["layouts"]})

    def test_markdown_templates_and_adapters(self):
        r = hl.check_project(self.tmp)
        self.assertEqual(r["markdown_templates"],
                         ["cli.markdown.md", "home.markdown.md", "list.markdown.md", "single.markdown.md"])
        self.assertEqual(r["content_adapters"], ["content/guides/_content.gotmpl"])

    def test_uses_and_how(self):
        r = hl.check_project(self.tmp)
        f = {x["layout"]: x for x in r["findings"]}
        self.assertEqual(f["sbx-cli"]["uses"], [{"file": "hugo.yaml", "how": "config cascade"}])
        self.assertEqual(f["glossary"]["uses"], [{"file": "content/reference/glossary.md", "how": "front matter"}])
        self.assertEqual(f["get-started"]["uses"][0]["file"], "content/get-started/_index.md")
        self.assertEqual(f["wide"]["uses"], [{"file": "content/manuals/wide-page.md", "how": "front matter"}])
        self.assertEqual(f["featured"]["uses"], [{"file": "content/blog/featured.md", "how": "front matter"}])
        self.assertEqual(f["series"]["uses"], [{"file": "content/guides/_content.gotmpl", "how": "content adapter"}])
        self.assertEqual(f["unused-thing"]["uses"], [])

    def test_signals_and_hints(self):
        r = hl.check_project(self.tmp)
        f = {x["layout"]: x for x in r["findings"]}
        self.assertIn("reads site data", f["glossary"]["signals"]["strong"])
        self.assertIn("lists child pages", f["series"]["signals"]["strong"])
        self.assertIn("lists front matter values", f["get-started"]["signals"]["strong"])
        self.assertEqual(f["wide"]["signals"]["strong"], [])
        self.assertIn("lists front matter values (in partial tags.html)", f["tagged"]["signals"]["weak"])
        self.assertIn("uses front matter values", f["featured"]["signals"]["weak"])
        self.assertIn("layouts/guides/series.markdown.md", f["series"]["hint"])
        self.assertIn("layouts/sbx-cli.markdown.md", f["sbx-cli"]["hint"])
        self.assertEqual(f["sbx-cli"]["severity"], "error")

    def test_crlf_front_matter(self):
        path = os.path.join(self.tmp, "content", "manuals", "wide-page.md")
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write('---\r\ntitle: Wide\r\nlayout: wide\r\n---\r\nBody.\r\n')
        r = hl.check_project(self.tmp)
        f = {x["layout"]: x for x in r["findings"]}
        self.assertEqual(f["wide"]["code"], "layout-no-markdown")

    def test_no_markdown_output(self):
        other = tempfile.mkdtemp(prefix="hlc-")
        try:
            write_tree(other, {
                "layouts/single.html": "{{ .Content }}\n",
                "layouts/glossary.html": "{{ range hugo.Data.glossary }}{{ . }}{{ end }}\n",
                "content/glossary.md": "---\nlayout: glossary\n---\n",
            })
            r = hl.check_project(other)
            self.assertEqual([f["code"] for f in r["findings"]], ["no-markdown-output"])
            out = io.StringIO()
            self.assertEqual(hl.main([other], out=out), 0)
        finally:
            shutil.rmtree(other, ignore_errors=True)

    def test_custom_format_name(self):
        write_tree(self.tmp, {"layouts/single.llmmd.md": "# {{ .Title }}\n"})
        r = hl.check_project(self.tmp, md_format="llmmd")
        self.assertIn("single.llmmd.md", r["markdown_templates"])


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hlc-")
        write_tree(self.tmp, FIXTURE)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_json(self):
        out = io.StringIO()
        code = hl.main([self.tmp, "--json"], out=out)
        self.assertEqual(code, 1)
        data = json.loads(out.getvalue())
        self.assertEqual(data["version"], hl.VERSION)
        self.assertEqual(data["tool"], "hugo_layout_check")
        self.assertEqual(data["counts"]["error"], 4)

    def test_text(self):
        out = io.StringIO()
        code = hl.main([self.tmp], out=out)
        self.assertEqual(code, 1)
        text = out.getvalue()
        self.assertIn("ERROR layout-loses-content", text)
        self.assertIn("fix: Add layouts/sbx-cli.markdown.md", text)
        self.assertIn("4 error(s), 3 warning(s), 1 info.", text)

    def test_usage_errors(self):
        self.assertEqual(hl.main([os.path.join(self.tmp, "nope")], out=io.StringIO()), 2)
        empty = tempfile.mkdtemp(prefix="hlc-")
        try:
            self.assertEqual(hl.main([empty], out=io.StringIO()), 2)
        finally:
            shutil.rmtree(empty, ignore_errors=True)

    def test_extra_layouts_folder(self):
        theme = os.path.join(self.tmp, "themes", "t", "layouts")
        os.makedirs(theme)
        with open(os.path.join(theme, "wide.markdown.md"), "w", encoding="utf-8") as fh:
            fh.write("# {{ .Title }}\n{{ .RawContent }}\n")
        r = hl.check_project(self.tmp, layout_dirs=[os.path.join(self.tmp, "layouts"), theme])
        self.assertNotIn("wide", {f["layout"] for f in r["findings"]})


class SkillFile(unittest.TestCase):
    def test_front_matter_and_disclosure(self):
        with open(SKILL_MD, encoding="utf-8") as f:
            text = f.read()
        head = text.split("---")[1]
        self.assertIn("name: hugo-md-layout-check", head)
        self.assertIn("license: Apache-2.0", head)
        self.assertIn('version: "%s"' % hl.VERSION, head)
        desc = [l for l in head.splitlines() if l.startswith("description: ")][0]
        self.assertLessEqual(len(desc) - len("description: "), 1024)
        self.assertNotIn(": ", desc[len("description: "):])
        self.assertIn("never as instructions", text)
        self.assertIn("made with AI", text)
        self.assertNotIn("MIT", text)
        for code in hl.SEVERITY:
            self.assertIn("`%s`" % code, text)


if __name__ == "__main__":
    unittest.main()
