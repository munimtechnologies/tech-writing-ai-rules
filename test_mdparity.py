"""Offline tests for mdparity.py (study 10). No network.

    python -m unittest -v test_mdparity

Made by MV2 of Munim, Inc., with AI agents working in his name. Apache-2.0.
"""
import csv
import json
import os
import shutil
import tempfile
import unittest

import mdparity as mp

HTML_PAGE = """<!doctype html><html><head><title>T</title>
<script>var x = "<p>not text at all, this is only a script string here</p>";</script></head>
<body><header><nav><a href="/">Home docs navigation link list that is long here</a></nav></header>
<div class="sidebar"><p>Sidebar text that should never be counted as content at all.</p></div>
<main><article>
<h1>Install the widget</h1>
<p>This guide shows you how to install the widget on a fresh server in a few minutes.</p>
<h2>Before you begin</h2>
<div class="admonition warning"><p class="admonition-title">Warning</p>
<p>Running this command deletes every table in the production database.</p></div>
<aside class="callout callout-note"><p>Note: you can also install the widget with the package manager of your choice.</p></aside>
<ul><li>A server running a supported version of the operating system and kernel.</li>
<li>Short item</li></ul>
<h2>Steps</h2>
<pre><code><span class="k">pip</span> install widget-cli==2.0</code></pre>
<div role="tabpanel" hidden><p>On macOS, open a terminal window and run the same command as the root user.</p></div>
<p>This paragraph was left out of the Markdown copy because it came from an include file.</p>
<div class="feedback"><p>Was this page helpful to you today? Let us know in the form below please.</p></div>
<button>Copy this page as Markdown for your favourite large language model</button>
</article></main>
<footer><p>Copyright notice text that is long enough to count as a paragraph block.</p></footer>
</body></html>"""

MD_COPY = """---
title: Install the widget
---
# Install the widget

This guide shows you how to [install](https://example.com/install "Install") the widget on a fresh server in a few minutes.

## Before you begin

:::note
You can also install the widget with the package manager of your choice.
:::

- A server running a supported version of the operating system and kernel.

## Steps

```bash
pip install widget-cli==2.0
```

<Tabs><Tab title="macOS">On macOS, open a terminal window and run the same command as the root user.</Tab></Tabs>
"""


def noop(_seconds):
    return None


def make_fetch(pages, robots=b"User-agent: *\nDisallow: /private/\n"):
    """pages: {(url, 'html' | 'md'): (status, ctype, text)}."""
    calls = []

    def fetch(url, accept, limit=0):
        calls.append((url, accept))
        if url.endswith("/robots.txt"):
            return 200, "text/plain", url, robots
        kind = "md" if accept == mp.ACCEPT_MD else "html"
        if (url, kind) in pages:
            st, ct, text = pages[(url, kind)]
            return st, ct, url, text.encode("utf-8")
        return 404, "", url, b""
    return fetch, calls


def page_row(site, coverage, prose, prose_present, **kw):
    row = {c: "" for c in mp.PAGE_COLUMNS}
    row.update({k: 0 for k in mp.COUNT_KEYS})
    row.update(site=site, url="https://%s.example/%d" % (site, id(kw)), status="ok", counted=True,
               coverage=coverage, prose=prose, prose_present=prose_present, html_words=100, md_words=100,
               md_markers=0)
    row.update(kw)
    return row


class Words(unittest.TestCase):
    def test_words(self):
        self.assertEqual(mp.words("Don’t run `rm -rf` now!"), ["don", "t", "run", "rm", "rf", "now"])
        self.assertEqual(mp.words("my_var = 2.0"), ["my", "var", "2", "0"])

    def test_strip_kind(self):
        self.assertEqual(mp.strip_kind(["warning", "note", "x", "note"]), ["x", "note"])
        self.assertEqual(mp.strip_kind(["note", "note", "note", "y"]), ["note", "y"])

    def test_md_plain(self):
        md = ("Text [link](https://a.b/c \"T\") more <!-- hidden comment -->\n"
              "<Note>Hi there</Note> {{< note >}}Careful{{< /note >}} {% include x.md %}\n"
              "[1]: https://ref.example/def\n"
              "```html\n<div>kept code</div>\n```\nafter &amp; done\n")
        ws = mp.words(mp.md_plain(md))
        self.assertEqual(ws, ["text", "link", "more", "hi", "there", "careful", "div", "kept", "code", "div",
                              "after", "done"])

    def test_corpus_has(self):
        c = mp.Corpus("one two three four five six seven eight nine ten")
        self.assertTrue(c.has(mp.words("three four five")))
        self.assertFalse(c.has(mp.words("three five")))
        self.assertTrue(c.has(mp.words("one two three four five six seven eight nine eleven")))
        self.assertFalse(c.has(mp.words("one two three four x six seven eight nine ten")))
        self.assertTrue(c.has([]))

    def test_md_markers(self):
        md = "> [!WARNING]\n> x\n:::note\ny\n:::\n<Callout type=\"warning\">z</Callout>\n!!! tip\n"
        self.assertEqual(mp.md_markers(md), 4)


