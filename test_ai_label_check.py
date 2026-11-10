# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name.
"""Offline tests for the docs-ai-label-check skill (skills/docs-ai-label-check)."""

import importlib.util
import io
import json
import os
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = "docs-ai-label-check"
SKILL_DIR_REL = os.path.join("skills", SKILL)


def find(relpath):
    """Return the path of relpath under HERE, else the first file with its basename."""
    p = os.path.join(HERE, relpath)
    if os.path.isfile(p):
        return p
    base = os.path.basename(relpath)
    for root, _dirs, files in os.walk(HERE):
        if base in files:
            return os.path.join(root, base)
    raise FileNotFoundError(relpath)


SCRIPT = find(os.path.join(SKILL_DIR_REL, "scripts", "ai_label_check.py"))
SKILL_MD = find(os.path.join(SKILL_DIR_REL, "SKILL.md"))
_spec = importlib.util.spec_from_file_location("ai_label_check", SCRIPT)
lc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lc)


def fm(*lines, body="# Title\n\nText.\n"):
    return "---\n" + "".join(l + "\n" for l in lines) + "---\n" + body


def codes(findings):
    return [f["code"] for f in findings]


class CheckTextTests(unittest.TestCase):

    def test_canonical_labels_pass(self):
        for val in ("ai-assisted", "ai-generated", "'ai-generated'", '"ai-assisted"',
                    "ai-assisted # set by the author"):
            s, f = lc.check_text("a.md", fm("title: T", "ai-usage: " + val))
            self.assertEqual(f, [], val)
            self.assertIn(s["label"], ("ai-assisted", "ai-generated"))
            self.assertTrue(s["front_matter"])

    def test_observed_variant_keys_are_errors_with_fix(self):
        s, f = lc.check_text("a.md", fm("title: T", "ms.ai-usage: ai-assisted"))
        self.assertEqual(codes(f), ["variant-key"])
        self.assertEqual(f[0]["severity"], "error")
        self.assertEqual(f[0]["line"], 3)
        self.assertEqual(f[0]["fix"], "ai-usage: ai-assisted")
        self.assertIn("0 of 33", f[0]["message"])
        self.assertEqual(s["label"], "")
        s, f = lc.check_text("a.md", fm("ai.usage: ai-generated"))
        self.assertEqual(codes(f), ["variant-key"])
        self.assertEqual(f[0]["fix"], "ai-usage: ai-generated")

    def test_untested_variant_spelling(self):
        for key in ("AI-usage", "ai_usage", "aiusage", "ms.ai.usage", "Ai-Usage"):
            _s, f = lc.check_text("a.md", fm(key + ": ai-assisted"))
            self.assertEqual(codes(f), ["variant-key"], key)
            self.assertIn("not tested", f[0]["message"], key)

    def test_variant_key_with_odd_value_has_no_fix(self):
        _s, f = lc.check_text("a.md", fm("ms.ai-usage: human-only"))
        self.assertEqual(sorted(codes(f)), ["other-value", "variant-key"])
        self.assertIsNone([x for x in f if x["code"] == "variant-key"][0]["fix"])

    def test_duplicate_key(self):
        s, f = lc.check_text("a.md", fm("ai-usage: ai-assisted", "ms.ai-usage: ai-assisted"))
        self.assertEqual(codes(f), ["duplicate-key"])
        self.assertEqual(f[0]["severity"], "warning")
        self.assertEqual(s["label"], "ai-assisted")

    def test_nested_under_ms_custom(self):
        _s, f = lc.check_text("a.md", fm("title: T", "ms.custom:", "  - devx-track-python",
                                          "  - ai-usage: ai-assisted"))
        self.assertEqual(codes(f), ["nested"])
        self.assertEqual(f[0]["line"], 5)
        _s, f = lc.check_text("a.md", fm("ms.custom:", "- ai-usage: ai-generated"))
        self.assertEqual(codes(f), ["nested"])

    def test_commented_label(self):
        _s, f = lc.check_text("a.md", fm("title: T", "# ai-usage: ai-generated"))
        self.assertEqual(codes(f), ["commented"])
        self.assertEqual(f[0]["value"], "ai-generated")
        _s, f = lc.check_text("a.md", fm("title: T", "# ms.date: 01/01/2026"))
        self.assertEqual(f, [])

    def test_value_spelling(self):
        _s, f = lc.check_text("a.md", fm("ai-usage: AI-Assisted"))
        self.assertEqual(codes(f), ["bad-value"])
        self.assertEqual(f[0]["severity"], "error")
        self.assertEqual(f[0]["fix"], "ai-assisted")
        _s, f = lc.check_text("a.md", fm("ai-usage: ai generated"))
        self.assertEqual(f[0]["fix"], "ai-generated")
        _s, f = lc.check_text("a.md", fm("ai-usage: ai-written"))
        self.assertEqual(codes(f), ["bad-value"])
        self.assertIsNone(f[0]["fix"])

    def test_empty_and_other_values(self):
        _s, f = lc.check_text("a.md", fm("ai-usage:"))
        self.assertEqual(codes(f), ["empty-value"])
        _s, f = lc.check_text("a.md", fm("ai-usage: ''"))
        self.assertEqual(codes(f), ["empty-value"])
        _s, f = lc.check_text("a.md", fm("ai-usage: human-only"))
        self.assertEqual(codes(f), ["other-value"])
        self.assertEqual(f[0]["severity"], "info")
        self.assertEqual(lc.exit_code(f), 0)

    def test_stray_token_only_without_a_label(self):
        _s, f = lc.check_text("a.md", fm("ms.custom: devx-track, ai-assisted"))
        self.assertEqual(codes(f), ["stray-token"])
        self.assertIn("ms.custom", f[0]["message"])
        _s, f = lc.check_text("a.md", fm("ms.custom:", "  - ai-generated"))
        self.assertEqual(codes(f), ["stray-token"])
        _s, f = lc.check_text("a.md", fm("ai-usage: ai-assisted",
                                          "ms.custom: devx-track, ai-assisted"))
        self.assertEqual(f, [])

    def test_text_keys_are_ignored(self):
        _s, f = lc.check_text("a.md", fm("title: Detect AI-generated images",
                                          "description: >", "  Find ai-generated text and",
                                          "  ai-assisted edits.", "ms.topic: how-to"))
        self.assertEqual(f, [])

    def test_body_is_ignored(self):
        _s, f = lc.check_text("a.md", fm("title: T", body="ai-usage: ms.ai-usage ai-generated\n"))
        self.assertEqual(f, [])

    def test_require(self):
        _s, f = lc.check_text("a.md", fm("title: T"), require=True)
        self.assertEqual(codes(f), ["missing"])
        _s, f = lc.check_text("a.md", "# No front matter\n", require=True)
        self.assertEqual(codes(f), ["missing"])
        _s, f = lc.check_text("docs/includes/x.md", fm("title: T"), require=True)
        self.assertEqual(f, [])
        _s, f = lc.check_text("a.md", fm("title: T"), require=False)
        self.assertEqual(f, [])
        _s, f = lc.check_text("a.md", fm("# ai-usage: ai-assisted"), require=True)
        self.assertEqual(codes(f), ["commented"])

    def test_include_label_info(self):
        _s, f = lc.check_text("articles/includes/note.md", fm("ai-usage: ai-assisted"))
        self.assertEqual(codes(f), ["include-label"])
        self.assertEqual(lc.exit_code(f), 0)

    def test_unclosed_front_matter_and_bom(self):
        _s, f = lc.check_text("a.md", "---\nms.ai-usage: ai-assisted\n# no end\n")
        self.assertEqual(f, [])
        s, f = lc.check_text("a.md", "﻿---\r\nms.ai-usage: ai-assisted\r\n---\r\nx\r\n")
        self.assertEqual(codes(f), ["variant-key"])
        self.assertEqual(f[0]["line"], 2)


