# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""Offline tests for the md-html-leak-check skill (skills/md-html-leak-check).

The HTML in these fixtures follows the shapes Docsy's shortcode templates emit
(tabpane, alert, swaggerui) and Hugo's code highlighter, written fresh here.
"""

import importlib.util
import io
import json
import os
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR_REL = os.path.join("skills", "md-html-leak-check")


def find(relpath):
    p = os.path.join(HERE, relpath)
    if os.path.isfile(p):
        return p
    base = os.path.basename(relpath)
    for root, _dirs, files in os.walk(HERE):
        if base in files:
            return os.path.join(root, base)
    raise FileNotFoundError(relpath)


SCRIPT = find(os.path.join(SKILL_DIR_REL, "scripts", "md_html_leak.py"))
SKILL_MD = find(os.path.join(SKILL_DIR_REL, "SKILL.md"))
_spec = importlib.util.spec_from_file_location("md_html_leak", SCRIPT)
mh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mh)

ALERT = ('<div class="alert alert-warning" role="alert">\n'
         '<div class="h4 alert-heading" role="heading">Note</div>\n'
         '\n'
         'Be careful.\n'
         '</div>\n')

TABPANE = ('<ul class="nav nav-tabs" id="tabs-01-tablist-abc" role="tablist">\n'
           '<li class="nav-item"><button class="nav-link active" id="tabs-01-00-tab-abc" '
           'data-bs-toggle="tab">Go</button></li>\n'
           '</ul>\n'
           '<div class="tab-content" id="tabs-01-content-abc">\n'
           '<div class="tab-pane fade show active" id="tabs-01-00-abc" role="tabpanel">\n'
           '<div class="highlight"><pre tabindex="0" class="chroma"><code class="language-go" '
           'data-lang="go"><span class="line">x := 1</span></code></pre></div>\n'
           '<p>Plain</p>\n'
           '</div>\n'
           '</div>\n')

SWAGGER_BODY = '\n  window.onload = function () { const ui = SwaggerUIBundle({ url: "/a.yaml" }); };\n'
SWAGGER = '<div id="docsy_swagger_ui"></div>\n<script>' + SWAGGER_BODY + '</script>\n'


class TestNotCounted(unittest.TestCase):
    def test_fenced_code_is_skipped(self):
        r = mh.scan('Intro\n\n```html\n<div class="x">hi</div>\n```\n\nEnd\n')
        self.assertEqual(r["tags"], 0)
        self.assertGreater(r["code_chars"], 0)

    def test_tilde_fence_needs_tilde_to_close(self):
        r = mh.scan('~~~\n<div>\n```\n<div>\n~~~\nafter <div class="a">x</div>\n')
        self.assertEqual(r["tags"], 2)

    def test_fence_in_blockquote(self):
        r = mh.scan('> ```\n> <div>\n> ```\n')
        self.assertEqual(r["tags"], 0)

    def test_inline_code_is_skipped(self):
        self.assertEqual(mh.scan("Use `<div>` here.\n")["tags"], 0)
        self.assertEqual(mh.scan("A `` <div> ` `` span.\n")["tags"], 0)

    def test_prose_placeholders_are_not_tags(self):
        text = ("Run it with <name> and <path> and List<String> and <your-image-name> "
                "and <path to file> and <a few words> and <https://example.com>.\n")
        self.assertEqual(mh.scan(text)["tags"], 0)

    def test_comments_are_counted_separately(self):
        r = mh.scan("<!-- a <div> b -->\nText\n")
        self.assertEqual(r["tags"], 0)
        self.assertEqual(r["comments"], 1)


class TestAttribution(unittest.TestCase):
    def test_docsy_alert(self):
        r = mh.scan(ALERT)
        self.assertEqual(r["tags"], 4)
        self.assertEqual(r["structural_tags"], 4)
        self.assertEqual(list(r["labels"]), ["docsy:alert"])
        self.assertEqual(r["docsy_labels"], ["docsy:alert"])

    def test_tabpane_with_highlighted_code(self):
        r = mh.scan(TABPANE)
        self.assertEqual(r["labels"]["docsy:tabpane"]["tags"], 12)
        self.assertEqual(r["labels"]["hugo:highlight"]["tags"], 8)
        self.assertEqual(r["tags"], 20)
        self.assertEqual(r["structural_tags"], 16)
        self.assertEqual(r["docsy_labels"], ["docsy:tabpane"])
        self.assertEqual(r["source_labels"], ["docsy:tabpane", "hugo:highlight"])

    def test_swaggerui_script_body_is_markup(self):
        r = mh.scan(SWAGGER)
        self.assertEqual(r["docsy_labels"], ["docsy:swaggerui"])
        self.assertEqual(r["labels"]["docsy:swaggerui"]["tags"], 4)
        expected = (len('<div id="docsy_swagger_ui">') + len("</div>") + len("<script>")
                    + len(SWAGGER_BODY) + len("</script>"))
        self.assertEqual(r["markup_chars"], expected)

    def test_redoc_element(self):
        r = mh.scan('<redoc spec-url="/api.yaml"></redoc>\n')
        self.assertEqual(r["docsy_labels"], ["docsy:redoc"])
        self.assertEqual(r["tags"], 2)

    def test_plain_html_by_element(self):
        r = mh.scan("<details>\n<summary>More</summary>\n\nText\n</details>\n")
        self.assertEqual(r["labels"]["html:details"]["tags"], 4)
        self.assertEqual(r["source_labels"], [])

    def test_inline_only(self):
        r = mh.scan('See <a href="/x">x</a> and <br> and <kbd>Ctrl</kbd>.\n')
        self.assertEqual(r["tags"], 5)
        self.assertEqual(r["structural_tags"], 0)
        self.assertEqual(list(r["labels"]), ["html:inline"])


class TestShare(unittest.TestCase):
    def test_markup_share(self):
        text = '<div class="x">\nhello\n</div>\n'
        r = mh.scan(text)
        self.assertEqual(r["text_chars"], len(text))
        self.assertEqual(r["markup_chars"], 21)
        self.assertAlmostEqual(r["markup_share"], round(21 / len(text), 4))
        self.assertEqual(list(r["labels"]), ["html:other"])

    def test_empty(self):
        r = mh.scan("")
        self.assertEqual(r["tags"], 0)
        self.assertEqual(r["markup_share"], 0.0)


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name, text):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        return p

    def test_json_and_exit_codes(self):
        bad = self.write("bad.md", ALERT)
        good = self.write("good.md", "# Title\n\nJust text with <kbd>Ctrl</kbd>.\n")
        out = io.StringIO()
        self.assertEqual(mh.main([bad, "--json"], out=out), 1)
        data = json.loads(out.getvalue())
        self.assertEqual(data["version"], mh.VERSION)
        self.assertEqual(data["results"][0]["docsy_labels"], ["docsy:alert"])
        out = io.StringIO()
        self.assertEqual(mh.main([good], out=out), 0)
        self.assertIn("0 structural", out.getvalue())

    def test_folder_and_usage_errors(self):
        self.write("a.md", ALERT)
        self.write("b.md", "plain\n")
        out = io.StringIO()
        self.assertEqual(mh.main([self.tmp, "--json"], out=out), 1)
        self.assertEqual(len(json.loads(out.getvalue())["results"]), 2)
        self.assertEqual(mh.main([], out=io.StringIO()), 2)
        self.assertEqual(mh.main([os.path.join(self.tmp, "missing.md")], out=io.StringIO()), 2)

    def test_html_page_is_refused(self):
        self.assertTrue(mh.looks_like_html("  <!DOCTYPE html><html>"))
        self.assertFalse(mh.looks_like_html("# Title\n<div>"))


class TestSkillFile(unittest.TestCase):
    def test_skill_front_matter(self):
        with open(SKILL_MD, encoding="utf-8") as fh:
            text = fh.read()
        self.assertTrue(text.startswith("---\nname: md-html-leak-check\n"))
        self.assertIn("description:", text.split("---")[1])
        self.assertIn("Apache-2.0", text)
        self.assertIn("made with AI", text)


if __name__ == "__main__":
    unittest.main()
