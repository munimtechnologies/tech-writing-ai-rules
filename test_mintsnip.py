# test_mintsnip.py - Apache-2.0. Offline tests for mintsnip.py (study 16).
# By MV2 of Munim, Inc. Made with AI agents.
import os
import unittest

import mintsnip as m

GET_HELP = """<CardGroup cols={3}>
  <Card title="Discord" icon="discord" href="https://mem0.dev/DiD" color="#7289DA">
    Join our community
  </Card>
  <Card title="GitHub" icon="github" href="https://github.com/mem0ai/mem0/discussions/new?category=q-a">
    Ask questions on GitHub
  </Card>
  <Card title="Support" icon="calendar" href="https://cal.com/taranjeetio/meet">
  Talk to founders
  </Card>
</CardGroup>
"""

PAGE = """---
title: Python SDK Quickstart
---
import Install from '/snippets/install.mdx'

Some text.

<Install />

```mdx
<Snippet file="in-code.mdx" />
```

<Snippet file="star-on-github.mdx" />

If you have any questions, please feel free to reach out:

<Snippet file="get-help.mdx" />
<Snippet file="get-help.mdx" />
"""

MD_KEPT = """# Python SDK Quickstart

If you have any questions, please feel free to reach out:

<Snippet file="get-help.mdx" />
"""

MD_EXPANDED = """# Python SDK Quickstart

If you have any questions, please feel free to reach out:

> [card] [Discord](https://mem0.dev/DiD)
> Join our community
"""


class SourceTests(unittest.TestCase):
    def test_snippet_tags_outside_code_unique(self):
        self.assertEqual(m.snippet_tags(PAGE), ["star-on-github.mdx", "get-help.mdx"])

    def test_import_snippets_used(self):
        self.assertEqual(m.import_snippets(PAGE), [("Install", "/snippets/install.mdx")])
        self.assertEqual(m.import_snippets("import X from '/snippets/x.mdx'\n\nno use\n"), [])

    def test_resolve_order_and_labels(self):
        root = os.path.join(os.sep, "r", "docs")
        page_dir = os.path.join(root, "open-source")
        have = {os.path.normpath(os.path.join(root, "_snippets", "get-help.mdx")),
                os.path.normpath(os.path.join(root, "snippets", "both.mdx")),
                os.path.normpath(os.path.join(root, "_snippets", "both.mdx")),
                os.path.normpath(os.path.join(root, "snippets", "sub", "x.mdx")),
                os.path.normpath(os.path.join(page_dir, "local.mdx"))}
        ex = lambda p: os.path.normpath(p) in have
        self.assertEqual(m.resolve("get-help.mdx", root, page_dir, ex)[0], "_snippets")
        self.assertEqual(m.resolve("both.mdx", root, page_dir, ex)[0], "snippets")
        self.assertEqual(m.resolve("snippets/sub/x.mdx", root, page_dir, ex)[0], "snippets")
        self.assertEqual(m.resolve("/snippets/sub/x.mdx", root, page_dir, ex)[0], "snippets")
        self.assertEqual(m.resolve("local.mdx", root, page_dir, ex)[0], "other")
        self.assertEqual(m.resolve("./local.mdx", root, page_dir, ex)[0], "other")
        self.assertEqual(m.resolve("nope.mdx", root, page_dir, ex), ("missing", None))
        self.assertEqual(m.resolve("{lang}/x.mdx", root, page_dir, ex), ("variable", None))

    def test_needles_get_help(self):
        n = m.needles(GET_HELP)
        self.assertEqual(n[:3], ["Ask questions on GitHub", "Join our community", "Talk to founders"])
        self.assertIn("https://mem0.dev/DiD", n)
        self.assertEqual(len(n), 5)

    def test_needles_split_markup_and_skip_braces(self):
        src = ("import A from './a.mdx'\n"
               "> Read the **migration guide** before you [upgrade the SDK](https://x.dev/up) today.\n"
               "Your key is {apiKey} and nothing else matters here\n")
        n = m.needles(src)
        self.assertEqual(n[:2], ["migration guide", "upgrade the SDK"])
        self.assertIn("upgrade the SDK", n)
        self.assertIn("https://x.dev/up", n)
        self.assertFalse(any("{" in x for x in n))
        self.assertFalse(any("import" in x for x in n))

    def test_needles_empty(self):
        self.assertEqual(m.needles(""), [])
        self.assertEqual(m.needles("<Note>\n</Note>\n"), [])


