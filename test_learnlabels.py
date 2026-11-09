# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0.
"""Offline tests for learnlabels.py (no network, no git). Run: python -m unittest -v test_learnlabels"""

import csv
import json
import os
import shutil
import tempfile
import unittest
import urllib.parse

import learnlabels as L


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def md(title="T", date="05/01/2026", label=None, key="ai-usage", extra=""):
    lines = ["---", "title: %s" % title, "ms.date: %s" % date, "ms.topic: how-to"]
    if label is not None:
        lines.append("%s: %s" % (key, label))
    if extra:
        lines.append(extra)
    lines += ["---", "", "# %s" % title, ""]
    return "\n".join(lines)


def art(cat="", year=2026, key=None, include=False):
    if key is None:
        key = "ai-usage" if cat else ""
    value = {"non-ai": "human-only", "other-ai": "AI assisted"}.get(cat, cat)
    return {"path": "a.md", "is_article": not include, "include": include, "ai_key": key,
            "ai_value": value, "category": cat, "year": year, "ms_topic": "how-to",
            "other_tokens": ""}


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class FrontMatterTests(unittest.TestCase):
    def test_basic_block(self):
        text = "---\ntitle: Foo\nai-usage: ai-assisted\n---\n# Foo\n"
        self.assertEqual(L.front_matter(text), ["title: Foo", "ai-usage: ai-assisted"])

    def test_bom_and_missing(self):
        self.assertEqual(L.front_matter("﻿---\ntitle: x\n---\n"), ["title: x"])
        self.assertIsNone(L.front_matter("# Foo\n"))
        self.assertIsNone(L.front_matter(""))
        self.assertIsNone(L.front_matter("---\ntitle: x\n"))

    def test_parse_fields(self):
        lines = ["title: 'Quickstart: hashtags (#)'", "description: plain # comment", "ms.custom:",
                 "  - ai-gen-docs", "- item: no", "# comment: no", "title: second",
                 'ms.date: "04/20/2026"']
        f = L.parse_fields(lines)
        self.assertEqual(list(f.keys()), ["title", "description", "ms.custom", "ms.date"])
        self.assertEqual(f["title"], "Quickstart: hashtags (#)")
        self.assertEqual(f["description"], "plain")
        self.assertEqual(f["ms.custom"], "")
        self.assertEqual(f["ms.date"], "04/20/2026")

    def test_ai_label_key_variants(self):
        for key in ("ai-usage", "ms.ai-usage", "ai.usage", "AI-Usage", "ai_usage"):
            self.assertEqual(L.ai_label({"title": "x", key: "ai-generated"}), (key, "ai-generated"))
        for key in ("ai-usage-note", "ms.custom", "usage"):
            self.assertEqual(L.ai_label({key: "ai-generated"}), ("", ""))

    def test_category(self):
        self.assertEqual(L.category("ai-usage", "ai-assisted"), "ai-assisted")
        self.assertEqual(L.category("ai-usage", "AI-Generated"), "ai-generated")
        self.assertEqual(L.category("ai-usage", "AI assisted"), "other-ai")
        self.assertEqual(L.category("ai-usage", "human-only"), "non-ai")
        self.assertEqual(L.category("ai-usage", "maintained"), "non-ai")
        self.assertEqual(L.category("ai-usage", ""), "non-ai")
        self.assertEqual(L.category("", "ai-generated"), "")

    def test_other_ai_tokens(self):
        lines = ["title: Use ai-generated images", "ai-usage: ai-assisted", "ms.custom:",
                 "  - ai-gen-docs-bap", "  - devx-track", "ms.collection: ai-assisted-x"]
        self.assertEqual(L.other_ai_tokens(lines, "ai-usage"), ["ai-gen-docs-bap", "ai-assisted"])
        self.assertEqual(L.other_ai_tokens(None, ""), [])

    def test_date_year(self):
        self.assertEqual(L.date_year("04/20/2026"), 2026)
        self.assertEqual(L.date_year("4/2/2025"), 2025)
        self.assertEqual(L.date_year("2025-12-05"), 2025)
        self.assertEqual(L.date_year("2025-12-05T00:00:00.0000000Z"), 2025)
        self.assertEqual(L.date_year("'01/02/2024'"), 2024)
        for bad in ("", "TBD", "01/01/1890", "04/20/20261"):
            self.assertIsNone(L.date_year(bad))

    def test_include_and_locale(self):
        self.assertTrue(L.is_include("articles/includes/foo.md"))
        self.assertTrue(L.is_include("docs\\Includes\\x.md"))
        self.assertFalse(L.is_include("includes.md"))
        self.assertFalse(L.is_include("articles/foo.md"))
        for name in ("azure-docs.de-de", "sql-docs.zh-tw", "x.sr-latn-rs", "OfficeDocs-SharePoint.ja-JP"):
            self.assertTrue(L.LOCALE_RE.search(name), name)
        for name in ("azure-docs", "dynamics-365-ai", "learn.microsoft.com"):
            self.assertIsNone(L.LOCALE_RE.search(name), name)

    def test_describe_file(self):
        text = md(label="ai-generated", key="ms.ai-usage", extra="ms.custom:\n  - ai-gen-title")
        d = L.describe_file("a\\b.md", text)
        self.assertEqual(d["path"], "a/b.md")
        self.assertTrue(d["is_article"])
        self.assertFalse(d["include"])
        self.assertEqual((d["ai_key"], d["ai_value"], d["category"]), ("ms.ai-usage", "ai-generated", "ai-generated"))
        self.assertEqual(d["year"], 2026)
        self.assertEqual(d["ms_topic"], "how-to")
        self.assertEqual(d["other_tokens"], "ai-gen-title")
        inc = L.describe_file("x/includes/i.md", text)
        self.assertFalse(inc["is_article"])
        self.assertTrue(inc["include"])
        bare = L.describe_file("r.md", "# hi")
        self.assertFalse(bare["is_article"])
        self.assertEqual(bare["category"], "")
        self.assertIsNone(bare["year"])

    def test_docfx_ai(self):
        obj = {"build": {"globalMetadata": {"ms.ai-usage": "ai-assisted", "ms.topic": "x"},
                         "fileMetadata": {"ai-usage": {"articles/foo/**.md": "ai-generated"},
                                          "ms.author": {"**": "x"}}}}
        self.assertEqual(L.docfx_ai(obj), [("globalMetadata", "ms.ai-usage", "", "ai-assisted"),
                                           ("fileMetadata", "ai-usage", "articles/foo/**.md", "ai-generated")])
        self.assertEqual(L.docfx_ai(None), [])
        self.assertEqual(L.docfx_ai({"build": []}), [])


class RepoTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_scan_repo(self):
        r = self.root
        write(os.path.join(r, "articles", "a.md"), md(label="ai-assisted"))
        write(os.path.join(r, "articles", "b.md"), md(date="01/05/2023"))
        write(os.path.join(r, "articles", "includes", "i.md"), md(label="ai-generated"))
        write(os.path.join(r, ".git", "x.md"), md(label="ai-assisted"))
        write(os.path.join(r, "README.md"), "# readme\n")
        write(os.path.join(r, "notes.txt"), md(label="ai-assisted"))
        write(os.path.join(r, "docfx.json"),
              json.dumps({"build": {"fileMetadata": {"ai-usage": {"articles/x/**": "ai-assisted"}}}}))
        files, docfx = L.scan_repo(r)
        self.assertEqual([f["path"] for f in files],
                         ["README.md", "articles/a.md", "articles/b.md", "articles/includes/i.md"])
        st = L.repo_stats(files)
        self.assertEqual((st["md"], st["articles"], st["ai_labelled"], st["ai_assisted"],
                          st["ai_generated"], st["include_ai_labelled"]), (4, 2, 1, 1, 0, 1))
        self.assertEqual(docfx, [{"path": "docfx.json", "where": "fileMetadata", "key": "ai-usage",
                                  "glob": "articles/x/**", "value": "ai-assisted"}])

    def test_build_frame(self):
        base = {"pushed_at": "2026-10-01T00:00:00Z", "default_branch": "main"}
        repos = [
            dict(base, full_name="MicrosoftDocs/a", name="a", size=10),
            dict(base, full_name="MicrosoftDocs/c", name="c", size=50),
            dict(base, full_name="MicrosoftDocs/b", name="b", size=50, default_branch="live"),
            dict(base, full_name="MicrosoftDocs/edge", name="edge", size=5, pushed_at="2026-05-01T00:00:00Z"),
            dict(base, full_name="MicrosoftDocs/f", name="f", size=99, fork=True),
            dict(base, full_name="MicrosoftDocs/g", name="g", size=99, archived=True),
            dict(base, full_name="MicrosoftDocs/azure-docs.de-de", name="azure-docs.de-de", size=99),
            dict(base, full_name="MicrosoftDocs/old", name="old", size=99, pushed_at="2026-04-30T23:59:59Z"),
            dict(base, full_name="MicrosoftDocs/p", name="p", size=99, private=True),
            {"name": "nofullname"},
        ]
        eligible, excluded = L.build_frame(repos)
        self.assertEqual([e["full_name"] for e in eligible],
                         ["MicrosoftDocs/b", "MicrosoftDocs/c", "MicrosoftDocs/a", "MicrosoftDocs/edge"])
        self.assertEqual(eligible[0]["default_branch"], "live")
        self.assertEqual(dict(excluded), {"fork": 1, "archived": 1, "localized copy": 1,
                                          "not pushed since 2026-05-01": 1, "not public": 1, "bad entry": 1})

    def test_list_org_pages_and_retry(self):
        calls, sleeps = [], []
        pages = [[{"full_name": "o/r%d" % i} for i in range(100)], [{"full_name": "o/x"}] * 3]
        state = {"failed": False}

        def opener(req):
            calls.append(req.full_url)
            if not state["failed"]:
                state["failed"] = True
                raise OSError("rate limited")
            page = int(urllib.parse.parse_qs(urllib.parse.urlparse(req.full_url).query)["page"][0])
            return json.dumps(pages[page - 1]).encode()

        repos = L.list_org(opener, sleeps.append)
        self.assertEqual(len(repos), 103)
        self.assertEqual(len(calls), 3)
        self.assertEqual(sleeps, [3700])

        def broken(req):
            raise OSError("down")
        sleeps2 = []
        with self.assertRaises(RuntimeError):
            L.list_org(broken, sleeps2.append)
        self.assertEqual(sleeps2, [3700])


