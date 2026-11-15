# test_nuxtraw.py - Apache-2.0 - MV2, Munim, Inc. (made with AI agents)
# Offline tests for nuxtraw.py 0.2.0 (no network).
import unittest

import nuxtraw as n

RAW = """# Button

> A button element.

## Usage

<component-code name="button"></component-code>

Some text with `<inline-code></inline-code>` that must be ignored.

```vue
<UButton></UButton>
<code-in-fence></code-in-fence>
```

<partial content="config-options">

</partial>

<callout icon="i-lucide-info">
Read this first.
</callout>

<read-more to="/docs/x"></read-more>

<field name="size" type="string" description="The size"></field>

<icon-link title="Home" />

<tabs><tab label="A"><nested-ex></nested-ex></tab></tabs>

<!-- <hidden-comment></hidden-comment> -->

Replace <your-token> with your token. A <br> and <div></div>.
"""

CODE_GROUP = """<code-group>

```yaml [a.yml]
name: A
```

```yaml [b.yml]
name: B
```

</code-group>

<tabs>
<tabs-item label="npm">

```bash
npm i x
```

</tabs-item>
</tabs>

<badge>`v1`</badge>

<code-group>

</code-group>
"""

LLMS = """# Site
- [Intro](https://ex.com/raw/docs/intro.md): intro
- [Intro again](https://ex.com/raw/docs/intro.md#top)
- [Index](https://ex.com/raw/index.md)
- [Other host](https://other.com/raw/docs/a.md)
- [Not raw](https://ex.com/docs/b.md)
- [Full](https://ex.com/llms-full.txt)
"""


class Components(unittest.TestCase):
    def setUp(self):
        self.c = n.components(RAW)
        self.names = [x["name"] for x in self.c]

    def test_code_and_comments_ignored(self):
        for name in ("inline-code", "ubutton", "code-in-fence", "hidden-comment"):
            self.assertNotIn(name, self.names)
            self.assertNotIn(name, [x["name"] for x in n.components(RAW, "v1")])

    def test_html_elements_ignored(self):
        self.assertNotIn("div", self.names)
        self.assertNotIn("br", self.names)

    def test_empty_detection(self):
        expected = {"component-code", "partial", "read-more", "field",
                    "icon-link", "nested-ex", "tab", "tabs"}
        self.assertEqual({x["name"] for x in self.c if x["empty"]}, expected)
        self.assertEqual({x["name"] for x in n.components(RAW, "v1") if x["empty"]}, expected)
        self.assertIn("callout", self.names)

    def test_code_wrapper_not_empty_v2(self):
        v2 = n.components(CODE_GROUP, "v2")
        self.assertEqual([(x["name"], x["empty"]) for x in v2],
                         [("code-group", False), ("tabs", False), ("tabs-item", False),
                          ("badge", False), ("code-group", True)])

    def test_code_wrapper_empty_v1(self):
        v1 = n.components(CODE_GROUP, "v1")
        self.assertEqual([x["empty"] for x in v1], [True, True, True, True, True])

    def test_unclosed_placeholder_not_empty(self):
        tok = [x for x in self.c if x["name"] == "your-token"]
        self.assertEqual(len(tok), 1)
        self.assertFalse(tok[0]["empty"])

    def test_attrs_and_kind(self):
        by = {x["name"]: x for x in self.c}
        self.assertEqual(by["partial"]["attrs"], ["content"])
        self.assertEqual(n.kind_of(by["partial"]), "bare")
        self.assertEqual(n.kind_of(by["read-more"]), "link-attr")
        self.assertEqual(n.kind_of(by["field"]), "text-attr")
        self.assertEqual(n.kind_of(by["icon-link"]), "text-attr")
        self.assertEqual(by["field"]["attrs"], ["description", "name", "type"])

    def test_nested_same_name(self):
        c = n.components("<x-box><x-box>hi</x-box></x-box>")
        self.assertEqual([x["empty"] for x in c], [False, False])

    def test_bound_attr(self):
        c = n.components('<comp-a :to="/y" v-if="ok"></comp-a>')
        self.assertEqual(c[0]["attrs"], ["to", "v-if"])


class Links(unittest.TestCase):
    def test_raw_links(self):
        self.assertEqual(n.raw_links(LLMS, "https://ex.com/llms.txt"),
                         ["https://ex.com/raw/docs/intro.md", "https://ex.com/raw/index.md"])

    def test_page_url(self):
        self.assertEqual(n.page_url("https://ex.com/raw/docs/intro.md"), "https://ex.com/docs/intro")
        self.assertEqual(n.page_url("https://ex.com/raw/index.md"), "https://ex.com/")
        self.assertEqual(n.page_url("https://ex.com/docs/raw/guide/index.md"), "https://ex.com/docs/guide/")

    def test_site_key(self):
        self.assertEqual(n.site_key("https://directus.com/docs/llms.txt"), "directus.com/docs")
        self.assertEqual(n.site_key("https://nuxt.com/llms.txt"), "nuxt.com")

    def test_sample_deterministic(self):
        links = ["u%03d" % i for i in range(100)]
        a = n.sample(links, "k")
        self.assertEqual(a, n.sample(links, "k"))
        self.assertEqual(len(a), 30)
        self.assertEqual(n.sample(links[:5], "k"), links[:5])