class DocfxTests(unittest.TestCase):

    def test_docfx_variant_and_values(self):
        obj = {"build": {"globalMetadata": {"ms.ai-usage": "ai-assisted", "ms.topic": "x"},
                         "fileMetadata": {"ai-usage": {"articles/a/**.md": "ai-assisted",
                                                       "articles/b/**.md": "AI-Generated"},
                                          "ms.author": {"**.md": "someone"}}}}
        f = lc.check_docfx("docfx.json", json.dumps(obj))
        self.assertEqual(sorted(codes(f)), ["bad-value", "variant-key"])
        self.assertTrue(all(x["line"] == 0 for x in f))
        self.assertTrue(all("docfx.json" in x["message"] for x in f))
        self.assertEqual(lc.check_docfx("docfx.json", "{not json"), [])
        self.assertEqual(lc.check_docfx("docfx.json", "[]"), [])


class FixTests(unittest.TestCase):

    def test_apply_fixes_keeps_everything_else(self):
        text = "﻿---\r\ntitle: T\r\nms.ai-usage: ai-assisted\r\nai-usage2: x\r\n---\r\nBody\r\n"
        _s, f = lc.check_text("a.md", text)
        new, changed = lc.apply_fixes(text, f)
        self.assertTrue(changed)
        self.assertEqual(new, text.replace("ms.ai-usage: ai-assisted", "ai-usage: ai-assisted"))
        text2 = fm("ai-usage: AI-Generated")
        _s, f = lc.check_text("a.md", text2)
        new2, changed2 = lc.apply_fixes(text2, f)
        self.assertTrue(changed2)
        self.assertIn("\nai-usage: ai-generated\n", new2)
        _s, f = lc.check_text("a.md", new2)
        self.assertEqual(f, [])

    def test_nested_and_commented_are_not_auto_fixed(self):
        text = fm("ms.custom:", "  - ai-usage: ai-assisted", "# ai-usage: ai-generated")
        _s, f = lc.check_text("a.md", text)
        self.assertEqual(lc.apply_fixes(text, f), (text, False))