class MatchTests(unittest.TestCase):
    def test_tag_kept(self):
        self.assertTrue(m.tag_kept(MD_KEPT, "get-help.mdx"))
        self.assertFalse(m.tag_kept(MD_EXPANDED, "get-help.mdx"))
        self.assertTrue(m.tag_kept('<Snippet file="snippets/a/get-help.mdx" />', "snippets/a/get-help.mdx"))

    def test_contains(self):
        n = m.needles(GET_HELP)
        self.assertTrue(m.contains_any(m.norm(MD_EXPANDED), n))
        self.assertFalse(m.contains_any(m.norm(MD_KEPT), n))
        self.assertTrue(m.contains_any(m.norm("Talk&nbsp;to   *founders*"), n))

    def test_html_text_visible_and_hrefs(self):
        h = ('<html><head><script>var x="Join our community"</script></head><body>'
             '<a href="https://mem0.dev/DiD">Discord</a><p>Ask questions on <b>GitHub</b></p></body></html>')
        t = m.norm(m.html_text(h))
        self.assertIn("ask questions on github", t)
        self.assertIn("https://mem0.dev/did", t)
        self.assertNotIn("join our community", t)

    def test_classify(self):
        self.assertEqual(m.classify(True, False, True), "tag-kept")
        self.assertEqual(m.classify(False, True, True), "expanded")
        self.assertEqual(m.classify(False, False, True), "lost")
        self.assertEqual(m.classify(False, False, False), "no-text")


class UrlTests(unittest.TestCase):
    def test_page_slug(self):
        self.assertEqual(m.page_slug("open-source/python-quickstart.mdx"), "open-source/python-quickstart")
        self.assertEqual(m.page_slug("platform/index.mdx"), "platform")
        self.assertEqual(m.page_slug("index.mdx"), "")
        self.assertEqual(m.page_slug("en/guide.md"), "en/guide")

    def test_llms_urls(self):
        t = ("# X\n- [A](https://docs.x.ai/a.md): Use when\n- [B](https://docs.x.ai/b/#h)\n"
             "MCP: https://mcp.x.ai\n")
        self.assertEqual(m.llms_urls(t), ["https://docs.x.ai/a", "https://docs.x.ai/b", "https://mcp.x.ai"])

    def test_map_slug_exact(self):
        urls = ["https://docs.x.ai/platform/overview", "https://docs.x.ai/overview",
                "https://x.com/docs/guide", "https://other.ai/overview"]
        self.assertEqual(m.map_slug("overview", urls, "https://docs.x.ai"), "https://docs.x.ai/overview")
        self.assertEqual(m.map_slug("guide", urls, "https://x.com/docs"), "https://x.com/docs/guide")
        self.assertIsNone(m.map_slug("platform", urls, "https://docs.x.ai"))
        self.assertIsNone(m.map_slug("", urls, "https://docs.x.ai"))

    def test_sample_seeded(self):
        items = ["p%02d" % i for i in range(40)]
        a = m.sample(items, "k", 15)
        self.assertEqual(a, m.sample(list(reversed(items)), "k", 15))
        self.assertEqual(len(a), 15)
        self.assertEqual(m.sample(["b", "a"], "k", 15), ["a", "b"])


class GradeTests(unittest.TestCase):
    def inst(self, repo, loc, status, html_has=True, has=True):
        return {"repo": repo, "loc": loc, "status": status, "html_has": html_has, "has_needles": has}

    def test_grade_all_true(self):
        sites = [{"repo": r, "counted": True} for r in ("mem0ai/mem0", "a/a", "b/b")]
        inst = ([self.inst("mem0ai/mem0", "_snippets", "tag-kept")] * 6
                + [self.inst("a/a", "_snippets", "tag-kept")] * 6
                + [self.inst("b/b", "snippets", "expanded")] * 10)
        ctl = [{"read": True, "has_needles": True, "md_has": True}] * 5
        g = m.grade(sites, inst, ctl)
        self.assertTrue(g["G1"])
        for k in ("P1", "P2", "P3", "P4", "P5"):
            self.assertIs(g[k], True, k)
        self.assertEqual(g["tag_kept_share_by_location"]["_snippets"], {"n": 12, "tag_kept": 1.0})

    def test_grade_false_and_too_few(self):
        sites = [{"repo": r, "counted": True} for r in ("mem0ai/mem0", "a/a", "b/b")]
        inst = ([self.inst("mem0ai/mem0", "_snippets", "tag-kept", html_has=False)] * 5
                + [self.inst("b/b", "snippets", "tag-kept")] * 10)
        g = m.grade(sites, inst, [])
        self.assertIs(g["P1"], False)
        self.assertIs(g["P3"], False)
        self.assertTrue(str(g["P4"]).startswith("too few"))

    def test_grade_g1_fails(self):
        sites = [{"repo": "mem0ai/mem0", "counted": True}, {"repo": "a/a", "counted": False}]
        g = m.grade(sites, [self.inst("mem0ai/mem0", "_snippets", "tag-kept")] * 6, [])
        self.assertFalse(g["G1"])
        self.assertTrue(str(g["P1"]).startswith("not graded"))


if __name__ == "__main__":
    unittest.main()
