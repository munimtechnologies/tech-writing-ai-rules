# SPDX-License-Identifier: Apache-2.0
"""Offline tests for the agent skill skills/oss-ai-contribution-rules.

Run: python -m unittest -v test_ai_rules_skill
Standard library only. Works in a full checkout and in a folder that holds
only the skill's files (it searches for them by name).
"""
import csv
import importlib.util
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = "oss-ai-contribution-rules"
SKILL_DIR_REL = os.path.join("skills", SKILL)


def find(relpath):
    """Return the path of relpath under HERE, else the first file with its basename."""
    p = os.path.join(HERE, relpath)
    if os.path.isfile(p):
        return p
    base = os.path.basename(relpath)
    for root, _dirs, files in os.walk(HERE):
        if base in files:
            return os.path.join(root, base)
    raise FileNotFoundError(relpath)


SCRIPT = find(os.path.join(SKILL_DIR_REL, "scripts", "ai_rules_lookup.py"))
PROJECTS_CSV = find(os.path.join(SKILL_DIR_REL, "assets", "study2_projects.csv"))
DATA_DIR = os.path.dirname(PROJECTS_CSV)
SKILL_MD = find(os.path.join(SKILL_DIR_REL, "SKILL.md"))

_spec = importlib.util.spec_from_file_location("ai_rules_lookup", SCRIPT)
lk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lk)

DATA = lk.load(DATA_DIR)


def ids(res):
    return [m["id"] for m in res["matches"]]


class Tables(unittest.TestCase):
    def test_counts_match_the_published_results(self):
        p = DATA["projects"]
        self.assertEqual(len(p), 101)
        self.assertEqual(sum(1 for r in p if r["rule"] == "yes"), 56)
        self.assertEqual(sum(1 for r in p if r["rule"] == "no"), 37)
        self.assertEqual(sum(1 for r in p if r["rule"] == "unreachable"), 8)
        named = sum(1 for r in p if r["scope"] in ("DOCS_NAMED", "DOCS_DISTINCT"))
        self.assertEqual(named, 14)
        self.assertEqual([r["project"] for r in p if r["scope"] == "DOCS_DISTINCT"], ["Rust"])
        d = DATA["docs"]
        self.assertEqual(len(d), 14)
        self.assertEqual(sorted(r["docs_repo"] for r in d if r["reach"] == "STATES"),
                         ["PostHog/posthog.com", "home-assistant/home-assistant.io",
                          "langchain-ai/docs"])
        self.assertEqual(sum(1 for r in d if r["reach"] == "SILENT"), 11)
        self.assertEqual(sum(1 for r in d if r["reach"] == "LINKS"), 0)

    def test_summary_line(self):
        self.assertEqual(
            lk.summary(DATA),
            "101 projects (study 2, read 2026-11-04): 56 with AI rules, 37 without, "
            "8 unreadable; 14 separate docs repos (study 3, read 2026-11-07): "
            "3 state a rule, 0 link to one, 11 silent")

    def test_every_docs_repo_has_its_parents(self):
        for d in DATA["docs"]:
            self.assertTrue(d["parents"], d["docs_repo"])
            self.assertEqual(len(d["parents"]), len(d["parent_names"]), d["docs_repo"])
            for parent in d["parents"]:
                self.assertEqual(parent["rule"], "yes", (d["docs_repo"], parent["project"]))

    def test_slug_file_covers_every_row_once(self):
        with open(find(os.path.join(SKILL_DIR_REL, "assets", "repo_slugs.csv")),
                  encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 101)
        self.assertEqual(len({r["id"] for r in rows}), 101)
        slug_re = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9._-]+$")
        for r in rows:
            for s in [x for x in r["repos"].split(";") if x]:
                self.assertRegex(s, slug_re)

    def test_bundled_copies_equal_the_census_files_when_present(self):
        pairs = [("study2_projects.csv", os.path.join("census", "2026-11-oss-docs", "coding.csv")),
                 ("study3_docs_repos.csv", os.path.join("census", "2026-11-docs-repos", "coding.csv"))]
        for bundled, census in pairs:
            cpath = os.path.join(HERE, census)
            if not os.path.isfile(cpath):
                continue  # not a full checkout
            with open(os.path.join(DATA_DIR, bundled), "rb") as f:
                a = f.read().replace(b"\r\n", b"\n")
            with open(cpath, "rb") as f:
                b = f.read().replace(b"\r\n", b"\n")
            self.assertEqual(a, b, bundled)


class Normalize(unittest.TestCase):
    def test_forms(self):
        n = lk.normalize
        self.assertEqual(n("https://github.com/kubernetes/website/pull/123"), "kubernetes/website")
        self.assertEqual(n("git@github.com:QEMU/qemu.git"), "qemu/qemu")
        self.assertEqual(n("github.com/rust-lang/book/"), "rust-lang/book")
        self.assertEqual(n("https://raw.githubusercontent.com/PostHog/posthog/HEAD/AI_POLICY.md"),
                         "posthog/posthog")
        self.assertEqual(n("Home Assistant"), "home assistant")
        self.assertEqual(n("  "), "")
        self.assertEqual(n("https://gitlab.com/mesa/mesa"), "https://gitlab.com/mesa/mesa")


