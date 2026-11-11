# Copyright 2026 Munim, Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
"""Offline tests for learnsnap.py (study 12). Run: python -m unittest -v test_learnsnap"""

import collections
import csv
import json
import os
import shutil
import tempfile
import unittest
import urllib.error

import learnsnap as S


def scanned(path, key="", value=""):
    """A file as learnlabels.scan_repo describes it."""
    return {"path": path, "is_article": True, "include": False, "ai_key": key,
            "ai_value": value, "category": S.LL.category(key, value), "year": 2026,
            "ms_topic": "", "other_tokens": ""}


def study7_row(path, key="ai-usage", value="ai-assisted", repo="MicrosoftDocs/p1"):
    """A row of study 7's labelled.csv (all values are text)."""
    return {"repo": repo, "path": path, "is_article": "True", "include": "False",
            "ai_key": key, "ai_value": value, "category": value, "year": "2026",
            "ms_topic": "", "other_tokens": ""}


def change(kind, key_a=""):
    return {"repo": "r", "path": "p", "change": kind, "key_a": key_a, "value_a": "",
            "key_b": "", "value_b": "", "is_article_b": True, "year_b": 2026}


class TestCompare(unittest.TestCase):
    def setUp(self):
        self.a_rows = [study7_row("a.md"),
                       study7_row("b.md", key="ms.ai-usage"),
                       study7_row("c.md", key="ms.ai-usage"),
                       study7_row("d.md"),
                       study7_row("e.md"),
                       study7_row("f.md", value="ai-generated")]
        self.b_files = [scanned("a.md", "ai-usage", "ai-assisted"),
                        scanned("b.md", "ai-usage", "ai-assisted"),
                        scanned("c.md", "ms.ai-usage", "ai-assisted"),
                        scanned("d.md"),
                        scanned("f.md", "ai-usage", "ai-assisted"),
                        scanned("g.md", "ai-usage", "ai-assisted"),
                        scanned("h.md", "ai-usage", "ai-generated"),
                        scanned("i.md")]

    def test_kinds(self):
        a_paths = {"a.md", "b.md", "c.md", "d.md", "e.md", "f.md", "g.md", "i.md"}
        rows = S.compare(self.a_rows, self.b_files, a_paths)
        kinds = dict((r["path"], r["change"]) for r in rows)
        self.assertEqual(kinds, {"a.md": "kept", "b.md": "key-fixed", "c.md": "kept",
                                 "d.md": "label-removed", "e.md": "file-gone",
                                 "f.md": "label-changed", "g.md": "new-label-existing-file",
                                 "h.md": "new-label-new-file"})

    def test_unknown_tree(self):
        rows = S.compare(self.a_rows, self.b_files, None)
        counts = collections.Counter(r["change"] for r in rows)
        self.assertEqual(counts["new-label-unknown-file"], 2)
        self.assertEqual(counts["new-label-existing-file"], 0)
        self.assertEqual(len(rows), 8)


class TestStatus(unittest.TestCase):
    def test_listing(self):
        listed = {"microsoftdocs/a": {"archived": False}, "microsoftdocs/b": {"archived": True}}
        self.assertEqual(S.repo_status("MicrosoftDocs/A", listed), "public")
        self.assertEqual(S.repo_status("MicrosoftDocs/b", listed), "archived")
        self.assertEqual(S.repo_status("MicrosoftDocs/c", listed), "not listed")

    def test_lookup_404(self):
        def opener(req):
            raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)
        self.assertEqual(S.api_lookup("MicrosoftDocs/gone", opener), "not public")

    def test_lookup_renamed(self):
        def opener(req):
            return json.dumps({"full_name": "MicrosoftDocs/new-name", "private": False,
                               "archived": False}).encode("utf-8")
        self.assertEqual(S.api_lookup("MicrosoftDocs/old", opener),
                         "renamed to MicrosoftDocs/new-name")