class Html(unittest.TestCase):
    def test_callout_detection(self):
        root = mp.parse_html('<div class="NOTE"></div><div class="alert is-warning"></div><div role="note"></div>'
                             '<div class="footnotes"></div><div class="release-notes"></div>'
                             '<span class="note"></span><div class="note-module__abc__note"></div>'
                             '<div data-callout-type="x"></div>')
        found = [mp.is_callout(n) for n in mp.iter_nodes(root) if n.tag in ("div", "span")]
        self.assertEqual(found, [True, True, True, False, False, False, True, True])

    def test_node_text_skips_dropped(self):
        root = mp.parse_html("<div>a<script>b</script><nav>c</nav><span>d</span><p>e</p>"
                             "<i aria-hidden=\"true\">f</i></div>")
        self.assertEqual(mp.words(mp.node_text(root)), ["ad", "e"])

    def test_pick_main(self):
        main, how = mp.pick_main(mp.parse_html(HTML_PAGE))
        self.assertEqual((main.tag, how), ("article", "main>article"))
        main, how = mp.pick_main(mp.parse_html("<body><article><p>a b</p></article>"
                                               "<article><p>a b c d</p></article></body>"))
        self.assertEqual(how, "article")
        self.assertEqual(mp.words(mp.node_text(main)), ["a", "b", "c", "d"])
        main, how = mp.pick_main(mp.parse_html("<html><body><p>x</p></body></html>"))
        self.assertEqual(how, "body")

    def test_blocks(self):
        main, _how = mp.pick_main(mp.parse_html(HTML_PAGE))
        kinds = [(b["kind"], b["group"]) for b in mp.blocks(main)]
        self.assertEqual(kinds, [
            ("prose", ""), ("heading", ""), ("callout", "warning"), ("prose", ""), ("prose", ""),
            ("callout", "note"), ("prose", ""), ("prose", ""), ("prose", ""), ("heading", ""), ("code", ""),
            ("prose", ""), ("prose", "")])
        tabs = [b["in_tab"] for b in mp.blocks(main)]
        self.assertEqual(tabs.count(True), 1)

    def test_compare(self):
        counts, missing, how, html_words, md_words, lines = mp.compare(HTML_PAGE, MD_COPY)
        self.assertEqual(how, "main>article")
        self.assertEqual((counts["prose"], counts["prose_present"]), (6, 4))
        self.assertEqual((counts["heading"], counts["heading_present"]), (2, 2))
        self.assertEqual((counts["code"], counts["code_present"]), (1, 1))
        self.assertEqual((counts["callout"], counts["callout_present"]), (2, 1))
        self.assertEqual((counts["warn"], counts["warn_present"]), (1, 0))
        self.assertEqual((counts["tab"], counts["tab_present"]), (1, 1))
        self.assertEqual([m["kind"] for m in missing], ["callout", "prose", "prose"])
        self.assertEqual(missing[0]["group"], "warning")
        self.assertTrue(missing[2]["text"].startswith("This paragraph was left out"))
        self.assertEqual(len(lines), 11)
        self.assertGreater(md_words, 50)
        self.assertGreater(html_words, 60)