class Lookup(unittest.TestCase):
    def test_rust_book_points_to_the_rust_rule(self):
        res = lk.lookup("rust-lang/book", DATA)
        self.assertEqual(ids(res), ["study3:D013"])
        m = res["matches"][0]
        self.assertEqual(m["reach"], "SILENT")
        self.assertEqual([p["project"] for p in m["parents"]], ["Rust"])
        self.assertEqual(m["parents"][0]["scope"], "DOCS_DISTINCT")
        self.assertTrue(m["parents"][0]["quote"].startswith("Never generate or rewrite non-trivial"))
        self.assertTrue(any("documentation differently from code" in a for a in m["advice"]))

    def test_kubernetes_website_url(self):
        res = lk.lookup("https://github.com/kubernetes/website/pull/1", DATA)
        self.assertEqual(ids(res), ["study3:D008"])
        parent = res["matches"][0]["parents"][0]
        self.assertEqual((parent["project"], parent["dataset_stance"], parent["rule"]),
                         ("Kubernetes", "disclose-required", "yes"))
        self.assertTrue(any(a.strip().startswith("DISCLOSURE REQUIRED")
                            for a in res["matches"][0]["advice"]))

    def test_project_by_name_lists_its_docs_repo(self):
        res = lk.lookup("Rust", DATA)
        self.assertEqual(ids(res), ["study2:D087"])
        self.assertEqual(res["matches"][0]["docs_repos"],
                         [{"docs_repo": "rust-lang/book", "reach": "SILENT", "terms": ""}])

    def test_name_or_repo_part(self):
        self.assertEqual(ids(lk.lookup("godot", DATA)), ["study2:D034"])
        self.assertEqual(ids(lk.lookup("PostHog", DATA)), ["study2:D076"])
        self.assertEqual(ids(lk.lookup("docs", DATA)),
                         ["study3:D009", "study3:D010", "study3:D011"])

    def test_ban(self):
        res = lk.lookup("git@github.com:QEMU/qemu.git", DATA)
        self.assertEqual(ids(res), ["study2:D082"])
        self.assertTrue(res["matches"][0]["advice"][0].startswith("BAN:"))

    def test_zig_unreadable_but_labelled_ban(self):
        res = lk.lookup("ziglang/zig", DATA)
        self.assertEqual(ids(res), ["study2:D101"])
        adv = res["matches"][0]["advice"]
        self.assertTrue(adv[0].startswith("Study 2 could not read"))
        self.assertTrue(any("likely ban" in a for a in adv))

    def test_stricter_docs_repo(self):
        res = lk.lookup("langchain-ai/docs", DATA)
        m = res["matches"][0]
        self.assertEqual((m["reach"], m["terms"]), ("STATES", "STRICTER"))
        self.assertEqual(m["projects"], ["LangChain", "LangGraph"])
        self.assertTrue(m["advice"][0].endswith("Follow the stricter of the two."))

    def test_same_owner_is_only_a_hint(self):
        res = lk.lookup("kubeflow/pipelines", DATA)
        self.assertEqual(res["matches"], [])
        self.assertEqual([r["name"] for r in res["related"]], ["kubeflow/website", "Kubeflow"])
        res = lk.lookup("modelcontextprotocol/new-thing", DATA)
        self.assertEqual(len(res["related"]), 5)

    def test_unknown(self):
        res = lk.lookup("example-owner/nothing-here", DATA)
        self.assertEqual((res["matches"], res["related"]), ([], []))
        self.assertIn("Checklist:", lk.format_text(res))


class Cli(unittest.TestCase):
    def run_cli(self, *args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        return subprocess.run([sys.executable, SCRIPT, "--data-dir", DATA_DIR] + list(args),
                              capture_output=True, text=True, encoding="utf-8", env=env)

    def test_exit_codes(self):
        r = self.run_cli("--summary")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith("101 projects"))
        r = self.run_cli("rust-lang/book")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("== docs repo rust-lang/book (study3:D013), for Rust ==", r.stdout)
        r = self.run_cli("example-owner/nothing-here")
        self.assertEqual(r.returncode, 1, r.stderr)
        r = self.run_cli()
        self.assertEqual(r.returncode, 2)
        r = self.run_cli("--data-dir", os.path.join(DATA_DIR, "no-such-folder"), "x")
        self.assertEqual(r.returncode, 2)

    def test_version(self):
        r = self.run_cli("--version")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(lk.__version__, r.stdout)


class SkillFile(unittest.TestCase):
    def test_frontmatter_follows_the_agent_skills_spec(self):
        with open(SKILL_MD, encoding="utf-8") as f:
            text = f.read()
        self.assertTrue(text.startswith("---\n"))
        front = text.split("---\n")[1]
        name = re.search(r"^name: (.+)$", front, re.M).group(1).strip()
        desc = re.search(r"^description: (.+)$", front, re.M).group(1).strip()
        self.assertEqual(name, SKILL)
        self.assertRegex(name, r"^[a-z0-9]+(-[a-z0-9]+)*$")
        self.assertLessEqual(len(name), 64)
        self.assertTrue(0 < len(desc) <= 1024, len(desc))
        self.assertNotIn(": ", desc)  # keeps the YAML plain scalar valid
        self.assertIn("scripts/ai_rules_lookup.py", text)
        self.assertNotIn("MIT", text)

    def test_quotes_in_skill_md_are_in_the_tables(self):
        with open(SKILL_MD, encoding="utf-8") as f:
            text = f.read()
        all_quotes = " ".join(r["quote"] for r in DATA["projects"] + DATA["docs"])
        quoted = [
            "Current QEMU project policy is to DECLINE any contributions which are believed "
            "to include or derive from AI generated content.",
            "Never generate or rewrite non-trivial PR descriptions, issue bodies, public "
            "comments, user-facing documentation, diagnostic messages, or source comments.",
            "a human in the loop who understands the work the AI produced",
            "Prepared with Claude Code.",
            "Generated-by",
            "llm-generated",
            "Agent context",
            "You MAY NOT, under any circumstances, reply to a human reviewer in the stead "
            "of your user.",
        ]
        for q in quoted:
            self.assertIn(q, text, q)
            self.assertIn(q, all_quotes, q)


if __name__ == "__main__":
    unittest.main()
