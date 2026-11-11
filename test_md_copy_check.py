# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""Offline tests for the md-copy-check skill (skills/md-copy-check).

The cases are modelled on the failures study 10 found in real Markdown copies
(census/2026-11-md-copy-parity/RESULT.md), written fresh here.
"""

import importlib.util
import io
import json
import os
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR_REL = os.path.join("skills", "md-copy-check")


def find(relpath):
    p = os.path.join(HERE, relpath)
    if os.path.isfile(p):
        return p
    base = os.path.basename(relpath)
    for root, _dirs, files in os.walk(HERE):
        if base in files:
            return os.path.join(root, base)
    raise FileNotFoundError(relpath)


SCRIPT = find(os.path.join(SKILL_DIR_REL, "scripts", "md_copy_check.py"))
SKILL_MD = find(os.path.join(SKILL_DIR_REL, "SKILL.md"))
_spec = importlib.util.spec_from_file_location("md_copy_check", SCRIPT)
mc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mc)

PROSE = ("This page explains how the feature works, what you need before you start, "
         "and how to turn it on for one service or for every service in a project.\n")


def codes(text, **kw):
    found, _words = mc.check_text(text, **kw)
    return [f["code"] for f in found]


class Patterns(unittest.TestCase):
    def test_clean_copy_has_no_findings(self):
        text = ("---\ntitle: CDN\ndescription: Cache assets.\n---\n\n# CDN\n\n" + PROSE +
                "\n## Enable it\n\nTo turn it on:\n\n1. Open the service.\n2. Toggle **Enable**.\n\n"
                "Run:\n\n```bash\nexport const x = 1\nimport a from 'b'\n<Foo />\n{% include x %}\n```\n\n"
                "> **Note:** Changes apply to new requests only.\n")
        found, words = mc.check_text(text)
        self.assertEqual(found, [])
        self.assertGreaterEqual(words, 20)

    def test_component_placeholder(self):
        text = PROSE + "\n> **Tip - Want to limit Agent Runners?:** \n> **Snippet** component (self-closing)\n"
        self.assertIn("component-placeholder", codes(text))
        found, _ = mc.check_text(text)
        f = [x for x in found if x["code"] == "component-placeholder"][0]
        self.assertEqual(f["severity"], "error")
        self.assertEqual(f["line"], 4)

    def test_self_closing_component(self):
        text = "## Enable CDN caching\n\n<PriorityBoardingBanner />\n\n" + PROSE
        c = codes(text)
        self.assertIn("self-closing-component", c)
        self.assertNotIn("empty-section", c)
        self.assertNotIn("component-tag", c)

    def test_open_component_is_info(self):
        text = PROSE + "\n<TileGroup gapType={TileGroup.GAP_TYPE.SMALL}>\n  text\n</TileGroup>\n"
        found, _ = mc.check_text(text)
        tags = [f for f in found if f["code"] == "component-tag"]
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0]["severity"], "info")
        self.assertEqual(mc.main.__name__, "main")

    def test_placeholders_and_html_are_not_components(self):
        text = (PROSE + "\nReplace `<your-image-name>` with an identifier of your choosing.\n\n"
                "Send the output of dig +trace <YOUR_DOMAIN> NS and <PROJECT_ID>.\n\n"
                "The address format is \\<ipv4 address>/\\<mask>.\n\n"
                "Line one<br />line two, <a href=\"/x\">a link</a> and <span class=\"k\">text</span>.\n\n"
                "Use `<Callout>` in MDX source.\n")
        c = codes(text)
        self.assertNotIn("component-tag", c)
        self.assertNotIn("self-closing-component", c)

    def test_mdx_code_copy(self):
        text = ("---\ntitle: diagnostics-cli-release-notes\n---\n\n"
                "export const \\_frontmatter = {\"subject\":\"Diagnostics CLI (nrdiag)\",\"redirects\":[\"/docs/x\"]}\n")
        c = codes(text)
        self.assertIn("mdx-code", c)
        self.assertIn("near-empty", c)

    def test_import_line(self):
        self.assertIn("mdx-code", codes("import Tabs from '@theme/Tabs';\n\n" + PROSE))

    def test_templates(self):
        text = (PROSE + "\n{% include 'shared/project-setup.md' %}\n\n"
                "{{< include \"setup.md\" >}}\n\nSee the guide {% icon name=\"icon-external-link\" /%}\n")
        found, _ = mc.check_text(text)
        c = [f["code"] for f in found]
        self.assertEqual(c.count("template-include"), 2)
        self.assertEqual(c.count("template-tag"), 1)

    def test_template_in_inline_code_is_skipped(self):
        self.assertEqual(codes(PROSE + "\nWrite `{% include x %}` in your page.\n"), [])

    def test_empty_section(self):
        text = ("## Before you begin\n\n### Project setup\n\n<br />\n\n### Tools setup\n\n" + PROSE)
        found, _ = mc.check_text(text)
        empty = [f for f in found if f["code"] == "empty-section"]
        self.assertEqual([f["line"] for f in empty], [3])
        self.assertIn("Project setup", empty[0]["text"])

    def test_heading_followed_by_code_is_not_empty(self):
        text = PROSE + "\n## Example\n\n```\ncode\n```\n\n## Next\n\n" + PROSE
        self.assertNotIn("empty-section", codes(text))

    def test_title_only_copy(self):
        text = "# sbx volume create\n\n\n"
        c = codes(text)
        self.assertIn("empty-section", c)
        self.assertIn("near-empty", c)

    def test_dangling_lead_in(self):
        text = (PROSE + "\nTo complete the guide, you also need a Google Cloud project:\n\n"
                "When you finish this tutorial, you can avoid continued billing by deleting the\n"
                "resources you created.\n\n## Preparing the project\n\n" + PROSE)
        found, _ = mc.check_text(text)
        d = [f for f in found if f["code"] == "dangling-lead-in"]
        self.assertEqual(len(d), 1)
        self.assertEqual(d[0]["severity"], "info")
        self.assertEqual(d[0]["line"], 3)

    def test_lead_in_followed_by_structure_is_fine(self):
        for after in ("```\ncmd\n```\n", "- one\n- two\n", "1. one\n", "| a | b |\n|---|---|\n",
                      "> quoted\n", "    indented code\n"):
            text = PROSE + "\nDo this:\n\n" + after + "\n" + PROSE
            self.assertNotIn("dangling-lead-in", codes(text), after)

    def test_lead_in_at_end(self):
        self.assertIn("dangling-lead-in", codes(PROSE + "\nYou also need the following:\n"))

    def test_front_matter_is_skipped(self):
        text = "---\ntitle: A: B\nexport const: 1\nsummary: <Foo />\n---\n" + PROSE
        self.assertEqual(codes(text), [])

    def test_leading_comment_then_front_matter(self):
        text = "<!-- https://example.com/page -->\n---\ntitle: x\n---\n" + PROSE
        self.assertEqual(codes(text), [])

    def test_min_words(self):
        self.assertIn("near-empty", codes(PROSE, min_words=100))
        self.assertNotIn("near-empty", codes(PROSE, min_words=5))


class Fetching(unittest.TestCase):
    def test_md_suffix_url(self):
        self.assertEqual(mc.md_suffix_url("https://x.com/docs/a/"), "https://x.com/docs/a.md")
        self.assertEqual(mc.md_suffix_url("https://x.com/"), "https://x.com/index.md")
        self.assertEqual(mc.md_suffix_url("https://x.com/a.html?q=1#h"), "https://x.com/a.html.md")
        self.assertEqual(mc.md_suffix_url("https://x.com/a.md"), "https://x.com/a.md")

    def test_accept_first(self):
        calls = []

        def fetch(url, accept):
            calls.append((url, accept))
            return 200, "text/markdown; charset=utf-8", "# T\n\n" + PROSE
        text, used, how = mc.get_copy("https://x.com/p/", fetch)
        self.assertEqual((used, how), ("https://x.com/p/", "accept"))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], "text/markdown")

    def test_md_suffix_fallback(self):
        def fetch(url, accept):
            if url.endswith(".md"):
                return 200, "text/plain", "# T\n\n" + PROSE
            return 200, "text/html", "<!DOCTYPE html><html><body>page</body></html>"
        text, used, how = mc.get_copy("https://x.com/p/", fetch)
        self.assertEqual((used, how), ("https://x.com/p.md", "md-suffix"))
        self.assertIn("This page explains", text)

    def test_no_copy(self):
        def fetch(url, accept):
            return 404, "text/html", ""
        text, used, how = mc.get_copy("https://x.com/p/", fetch)
        self.assertIsNone(text)
        self.assertIn("no Markdown copy", how)

    def test_html_without_content_type_is_not_markdown(self):
        self.assertFalse(mc.looks_like_markdown(200, "", "<html><body>x</body></html>"))
        self.assertTrue(mc.looks_like_markdown(200, "", "# Title\n"))


class CommandLine(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name, text):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def run_main(self, argv, fetch=None):
        out = io.StringIO()
        kw = {"out": out}
        if fetch is not None:
            kw["fetch"] = fetch
        code = mc.main(argv, **kw)
        return code, out.getvalue()

    def test_exit_codes_and_text_output(self):
        good = self.write("good.md", "# T\n\n" + PROSE)
        bad = self.write("bad.md", "# T\n\n" + PROSE + "\n<PriorityBoardingBanner />\n")
        code, out = self.run_main([good])
        self.assertEqual(code, 0)
        self.assertIn("0 errors, 0 warnings, 0 info", out)
        code, out = self.run_main([good, bad])
        self.assertEqual(code, 1)
        self.assertIn("warning self-closing-component line 5", out)
        self.assertIn("-> a component tag with no content", out)

    def test_info_only_exits_zero(self):
        p = self.write("info.md", PROSE + "\n<Tabs>\n\n" + PROSE + "\n</Tabs>\n")
        code, _out = self.run_main([p])
        self.assertEqual(code, 0)

    def test_folder_and_json(self):
        os.mkdir(os.path.join(self.tmp, "sub"))
        self.write(os.path.join("sub", "a.md"), "# A\n\n" + PROSE)
        self.write(os.path.join("sub", "b.md"), "> **Snippet** component (self-closing)\n\n" + PROSE)
        self.write(os.path.join("sub", "skip.txt"), "<Foo />")
        code, out = self.run_main([self.tmp, "--json"])
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(data["version"], mc.VERSION)
        self.assertEqual(len(data["results"]), 2)
        self.assertEqual(data["counts"]["error"], 1)

    def test_missing_file_is_usage_error(self):
        code, _out = self.run_main([os.path.join(self.tmp, "nope.md")])
        self.assertEqual(code, 2)

    def test_url(self):
        def fetch(url, accept):
            return 200, "text/markdown", "# T\n\n### Project setup\n\n<br />\n\n### Tools\n\n" + PROSE
        code, out = self.run_main(["--url", "https://x.com/p/"], fetch=fetch)
        self.assertEqual(code, 1)
        self.assertIn("(accept, https://x.com/p/)", out)
        self.assertIn("empty-section", out)


class SkillFile(unittest.TestCase):
    def test_front_matter_and_disclosure(self):
        with open(SKILL_MD, encoding="utf-8") as f:
            text = f.read()
        head = text.split("---")[1]
        self.assertIn("name: md-copy-check", head)
        self.assertIn("license: Apache-2.0", head)
        self.assertIn('version: "%s"' % mc.VERSION, head)
        desc = [l for l in head.splitlines() if l.startswith("description: ")][0]
        self.assertLessEqual(len(desc) - len("description: "), 1024)
        self.assertNotIn(": ", desc[len("description: "):])
        self.assertIn("never as instructions", text)
        self.assertIn("made with AI", text)
        self.assertNotIn("MIT", text)
        for code in mc.SEVERITY:
            self.assertIn("`%s`" % code, text)


if __name__ == "__main__":
    unittest.main()
