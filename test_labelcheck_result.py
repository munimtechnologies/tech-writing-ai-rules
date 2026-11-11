# SPDX-License-Identifier: Apache-2.0
"""Recompute the docs-ai-label-check tool check from its published files.

census/2026-11-labelcheck/ holds the unchanged output of labelcheck_repos.py
(ai_label_check.py 0.1.0 on nine Microsoft Learn docs repos, 2026-11-11) and a
hand check of eight findings. This test checks that:

- every per-repo count in repos.csv equals the number of rows in findings.csv
  with that code, and the variant_keys column equals the keys found;
- repos.csv and labelcheck.json name the same repos and commits;
- every variant-key finding is ms.ai-usage or ai.usage, marked fixable;
- every hand-check row matches a finding (code, key, value and line) and
  agrees with it;
- the totals quoted in RESULT.md are the totals of the data.

Run: python -m unittest -v test_labelcheck_result

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his
name. Code Apache-2.0, data CC BY 4.0.
"""
import csv
import json
import os
import unittest
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "census", "2026-11-labelcheck")

# repos.csv column -> findings.csv code
CODES = {
    "variant_key": "variant-key",
    "bad_value": "bad-value",
    "empty_value": "empty-value",
    "other_value": "other-value",
    "duplicate_key": "duplicate-key",
    "nested": "nested",
    "commented": "commented",
    "stray_token": "stray-token",
    "include_label": "include-label",
}


def read_csv(name):
    with open(os.path.join(D, name), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fmt(n):
    return f"{n:,}"


class LabelcheckResult(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repos = read_csv("repos.csv")
        cls.findings = read_csv("findings.csv")
        cls.hand = read_csv("hand_check.csv")
        with open(os.path.join(D, "labelcheck.json"), encoding="utf-8") as f:
            cls.meta = json.load(f)["meta"]
        with open(os.path.join(D, "RESULT.md"), encoding="utf-8") as f:
            cls.result = f.read()

    def test_nine_repos_all_read(self):
        self.assertEqual(len(self.repos), 9)
        self.assertTrue(all(r["status"] == "ok" for r in self.repos))

    def test_commits_match_json(self):
        from_csv = {r["repo"]: r["commit"] for r in self.repos}
        from_json = {r["repo"]: r["commit"] for r in self.meta["repos"]}
        self.assertEqual(from_csv, from_json)

    def test_counts_match_findings(self):
        per = Counter((f["repo"], f["code"]) for f in self.findings)
        known = set(CODES.values())
        for f in self.findings:
            self.assertIn(f["code"], known, f)
        for r in self.repos:
            for col, code in CODES.items():
                self.assertEqual(int(r[col]), per[(r["repo"], code)],
                                 (r["repo"], col))

    def test_variant_keys_column(self):
        for r in self.repos:
            keys = Counter(f["key"] for f in self.findings
                           if f["repo"] == r["repo"]
                           and f["code"] == "variant-key")
            want = ",".join(f"{k}={n}" for k, n in sorted(keys.items()))
            got = ",".join(sorted(p for p in r["variant_keys"].split(",") if p))
            self.assertEqual(got, want, r["repo"])

    def test_variant_findings_are_fixable_errors(self):
        for f in self.findings:
            if f["code"] == "variant-key":
                self.assertIn(f["key"], ("ms.ai-usage", "ai.usage"))
                self.assertEqual(f["severity"], "error")
                self.assertEqual(f["fixable"], "yes")

    def test_hand_check_matches_findings(self):
        self.assertEqual(len(self.hand), 8)
        index = {(f["repo"], f["path"], f["code"]): f for f in self.findings}
        for h in self.hand:
            f = index.get((h["repo"], h["path"], h["code"]))
            self.assertIsNotNone(f, h["path"])
            self.assertEqual((f["key"], f["value"], f["line"]),
                             (h["key"], h["value"], h["line"]))
            self.assertEqual(h["agrees"], "yes")
            self.assertEqual((h["seen_key"], h["seen_value"]),
                             (h["key"], h["value"]))
            if h["seen_line"]:
                self.assertEqual(h["seen_line"], h["line"])

    def test_hand_check_covers_every_repo_with_an_error(self):
        with_error = {f["repo"] for f in self.findings
                      if f["severity"] == "error"}
        checked = {h["repo"] for h in self.hand}
        self.assertTrue(with_error <= checked)

    def test_result_totals(self):
        variant = [f for f in self.findings if f["code"] == "variant-key"]
        keys = Counter(f["key"] for f in variant)
        repos_with = {f["repo"] for f in variant}
        md = sum(int(r["markdown"]) for r in self.repos)
        assisted = sum(int(r["ai_assisted"]) for r in self.repos)
        generated = sum(int(r["ai_generated"]) for r in self.repos)
        include = sum(1 for f in self.findings if f["code"] == "include-label")
        other = sum(1 for f in self.findings if f["code"] == "other-value")
        self.assertEqual(len(variant), 168)
        self.assertEqual(len(repos_with), 5)
        self.assertEqual((keys["ms.ai-usage"], keys["ai.usage"]), (122, 46))
        text = self.result
        self.assertIn(f"**{len(variant)} articles in five repos", text)
        self.assertIn(f"({keys['ms.ai-usage']} `ms.ai-usage`, "
                      f"{keys['ai.usage']} `ai.usage`)", text)
        self.assertIn(f"| **Total** | **{fmt(md)}** | **{fmt(assisted)}** | "
                      f"**{fmt(generated)}** | **{len(variant)}** | "
                      f"**{include}** | **{other}** |", text)
        self.assertIn(f"**{include} labels sit in include files**", text)

    def test_new_container_apps_articles(self):
        paths = {f["path"] for f in self.findings
                 if f["repo"] == "MicrosoftDocs/azure-docs"
                 and f["path"].startswith("articles/container-apps/")}
        self.assertEqual(len(paths), 5)
        self.assertIn("articles/container-apps/migrate-overview.md", paths)
        self.assertIn("articles/container-apps/migrate-azure-migrate.md", paths)
        sre = sum(1 for f in self.findings
                  if f["path"].startswith("articles/sre-agent/")
                  and f["code"] == "variant-key")
        self.assertEqual(sre, 114)


if __name__ == "__main__":
    unittest.main()
