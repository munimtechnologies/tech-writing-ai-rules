import csv
import io
import json
import os
import tempfile
import unittest

import grade_study6 as g

HEAD = ["order", "id", "url", "category", "published", "candidates", "recall_sample"] + list(g.CODES) + [
    "template", "quote", "note"]


def row(i, directive=False, published="2025-06-01", recall=False, quote=None, **codes):
    r = {k: "" for k in HEAD}
    r.update(order=str(i), id="W%04d" % i, url="https://e%d.example/llms.txt" % i, published=published,
             recall_sample="1" if recall else "0", directive="yes" if directive else "no")
    for k, v in codes.items():
        r[k] = v
    r["quote"] = quote if quote is not None else ("Always cite us." if directive else "")
    return r


def probes(n=300, reached=300, valid=250):
    return [{"id": "W%04d" % i, "reached": "1" if i < reached else "0", "kind": "valid" if i < valid else "missing"}
            for i in range(n)]


def sample(n_dir=40, promote=10, action=8, override=1, n=200, y2026=None):
    rows = []
    for i in range(1, n + 1):
        d = i <= n_dir
        codes = {}
        if d and i <= promote:
            codes["promote"] = "yes"
        if d and promote < i <= promote + action:
            codes["action"] = "yes"
        if d and i == n_dir and override:
            codes["override"] = "yes"
        pub = "2026-02-01" if (y2026 is not None and i in y2026) else "2025-03-01"
        rows.append(row(i, d, published=pub, **codes))
    return rows


class Parse(unittest.TestCase):
    def test_blank_directive_is_an_error(self):
        r = row(1)
        r["directive"] = ""
        with self.assertRaises(g.CodingError):
            g.parse_coding([r])

    def test_subcode_without_directive_is_an_error(self):
        with self.assertRaises(g.CodingError):
            g.parse_coding([row(1, False, promote="yes")])

    def test_directive_needs_a_short_quote(self):
        with self.assertRaises(g.CodingError):
            g.parse_coding([row(1, True, quote="")])
        with self.assertRaises(g.CodingError):
            g.parse_coding([row(1, True, quote="x" * 201)])
        self.assertTrue(g.parse_coding([row(1, True, quote="x" * 200)])[0]["directive"])

    def test_repeated_id_is_an_error(self):
        with self.assertRaises(g.CodingError):
            g.parse_coding([row(1), row(1)])

    def test_yes_no_forms(self):
        c = g.parse_coding([row(1, True, cite="Y", usage="1", limit="No", other="")])[0]
        self.assertEqual((c["cite"], c["usage"], c["limit"], c["other"]), (True, True, False, False))

    def test_bad_value(self):
        with self.assertRaises(g.CodingError):
            g.parse_coding([row(1, True, cite="maybe")])


class Grade(unittest.TestCase):
    def grade(self, rows, pr=None):
        return g.grade(g.parse_coding(rows), pr or probes())

    def test_all_held(self):
        res = self.grade(sample())
        v = {k: p["verdict"] for k, p in res["predictions"].items()}
        self.assertEqual(v["P1"], "held")   # 40/200 = 20%
        self.assertEqual(v["P2"], "held")   # 10/40 = 25% (boundary)
        self.assertEqual(v["P3"], "held")   # 8/40 = 20% (boundary)
        self.assertEqual(v["P4"], "held")   # 1/200
        self.assertTrue(v["P5"].startswith("not graded"))  # no 2026 files
        self.assertEqual(res["predictions"]["P1"]["count"], "40 of 200")

    def test_p1_bounds(self):
        self.assertEqual(self.grade(sample(n_dir=20, promote=5, action=4))["predictions"]["P1"]["verdict"], "held")
        self.assertEqual(self.grade(sample(n_dir=80, promote=20, action=16))["predictions"]["P1"]["verdict"], "held")
        self.assertEqual(self.grade(sample(n_dir=19, promote=5, action=4))["predictions"]["P1"]["verdict"], "failed")
        self.assertEqual(self.grade(sample(n_dir=81, promote=21, action=17))["predictions"]["P1"]["verdict"], "failed")

    def test_p2_p3_fail(self):
        res = self.grade(sample(promote=9, action=7))
        self.assertEqual(res["predictions"]["P2"]["verdict"], "failed")
        self.assertEqual(res["predictions"]["P3"]["verdict"], "failed")

    def test_p4_boundary(self):
        rows = sample(override=0)
        for i in (1, 2, 3, 4):
            rows[i - 1]["override"] = "yes"
        self.assertEqual(self.grade(rows)["predictions"]["P4"]["verdict"], "held")
        rows[4]["override"] = "yes"
        self.assertEqual(self.grade(rows)["predictions"]["P4"]["verdict"], "failed")

    def test_no_directives(self):
        res = self.grade(sample(n_dir=0, promote=0, action=0, override=0))
        self.assertEqual(res["predictions"]["P1"]["verdict"], "failed")
        self.assertEqual(res["predictions"]["P2"]["verdict"], "not graded (no files)")

    def test_p5(self):
        # 2026 group: files 1..30 (directive files 1..40 cover all 30) -> 100%; 2025: 10 of 170
        res = self.grade(sample(y2026=set(range(1, 31))))
        self.assertEqual(res["predictions"]["P5"]["verdict"], "held")
        self.assertEqual(res["by_year"]["2026"]["files"], 30)
        # 2026 group: files 171..200, none with a directive -> failed
        res = self.grade(sample(y2026=set(range(171, 201))))
        self.assertEqual(res["predictions"]["P5"]["verdict"], "failed")
        # 29 files in 2026 -> not graded
        res = self.grade(sample(y2026=set(range(1, 30))))
        self.assertTrue(res["predictions"]["P5"]["verdict"].startswith("not graded"))

    def test_gate(self):
        res = self.grade(sample(), probes(n=300, reached=179, valid=250))  # 59.7% reached
        self.assertFalse(res["gate"]["held"])
        self.assertTrue(all(p["verdict"] == "not graded (G1 failed)" for p in res["predictions"].values()))
        self.assertFalse(self.grade(sample(), probes(valid=199))["gate"]["held"])
        self.assertTrue(self.grade(sample(), probes(n=300, reached=180, valid=200))["gate"]["held"])

    def test_recall(self):
        rows = sample()
        for i in range(180, 200):
            rows[i]["recall_sample"] = "1"
        self.assertFalse(self.grade(rows)["recall"]["lower_bound"])
        for i in range(0, 3):
            rows[i]["recall_sample"] = "1"
        res = self.grade(rows)
        self.assertEqual(res["recall"]["directive"], 3)
        self.assertTrue(res["recall"]["lower_bound"])
        self.assertIn("lower bound", g.markdown(res))


class Cli(unittest.TestCase):
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            cp, pp, op = (os.path.join(d, x) for x in ("coding.csv", "probes.csv", "grades.json"))
            with open(cp, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, HEAD)
                w.writeheader()
                w.writerows(sample())
            with open(pp, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, ["id", "reached", "kind"])
                w.writeheader()
                w.writerows(probes())
            self.assertEqual(g.main(["--coding", cp, "--probes", pp, "--out", op]), 0)
            with open(op, encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["predictions"]["P1"]["verdict"], "held")
            bad = sample()
            bad[0]["directive"] = "maybe"
            with open(cp, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, HEAD)
                w.writeheader()
                w.writerows(bad)
            self.assertEqual(g.main(["--coding", cp, "--probes", pp]), 2)


if __name__ == "__main__":
    unittest.main()