class TestSummary(unittest.TestCase):
    def setUp(self):
        self.rows = []
        for i in range(25):
            self.rows.append({"repo": "p%d" % i, "group": "panel", "status_now": "public",
                              "read": "read", "a_tree": "yes", "articles": 100,
                              "ai_labelled": 5})
        self.rows.append({"repo": "x1", "group": "study7-other", "status_now": "not public",
                          "read": "not read", "a_tree": ""})
        self.rows.append({"repo": "x2", "group": "study7-other", "status_now": "archived",
                          "read": "not read", "a_tree": ""})
        for i in range(10):
            self.rows.append({"repo": "n%d" % i, "group": "new", "status_now": "public",
                              "read": "read", "a_tree": "", "articles": 200,
                              "ai_labelled": 2 if i < 5 else 0})
        self.changes = ([change("new-label-existing-file")] * 30
                        + [change("new-label-new-file")] * 10
                        + [change("label-removed", "ai-usage")] * 2
                        + [change("key-fixed", "ms.ai-usage")]
                        + [change("kept", "ms.ai-usage")] * 2)

    def test_wave1(self):
        s = S.summarise(self.rows, self.changes, 1, 2.0)
        p = s["predictions"]
        self.assertEqual(s["new_labels"], 40)
        self.assertEqual(s["new_labels_per_day"], 20.0)
        self.assertTrue(p["G1"]["held"])
        self.assertTrue(p["P1"]["held"])
        self.assertTrue(p["P2"]["held"])
        self.assertTrue(p["P3"]["held"])
        self.assertEqual(p["P4"]["variant_a"], 3)
        self.assertEqual(p["P4"]["key_fixed"], 1)
        self.assertTrue(p["P4"]["held"])
        self.assertEqual(s["study7_repos"], 27)
        self.assertTrue(p["P5"]["held"])
        self.assertEqual(p["P6"]["pct"], 50.0)
        self.assertTrue(p["P6"]["held"])
        self.assertEqual(p["P7"]["pct"], 0.5)
        self.assertFalse(p["P7"]["held"])

    def test_wave2(self):
        s = S.summarise(self.rows, self.changes, 2, 2.0)
        p = s["predictions"]
        self.assertFalse(p["W2-P1"]["held"])
        self.assertTrue(p["W2-P2"]["held"])
        self.assertTrue(p["W2-P3"]["held"])

    def test_days(self):
        self.assertEqual(S.days_between("2026-11-09T11:21:00Z", "2026-11-11T11:21:00Z"), 2.0)


class TestMain(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.s7 = os.path.join(self.tmp, "s7")
        self.out = os.path.join(self.tmp, "out")
        os.makedirs(self.s7)
        with open(os.path.join(self.s7, "frame.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["rank", "repo", "status", "commit", "default_branch"])
            w.writerow(["1", "MicrosoftDocs/p1", "read", "aaa", "main"])
            w.writerow(["2", "MicrosoftDocs/p2", "read", "bbb", "main"])
            w.writerow(["3", "MicrosoftDocs/o1", "not reached", "", ""])
        with open(os.path.join(self.s7, "labelled.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=S.LL.FILE_COLUMNS)
            w.writeheader()
            w.writerow(study7_row("x.md", repo="MicrosoftDocs/p1"))
            w.writerow(study7_row("y.md", key="ms.ai-usage", repo="MicrosoftDocs/p2"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_offline_run(self):
        def repo(name, size):
            return {"full_name": "MicrosoftDocs/" + name, "name": name, "size": size,
                    "default_branch": "main", "pushed_at": "2026-11-10T00:00:00Z",
                    "fork": False, "archived": False, "private": False, "visibility": "public"}
        listing = [repo("p1", 30), repo("o1", 20), repo("n1", 10)]

        def opener(req):
            return json.dumps(listing).encode("utf-8")

        cloned = {}

        def cloner(full_name, branch, dest):
            os.makedirs(dest)
            cloned[dest] = full_name
            return None, "c-" + full_name

        content = {"MicrosoftDocs/p1": [scanned("x.md", "ai-usage", "ai-assisted"),
                                        scanned("z.md", "ai-usage", "ai-generated")],
                   "MicrosoftDocs/o1": [scanned("o.md", "ai-usage", "ai-assisted"),
                                        scanned("o2.md")],
                   "MicrosoftDocs/n1": [scanned("n.md")]}

        def scanner(dest):
            return [dict(f) for f in content[cloned[dest]]], []

        def tree(dest, sha):
            return {"x.md"}

        rc = S.main(["--out-dir", self.out, "--wave", "1", "--study7-dir", self.s7,
                     "--no-prereg-check"], opener=opener, cloner=cloner, scanner=scanner,
                    tree=tree, lookup=lambda name: "not public",
                    now=lambda: "2026-11-11T11:21:00Z")
        self.assertEqual(rc, 0)
        with open(os.path.join(self.out, "changes.csv"), encoding="utf-8") as fh:
            changes = list(csv.DictReader(fh))
        self.assertEqual(sorted((c["path"], c["change"]) for c in changes),
                         [("x.md", "kept"), ("z.md", "new-label-new-file")])
        with open(os.path.join(self.out, "frame.csv"), encoding="utf-8") as fh:
            frame = dict((r["repo"], r) for r in csv.DictReader(fh))
        self.assertEqual(frame["MicrosoftDocs/p2"]["status_now"], "not public")
        self.assertEqual(frame["MicrosoftDocs/p2"]["read"], "not read")
        self.assertEqual(frame["MicrosoftDocs/n1"]["group"], "new")
        self.assertEqual(frame["MicrosoftDocs/o1"]["read"], "read")
        with open(os.path.join(self.out, "labelled.csv"), encoding="utf-8") as fh:
            self.assertEqual(len(list(csv.DictReader(fh))), 3)
        with open(os.path.join(self.out, "snapshot.json"), encoding="utf-8") as fh:
            snap = json.load(fh)
        self.assertEqual(snap["summary"]["not_public"], 1)
        self.assertEqual(snap["summary"]["new_labels"], 1)

    def test_wave2_too_early(self):
        rc = S.main(["--out-dir", self.out, "--wave", "2", "--no-prereg-check"],
                    now=lambda: "2026-12-01T00:00:00Z")
        self.assertEqual(rc, 5)


if __name__ == "__main__":
    unittest.main()
