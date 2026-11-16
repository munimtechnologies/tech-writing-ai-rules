# SPDX-License-Identifier: Apache-2.0
"""Recompute study 15's verdicts from the published files.

Study 15 (census/2026-11-nuxt-raw/) counts empty component tags in Nuxt
Content /raw/ copies. This test reads the unchanged output of the graded run
(run-v2/: nuxtraw 0.2.0) and the hand check (hand_check.csv) and checks:

- the tool's own grade (G1, P1-P5) as pre-registered;
- the grade after the hand check, which found two flagged copies whose only
  "empty tag" was code inside a blockquoted callout (a tool error);
- that the hand check covers exactly the pre-registered sample rows;
- the decoration rule, the bare-only sensitivity count and the exploratory
  content-negotiation counts quoted in RESULT.md.

Run: python -m unittest -v test_study15_result

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his
name. Code Apache-2.0, data CC BY 4.0.
"""
import csv
import os
import statistics
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "census", "2026-11-nuxt-raw")
RUN = os.path.join(D, "run-v2")


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def yes(v):
    return str(v) in ("True", "true", "1")


def grade(sites, pages, flagged):
    """flagged(row) -> bool. Same rules as nuxtraw.grade."""
    counted = [s["key"] for s in sites if yes(s["counted"])]
    read = [p for p in pages if yes(p["read"]) and p["key"] in counted]
    by = {k: [p for p in read if p["key"] == k] for k in counted}
    share = {k: sum(1 for p in v if flagged(p)) / len(v) for k, v in by.items()}
    pooled = sum(1 for p in read if flagged(p)) / len(read)
    re_ = [float(p["ratio"]) for p in read if flagged(p) and p["ratio"] != ""]
    rn = [float(p["ratio"]) for p in read if not flagged(p) and p["ratio"] != ""]
    med = {k: statistics.median([float(p["ratio"]) for p in v if p["ratio"] != ""]) for k, v in by.items()}
    return {
        "counted": len(counted), "read": len(read), "G1": len(counted) >= 4,
        "n_flagged": sum(1 for p in read if flagged(p)),
        "share": share, "pooled": pooled, "med_e": statistics.median(re_), "med_n": statistics.median(rn),
        "site_med": med,
        "P1": sum(1 for v in share.values() if v > 0) * 2 >= len(counted),
        "P2": pooled >= 0.15,
        "P3": sum(1 for k, v in share.items() if v >= 0.10 and not k.startswith("directus.com")) >= 2,
        "P4": statistics.median(re_) < statistics.median(rn),
        "P5": all(v >= 0.5 for v in med.values()),
    }