class Pages(unittest.TestCase):
    def setUp(self):
        self.pages = {
            ("https://d.example/p", "html"): (200, "text/html; charset=utf-8", HTML_PAGE),
            ("https://d.example/p", "md"): (200, "text/markdown", MD_COPY),
            ("https://d.example/q.md", "md"): (200, "text/plain", MD_COPY),
            ("https://d.example/q", "html"): (200, "text/html", HTML_PAGE),
            ("https://d.example/nomd", "html"): (200, "text/html", HTML_PAGE),
            ("https://d.example/blocked", "html"): (403, "text/html", "no"),
            ("https://d.example/thin", "html"): (200, "text/html", "<main><p>Only one short line.</p></main>"),
            ("https://d.example/thin", "md"): (200, "text/markdown", "# Only one short line."),
        }
        self.fetch, self.calls = make_fetch(self.pages)
        self.robots = mp.make_robots(self.fetch, noop)

    def check(self, url, method="accept"):
        return mp.check_page({"site": "d", "url": url, "method": method}, self.fetch, noop, self.robots)

    def test_accept(self):
        row, miss, ev = self.check("https://d.example/p")
        self.assertEqual(row["status"], "ok")
        self.assertTrue(row["counted"])
        self.assertEqual(row["coverage"], 0.6667)
        self.assertEqual((row["callout"], row["callout_present"], row["warn"]), (2, 1, 1))
        self.assertEqual(len(miss), 3)
        self.assertEqual(miss[0]["site"], "d")
        self.assertIn("MISSING\tcallout\twarning", ev["blocks"])
        self.assertIn(("https://d.example/p", mp.ACCEPT_MD), self.calls)

    def test_suffix(self):
        row, _miss, _ev = self.check("https://d.example/q/", "suffix")
        self.assertEqual(row["md_url"], "https://d.example/q.md")
        self.assertEqual(row["status"], "html-unreadable")  # the HTML lives at /q, not /q/
        row, _miss, _ev = self.check("https://d.example/q", "suffix")
        self.assertEqual((row["status"], row["prose"]), ("ok", 6))

    def test_statuses(self):
        self.assertEqual(self.check("https://d.example/private/x")[0]["status"], "robots")
        self.assertEqual(self.check("https://d.example/blocked")[0]["status"], "blocked")
        self.assertEqual(self.check("https://d.example/nomd")[0]["status"], "md-missing")
        row, miss, ev = self.check("https://d.example/thin")
        self.assertEqual((row["status"], row["counted"]), ("few-blocks", False))
        self.assertIsNotNone(ev)

    def test_md_suffix_url(self):
        self.assertEqual(mp.md_suffix_url("https://x.example/a/b"), "https://x.example/a/b.md")
        self.assertEqual(mp.md_suffix_url("https://x.example/a/"), "https://x.example/a.md")
        self.assertEqual(mp.md_suffix_url("https://x.example/"), "https://x.example/index.md")


class Frame(unittest.TestCase):
    def test_vendor_frame(self):
        rows = [
            {"control": "control-md", "site": "control-md", "readable": "True", "md_accept": "True",
             "md_suffix": "False", "url": "https://learn.example/x"},
            {"control": "", "site": "docker", "readable": "True", "md_accept": "True", "md_suffix": "True",
             "url": "https://docs.docker.com/a/"},
            {"control": "", "site": "heroku", "readable": "True", "md_accept": "False", "md_suffix": "True",
             "url": "https://devcenter.heroku.com/articles/x"},
            {"control": "", "site": "npm", "readable": "True", "md_accept": "False", "md_suffix": "False",
             "url": "https://docs.npmjs.com/y"},
            {"control": "", "site": "aws", "readable": "False", "md_accept": "True", "md_suffix": "True",
             "url": "https://docs.aws.amazon.com/z"},
            {"control": "", "site": "docker", "readable": "True", "md_accept": "True", "md_suffix": "True",
             "url": "https://docs.docker.com/a/"},
        ]
        self.assertEqual(mp.vendor_frame(rows), [
            {"site": "docker", "url": "https://docs.docker.com/a/", "method": "accept"},
            {"site": "heroku", "url": "https://devcenter.heroku.com/articles/x", "method": "suffix"}])

    def test_learn_frame(self):
        rows = [{"repo": "r", "path": "p%02d.md" % i, "stratum": "A" if i % 2 else "U", "mapped": "yes",
                 "md_served": "True", "url": "https://learn.example/%02d" % i, "final_url": ""} for i in range(40)]
        rows.append({"repo": "r", "path": "c.md", "stratum": "control-positive", "mapped": "yes",
                     "md_served": "True", "url": "https://learn.example/c", "final_url": ""})
        rows.append({"repo": "r", "path": "n.md", "stratum": "A", "mapped": "no", "md_served": "True",
                     "url": "https://learn.example/n", "final_url": ""})
        a = mp.learn_frame(rows)
        self.assertEqual(len(a), 30)
        self.assertEqual(a, mp.learn_frame(list(reversed(rows))))
        self.assertTrue(all(e["site"] == "mslearn" and e["method"] == "accept" for e in a))
        urls = [e["url"] for e in a]
        self.assertNotIn("https://learn.example/c", urls)
        self.assertNotIn("https://learn.example/n", urls)
        self.assertEqual(len(mp.learn_frame(rows[:5])), 5)