class SummaryTests(unittest.TestCase):
    def preds(self, files, rows=None):
        return L.summarise(files, rows or [{"status": "read", "ai_labelled": 1}])["predictions"]

    def test_p1_boundaries_inclusive(self):
        self.assertTrue(self.preds([art("ai-assisted")] + [art()] * 19)["P1"]["held"])        # 5%
        self.assertFalse(self.preds([art()] * 20)["P1"]["held"])                             # 0%
        self.assertTrue(self.preds([art("ai-assisted")] * 7 + [art()] * 13)["P1"]["held"])   # 35%
        self.assertFalse(self.preds([art("ai-assisted")] * 8 + [art()] * 12)["P1"]["held"])  # 40%
        self.assertIsNone(self.preds([])["P1"]["held"])

    def test_p2_ratio(self):
        self.assertTrue(self.preds([art("ai-assisted")] * 3 + [art("ai-generated")])["P2"]["held"])
        self.assertFalse(self.preds([art("ai-assisted")] * 2 + [art("ai-generated")])["P2"]["held"])
        p = self.preds([art("ai-assisted")])["P2"]
        self.assertTrue(p["held"])
        self.assertIsNone(p["ratio"])
        self.assertIsNone(self.preds([art()])["P2"]["held"])

    def test_p3_recent_share(self):
        files = [art("ai-assisted", 2025), art("ai-assisted", 2026), art("ai-generated", 2026),
                 art("ai-assisted", 2024), art("ai-assisted", None)]
        p = self.preds(files)["P3"]
        self.assertEqual(p["known_year"], 4)
        self.assertEqual(p["value_pct"], 75.0)
        self.assertTrue(p["held"])
        files[0] = art("ai-assisted", 2023)
        self.assertFalse(self.preds(files)["P3"]["held"])

    def test_p4_three_times(self):
        new = [art("ai-assisted", 2026)] * 3 + [art("", 2026)] * 97
        old = [art("ai-assisted", 2023)] + [art("", 2023)] * 99
        self.assertTrue(self.preds(new + old)["P4"]["held"])             # 3% vs 1%: exactly 3x
        new2 = [art("ai-assisted", 2026)] * 2 + [art("", 2026)] * 98
        self.assertFalse(self.preds(new2 + old)["P4"]["held"])           # 2x
        self.assertIsNone(self.preds(new + old[:99])["P4"]["held"])      # old group under 100
        none_old = [art("", 2023)] * 100
        self.assertTrue(self.preds(new + none_old)["P4"]["held"])        # 0% before: any label held
        self.assertFalse(self.preds([art("", 2026)] * 100 + none_old)["P4"]["held"])

    def test_p5_repos(self):
        rows = [{"status": "read", "ai_labelled": 2}] * 3 + [{"status": "read", "ai_labelled": 0},
                                                              {"status": "too few articles", "ai_labelled": 0}]
        p = L.summarise([art()], rows)["predictions"]["P5"]
        self.assertEqual((p["repos_with_label"], p["repos_read"]), (3, 4))
        self.assertFalse(p["held"])                                      # 75%
        rows.append({"status": "read", "ai_labelled": "5"})
        self.assertTrue(L.summarise([art()], rows)["predictions"]["P5"]["held"])  # 80%

    def test_p6_noncanonical(self):
        ten = [art("ai-assisted")] * 9 + [art("ai-assisted", key="ms.ai-usage")]
        self.assertFalse(self.preds(ten)["P6"]["held"])                  # 10% is not under 10%
        self.assertTrue(self.preds(ten + [art("ai-generated")])["P6"]["held"])
        self.assertFalse(self.preds([art("other-ai")] + [art("ai-assisted")] * 8)["P6"]["held"])
        self.assertIsNone(self.preds([art()])["P6"]["held"])

    def test_gate_and_includes(self):
        s = L.summarise([art("ai-assisted"), art("ai-generated", include=True)], [{"status": "read", "ai_labelled": 1}])
        self.assertFalse(s["gate"]["passed"])
        self.assertEqual((s["articles"], s["ai_labelled"], s["include_ai_labelled"]), (1, 1, 1))
        old = (L.GATE_REPOS, L.GATE_ARTICLES)
        try:
            L.GATE_REPOS, L.GATE_ARTICLES = 1, 1
            self.assertTrue(L.summarise([art()], [{"status": "read", "ai_labelled": 0}])["gate"]["passed"])
        finally:
            L.GATE_REPOS, L.GATE_ARTICLES = old


class MainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.out = os.path.join(self.tmp, "out")
        self.work = os.path.join(self.tmp, "work")
        os.makedirs(self.work)
        self.calls = []

    def opener(self, prereg=True):
        base = {"pushed_at": "2026-11-01T00:00:00Z", "default_branch": "main"}
        page1 = [dict(base, full_name="MicrosoftDocs/fail", name="fail", size=300),
                 dict(base, full_name="MicrosoftDocs/small", name="small", size=200),
                 dict(base, full_name="MicrosoftDocs/big", name="big", size=100),
                 dict(base, full_name="MicrosoftDocs/extra", name="extra", size=50)]

        def opener(req):
            url = req.full_url
            self.calls.append(url)
            if url.startswith(L.REPO_API):
                if not prereg:
                    return b"[]"
                return json.dumps([
                    {"sha": "s2", "commit": {"committer": {"date": "2026-11-09T03:00:00Z"}}},
                    {"sha": "s1", "commit": {"committer": {"date": "2026-11-09T02:00:00Z"}}}]).encode()
            if url.startswith(L.ORG_API):
                return json.dumps(page1).encode()
            raise AssertionError(url)
        return opener

    def cloner(self, full_name, branch, dest):
        if full_name.endswith("/fail"):
            return "clone failed: boom", ""
        if full_name.endswith("/small"):
            write(os.path.join(dest, "articles", "only.md"), md())
        else:
            write(os.path.join(dest, "articles", "one.md"), md(label="ai-assisted"))
            write(os.path.join(dest, "articles", "two.md"), md(date="2025-03-01", label="ai-generated", key="ms.ai-usage"))
            write(os.path.join(dest, "articles", "three.md"), md(date="02/02/2022"))
            write(os.path.join(dest, "docfx.json"), json.dumps({"build": {"globalMetadata": {"ai-usage": "ai-assisted"}}}))
        return None, "abc123"

    def test_full_run(self):
        rc = L.main(["--out-dir", self.out, "--target", "1", "--min-articles", "2", "--work-dir", self.work],
                    opener=self.opener(), cloner=self.cloner, sleep=lambda s: None)
        self.assertEqual(rc, 0)
        frame = read_csv(os.path.join(self.out, "frame.csv"))
        self.assertEqual([r["status"] for r in frame], ["clone failed: boom", "too few articles", "read", "not reached"])
        self.assertEqual(frame[2]["commit"], "abc123")
        self.assertEqual(frame[2]["ai_labelled"], "2")
        files = read_csv(os.path.join(self.out, "files.csv"))
        self.assertEqual(len(files), 3)
        labelled = read_csv(os.path.join(self.out, "labelled.csv"))
        self.assertEqual(sorted(r["path"] for r in labelled), ["articles/one.md", "articles/two.md"])
        self.assertTrue(all(r["repo"] == "MicrosoftDocs/big" for r in labelled))
        self.assertEqual(len(read_csv(os.path.join(self.out, "docfx_ai.csv"))), 1)
        with open(os.path.join(self.out, "census.json"), encoding="utf-8") as fh:
            census = json.load(fh)
        self.assertEqual(census["meta"]["prereg"]["committed_at"], "2026-11-09T02:00:00Z")
        self.assertEqual((census["summary"]["articles"], census["summary"]["ai_labelled"]), (3, 2))
        self.assertEqual(census["meta"]["clones"], 3)
        with open(os.path.join(self.out, "LEARNLABELS_AUTO.md"), encoding="utf-8") as fh:
            self.assertIn("MicrosoftDocs/big", fh.read())
        self.assertEqual(os.listdir(self.work), [])

    def test_waits_for_prereg_then_stops(self):
        sleeps = []
        rc = L.main(["--out-dir", self.out, "--wait-prereg-minutes", "30", "--work-dir", self.work],
                    opener=self.opener(prereg=False), cloner=self.cloner, sleep=sleeps.append)
        self.assertEqual(rc, 3)
        self.assertEqual(sleeps, [900, 900])
        self.assertFalse(any(u.startswith(L.ORG_API) for u in self.calls))
        self.assertTrue(os.path.exists(os.path.join(self.out, "census.json")))


if __name__ == "__main__":
    unittest.main()
