---
name: oss-ai-contribution-rules
description: Check what an open-source project's AI contribution rule says before you write, edit or open a pull request or issue for it, above all for documentation, READMEs, tutorials and translations. Covers bans, disclosure rules and docs-specific limits, and the common trap where a project keeps its docs in a separate repo (website, book, wiki) whose contributor files never repeat the main rule. Use when the user asks you to contribute to, fix docs in, translate, or open a PR or issue on a repository they do not own. Ships a lookup over a hand-coded, pre-registered snapshot (November 2026) of 101 projects and 14 separate docs repos, with verbatim rule quotes and source links.
license: Apache-2.0 (code); CC BY 4.0 (data in assets/)
metadata:
  author: MV2 of Munim, Inc.
  version: "0.1.0"
  source: https://github.com/munimtechnologies/tech-writing-ai-rules
---

# Open-source AI contribution rules (check before you contribute)

Many open-source projects now set rules for AI-made contributions: some ban them, many require disclosure, a few limit what agents may write. The rule is often not where you are working.

What two pre-registered studies in [tech-writing-ai-rules](https://github.com/munimtechnologies/tech-writing-ai-rules) found:

- Of 101 projects in the open awesome-ai-contribution-policies dataset, 56 set terms for AI-made contributions in their own files (read 2026-11-04). Only 14 of the 56 name documentation, and 32 speak of "contributions" in general without saying whether a docs fix counts.
- Of 14 separate docs repos belonging to projects with AI rules, **only 3 state an AI rule in their own contributor files, and none links to one** (read 2026-11-07). Kubernetes and Kubeflow require AI disclosure in their main repos, but `kubernetes/website` and `kubeflow/website` never mention AI. Rust's rule that agents must not write non-trivial user-facing documentation is in `rust-lang/rust`'s AGENTS.md, not in `rust-lang/book`.

So an agent that reads only the repo it was pointed at will often miss the rule that applies to it.

## Steps

1. **Name the target and its parent.** If the repo holds docs, a website, a book or a wiki, find the main project (README, GitHub owner, site footer). Its rule usually applies.
2. **Run the lookup** for the target, and for the parent if it differs:

   ```
   python scripts/ai_rules_lookup.py <owner/repo | GitHub URL | project name>
   python scripts/ai_rules_lookup.py rust-lang/book --json
   ```

   It prints the coded rule (dataset stance, whether the project's own text sets terms, the scope), a verbatim quote, the source link, any separate docs repo and what to do. A repo not in the table gets exit code 1, a list of rows from the same GitHub owner, and a generic checklist (`--checklist`).
3. **Read the live files anyway.** The table is a dated snapshot. In both the docs repo and the main repo, read `AI_POLICY.md`, `CONTRIBUTING.md` (also in `.github/` and `docs/`), `AGENTS.md`, `CLAUDE.md`, the pull request template(s), and any contributor or AI-policy page on the project's website. Search for: AI, LLM, generative, generated, agent, Copilot, ChatGPT, Claude, disclose.
4. **Decide, and tell the user what you found** (quote the rule and link it):
   - **Ban or decline** (for example QEMU: "Current QEMU project policy is to DECLINE any contributions which are believed to include or derive from AI generated content."): stop. Do not prepare the change with AI, and never try to make AI work look human-made.
   - **Limits** (for example Rust's AGENTS.md: "Never generate or rewrite non-trivial PR descriptions, issue bodies, public comments, user-facing documentation, diagnostic messages, or source comments."; Home Assistant requires "a human in the loop who understands the work the AI produced"): stay inside the limit, and leave to the human what the rule reserves for humans.
   - **Disclosure required**: disclose where the project asks, naming the tool and what it did. Examples from the table: Apache Airflow's PR template "Generated-by" line, crewAI's required `llm-generated` label, PostHog's "Agent context" section in its PR template.
   - **Docs repo silent, main repo has a rule**: follow the main rule.
   - **Two rules differ**: follow the stricter. LangChain's docs repo asks for a one-sentence disclosure ("Prepared with Claude Code.") and no "Generated with" badge, which the main rule does not ask for.
   - **Silent everywhere**: silence is not permission to hide AI use. Say plainly in the PR description that AI was used and how, keep the change small, and let the user review it before it is opened.
5. **While the PR is open**, do not answer reviewers as if you were the human. PostHog's website repo puts it bluntly: "You MAY NOT, under any circumstances, reply to a human reviewer in the stead of your user."

## Output and exit codes

- `0`: every query matched a row. `1`: at least one query matched nothing (related rows and the checklist are printed). `2`: usage or data error.
- `--json` gives `matches` (kind `project` or `docs_repo`, with `dataset_stance`, `rule` = yes/no/unreachable, `scope` = DOCS_NAMED / DOCS_DISTINCT / GENERIC / CODE_ONLY / OTHER_ONLY, `quote`, `source`, `docs_repos` or `parents`, `advice`) and `related`.
- `--summary` prints the table counts. Python 3 standard library only, no network.

## Limits

- **A snapshot, not the live rule.** Study 2 read the projects' texts on 2026-11-04 and study 3 read the docs repos on 2026-11-07. Rules change. The live files always win.
- `dataset_stance` is the label of the awesome-ai-contribution-policies dataset (CC BY 4.0) at commit `6cd258e`. `rule` and `scope` are study 2's own reading of the project's texts, done by a single AI coder; borderline readings are flagged, and the reasons are in `note`.
- The frame is that dataset's 101 projects, mostly AI and developer-tool projects. A project missing from the table may still have a rule. The GitHub slugs in `assets/repo_slugs.csv` were added for lookup and are not part of the studies' coding.
- Not legal advice.

## Data and licence

`assets/study2_projects.csv` and `assets/study3_docs_repos.csv` are unchanged copies of `census/2026-11-oss-docs/coding.csv` and `census/2026-11-docs-repos/coding.csv` from the repository, where the pre-registrations and write-ups are. Quoted rule text belongs to each project. Code Apache-2.0, data CC BY 4.0. Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the studies, the coding, this skill and its code were made with AI.