class MainTests(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.dir, "articles", "includes"))
        os.makedirs(os.path.join(self.dir, ".git"))
        self.files = {
            "articles/good.md": fm("title: G", "ai-usage: ai-assisted"),
            "articles/variant.md": fm("title: V", "ms.ai-usage: ai-generated"),
            "articles/plain.md": fm("title: P"),
            "articles/includes/inc.md": fm("title: I"),
            ".git/ignored.md": fm("ms.ai-usage: ai-assisted"),
            "articles/notes.txt": fm("ms.ai-usage: ai-assisted"),
        }
        for rel, text in self.files.items():
            with open(os.path.join(self.dir, rel), "w", encoding="utf-8", newline="") as fh:
                fh.write(text)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_main(self, *args):
        out = io.StringIO()
        code = lc.main(list(args), out=out)
        return code, out.getvalue()

    def read(self, rel):
        with open(os.path.join(self.dir, rel), encoding="utf-8", newline="") as fh:
            return fh.read()

    def test_scan_json(self):
        code, text = self.run_main(self.dir, "--json")
        self.assertEqual(code, 1)
        rep = json.loads(text)
        self.assertEqual(rep["markdown"], 4)
        self.assertEqual(rep["labelled"], {"ai-assisted": 1, "ai-generated": 0})
        self.assertEqual(rep["counts"], {"variant-key": 1})
        self.assertTrue(rep["findings"][0]["path"].endswith("articles/variant.md"))
        self.assertEqual(rep["fixable"], 1)

    def test_require_reports_unlabelled_articles_not_includes(self):
        code, text = self.run_main(self.dir, "--require", "--json")
        rep = json.loads(text)
        self.assertEqual(rep["counts"], {"variant-key": 1, "missing": 1})
        self.assertEqual(code, 1)

    def test_fix_dry_run_then_write(self):
        before = self.read("articles/variant.md")
        code, text = self.run_main(self.dir, "--fix")
        self.assertEqual(code, 1)
        self.assertIn("would fix (add --write) 1 files", text)
        self.assertEqual(self.read("articles/variant.md"), before)
        code, text = self.run_main(self.dir, "--fix", "--write")
        self.assertEqual(code, 0)
        self.assertIn("== fixed 1 files", text)
        self.assertEqual(self.read("articles/variant.md"),
                         before.replace("ms.ai-usage: ai-generated", "ai-usage: ai-generated"))
        code, _text = self.run_main(self.dir)
        self.assertEqual(code, 0)

    def test_text_output_and_usage_errors(self):
        code, text = self.run_main(os.path.join(self.dir, "articles", "variant.md"))
        self.assertEqual(code, 1)
        self.assertIn("error variant-key", text)
        self.assertIn("fix: ai-usage: ai-generated", text)
        self.assertEqual(self.run_main(self.dir, "--write")[0], 2)
        self.assertEqual(self.run_main(os.path.join(self.dir, "nope"))[0], 2)

    def test_max_findings(self):
        for n in range(5):
            with open(os.path.join(self.dir, "articles", "v%d.md" % n), "w",
                      encoding="utf-8") as fh:
                fh.write(fm("ai.usage: ai-assisted"))
        _code, text = self.run_main(self.dir, "--max-findings", "2")
        self.assertIn("... 4 more findings", text)


