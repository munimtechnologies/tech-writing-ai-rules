# SPDX-License-Identifier: Apache-2.0
"""Recompute study 10's gates and predictions from the published files.

Study 10 (census/2026-11-md-copy-parity/) asks whether the Markdown copies docs
sites serve to AI agents keep what the page shows people. This test reads the
tool's unchanged pages.csv, sites.csv, missing.csv and mdparity.json plus the
hand check (hand_check.csv) and checks:

- the gates and P1, P2, P5 and P6 on the tool's numbers, as pre-registered;
- P3 and P4 on the hand-checked counts (every missing callout was read);
- that the hand check covers exactly the pre-registered rows: every missing
  callout, and the first 10 missing prose blocks of the two counted pages with
  the lowest coverage on each site;
- the descriptive figures quoted in RESULT.md.

Run: python -m unittest -v test_study10_result

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his
name. Code Apache-2.0, data CC BY 4.0.
"""
import csv
import json
import os
import statistics
import unittest
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "census", "2026-11-md-copy-parity")

# Page-template text the hand check coded as chrome on the two hand-checked
# pages of these sites, and that recurs on every page of the site.
CHROME = {
    "aws": ("Thanks for letting us know", "got a moment, please tell us"),
    "mslearn": ("Access to this page requires authorization",
                "Want to try using Ask Learn"),
    "gcloud": ("Develop with our latest Generative AI models and tools",
               "Get free usage of 20+ popular products",
               "Access 20+ free products for common use cases"),
}