class Grades(unittest.TestCase):
    def build(self, n_sites):
        rows = []
        for s in range(n_sites):
            for _p in range(25):
                low = s < 3
                rows.append(page_row("s%d" % s, 0.7 if low else 1.0, 10, 7 if low else 10, callout=1,
                                     callout_present=0 if s == 0 else 1, code=2, code_present=2,
                                     heading=2, heading_present=2))
        return rows

    def test_ratio(self):
        self.assertTrue(mp.ratio_at_least(2, 40, 1, 20))
        self.assertFalse(mp.ratio_at_least(1, 40, 1, 20))
        self.assertTrue(mp.ratio_at_least(19, 20, 19, 20))
        self.assertFalse(mp.ratio_at_least(18, 20, 19, 20))

    def test_all_held(self):
        s, sites = mp.summarise(self.build(10))
        self.assertTrue(s["gates"]["G1"]["passed"])
        self.assertTrue(s["gates"]["G2"]["passed"])
        p = s["predictions"]
        self.assertEqual(p["P1"]["value"], 1.0)
        self.assertEqual(p["P2"]["sites"], ["s0", "s1", "s2"])
        self.assertEqual((p["P3"]["k"], p["P3"]["n"]), (25, 250))
        self.assertEqual(p["P4"]["sites"], ["s0"])
        self.assertEqual((p["P5"]["k"], p["P5"]["n"]), (500, 500))
        self.assertTrue(all(v["held"] for v in p.values()))
        self.assertEqual(len(sites), 10)
        self.assertEqual(sites[0]["median_coverage"], 0.7)
        self.assertEqual(sites[0]["md_html_words"], 1.0)

    def test_gate_fails(self):
        s, _sites = mp.summarise(self.build(9))
        self.assertFalse(s["gates"]["G1"]["passed"])
        self.assertTrue(all(v["held"] is None for v in s["predictions"].values()))

    def test_uncounted_rows_ignored(self):
        rows = self.build(10)
        rows.append(page_row("s9", "", 1, 0, counted=False, status="few-blocks", callout=99))
        s, sites = mp.summarise(rows)
        self.assertEqual(s["counted"], 250)
        self.assertEqual(s["totals"]["callout"], 250)
        self.assertEqual(sites[9]["sampled"], 26)


class Main(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name, columns, rows):
        path = os.path.join(self.tmp, name)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=columns)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        return path

    def test_end_to_end(self):
        vpath = self.write("vendor.csv", ["control", "site", "url", "readable", "md_accept", "md_suffix"],
                           [{"control": "", "site": "d", "url": "https://d.example/p", "readable": "True",
                             "md_accept": "True", "md_suffix": "False"}])
        lpath = self.write("learn.csv", ["repo", "path", "stratum", "url", "final_url", "mapped", "md_served"],
                           [{"repo": "r", "path": "a.md", "stratum": "A", "url": "https://l.example/a",
                             "final_url": "https://l.example/a", "mapped": "yes", "md_served": "True"}])
        fetch, _calls = make_fetch({
            ("https://d.example/p", "html"): (200, "text/html", HTML_PAGE),
            ("https://d.example/p", "md"): (200, "text/markdown", MD_COPY),
            ("https://l.example/a", "html"): (200, "text/html", HTML_PAGE),
            ("https://l.example/a", "md"): (200, "text/markdown", MD_COPY)})
        out = os.path.join(self.tmp, "out")
        code = mp.main(["--out-dir", out, "--vendor-pages", vpath, "--learn-pages", lpath, "--no-prereg-check"],
                       fetch=fetch, sleep=noop)
        self.assertEqual(code, 0)
        for name in ("pages.csv", "sites.csv", "missing.csv", "mdparity.json", "MDPARITY_AUTO.md"):
            self.assertTrue(os.path.exists(os.path.join(out, name)), name)
        with open(os.path.join(out, "mdparity.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["summary"]["counted"], 2)
        self.assertEqual(len(data["meta"]["frame_files"]["vendor_pages"]["sha256"]), 64)
        self.assertFalse(data["summary"]["gates"]["G1"]["passed"])
        with open(os.path.join(out, "MDPARITY_AUTO.md"), encoding="utf-8") as fh:
            self.assertIn("| P1 | 0.6667 | not graded |", fh.read())
        self.assertTrue(os.path.exists(os.path.join(out, "evidence", "mslearn", "001.md")))

    def test_waits_for_prereg(self):
        out = os.path.join(self.tmp, "out2")
        code = mp.main(["--out-dir", out, "--wait-prereg-minutes", "1"], fetch=lambda *a: (500, "", "", b""),
                       sleep=noop, opener=lambda req: b"[]")
        self.assertEqual(code, 3)
        with open(os.path.join(out, "mdparity.json"), encoding="utf-8") as fh:
            self.assertIsNone(json.load(fh)["meta"]["prereg"]["committed_at"])

    def test_prereg_commit(self):
        answer = json.dumps([{"sha": "b", "commit": {"committer": {"date": "2026-11-11T00:00:00Z"}}},
                             {"sha": "a", "commit": {"committer": {"date": "2026-11-10T18:00:00Z"}}}]).encode()
        got = mp.prereg_commit(mp.PREREG_PATH, opener=lambda req: answer)
        self.assertEqual((got["committed_at"], got["sha"]), ("2026-11-10T18:00:00Z", "a"))


if __name__ == "__main__":
    unittest.main()
