# SPDX-License-Identifier: Apache-2.0
# Offline tests for rawlink's pure helpers (no Mem0 needed).
# Made with AI agents working in the name of MV2 of Munim, Inc.
import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rawlink as rl  # noqa: E402


class Helpers(unittest.TestCase):
    def test_design(self):
        self.assertEqual(len(rl.RULES), 20)
        self.assertEqual(len(rl.EDITED), 10)
        self.assertEqual(len(rl.UNTOUCHED), 10)
        self.assertFalse(set(rl.EDITED) & set(rl.UNTOUCHED))
        self.assertEqual(len({e for e, _ in rl.RULES}), 20)
        for entity, text in rl.RULES:
            self.assertIn(entity, text)

    def test_final_text(self):
        self.assertTrue(rl.final_text(0).endswith(rl.SUFFIX))
        self.assertEqual(rl.final_text(1), rl.RULES[1][1])

    def test_rows_of(self):
        self.assertEqual(rl.rows_of(([1, 2], None)), [1, 2])
        self.assertEqual(rl.rows_of([[1, 2]]), [1, 2])
        self.assertEqual(rl.rows_of([1, 2]), [1, 2])
        self.assertEqual(rl.rows_of(None), [])
        self.assertEqual(rl.rows_of(([], None)), [])

    def test_linked_ids(self):
        rows = [SimpleNamespace(payload={"linked_memory_ids": ["a", "b"]}),
                SimpleNamespace(payload={"linked_memory_ids": ["b", "c"]}),
                SimpleNamespace(payload=None),
                {"payload": {"linked_memory_ids": ["d"]}},
                SimpleNamespace(payload={"linked_memory_ids": "x"})]
        self.assertEqual(rl.linked_ids(rows), {"a", "b", "c", "d"})

    def test_score_for(self):
        items = [{"id": "a", "score": 0.5}, {"id": "b", "score": None}]
        self.assertEqual(rl.score_for(items, "a"), 0.5)
        self.assertIsNone(rl.score_for(items, "b"))
        self.assertIsNone(rl.score_for(items, "z"))

    def _obs(self, **kw):
        base = {"spacy_loaded": True, "queries_with_entities": 20, "linked_after_adds": 0,
                "edited_linked_after_update": 10, "untouched_linked_after_update": 0,
                "team_b_linked": 0, "delta_edited": [0.05] * 10, "delta_untouched": [0.0] * 10}
        base.update(kw)
        return base

    def test_grade_all_hold(self):
        v = rl.grade(self._obs())
        self.assertEqual(v["status"], "graded")
        self.assertTrue(all(v[k] for k in ("P1", "P2", "P3", "P4")))

    def test_grade_gate(self):
        self.assertFalse(rl.grade(self._obs(spacy_loaded=False))["gate"])
        self.assertFalse(rl.grade(self._obs(queries_with_entities=14))["gate"])
        self.assertNotIn("P1", rl.grade(self._obs(spacy_loaded=False)))

    def test_grade_failures(self):
        self.assertFalse(rl.grade(self._obs(linked_after_adds=3))["P1"])
        self.assertFalse(rl.grade(self._obs(edited_linked_after_update=7))["P2"])
        self.assertFalse(rl.grade(self._obs(team_b_linked=1))["P2"])
        self.assertFalse(rl.grade(self._obs(delta_edited=[0.0] * 3 + [0.05] * 7))["P3"])
        self.assertFalse(rl.grade(self._obs(delta_edited=[0.05] * 9 + [None]))["P3"])
        self.assertFalse(rl.grade(self._obs(delta_untouched=[0.01] * 2 + [0.0] * 8))["P4"])
        self.assertTrue(rl.grade(self._obs(delta_untouched=[0.01] + [0.0] * 9))["P4"])


if __name__ == "__main__":
    unittest.main()
