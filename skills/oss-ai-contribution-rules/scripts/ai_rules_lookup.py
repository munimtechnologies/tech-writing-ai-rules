#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Look up what an open-source project's AI contribution rule said, and whether
its separate documentation repo repeats it.

Part of the agent skill ``oss-ai-contribution-rules`` in
https://github.com/munimtechnologies/tech-writing-ai-rules (code Apache-2.0,
data CC BY 4.0). Made by MV2 of Munim, Inc., with AI agents working in his name.

The data is a dated snapshot: study 2 of that repository (101 projects of the
awesome-ai-contribution-policies dataset, own texts read 2026-11-04) and study 3
(14 separate docs repos, read 2026-11-07). Rules change. The live files always
win over this table.

Usage:
  python ai_rules_lookup.py rust-lang/book
  python ai_rules_lookup.py https://github.com/kubernetes/website/pull/1
  python ai_rules_lookup.py "Home Assistant" --json
  python ai_rules_lookup.py --summary

Exit codes: 0 = at least one row matched; 1 = no row matched (related rows in
the same GitHub owner may still be printed); 2 = usage or data error.
Python standard library only.
"""
import argparse
import csv
import json
import os
import re
import sys

__version__ = "0.1.0"

STUDY2_READ = "2026-11-04"
STUDY3_READ = "2026-11-07"
REPO_URL = "https://github.com/munimtechnologies/tech-writing-ai-rules"
STUDY2_RESULT = REPO_URL + "/blob/main/census/2026-11-oss-docs/RESULT.md"
STUDY3_RESULT = REPO_URL + "/blob/main/census/2026-11-docs-repos/RESULT.md"

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_DIR = os.path.normpath(os.path.join(HERE, "..", "assets"))
FILES = {
    "projects": "study2_projects.csv",
    "docs": "study3_docs_repos.csv",
    "slugs": "repo_slugs.csv",
}

LIVE_FILES = (
    "AI_POLICY.md, CONTRIBUTING.md (also in .github/ and docs/), AGENTS.md, "
    "CLAUDE.md, the pull request template(s), and any contributor or AI-policy "
    "page on the project's website"
)

CHECKLIST = [
    "Find the parent project if this repo holds docs, a website, a book or a wiki "
    "(README, GitHub owner, site footer). Rules usually live in the main repo.",
    "Read the live files of BOTH repos: " + LIVE_FILES + ". Search them for: AI, "
    "LLM, generative, generated, agent, Copilot, ChatGPT, Claude, disclose.",
    "If any rule bans or declines AI-made contributions, stop and tell the user. "
    "Do not prepare the change with AI and do not hide AI use.",
    "If a rule limits AI use (for example, no agent-written user-facing docs, or a "
    "human in the loop), stay inside the limit and say so to the user.",
    "If a rule asks for disclosure, disclose where it asks (template field, label, "
    "section), naming the tool and what it did.",
    "If two rules differ (docs repo and main repo), follow the stricter one.",
    "If nothing is said anywhere, silence is not permission to hide AI use: say "
    "plainly in the PR description that AI was used and how, and let the user "
    "review the change before it is opened.",
]


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load(data_dir=None):
    """Load the three bundled tables and link them together."""
    d = data_dir or DEFAULT_DATA_DIR
    paths = {k: os.path.join(d, v) for k, v in FILES.items()}
    missing = [p for p in paths.values() if not os.path.isfile(p)]
    if missing:
        raise FileNotFoundError("missing data file(s): " + ", ".join(missing))
    projects = read_csv(paths["projects"])
    docs = read_csv(paths["docs"])
    slugs = read_csv(paths["slugs"])
    by_id = {r["id"]: r for r in projects}
    if len(by_id) != len(projects):
        raise ValueError("duplicate id in " + FILES["projects"])
    repos = {}
    for s in slugs:
        row = by_id.get(s["id"])
        if row is None:
            raise ValueError("repo_slugs.csv id %s is not in %s" % (s["id"], FILES["projects"]))
        if s["project"] != row["project"]:
            raise ValueError("repo_slugs.csv name mismatch for %s: %r vs %r"
                             % (s["id"], s["project"], row["project"]))
        repos[s["id"]] = [x.strip() for x in s["repos"].split(";") if x.strip()]
    by_name = {}
    for r in projects:
        r["repos"] = repos.get(r["id"], [])
        r["docs_repos"] = []
        by_name[r["project"].lower()] = r
    for d_ in docs:
        names = [n.strip() for n in d_["projects"].split(",") if n.strip()]
        d_["parent_names"] = names
        d_["parents"] = [by_name[n.lower()] for n in names if n.lower() in by_name]
        for p in d_["parents"]:
            p["docs_repos"].append(d_)
    return {"projects": projects, "docs": docs}


_GH = re.compile(
    r"^(?:git\+)?(?:https?://)?(?:www\.)?(?:raw\.githubusercontent\.com|github\.com)[/:]",
    re.I)


def normalize(query):
    """Turn a GitHub URL, an SSH remote, an owner/repo slug or a name into a key.

    Slugs come back as lower-case 'owner/repo'; names come back lower-case.
    """
    s = (query or "").strip()
    if not s:
        return ""
    s = re.sub(r"^git@github\.com:", "", s, flags=re.I)
    is_url = bool(_GH.match(s))
    if not is_url and re.match(r"^[a-z][a-z0-9+.-]*://", s, flags=re.I):
        # A URL on another host (GitLab, a website): the table only knows GitHub slugs.
        return s.lower()
    s = _GH.sub("", s)
    s = s.split("#")[0].split("?")[0].strip().strip("/")
    if "/" in s and (is_url or " " not in s):
        parts = [p for p in s.split("/") if p]
        if len(parts) >= 2:
            repo = parts[1]
            if repo.lower().endswith(".git"):
                repo = repo[:-4]
            return (parts[0] + "/" + repo).lower()
    if s.lower().endswith(".git"):
        s = s[:-4]
    return s.lower()


def _owner(slug):
    return slug.split("/")[0].lower() if "/" in slug else ""


def _repo_part(slug):
    return slug.split("/")[1].lower() if "/" in slug else ""


def project_advice(p):
    a = []
    rule, stance, scope = p["rule"], p["stance"], p["scope"]
    if rule == "unreachable":
        a.append("Study 2 could not read this project's own texts, so the table has no "
                 "reading of its rule. Read the live files.")
        if stance == "ban":
            a.append("The source dataset labels it 'ban' (not confirmed from its own text "
                     "here). Treat that as a likely ban until the live rule says otherwise.")
    elif rule == "no":
        a.append("Study 2 found no terms for AI-made contributions in this project's own "
                 "files. That is not permission: read the live files, and if you go ahead, "
                 "say plainly that AI was used.")
    else:
        if stance == "ban":
            a.append("BAN: the source dataset labels this project 'ban'. Do not prepare an "
                     "AI-made contribution for it unless the live rule clearly allows your "
                     "case. Tell the user what the rule says.")
        elif stance == "restricted":
            a.append("RESTRICTED: AI help is allowed only within limits. Read the rule and "
                     "stay inside them.")
        elif stance == "disclose-required":
            a.append("DISCLOSURE REQUIRED: disclose in the place the project asks (PR "
                     "template field, label or section), naming the tool and what it did.")
        if scope == "DOCS_DISTINCT":
            a.append("This rule treats documentation differently from code. Read it before "
                     "you touch any docs.")
        elif scope == "DOCS_NAMED":
            a.append("The rule names documentation, so it covers docs changes.")
        elif scope == "GENERIC":
            a.append("The rule speaks of contributions in general. Treat it as covering "
                     "docs, translations and READMEs too.")
        elif scope == "CODE_ONLY":
            a.append("The rule is worded for code only and does not mention docs. The "
                     "cautious reading is to apply its terms to docs as well.")
        elif scope == "OTHER_ONLY":
            a.append("The rule covers only issues or PR text. Its terms still apply to what "
                     "you write there.")
    for d in p.get("docs_repos", []):
        if d["reach"] == "STATES":
            a.append("Its docs live in %s, which states a rule of its own (compared with "
                     "this rule: %s). Follow the stricter of the two."
                     % (d["docs_repo"], d["terms"] or "unclear"))
        else:
            a.append("Its docs live in %s, whose own contributor files set no AI terms "
                     "(study 3, read %s). This project's rule still applies there."
                     % (d["docs_repo"], STUDY3_READ))
    return a


def docs_advice(d):
    a = []
    if d["reach"] == "STATES":
        a.append("This docs repo states an AI rule in its own files (compared with the main "
                 "rule: %s). Follow the stricter of the two." % (d["terms"] or "unclear"))
    else:
        a.append("This docs repo's own contributor files set no AI terms (study 3, read %s; "
                 "%s). Follow the parent project's rule, shown below."
                 % (STUDY3_READ, d["silent_subcode"] or d["reach"]))
    for p in d["parents"]:
        if p["rule"] == "yes":
            a.append("Parent %s: dataset stance '%s', scope %s." % (p["project"], p["stance"], p["scope"]))
        else:
            a.append("Parent %s: study 2 coded its own-text rule as '%s'." % (p["project"], p["rule"]))
        for line in project_advice(dict(p, docs_repos=[])):
            a.append("  " + line)
    return a


def _project_view(p, with_advice=True):
    v = {
        "kind": "project",
        "id": "study2:" + p["id"],
        "project": p["project"],
        "repos": list(p["repos"]),
        "dataset_stance": p["stance"],
        "rule": p["rule"],
        "scope": p["scope"],
        "borderline": p["borderline"] == "yes",
        "quote": p["quote"],
        "source": p["source"],
        "note": p["note"],
        "docs_repos": [{"docs_repo": d["docs_repo"], "reach": d["reach"], "terms": d["terms"]}
                       for d in p.get("docs_repos", [])],
    }
    if with_advice:
        v["advice"] = project_advice(p)
    return v


def _docs_view(d):
    return {
        "kind": "docs_repo",
        "id": "study3:" + d["id"],
        "docs_repo": d["docs_repo"],
        "projects": list(d["parent_names"]),
        "reach": d["reach"],
        "terms": d["terms"],
        "borderline": d["borderline"] == "yes",
        "quote": d["quote"],
        "source": d["source"],
        "note": d["note"],
        "parents": [_project_view(p, with_advice=False) for p in d["parents"]],
        "advice": docs_advice(d),
    }


def lookup(query, data):
    key = normalize(query)
    res = {"query": query, "key": key, "matches": [], "related": [],
           "snapshot": {"study2_read": STUDY2_READ, "study3_read": STUDY3_READ}}
    if not key:
        return res
    seen = set()

    def add(view):
        if view["id"] not in seen:
            seen.add(view["id"])
            res["matches"].append(view)

    if "/" in key:
        for d in data["docs"]:
            if d["docs_repo"].lower() == key:
                add(_docs_view(d))
        for p in data["projects"]:
            if key in [r.lower() for r in p["repos"]]:
                add(_project_view(p))
        if not res["matches"]:
            owner = _owner(key)
            rel = set()
            for d in data["docs"]:
                if _owner(d["docs_repo"]) == owner:
                    if d["docs_repo"] not in rel:
                        rel.add(d["docs_repo"])
                        res["related"].append({"kind": "docs_repo", "name": d["docs_repo"],
                                               "id": "study3:" + d["id"]})
                    for p in d["parents"]:
                        if p["project"] not in rel:
                            rel.add(p["project"])
                            res["related"].append({"kind": "project", "name": p["project"],
                                                   "id": "study2:" + p["id"]})
            for p in data["projects"]:
                if any(_owner(r) == owner for r in p["repos"]) and p["project"] not in rel:
                    rel.add(p["project"])
                    res["related"].append({"kind": "project", "name": p["project"],
                                           "id": "study2:" + p["id"]})
    else:
        for p in data["projects"]:
            if p["project"].lower() == key or key in [_repo_part(r) for r in p["repos"]]:
                add(_project_view(p))
        for d in data["docs"]:
            if _repo_part(d["docs_repo"]) == key:
                add(_docs_view(d))
    return res


def summary(data):
    p = data["projects"]
    d = data["docs"]
    n_rule = {k: sum(1 for r in p if r["rule"] == k) for k in ("yes", "no", "unreachable")}
    n_reach = {k: sum(1 for r in d if r["reach"] == k) for k in ("STATES", "LINKS", "SILENT")}
    return ("%d projects (study 2, read %s): %d with AI rules, %d without, %d unreadable; "
            "%d separate docs repos (study 3, read %s): %d state a rule, %d link to one, %d silent"
            % (len(p), STUDY2_READ, n_rule["yes"], n_rule["no"], n_rule["unreachable"],
               len(d), STUDY3_READ, n_reach["STATES"], n_reach["LINKS"], n_reach["SILENT"]))


def format_text(res):
    out = []
    if not res["matches"]:
        out.append("No row for %r in the table (key %r)." % (res["query"], res["key"]))
        if res["related"]:
            out.append("Same GitHub owner as these rows; their rule may cover this repo, so read it:")
            for r in res["related"]:
                out.append("  - %s (%s)" % (r["name"], r["id"]))
        out.append("Checklist:")
        for i, c in enumerate(CHECKLIST, 1):
            out.append("  %d. %s" % (i, c))
        return "\n".join(out)
    for m in res["matches"]:
        if m["kind"] == "project":
            out.append("== %s (%s) ==" % (m["project"], m["id"]))
            if m["repos"]:
                out.append("repos: " + ", ".join(m["repos"]))
            out.append("dataset stance: %s | own-text rule: %s | scope: %s%s"
                       % (m["dataset_stance"], m["rule"], m["scope"] or "-",
                          " | borderline" if m["borderline"] else ""))
        else:
            out.append("== docs repo %s (%s), for %s ==" % (m["docs_repo"], m["id"], ", ".join(m["projects"])))
            out.append("reach: %s | terms vs main rule: %s%s"
                       % (m["reach"], m["terms"] or "-", " | borderline" if m["borderline"] else ""))
        if m["quote"]:
            out.append('quote: "%s"' % m["quote"])
        if m["source"]:
            out.append("source: " + m["source"])
        if m["note"]:
            out.append("note: " + m["note"])
        if m["kind"] == "docs_repo":
            for p in m["parents"]:
                out.append("parent %s rule quote: %s" % (p["project"], ('"%s"' % p["quote"]) if p["quote"] else "-"))
                if p["source"]:
                    out.append("parent %s source: %s" % (p["project"], p["source"]))
        out.append("what to do:")
        for line in m["advice"]:
            out.append("  - " + line)
        out.append("")
    out.append("Snapshot: study 2 read %s, study 3 read %s. Rules change: read the live files "
               "(%s) before contributing." % (STUDY2_READ, STUDY3_READ, LIVE_FILES))
    out.append("Write-ups: %s and %s" % (STUDY2_RESULT, STUDY3_RESULT))
    return "\n".join(out)


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(
        description="Look up an open-source project's AI contribution rule (snapshot, Nov 2026).")
    ap.add_argument("query", nargs="*", help="GitHub URL, owner/repo, or project name")
    ap.add_argument("--json", action="store_true", help="print JSON")
    ap.add_argument("--summary", action="store_true", help="print table counts")
    ap.add_argument("--checklist", action="store_true", help="print the generic checklist")
    ap.add_argument("--data-dir", help="folder holding the three CSV files (default: ../assets)")
    ap.add_argument("--version", action="version", version="%(prog)s " + __version__)
    args = ap.parse_args(argv)
    try:
        data = load(args.data_dir)
    except (OSError, ValueError, KeyError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    if args.summary:
        print(summary(data))
    if args.checklist:
        for i, c in enumerate(CHECKLIST, 1):
            print("%d. %s" % (i, c))
    if not args.query:
        if args.summary or args.checklist:
            return 0
        ap.print_usage(sys.stderr)
        return 2
    results = [lookup(q, data) for q in args.query]
    if args.json:
        print(json.dumps(results if len(results) > 1 else results[0], ensure_ascii=False, indent=2))
    else:
        print("\n\n".join(format_text(r) for r in results))
    return 0 if all(r["matches"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