class Study15(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sites = read_csv(os.path.join(RUN, "sites.csv"))
        cls.pages = read_csv(os.path.join(RUN, "pages.csv"))
        cls.sample = read_csv(os.path.join(RUN, "hand_check_sample.csv"))
        cls.hand = read_csv(os.path.join(D, "hand_check.csv"))
        with open(os.path.join(D, "RESULT.md"), encoding="utf-8") as f:
            cls.result = f.read()
        cls.tool_errors = {h["raw_url"] for h in cls.hand if h["category"] == "tool-error-blockquote-fence"}

    def auto(self, p):
        return int(p["empty_tags"]) > 0

    def corrected(self, p):
        return int(p["empty_tags"]) > 0 and p["raw_url"] not in self.tool_errors

    def test_tool_grade(self):
        g = grade(self.sites, self.pages, self.auto)
        self.assertTrue(g["G1"])
        self.assertEqual((g["counted"], g["read"], g["n_flagged"]), (7, 193, 24))
        self.assertEqual(round(g["pooled"], 3), 0.124)
        self.assertEqual((g["P1"], g["P2"], g["P3"], g["P4"], g["P5"]), (True, False, True, False, True))
        self.assertEqual(round(g["med_e"], 3), 1.034)
        self.assertEqual(round(g["med_n"], 3), 1.029)

    def test_corrected_grade(self):
        self.assertEqual(len(self.tool_errors), 2)
        g = grade(self.sites, self.pages, self.corrected)
        self.assertEqual(g["n_flagged"], 22)
        self.assertAlmostEqual(g["pooled"], 22 / 193)
        self.assertEqual(sum(1 for v in g["share"].values() if v > 0), 5)
        self.assertEqual(g["share"]["nuxt.com"], 0)
        self.assertEqual(g["share"]["ui.nuxt.com"], 0)
        self.assertEqual((g["P1"], g["P2"], g["P3"], g["P4"], g["P5"]), (True, False, True, False, True))
        self.assertAlmostEqual(g["med_e"], 1.0405, places=6)
        self.assertAlmostEqual(g["med_n"], 1.0275, places=6)
        self.assertEqual(round(min(g["site_med"].values()), 3), 0.781)
        per_site = {k: round(v * (13 if k == "supabase.nuxtjs.org" else 30)) for k, v in g["share"].items()}
        self.assertEqual(per_site, {"content.nuxt.com": 7, "directus.com/docs": 7, "docus.dev": 6,
                                    "supabase.nuxtjs.org": 1, "i18n.nuxtjs.org": 1,
                                    "nuxt.com": 0, "ui.nuxt.com": 0})

    def test_hand_check_covers_the_sample(self):
        self.assertEqual({r["raw_url"] for r in self.sample}, {h["raw_url"] for h in self.hand})
        flagged = [h for h in self.hand if h["auto_flag"] == "empty"]
        clean = [h for h in self.hand if h["auto_flag"] == "clean"]
        self.assertEqual((len(flagged), len(clean)), (10, 7))
        auto = {r["raw_url"]: int(r["empty_tags"]) > 0 for r in self.sample}
        for h in self.hand:
            self.assertEqual(auto[h["raw_url"]], h["auto_flag"] == "empty", h["raw_url"])
        self.assertTrue(all(h["category"] == "clean" for h in clean))

    def test_hand_check_categories(self):
        cats = {}
        for h in self.hand:
            if h["auto_flag"] == "empty":
                cats[h["category"]] = cats.get(h["category"], 0) + 1
        self.assertEqual(cats, {"tool-error-blockquote-fence": 2, "text-in-attributes": 5,
                                "decoration": 1, "content-missing": 2})
        missing = [h for h in self.hand if h["shown_on_page_missing_from_copy"] == "yes"]
        self.assertEqual({h["site"] for h in missing}, {"directus.com/docs"})
        # decoration rule: recount on bare tags only if more than 1 in 5 checked copies are decoration
        self.assertFalse(cats["decoration"] * 5 > 10)

    def test_bare_only_sensitivity(self):
        bare = lambda p: int(p["empty_bare"] or 0) > 0 and p["raw_url"] not in self.tool_errors
        g = grade(self.sites, self.pages, bare)
        self.assertEqual(g["n_flagged"], 11)
        self.assertEqual(sum(1 for v in g["share"].values() if v > 0), 3)
        self.assertFalse(g["P1"])
        self.assertFalse(g["P3"])

    def test_negotiation(self):
        read = [p for p in self.pages if yes(p["read"])]
        self.assertEqual(sum(1 for p in read if yes(p["page_is_html"])), 192)
        self.assertEqual(sum(1 for p in read if yes(p["neg_is_md"])), 163)
        self.assertEqual(sum(1 for p in read if yes(p["neg_same_as_raw"])), 133)
        d = [p for p in read if p["key"] == "directus.com/docs"]
        self.assertEqual((sum(1 for p in d if yes(p["neg_is_md"])), sum(1 for p in d if yes(p["neg_same_as_raw"]))),
                         (30, 0))
        self.assertEqual(sum(1 for p in read if p["key"] == "i18n.nuxtjs.org" and yes(p["neg_is_md"])), 0)

    def test_result_quotes_these_numbers(self):
        for s in ("22 of 193", "11.4%", "24/193 = 12.4%", "1.0405 vs 1.0275", "0.781",
                  "11/193 copies (5.7%)", "163 of 193", "133 copies", "1 in 10"):
            self.assertIn(s, self.result)


if __name__ == "__main__":
    unittest.main()