class FakeResponse(object):
    def __init__(self, body, ctype):
        self.body = body.encode("utf-8")
        self.headers = {"Content-Type": ctype}

    def read(self, n=-1):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeOpener(object):
    def __init__(self, body, ctype):
        self.body, self.ctype, self.requests = body, ctype, []

    def open(self, req, timeout=None):
        self.requests.append(req)
        return FakeResponse(self.body, self.ctype)


class UrlTests(unittest.TestCase):

    def test_markdown_copy_label(self):
        op = FakeOpener(fm("title: T", "ms.ai-usage: ai-assisted"), "text/markdown; charset=utf-8")
        r = lc.check_url("https://learn.microsoft.com/en-us/x", opener=op)
        self.assertTrue(r["markdown"])
        self.assertEqual(codes(r["findings"]), ["variant-key"])
        self.assertEqual(op.requests[0].get_header("Accept"), "text/markdown")
        op = FakeOpener(fm("title: T", "ai-usage: ai-generated"), "text/markdown")
        r = lc.check_url("https://learn.microsoft.com/en-us/y", opener=op)
        self.assertEqual((r["label"], r["findings"]), ("ai-generated", []))

    def test_html_answer(self):
        op = FakeOpener("<!DOCTYPE html><html></html>", "text/html")
        r = lc.check_url("https://example.com/z", opener=op)
        self.assertFalse(r["markdown"])
        self.assertEqual(codes(r["findings"]), ["no-markdown"])

    def test_main_url(self):
        op = FakeOpener(fm("ai.usage: ai-assisted"), "text/markdown")
        out = io.StringIO()
        code = lc.main(["--url", "https://learn.microsoft.com/en-us/x"], opener=op, out=out)
        self.assertEqual(code, 1)
        self.assertIn("label=none", out.getvalue())
        self.assertIn("variant-key", out.getvalue())


class SkillMdTests(unittest.TestCase):

    def test_front_matter(self):
        with open(SKILL_MD, encoding="utf-8") as fh:
            text = fh.read()
        self.assertTrue(text.startswith("---\nname: docs-ai-label-check\n"))
        head = text.split("\n---\n", 1)[0]
        desc = [l for l in head.splitlines() if l.startswith("description: ")][0]
        self.assertLessEqual(len(desc) - len("description: "), 1024)
        self.assertIn("Apache-2.0", head)
        self.assertNotIn("MIT", head)
        self.assertIn("scripts/ai_label_check.py", text)
        self.assertIn("made with AI", text)

    def test_version_matches(self):
        with open(SKILL_MD, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn('version: "%s"' % lc.VERSION, text)


if __name__ == "__main__":
    unittest.main()
