# SPDX-License-Identifier: Apache-2.0
"""Recompute study 16's gate and predictions from the published files.

Study 16 (census/2026-11-mintlify-snippets/) asks whether Mintlify's Markdown
copies for AI agents carry the content of <Snippet file> tags. This test reads
the unchanged sites.csv, instances.csv and controls.csv written by mintsnip.py
0.1.0 and the hand check, and checks the verdicts and figures in RESULT.md.

Run: python -m unittest -v test_study16_result

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his
name. Code Apache-2.0, data CC BY 4.0.
"""
import csv
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "census", "2026-11-mintlify-snippets")


def read_csv(name):
    with open(os.path.join(D, name), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def yes(v):
    return str(v) in ("True", "true", "1")


def share(rows, pred):
    return sum(1 for r in rows if pred(r)) / len(rows)


class Study16(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sites = read_csv("sites.csv")
        cls.all_inst = read_csv("instances.csv")
        cls.controls = read_csv("controls.csv")
        cls.hand = read_csv("hand_check.csv")
        with open(os.path.join(D, "RESULT.md"), encoding="utf-8") as f:
            cls.result = f.read()
        cls.counted = [s["repo"] for s in cls.sites if yes(s["counted"])]
        cls.inst = [r for r in cls.all_inst if r["repo"] in cls.counted]

    def test_gate(self):
        self.assertEqual(sorted(self.counted), ["Helicone/helicone", "agno-agi/docs", "mem0ai/mem0",
                                                "supermemoryai/supermemory"])
        self.assertEqual(len(self.counted), 4)    # G1 needs 3
        self.assertEqual(len(self.inst), 37)

    def test_p1_mem0(self):
        mem = [r for r in self.inst if r["repo"] == "mem0ai/mem0" and r["loc"] == "_snippets"
               and yes(r["has_needles"])]
        self.assertEqual(len(mem), 15)
        self.assertEqual(share(mem, lambda r: r["status"] == "tag-kept"), 1.0)
        self.assertEqual(share(mem, lambda r: yes(r["html_has"])), 1.0)

    def test_p2_fails(self):
        und = [r for r in self.inst if r["loc"] == "_snippets" and (yes(r["has_needles"]) or r["status"] == "tag-kept")]
        self.assertEqual(len(und), 35)
        kept = sum(1 for r in und if r["status"] == "tag-kept")
        self.assertEqual(kept, 15)
        self.assertLess(kept / len(und), 0.8)
        agno = [r for r in und if r["repo"] == "agno-agi/docs"]
        self.assertEqual(len(agno), 20)
        self.assertTrue(all(r["status"] == "expanded" for r in agno))

    def test_p3_too_few(self):
        snp = [r for r in self.inst if r["loc"] == "snippets" and (yes(r["has_needles"]) or r["status"] == "tag-kept")]
        self.assertEqual(len(snp), 2)
        self.assertTrue(all(r["status"] == "tag-kept" for r in snp))
        self.assertEqual({r["repo"] for r in snp}, {"Helicone/helicone", "supermemoryai/supermemory"})

    def test_p4_controls(self):
        ctl = [c for c in self.controls if yes(c["read"]) and yes(c["has_needles"])]
        self.assertEqual(len(ctl), 25)
        self.assertEqual(share(ctl, lambda c: yes(c["md_has"])), 1.0)
        self.assertEqual(len({c["repo"] for c in ctl}), 7)
        self.assertIn("Helicone/helicone", {c["repo"] for c in ctl})
        self.assertIn("supermemoryai/supermemory", {c["repo"] for c in ctl})

    def test_p5_people_see_it(self):
        rows = [r for r in self.inst if r["loc"] not in ("missing", "variable") and yes(r["has_needles"])]
        self.assertEqual(len(rows), 37)
        self.assertEqual(sum(1 for r in rows if yes(r["html_has"])), 34)
        self.assertGreaterEqual(34 / 37, 0.8)

    def test_hand_check(self):
        self.assertEqual(len(self.hand), 11)
        self.assertGreaterEqual(len({h["repo"] for h in self.hand}), 3)
        self.assertGreaterEqual(sum(1 for h in self.hand if "live" in h["checked"]), 5)
        counts = {}
        for h in self.hand:
            counts[h["status_right"]] = counts.get(h["status_right"], 0) + 1
        self.assertEqual(counts, {"yes": 9, "no": 1, "uncertain": 1})
        keyed = {(r["repo"], r["page"], r["file"]): r["status"] for r in self.all_inst}
        for h in self.hand:
            self.assertEqual(keyed[(h["repo"], h["page"], h["file"])], h["tool_status"], h["excerpt"])
        wrong = [h for h in self.hand if h["status_right"] == "no"]
        self.assertEqual([h["repo"] for h in wrong], ["mintlify/docs"])
        self.assertNotIn("mintlify/docs", self.counted)

    def test_result_quotes_these_numbers(self):
        for s in ("15/35 = 42.9%", "34/37 = 91.9%", "25/25", "15/15 kept, 15/15 shown", "9 of 11",
                  "**fails**", "**too few**"):
            self.assertIn(s, self.result)


if __name__ == "__main__":
    unittest.main()
