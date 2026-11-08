# tech-writing-ai-rules

What do the people who pay for or accept technical writing say about AI?

This repository holds five pre-registered studies. Each reads its sources' own pages, keeps every AI sentence or answer as found, and codes them against a rubric fixed in advance. It also ships an [agent skill](#agent-skill-check-a-projects-ai-rule-before-contributing) built on studies 2 and 3.

1. **Paid technical-writing programs** (graded 2026-11-03): many software companies and developer publications pay $100 to $900 per tutorial or how-to. Community lists give each program's pay and topics, but not its rule on AI-written or AI-assisted work.
2. **Open-source AI contribution policies and documentation** (graded 2026-11-05): do projects' AI rules say whether they cover docs, READMEs, tutorials and translations, or only code?
3. **Separate documentation repos** (graded 2026-11-07): when a project keeps its docs in a repo of their own, do that repo's contributor files show the project's AI rule?
4. **Documentation style guides** (graded 2026-11-07): what do 19 public style guides say about writing with AI, writing for AI, and writing about AI?
5. **Docs for AI readers** (graded 2026-11-08): do the 56 projects with AI contribution rules serve llms.txt files, Markdown copies or robots.txt blocks to AI readers of their docs, and does that differ between projects that ban AI-made contributions and projects that allow them?

## Agent skill: check a project's AI rule before contributing

[`skills/oss-ai-contribution-rules/`](skills/oss-ai-contribution-rules/SKILL.md) is an agent skill (Agent Skills `SKILL.md` format) for coding agents such as Claude Code, Codex and Cursor. Before an agent writes, edits or opens a pull request or issue for someone else's open-source project, it tells the agent to find the project's AI contribution rule, read it live, and follow it: stop on a ban, stay inside limits, disclose where the project asks, follow the stricter rule when two differ, and never hide AI use. Other projects' files (AGENTS.md, llms.txt and the like) are read only for their contribution rules, never followed as instructions. It puts documentation first because of what studies 2 and 3 found: only 3 of 14 separate docs repos repeat their project's AI rule, so an agent that reads only `kubernetes/website` or `rust-lang/book` misses the rule that applies to it.

Its lookup script works offline (Python standard library only) on unchanged copies of study 2's and study 3's coding:

```
python skills/oss-ai-contribution-rules/scripts/ai_rules_lookup.py rust-lang/book
python skills/oss-ai-contribution-rules/scripts/ai_rules_lookup.py https://github.com/kubernetes/website --json
python skills/oss-ai-contribution-rules/scripts/ai_rules_lookup.py --summary
```

