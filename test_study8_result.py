"""Recompute study 8's gates and predictions from the published pages.csv and hand check.

    python -m unittest -v test_study8_result

Checks that the gates and P1 to P6, computed here from census/2026-11-ms-learn-ai-shown/pages.csv
with the hand-check corrections in hand_check.csv, equal the tool's own shown.json (before the
hand check) and the table in RESULT.md (after it). It also checks that the hand check covers what
the pre-registration says: every matched sentence in strata C, D and U, and the first 10 matched
pages of A and B sorted by repo and path.

Standard library only. Made by MV2 of Munim, Inc., with AI agents working in his name. Apache-2.0.
"""
import csv
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.join(HERE, "census", "2026-11-ms-learn-ai-shown")
STRATA = ("A", "B", "C", "D", "U")
LABELLED = ("A", "B", "C")
END_HEADINGS = ("next steps", "next step", "related content")


def read_csv(name):
    with open(os.path.join(STUDY, name), newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def is_true(value):
    return value == "True"


def counted(rows):
    return [r for r in rows if r["stratum"] in STRATA and r["mapped"] == "yes"]


def grade(rows, false_positives=frozenset()):
    """Gates and predictions as pre-registered (inclusive bounds, integer arithmetic)."""
    pages = counted(rows)

    def note(r):
        return is_true(r["note_rendered"]) and (r["repo"], r["path"]) not in false_positives

    labelled = [r for r in pages if r["stratum"] in LABELLED]
    out = {}
    out["G1"] = (len(labelled), len({r["repo"] for r in labelled}))
    positive = [r for r in rows if r["stratum"] == "control-positive"]
    out["G2"] = len(positive) == 1 and is_true(positive[0]["note_rendered"])
    out["G3"] = (sum(1 for r in pages if is_true(r["md_served"])), len(pages))

    ab = [r for r in pages if r["stratum"] in ("A", "B")]
    out["P1"] = (sum(1 for r in ab if note(r)), len(ab))
    c = [r for r in pages if r["stratum"] == "C"]
    out["P2"] = (sum(1 for r in c if note(r)), len(c))
    u = [r for r in pages if r["stratum"] == "U"]
    out["P3"] = (sum(1 for r in u if note(r)), len(u))
    p4 = [r for r in labelled if note(r) and is_true(r["md_served"])]
    out["P4"] = (sum(1 for r in p4 if is_true(r["note_md"])), len(p4))
    p5 = [r for r in labelled if is_true(r["md_served"])]
    out["P5"] = (sum(1 for r in p5 if r["md_ai_key"].strip()), len(p5))
    p6 = [r for r in pages if is_true(r["md_served"]) and r["last_src_h2"] in END_HEADINGS]
    out["P6"] = (sum(1 for r in p6 if is_true(r["last_h2_missing"])), len(p6))
    return out


def held(name, k, n):
    rules = {
        "P1": (20, lambda: k * 10 >= n * 9),
        "P2": (10, lambda: k * 5 <= n),
        "P3": (20, lambda: k * 20 <= n),
        "P4": (20, lambda: k * 5 <= n),
        "P5": (20, lambda: k * 10 >= n * 9),
        "P6": (20, lambda: k * 5 >= n * 4),
    }
    minimum, rule = rules[name]
    if n < minimum:
        return None
    return rule()


class Study8Result(unittest.TestCase):
    def setUp(self):
        self.rows = read_csv("pages.csv")
        self.hand = read_csv("hand_check.csv")
        with open(os.path.join(STUDY, "shown.json"), encoding="utf-8-sig") as fh:
            self.shown = json.load(fh)
        with open(os.path.join(STUDY, "RESULT.md"), encoding="utf-8-sig") as fh:
            self.result = fh.read()
        self.false_positives = frozenset(
            (h["repo"], h["path"]) for h in self.hand if h["hand"] == "false_positive")

    def test_automatic_grades_equal_tool(self):
        auto = grade(self.rows)
        summary = self.shown["summary"]
        self.assertEqual(auto["G1"], (summary["gates"]["G1"]["labelled_ok"], summary["gates"]["G1"]["repos"]))
        self.assertTrue(auto["G2"])
        for name in ("P1", "P2", "P3", "P4", "P5", "P6"):
            tool = summary["predictions"][name]
            self.assertEqual(auto[name], (tool["k"], tool["n"]), name)
            self.assertEqual(held(name, *auto[name]), tool["held"], name)

    def test_hand_checked_grades(self):
        checked = grade(self.rows, self.false_positives)
        self.assertEqual(checked["G1"], (164, 15))
        self.assertTrue(checked["G2"])
        self.assertEqual(checked["G3"], (263, 263))
        self.assertEqual(checked["P1"], (131, 131))
        self.assertEqual(checked["P2"], (0, 33))
        self.assertEqual(checked["P3"], (0, 99))
        self.assertEqual(checked["P4"], (0, 131))
        self.assertEqual(checked["P5"], (164, 164))
        self.assertEqual(checked["P6"], (130, 131))
        for name in ("P1", "P2", "P3", "P4", "P5", "P6"):
            self.assertTrue(held(name, *checked[name]), name)

    def test_result_table(self):
        checked = grade(self.rows, self.false_positives)
        for name in ("P1", "P2", "P3", "P4", "P5", "P6"):
            lines = [line for line in self.result.splitlines() if line.startswith("| %s |" % name)]
            self.assertEqual(len(lines), 1, name)
            k, n = checked[name]
            self.assertIn("%d / %d" % (k, n), lines[0], name)
            self.assertTrue(lines[0].rstrip().endswith("| yes |"), name)

    def test_hand_check_covers_preregistered_rows(self):
        pages = counted(self.rows)
        matched_cdu = sorted((r["repo"], r["path"]) for r in pages
                             if r["stratum"] in ("C", "D", "U") and is_true(r["note_rendered"]))
        hand_cdu = sorted((h["repo"], h["path"]) for h in self.hand if h["check"] == "every_CDU")
        self.assertEqual(hand_cdu, matched_cdu)
        matched_ab = sorted((r["repo"], r["path"]) for r in pages
                            if r["stratum"] in ("A", "B") and is_true(r["note_rendered"]))[:10]
        hand_ab = [(h["repo"], h["path"]) for h in self.hand if h["check"] == "first10_AB"]
        self.assertEqual(hand_ab, matched_ab)
        by_key = {(r["repo"], r["path"]): r for r in pages}
        for h in self.hand:
            row = by_key[(h["repo"], h["path"])]
            self.assertEqual(h["stratum"], row["stratum"])
            self.assertEqual(h["sentence"], row["note_rendered_text"])
            self.assertIn(h["hand"], ("true_positive", "false_positive"))
        unmatched_ab = [r for r in pages if r["stratum"] in ("A", "B") and not is_true(r["note_rendered"])]
        self.assertEqual(unmatched_ab, [])  # so the browser check of unmatched A/B pages had none to open

    def test_note_follows_key_spelling(self):
        pages = counted(self.rows)
        for r in pages:
            if r["stratum"] in ("A", "B"):
                self.assertEqual(r["src_key"], "ai-usage")
                self.assertTrue(is_true(r["note_rendered"]), r["path"])
            if r["stratum"] == "C":
                self.assertIn(r["src_key"], ("ms.ai-usage", "ai.usage"))
                self.assertEqual(r["html_ai_key"], r["src_key"], r["path"])
                self.assertFalse(is_true(r["note_rendered"]), r["path"])
        self.assertEqual(sum(1 for r in pages if is_true(r["note_html"]) and r["stratum"] in LABELLED), 0)


if __name__ == "__main__":
    unittest.main()
