# Apache-2.0. Offline tests for rawcopy_scan.py (MV2 of Munim, Inc.; made with AI agents).
import os
import tempfile
import unittest

import rawcopy_scan as rs

RAW = """# Overview

> Learn what Directus is.

<partial content="engine-studio-box">



</partial>

## How It Works

<video-embed video-id="abc">



</video-embed>

Some prose here.

<callout color="secondary" to="/tutorials/self-hosting">

See all deployment options.

</callout>

```html
<partial content="inside-code"></partial>
<cta-cloud></cta-cloud>
```

<partial content="license">



</partial>
"""

TWIN = """# Overview

> Learn what Directus is.

Data Studio: a web app for your whole team to manage content, files, users, and dashboards.

## How It Works

[Watch video](https://www.youtube.com/watch?v=abc)

Some prose here.

See all deployment options.

**Licensing**
Directus is licensed under the Monospace Sustainable Core License (MSCL).
"""

LLMS = """# Directus Documentation
> summary
## Documentation Sets
- [Complete Directus Documentation](https://directus.com/docs/llms-full.txt)
## Getting Started
- [Overview](https://directus.com/docs/raw/getting-started/overview.md): Learn.
- [Overview again](https://directus.com/docs/raw/getting-started/overview.md): dup.
- [Query](https://directus.com/docs/raw/guides/connect/query-parameters.md): q.
- [Other site](https://example.com/raw/x.md): other.
"""


class TestParsing(unittest.TestCase):
    def test_partials_empty_and_code_ignored(self):
        p = rs.partials(RAW)
        self.assertEqual(p, [("engine-studio-box", True), ("license", True)])

    def test_partial_with_content_not_empty(self):
        p = rs.partials('<partial content="x">\nhello\n</partial>')
        self.assertEqual(p, [("x", False)])

    def test_component_tags(self):
        c = rs.component_tags(RAW)
        self.assertEqual(c, {"partial": 2, "video-embed": 1, "callout": 1})

    def test_autolink_not_a_component(self):
        self.assertEqual(rs.component_tags("see <https://a.b/c> and <br>"), {})

    def test_word_count_ignores_tags_and_code(self):
        self.assertEqual(rs.word_count("<x-y a='1'>\nHello world\n```\ncode here\n```\n"), 2)

    def test_raw_links_unique_and_domain(self):
        links = rs.raw_links(LLMS)
        self.assertEqual(links[:2], ["https://directus.com/docs/raw/getting-started/overview.md",
                                     "https://directus.com/docs/raw/guides/connect/query-parameters.md"])
        self.assertEqual(len(links), 3)
        self.assertEqual(len(rs.raw_links(LLMS, domain="https://directus.com/")), 2)

    def test_twin_url(self):
        self.assertEqual(rs.twin_url("https://directus.com/docs/raw/a/b.md"),
                         "https://directus.com/docs/a/b.md")

    def test_analyse_pair(self):
        a = rs.analyse_pair(RAW, TWIN)
        self.assertEqual(a["raw_empty_partials"], 2)
        self.assertEqual(a["raw_empty_partial_names"], "engine-studio-box;license")
        self.assertEqual(a["twin_partial_tags"], 0)
        self.assertGreater(a["twin_words"], a["raw_words"])

    def test_looks_html(self):
        self.assertTrue(rs.looks_html("text/html; charset=utf-8", "x"))
        self.assertTrue(rs.looks_html("", "  <!DOCTYPE html><html>"))
        self.assertFalse(rs.looks_html("text/markdown", "# Title"))

    def test_summarise_and_render(self):
        row = {"raw_url": "u", "raw_status": 200, "twin_url": "t", "twin_status": 200,
               "twin_is_html": False}
        row.update(rs.analyse_pair(RAW, TWIN))
        row2 = {"raw_url": "u2", "raw_status": 404, "twin_url": "t2", "twin_status": 404,
                "twin_is_html": False}
        row2.update(rs.analyse_pair("", ""))
        s = rs.summarise([row, row2], "L", 200, {"https://x/llms-full.txt": 404})
        self.assertEqual(s["raw_links"], 2)
        self.assertEqual(s["raw_ok"], 1)
        self.assertEqual(s["pages_with_empty_partial"], 1)
        self.assertEqual(s["pages_by_partial_name"], {"engine-studio-box": 1, "license": 1})
        md = rs.render_md(s)
        self.assertIn("`license`: 1", md)
        self.assertIn("llms-full.txt: HTTP 404", md)

    def test_main_rejects_missing_llms(self):
        orig = rs.fetch
        rs.fetch = lambda url, timeout=30: (404, "", "")
        try:
            with tempfile.TemporaryDirectory() as d:
                self.assertEqual(rs.main(["--out-dir", d, "--llms", "https://x/llms.txt"]), 3)
        finally:
            rs.fetch = orig

    def test_main_offline_end_to_end(self):
        pages = {
            "https://d/llms.txt": (200, "text/plain", "- [O](https://d/raw/o.md)\n"),
            "https://d/raw/o.md": (200, "text/markdown", RAW),
            "https://d/o.md": (200, "text/markdown", TWIN),
            "https://d/llms-full.txt": (404, "", ""),
        }
        orig = rs.fetch
        rs.fetch = lambda url, timeout=30: pages.get(url, (404, "", ""))
        try:
            with tempfile.TemporaryDirectory() as d:
                rc = rs.main(["--out-dir", d, "--llms", "https://d/llms.txt", "--delay", "0",
                              "--also", "https://d/llms-full.txt"])
                self.assertEqual(rc, 0)
                for f in ("pages.csv", "summary.json", "RAWCOPY_AUTO.md", "llms.txt"):
                    self.assertTrue(os.path.exists(os.path.join(d, f)), f)
                with open(os.path.join(d, "RAWCOPY_AUTO.md"), encoding="utf-8") as fh:
                    self.assertIn("at least one empty <partial>: 1", fh.read())
        finally:
            rs.fetch = orig


if __name__ == "__main__":
    unittest.main()