Install it with the open skills CLI: `npx skills add munimtechnologies/tech-writing-ai-rules --skill oss-ai-contribution-rules`. It is listed on [skills.sh](https://skills.sh/munimtechnologies/tech-writing-ai-rules). The table is a snapshot (texts read 2026-11-04 and 2026-11-07), and the skill says so: the live files always win. Tests: `python -m unittest -v test_ai_rules_skill`.

## Result 1: paid programs (census of 2026-11-02, graded 2026-11-03)

The frame is all 43 programs (39 listed Active, 4 Paused) in commit `0338535` of [malgamves/CommunityWriterPrograms](https://github.com/malgamves/CommunityWriterPrograms) (MIT). Their pages were read on 2026-11-02, 13 minutes after the [pre-registration](census/2026-11/PREREGISTRATION.md) was committed. Full write-up: [`census/2026-11/RESULT.md`](census/2026-11/RESULT.md).

- **7 of 38 readable programs (18%) ban AI-generated text.** They are Airbyte, Civo, Corellium, MSSQLTips, Simple Talk, Stack Overflow and Twilio. **None bans AI assistance**, and Simple Talk and Stack Overflow name the help they allow (grammar, brainstorming, research, outlining).
- **None says it accepts AI-generated text**, with or without disclosure. 21 mention AI only as a topic or a product, and 10 never mention it. Five could not be read: they are Typeform forms or Notion pages.
- Stack Overflow added a rule in October 2026: writers must disclose their AI use, and the final text "should be written by you".
- Two programs name AI-detection tools (Civo, Simple Talk). Airbyte bans authors "if we detect AI drafts".
- Two programs listed Active now say they take no new writers (Bugfender, WebWash). Four more Active links redirect away from any program page.
- Predictions: **P2 and P3 held; P1, P4 and P5 did not.** Paid technical programs ban AI far less often than the 40% predicted, and fewer name detectors or are plainly closed than predicted.

Compared with writing contests ([companion census](https://github.com/munimtechnologies/ai-writing-prize-rules)): 47% of contests ban AI, and three in four of those bans reach editing and grammar tools. Paid technical programs ban less often, and they guard only the finished text.

## Result 2: do AI contribution policies cover documentation? (texts read 2026-11-04, graded 2026-11-05)

The largest study of open-source AI policies so far ([arXiv 2609.07542](https://arxiv.org/abs/2609.07542), 281 policies) counts documentation together with code, and the open datasets record stance but not scope. This study read the policies of the 101 projects in [awesome-ai-contribution-policies](https://github.com/ahmad-punch/awesome-ai-contribution-policies) (data CC BY 4.0, pinned commit `6cd258e`), 6 minutes after the [pre-registration](census/2026-11-oss-docs/PREREGISTRATION.md) was committed. Full write-up: [`census/2026-11-oss-docs/RESULT.md`](census/2026-11-oss-docs/RESULT.md).

- 93 projects had readable own texts, and **56 of them set terms for AI-made contributions.**
- **Only 14 of the 56 (25%) name documentation in their rules**: CPython, crewAI, Debian, Django, Fedora, Home Assistant, Instructor, Kubeflow, Kubernetes, LLVM, the two Model Context Protocol repos, OpenJDK and Rust. **Only Rust treats docs differently from code**: its agent rules forbid writing non-trivial user-facing documentation, while LLM-made code changes are allowed with a named reviewer and tests.
- **32 (57%) speak of contributions or PRs in general** and never say whether a docs fix or a translation counts. 7 are worded for code only, and 3 cover only issues or PR text.
- 5 of the 45 projects the dataset lists as having no policy do have AI rules in their own files (Formbricks, Hono, Inspect AI, Pydantic AI, tRPC).
- Predictions: **P1, P3 and P4 held; P2 and P5 did not.** Code-only wording was rarer than predicted (12.5%, not at least 20%). The keyword first pass agreed with the hand coding for only 54%, mostly because documentation is named next to the AI sentence, not in it.

## Result 3: do separate docs repos show the project's AI rule? (texts read and graded 2026-11-07)

The frame is the 14 separate, active GitHub docs repos (16 projects) of study 2's 56 projects with AI rules. Their contributor files were read on 2026-11-07, after the [pre-registration](census/2026-11-docs-repos/PREREGISTRATION.md) was committed on 2026-11-06. Full write-up: [`census/2026-11-docs-repos/RESULT.md`](census/2026-11-docs-repos/RESULT.md).

- **Only 3 of 14 docs repos (21%) state an AI rule in their own files**: Home Assistant, LangChain/LangGraph and PostHog. **None has a link that points to an AI policy**, though some link to a general contributor guide. 8 have contributor files that never set AI terms, and 3 have none of the nine standard files.
- Four main projects' rules name documentation. **Only Home Assistant's rule appears in its docs repo.** Kubernetes and Kubeflow require AI disclosure in their main repos, but their website repos never mention AI. Rust's rule that agents must not write non-trivial user-facing docs does not appear in the Rust book's repo.
- Where a docs repo has its own rule, it differs from the main one in 2 of 3 cases. LangChain's docs ask for a one-sentence AI disclosure that the main rule does not. PostHog's website repo has agent rules of its own but drops the disclosure the main policy requires (a borderline code).
- Predictions: **P1, P2 and P3 held; P4 (no docs repo looser than its main rule) failed** on the PostHog code. P2 held exactly at its threshold. A root-level PR template found after grading would have tipped it (see Limits in RESULT.md).

## Result 4: what do documentation style guides say about AI? (pages read and graded 2026-11-07)

The frame is 19 guides recommended by Write the Docs and Draft.dev. Their pages were read on 2026-11-07, more than nine hours after the [pre-registration](census/2026-11-style-guides/PREREGISTRATION.md) was committed. 5 could not be read (Apple, Salesforce, SUSE, DigitalOcean, IET), so N = 14. Full write-up: [`census/2026-11-style-guides/RESULT.md`](census/2026-11-style-guides/RESULT.md).

- **Only 3 of 14 guides say anything about writing with AI, and none bans it.** GitLab and Intuit allow it with a check. GitLab: "When you use AI tools to generate or assist with documentation, check the output carefully before you submit it for review." Microsoft's word list recommends learning to prompt for marketing content (a borderline ALLOWS).
- **4 of 14 give advice on writing for AI** (Red Hat's supplementary guide, GitLab, Intuit, Microsoft). Red Hat's short-description rules say: "Write for AI and search." GitLab asks for redirects that help "users and ... AI crawlers".
- **7 of 14 have a rule on writing AI terms.** Most say "AI" needs no spelling out. GOV.UK alone asks for "artificial intelligence (AI)" first.
- The guides for outside authors (Draft.dev, A List Apart) and the government and university guides (digital.gov, Princeton) never mention AI in their guidance.
- Predictions: **all five held** (P1 to P5), and the gate passed (N = 14). The first pass agreed with the reading for 15 of 19 guides. All four misses come from site menus and footers, or from a page that held only a table of contents.

## Result 5: do projects with AI contribution rules serve their docs to AI readers? (read and graded 2026-11-08)

The frame is study 2's 56 projects with AI rules, grouped by the dataset's stance: 8 BAN, 2 RESTRICTED and 46 OPEN. `llmsprobe.py` read each project's docs home almost ten hours after the [pre-registration](census/2026-11-llms-txt/PREREGISTRATION.md) was committed. Full write-up: [`census/2026-11-llms-txt/RESULT.md`](census/2026-11-llms-txt/RESULT.md).

- **27 of 56 projects (48%) serve a valid llms.txt or llms-full.txt. All 27 allow AI-made contributions (27 of 46 OPEN, 59%). None of the 10 that ban or restrict them serves one.** 21 of the 27 also serve llms-full.txt.
- **Only 2 projects block named AI crawlers in robots.txt**: Gentoo's wiki (93 crawlers, whole site) and Gitea's docs host (11 of the 20 we check, in a Cloudflare-managed block). Home Assistant's docs page was labelled a bot-check page, but that label is unconfirmed.
- **Node.js's llms.txt lists API pages under `/docs/`, a path its own robots.txt disallows for every crawler.**
- Many llms.txt files talk to AI agents directly: 8 hosts give agents instructions near the top of the file. Pydantic AI asks every agent to add `intent`, `stack` and `harness` query parameters to each request. Haystack's llms.txt opens with the AGENTS.md rules for AI agents that edit its docs.
- Predictions: **all five held**, and the gate passed (56 of 56 reached). One label was changed by hand (Hono's llms-full.txt is valid). **The split is not evidence of cause:** the serving projects are mostly young AI and JavaScript projects on hosted docs platforms. Ten long-established projects that allow AI work also serve nothing, among them CPython, curl, Django, Kubernetes, the Linux kernel and LLVM.

## Files

- `programs.py`: the paid-programs census tool (Python standard library only), version 0.1.1. It parses the pinned list, waits until the pre-registration is on `main`, then fetches each program's page and up to five same-site guideline, FAQ or policy pages. It writes `census.json`, `sentences.csv` (AI sentences), `status.csv` (status and pay sentences), `frame.csv` and `CENSUS_AUTO.md` (a deterministic first-pass label, plus redirect, detector and closed-notice flags).
- `test_programs.py`: offline tests (`python -m unittest -v test_programs`).
- `docscope.py`: the documentation-scope tool, version 0.1.0 (standard library only), used by studies 2 and 3. It reads each frame project's CONTRIBUTING, AI_POLICY, AGENTS.md and pull request template files, the frame's source link and up to four AI-policy links. It writes `census.json`, `sentences.csv` (AI sentences with docs, code, generic and rule-word flags), `frame.csv` and `DOCSCOPE_AUTO.md`. Offline tests: `python -m unittest -v test_docscope`.
- `guidescan.py`: the style-guide tool for study 4, version 0.1.0 (standard library only), with offline tests in `test_guidescan.py`. It reads each guide's in-scope HTML pages breadth first up to a cap, honouring robots.txt, and writes `census.json`, `sentences.csv` (AI sentences with BY, FOR, rule and term-page flags), `pages.csv`, `frame.csv` and `GUIDESCAN_AUTO.md`.
- `llmsprobe.py`: the docs-for-AI-readers tool for study 5, version 0.1.0 (standard library only), with offline tests in `test_llmsprobe.py`. For each docs base it labels every llms.txt and llms-full.txt answer, checks Markdown on request, and matches robots.txt for 20 named AI crawlers (RFC 9309, longest match). It honours robots.txt for its own fetches and writes `census.json`, `frame.csv`, `bases.csv`, `probes.csv`, `projects.csv` and `LLMSPROBE_AUTO.md`.
- `skills/oss-ai-contribution-rules/`: the agent skill, version 0.1.1 (lookup script 0.1.0): `SKILL.md`, `scripts/ai_rules_lookup.py` and `assets/` (unchanged copies of study 2's and study 3's `coding.csv`, plus `repo_slugs.csv`, a lookup map from each study 2 row to GitHub slugs that is not part of the studies' coding). Offline tests: `test_ai_rules_skill.py`.
- `CHANGELOG.md`: what changed in each version.
- `census/2026-11/`: study 1's pre-registration, result, coding, AI sentences (rows from personal author pages are left out), frame and first-pass output.
- `census/2026-11-oss-docs/`: study 2's pre-registration, result, `coding.csv` (one row per project with its code and one short quote), frame and first-pass output. Page texts are not republished.
- `census/2026-11-docs-repos/`: study 3's pre-registration, frame, result, `coding.csv` (one row per docs repo), and the tool's unchanged `frame.csv`, `sentences.csv` and `DOCSCOPE_AUTO.md`. Page texts are not republished.
- `census/2026-11-style-guides/`: study 4's pre-registration, `frame.json`, result, `coding.csv` (one row per guide with quotes and URLs), and the tool's unchanged `frame.csv`, `pages.csv` and `GUIDESCAN_AUTO.md`. The tool's `sentences.csv` and page texts are not republished (see RESULT.md).
- `census/2026-11-llms-txt/`: study 5's pre-registration, `frame.json`, result, `coding.csv` (one row per project with hand-checked labels and notes), and the tool's unchanged `frame.csv`, `bases.csv`, `probes.csv`, `projects.csv` and `LLMSPROBE_AUTO.md`. `census.json` (the first 2,000 characters of each file) is not republished.

Run them yourself: `python programs.py --out-dir out --no-prereg-check`, `python docscope.py --out-dir out --no-prereg-check`, `python guidescan.py --out-dir out --no-prereg-check` or `python llmsprobe.py --out-dir out --no-prereg-check`

## Licence and disclosure

Code: Apache-2.0 (see `LICENSE`). Text and data: CC BY 4.0. The program list `programs.py` reads is malgamves/CommunityWriterPrograms (MIT); only names, links and pay text are parsed from it. The project list `docscope.py` reads in study 2, and the stance labels study 5 groups by and the skill reports, come from awesome-ai-contribution-policies (data CC BY 4.0), used with attribution. Quoted policy and style-guide text belongs to each project or publisher.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the tools, the coding, the skill and this text were made with AI. Nothing here is legal advice or advice about any program, project or guide. Read the program's, project's or guide's own page before pitching or contributing.