def read_csv(name):
    with open(os.path.join(D, name), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def is_true(value):
    return str(value).strip().lower() == "true"


def is_chrome(row):
    marks = CHROME.get(row["site"], ())
    return row["kind"] == "prose" and any(m in row["text"] for m in marks)


class Study10Result(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = read_csv("pages.csv")
        cls.sites = {r["site"]: r for r in read_csv("sites.csv")}
        cls.missing = read_csv("missing.csv")
        cls.hand_rows = read_csv("hand_check.csv")
        with open(os.path.join(D, "mdparity.json"), encoding="utf-8") as f:
            cls.auto = json.load(f)
        with open(os.path.join(D, "RESULT.md"), encoding="utf-8") as f:
            cls.result = f.read()
        cls.counted = [p for p in cls.pages if is_true(p["counted"])]
        cls.counted_urls = {p["url"] for p in cls.counted}
        cls.cmissing = [m for m in cls.missing if m["url"] in cls.counted_urls]
        cls.per_site = defaultdict(list)
        for p in cls.counted:
            cls.per_site[p["site"]].append(p)

    def total(self, field, site=None):
        rows = self.per_site[site] if site else self.counted
        return sum(int(p[field]) for p in rows)

    # ---- frame and gates -------------------------------------------------
    def test_frame_and_gates(self):
        self.assertEqual(len(self.pages), 425)
        self.assertEqual(len(self.counted), 384)
        big = sorted(s for s, rows in self.per_site.items() if len(rows) >= 15)
        self.assertEqual(len(big), 14)
        self.assertNotIn("supabase", big)
        self.assertTrue(len(big) >= 10 and len(self.counted) >= 250)  # G1
        callouts = self.total("callout")
        with_callouts = [s for s in self.per_site if self.total("callout", s) > 0]
        self.assertEqual(callouts, 410)
        self.assertEqual(len(with_callouts), 14)
        self.assertTrue(callouts >= 40 and len(with_callouts) >= 5)  # G2
        g = self.auto["summary"]["gates"]
        self.assertTrue(g["G1"]["passed"] and g["G2"]["passed"])
        self.assertEqual(g["G1"]["counted"], 384)
        self.assertEqual(g["G2"]["callouts"], 410)

    def test_sites_csv_matches_pages(self):
        for site, rows in self.per_site.items():
            s = self.sites[site]
            self.assertEqual(int(s["counted"]), len(rows), site)
            for field in ("prose", "prose_present", "heading", "heading_present",
                          "code", "code_present", "callout", "callout_present"):
                self.assertEqual(int(s[field]), self.total(field, site), (site, field))

    # ---- P1 and P2: tool's numbers ----------------------------------------
    def test_p1_median_coverage(self):
        med = statistics.median(float(p["coverage"]) for p in self.counted)
        self.assertEqual(med, 1.0)
        self.assertTrue(med >= 0.90)  # P1 held
        self.assertTrue(self.auto["summary"]["predictions"]["P1"]["held"])

    def test_p2_sites_below_80(self):
        low = []
        for site, rows in self.per_site.items():
            if len(rows) < 15:
                continue
            med = statistics.median(float(p["coverage"]) for p in rows)
            self.assertAlmostEqual(med, float(self.sites[site]["median_coverage"]),
                                   places=3, msg=site)
            if med < 0.80:
                low.append(site)
        self.assertEqual(low, ["aws"])
        self.assertFalse(len(low) >= 2)  # P2 failed
        self.assertFalse(self.auto["summary"]["predictions"]["P2"]["held"])

    # ---- hand check of callouts; P3 and P4 ---------------------------------
    def hand(self, part):
        return [h for h in self.hand_rows if h["part"] == part]

    def test_hand_check_covers_every_missing_callout(self):
        pool = [m for m in self.cmissing if m["kind"] == "callout"]
        self.assertEqual(len(pool), 17)
        self.assertEqual(len(pool), self.total("callout") - self.total("callout_present"))
        hand = self.hand("callout")
        self.assertEqual(len(hand), 17)
        for h in hand:
            for i, m in enumerate(pool):
                if (m["url"] == h["url"] and m["kind"] == h["kind"]
                        and m["group"] == h["group"] and m["text"].startswith(h["text"])):
                    pool.pop(i)
                    break
            else:
                self.fail("hand row not in missing.csv: %r" % (h["text"],))
        self.assertEqual(pool, [])

    def test_codes_are_known(self):
        for h in self.hand_rows:
            self.assertIn(h["code"], ("lost", "variant", "chrome"), h)
            self.assertTrue(h["note"].strip(), h)

    def test_p3_hand_checked(self):
        hand = self.hand("callout")
        codes = Counter(h["code"] for h in hand)
        self.assertEqual(codes, Counter({"lost": 7, "variant": 9, "chrome": 1}))
        k = codes["lost"]
        n = self.total("callout") - codes["chrome"]
        self.assertEqual((k, n), (7, 409))
        self.assertFalse(k / n >= 0.05)  # P3 failed
        # the tool's count also fails: 17 of 410
        self.assertFalse(17 / 410 >= 0.05)
        warn = [h for h in hand if h["group"] == "warning"]
        self.assertEqual(Counter(h["code"] for h in warn),
                         Counter({"variant": 4, "lost": 1}))
        self.assertEqual(self.total("warn"), 92)

    def test_p4_hand_checked(self):
        hand = self.hand("callout")
        lost = Counter(h["site"] for h in hand if h["code"] == "lost")
        chrome = Counter(h["site"] for h in hand if h["code"] == "chrome")
        hit = []
        for site in self.per_site:
            n = self.total("callout", site) - chrome[site]
            if n >= 5 and lost[site] / n >= 0.25:
                hit.append(site)
        self.assertEqual(hit, [])  # P4 failed on the hand-checked counts
        self.assertEqual(dict(lost), {"gcloud": 4, "netlify": 1, "heroku": 1, "railway": 1})
        # the tool's count would have passed P4 through Firebase (2 of 5)
        self.assertEqual(self.auto["summary"]["predictions"]["P4"]["sites"], ["firebase"])
        self.assertEqual(lost["firebase"], 0)

    # ---- P5 and P6: tool's numbers ----------------------------------------
    def test_p5_code(self):
        k, n = self.total("code_present"), self.total("code")
        self.assertEqual((k, n), (1697, 1869))
        self.assertFalse(k / n >= 0.95)  # P5 failed
        dk = self.total("code_present", "datadog")
        dn = self.total("code", "datadog")
        self.assertEqual((dk, dn), (169, 320))
        self.assertEqual(round((k - dk) / (n - dn), 3), 0.986)
        dd = [m for m in self.cmissing if m["site"] == "datadog" and m["kind"] == "code"]
        self.assertEqual(len(dd), 151)
        region = [m for m in dd if "DD_SITE=" in m["text"]]
        self.assertEqual(len(region), 104)

    def test_p6_headings(self):
        k, n = self.total("heading_present"), self.total("heading")
        self.assertEqual((k, n), (3500, 3624))
        self.assertTrue(k / n >= 0.95)  # P6 held

    # ---- hand check of prose (reported next to P1 and P2) -------------------
    def test_prose_hand_check_rows(self):
        expected = set()
        for site, rows in self.per_site.items():
            low = [(float(p["coverage"]), i, p["url"]) for i, p in enumerate(rows)
                   if float(p["coverage"]) < 1.0]
            for _, _, url in sorted(low)[:2]:
                expected.add(url)
        hand = self.hand("prose")
        self.assertEqual({h["url"] for h in hand}, expected)
        self.assertEqual(len(expected), 25)
        for url in expected:
            miss = [m for m in self.cmissing if m["url"] == url and m["kind"] == "prose"]
            mine = [h for h in hand if h["url"] == url]
            self.assertEqual(len(mine), min(10, len(miss)), url)
            for h, m in zip(mine, miss):
                self.assertTrue(m["text"].startswith(h["text"]), (url, h["text"]))
        self.assertEqual(len(hand), 89)
        self.assertEqual(Counter(h["code"] for h in hand),
                         Counter({"variant": 45, "lost": 22, "chrome": 22}))

    def test_chrome_adjusted_figures(self):
        chrome = Counter(m["site"] for m in self.cmissing if is_chrome(m))
        self.assertEqual(dict(chrome), {"aws": 112, "mslearn": 90, "gcloud": 27})
        per_url = Counter(m["url"] for m in self.cmissing if is_chrome(m))
        miss_url = Counter(m["url"] for m in self.cmissing if m["kind"] == "prose")
        # AWS: the feedback widget's four lines on every page
        aws = self.per_site["aws"]
        adj = [int(p["prose_present"]) / (int(p["prose"]) - per_url[p["url"]]) for p in aws]
        self.assertEqual(statistics.median(adj), 1.0)
        self.assertEqual(sum(1 for p in aws if miss_url[p["url"]] == per_url[p["url"]] == 4), 26)
        learn = self.per_site["mslearn"]
        self.assertEqual(sum(1 for p in learn if miss_url[p["url"]] == per_url[p["url"]] == 3), 18)
        k = self.total("prose_present")
        n = self.total("prose") - sum(chrome.values())
        self.assertEqual(round(k / n, 3), 0.975)
        self.assertEqual(round(k / self.total("prose"), 3), 0.955)
        a = self.sites["aws"]
        self.assertEqual(round(int(a["prose_present"]) / (int(a["prose"]) - 112), 3), 0.993)
        m = self.sites["mslearn"]
        self.assertEqual(round(int(m["prose_present"]) / (int(m["prose"]) - 90), 3), 0.967)

    # ---- RESULT.md --------------------------------------------------------
    def test_result_md(self):
        r = self.result
        for text in ("| P1 | The median page coverage is at least 90%. | 100% | **held** |",
                     "| P2 |", "| P3 |", "| P4 |", "| P5 |", "| P6 |",
                     "7 of 409", "1 of 92", "1,697 of 1,869", "3,500 of 3,624",
                     "2 of 6 predictions held", "22 of 89", "45 of 89"):
            self.assertIn(text, r)
        rows = {line.split("|")[1].strip(): line for line in r.splitlines()
                if line.startswith("| P") and line.count("|") >= 5}
        self.assertIn("**held**", rows["P1"])
        self.assertIn("**failed**", rows["P2"])
        self.assertIn("**failed**", rows["P3"])
        self.assertIn("**failed**", rows["P4"])
        self.assertIn("**failed**", rows["P5"])
        self.assertIn("**held**", rows["P6"])


if __name__ == "__main__":
    unittest.main()
