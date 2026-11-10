"""Check that study 6's published grades.json is exactly what grade_study6.py computes from the published coding.

    python -m unittest -v test_study6_result

Standard library only. Made by MV2 of Munim, Inc., with AI agents working in his name. Apache-2.0.
"""
import csv
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import grade_study6  # noqa: E402

STUDY = os.path.join(HERE, "census", "2026-11-llms-txt-agents")


def path(name):
    return os.path.join(STUDY, name)


class Study6Result(unittest.TestCase):
    def setUp(self):
        self.coding = grade_study6.parse_coding(grade_study6.read_csv(path("coding.csv")))
        self.probes = grade_study6.read_csv(path("probes.csv"))
        with open(path("grades.json"), encoding="utf-8-sig") as fh:
            self.published = json.load(fh)

    def test_grades_match_the_script(self):
        self.assertEqual(grade_study6.grade(self.coding, self.probes), self.published)

    def test_every_code_sample_file_coded_once(self):
        ids = [c["id"] for c in self.coding]
        self.assertEqual(len(ids), 200)
        self.assertEqual(len(set(ids)), 200)
        self.assertEqual(sum(1 for c in self.coding if c["recall"]), 20)

    def test_coded_files_are_the_tool_code_sample(self):
        sample = {p["id"] for p in self.probes if (p.get("code_sample") or "").strip() == "1"}
        recall = {p["id"] for p in self.probes if (p.get("recall_sample") or "").strip() == "1"}
        self.assertEqual({c["id"] for c in self.coding}, sample)
        self.assertEqual({c["id"] for c in self.coding if c["recall"]}, recall)

    def test_override_list(self):
        with open(path("overrides.csv"), newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))
        flagged = {p["id"] for p in self.probes if (p.get("override") or "0").strip() not in ("", "0")}
        self.assertEqual({r["id"] for r in rows}, flagged)
        for r in rows:
            self.assertIn(r["override"], ("yes", "no"), r["id"])
            self.assertLessEqual(len(r["quote"]), 200, r["id"])
        self.assertEqual([r["id"] for r in rows if r["override"] == "yes"], ["W0560"])


if __name__ == "__main__":
    unittest.main()
