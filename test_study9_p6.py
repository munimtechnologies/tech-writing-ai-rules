"""Recount study 9's P6 (vendor statements on AI use in their docs) from the published reading notes.

    python -m unittest -v test_study9_p6

Checks that p6_notes.csv covers exactly the 20 pre-registered vendors, that every coded
statement or contributor rule has a link and a quote of at most 200 characters, and that the
P6 row and counts in RESULT.md equal what the notes give.

Standard library only. Made by MV2 of Munim, Inc., with AI agents working in his name. Apache-2.0.
"""
import csv
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.join(HERE, "census", "2026-11-vendor-docs-ai-labels")

# The 20 vendors of the pre-registration's frame, in its order.
VENDORS = [
    "Docker", "npm", "Amazon Web Services", "Google Cloud", "Cloudflare",
    "Terraform (HashiCorp)", "Firebase", "Ansible", "Chocolatey", "DigitalOcean",
    "Vercel", "Datadog", "Netlify", "Supabase", "Heroku",
    "Splunk", "New Relic", "Railway", "IBM Cloud", "Yandex Cloud",
]
P6_LIMIT = 3  # P6: at most 3 of 20 vendors publish a statement (inclusive)
YES_NO = ("yes", "no")


def read_notes():
    with open(os.path.join(STUDY, "p6_notes.csv"), newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def read_result():
    with open(os.path.join(STUDY, "RESULT.md"), encoding="utf-8-sig") as fh:
        return fh.read()


def p6_counts(rows):
    statements = [r for r in rows if r["statement"] == "yes"]
    return {
        "statements": len(statements),
        "strict": sum(1 for r in statements if r["where_kind"] in ("site", "blog")),
        "contributor_rules": sum(1 for r in rows if r["contributor_rule"] == "yes"),
        "docs_repos": sum(1 for r in rows if r["docs_repo"].strip()),
        "translation_notices": sum(1 for r in rows if r["ai_translation_notice"] == "yes"),
    }


class Study9P6(unittest.TestCase):
    def setUp(self):
        self.rows = read_notes()
        self.result = read_result()

    def test_frame(self):
        self.assertEqual([r["vendor"] for r in self.rows], VENDORS)

    def test_codes_and_quotes(self):
        for r in self.rows:
            v = r["vendor"]
            for col in ("statement", "contributor_rule", "ai_translation_notice"):
                self.assertIn(r[col], YES_NO, (v, col))
            if r["statement"] == "yes":
                self.assertTrue(r["statement_url"].startswith("https://"), v)
                self.assertTrue(0 < len(r["statement_quote"]) <= 200, v)
                self.assertIn(r["where_kind"], ("site", "blog", "repo"), v)
                found = set(r["found_by"].split(","))
                self.assertTrue(found and found <= {"a", "b", "c"}, v)
            else:
                self.assertEqual((r["where_kind"], r["statement_url"], r["statement_quote"], r["found_by"]),
                                 ("", "", "", ""), v)
            if r["contributor_rule"] == "yes":
                self.assertTrue(r["contributor_rule_url"].startswith("https://"), v)
                self.assertTrue(0 < len(r["contributor_rule_quote"]) <= 200, v)
                self.assertTrue(r["docs_repo"].strip(), v)
            else:
                self.assertEqual((r["contributor_rule_url"], r["contributor_rule_quote"]), ("", ""), v)
            if "c" in r["found_by"].split(","):
                self.assertTrue(r["docs_repo"].strip(), v)
            self.assertNotIn("@", "".join(r.values()), v)  # no e-mail addresses or handles

    def test_counts(self):
        self.assertEqual(p6_counts(self.rows), {
            "statements": 4, "strict": 3, "contributor_rules": 5,
            "docs_repos": 11, "translation_notices": 1,
        })

    def test_result_p6_row(self):
        n = p6_counts(self.rows)["statements"]
        verdict = "held" if n <= P6_LIMIT else "failed"
        rows = [line for line in self.result.splitlines() if line.startswith("| P6 |")]
        self.assertEqual(len(rows), 1)
        self.assertIn("| %d of 20 |" % n, rows[0])
        self.assertIn("**%s**" % verdict, rows[0])
        self.assertIn("**%d of 20 vendors publish a statement**" % n, self.result)

    def test_result_lists_each_statement(self):
        for r in self.rows:
            if r["statement"] == "yes":
                self.assertIn(r["statement_url"], self.result, r["vendor"])
                self.assertIn(r["statement_quote"], self.result, r["vendor"])


if __name__ == "__main__":
    unittest.main()