class Words(unittest.TestCase):
    def test_page_words_main(self):
        html = "<html><nav>skip me</nav><main><h1>Title</h1><p>one two</p><script>x y</script></main></html>"
        self.assertEqual(n.page_words(html), 3)

    def test_page_words_no_main(self):
        self.assertEqual(n.page_words("<body><p>a b c d</p><footer>z</footer></body>"), 4)

    def test_md_words(self):
        self.assertEqual(n.md_words("# T\n<x-a b='c d'></x-a> one <!-- no -->\n```\ncode\n```"), 3)

    def test_analyse(self):
        a = n.analyse(RAW, "<main>" + "w " * 400 + "</main>")
        self.assertEqual(a["empty_tags"], 8)
        self.assertEqual(a["empty_tags_v1"], 8)
        self.assertEqual(a["page_words"], 400)
        self.assertTrue(0 < a["ratio"] < 1)
        self.assertIn("partial", a["empty_names"].split(";"))

    def test_analyse_code_group(self):
        a = n.analyse(CODE_GROUP, "")
        self.assertEqual(a["empty_tags"], 1)
        self.assertEqual(a["empty_tags_v1"], 5)
        self.assertEqual(a["ratio"], "")
        self.assertEqual(a["page_words"], "")

    def test_looks_html(self):
        self.assertTrue(n.looks_html("text/html; charset=utf-8", "x"))
        self.assertTrue(n.looks_html("", "  <!DOCTYPE html><html>"))
        self.assertFalse(n.looks_html("text/markdown", "# Hi"))

    def test_same_text(self):
        self.assertTrue(n.same_text("# A\n\nb  c\n", "# A b c"))
        self.assertFalse(n.same_text("# A", "# B"))


class Grade(unittest.TestCase):
    def _pages(self, key, n_read, n_empty, ratio_e=0.6, ratio_n=0.9):
        rows = []
        for i in range(n_read):
            e = i < n_empty
            rows.append({"key": key, "read": True, "empty_tags": 2 if e else 0,
                         "ratio": ratio_e if e else ratio_n})
        return rows

    def test_all_hold(self):
        sites = [{"key": k, "counted": True} for k in ("a", "b", "c", "directus.com/docs")]
        pages = (self._pages("a", 20, 5) + self._pages("b", 20, 4) + self._pages("c", 20, 0)
                 + self._pages("directus.com/docs", 20, 10))
        g = n.grade(sites, pages)
        self.assertTrue(g["G1"])
        self.assertTrue(g["P1"])
        self.assertTrue(g["P2"])          # 19/80 = 0.2375
        self.assertTrue(g["P3"])          # a 0.25, b 0.20
        self.assertTrue(g["P4"])
        self.assertTrue(g["P5"])

    def test_p3_excludes_directus_and_p5_fails(self):
        sites = [{"key": k, "counted": True} for k in ("a", "b", "c", "directus.com/docs")]
        pages = (self._pages("a", 20, 5) + self._pages("b", 20, 1) + self._pages("c", 20, 0, ratio_n=0.3)
                 + self._pages("directus.com/docs", 20, 20))
        g = n.grade(sites, pages)
        self.assertFalse(g["P3"])
        self.assertFalse(g["P5"])

    def test_gate(self):
        sites = [{"key": "a", "counted": True}, {"key": "b", "counted": False}]
        g = n.grade(sites, self._pages("a", 12, 3) + self._pages("b", 3, 3))
        self.assertFalse(g["G1"])
        self.assertEqual(g["copies_read"], 12)
        self.assertTrue(str(g["P2"]).startswith("not graded"))

    def test_string_rows(self):
        sites = [{"key": k, "counted": "True"} for k in "abcd"]
        pages = [{"key": k, "read": "True", "empty_tags": "1", "ratio": "0.5"} for k in "abcd"] * 3
        g = n.grade(sites, pages)
        self.assertEqual(g["pooled_share_with_empty"], 1.0)
        self.assertFalse(g["P4"])         # no copies without an empty tag

    def test_blank_ratios(self):
        sites = [{"key": k, "counted": True} for k in "abcd"]
        pages = [{"key": k, "read": True, "empty_tags": 0, "ratio": ""} for k in "abcd"] * 3
        g = n.grade(sites, pages)
        self.assertEqual(g["copies_with_ratio"], 0)
        self.assertFalse(g["P4"])
        self.assertFalse(g["P5"])         # nothing measured: not a pass

    def test_negotiation_summary(self):
        pages = [{"key": "a", "read": True, "page_is_html": True, "neg_is_md": True, "neg_same_as_raw": False},
                 {"key": "a", "read": "True", "page_is_html": "False", "neg_is_md": "True",
                  "neg_same_as_raw": "True"},
                 {"key": "a", "read": False}]
        self.assertEqual(n.negotiation_summary(pages),
                         {"a": {"copies": 2, "page_html": 1, "md_on_ask": 2, "md_same_as_raw": 1}})


class Version(unittest.TestCase):
    def test_version(self):
        self.assertEqual(n.VERSION, "0.2.0")
        self.assertEqual(len(n.SITES), 20)


if __name__ == "__main__":
    unittest.main()
