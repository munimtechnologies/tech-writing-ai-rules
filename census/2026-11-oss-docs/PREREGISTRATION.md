# Pre-registration: do open-source AI contribution policies say whether they cover documentation?

Registered 2026-11-04 by MV2 of Munim, Inc., with AI agents working in his name. The tool (`docscope.py` 0.1.0) waits until this file is on `main` before it reads any policy text. This file is never edited after it is committed. Corrections go in a dated note in RESULT.md.

## Question

Many open-source projects now publish rules for contributions made with AI: some allow them with disclosure, some ban them. Technical writers, translators and docs contributors need to know whether those rules also cover **documentation** (docs, READMEs, tutorials, translations, docstrings, typo fixes), or whether they talk about code only and leave docs unstated.

The largest study we found, Hora, Robbes and Zacchiroli, ["We Permit the Use of AI, but [...]": The Landscape of AI Policies in Popular Open Source Projects](https://arxiv.org/abs/2609.07542) (arXiv 2609.07542, 281 policies), counts documentation together with code ("code contributions, including code, pull requests, commits, and documentation"), so it gives no figure for docs. The open dataset this study uses as its frame ([awesome-ai-contribution-policies](https://github.com/ahmad-punch/awesome-ai-contribution-policies), data CC BY 4.0) records stance, disclosure, gates and sanctions, but it has no field for scope. The lists by melissawm and gsauthof, and The Consensus's survey of 112 projects, sort projects by stance only. As far as we can find, no one has counted how many policies name documentation, treat it differently, or are worded for code only.

## Frame

All entries of `policies.json` at commit `6cd258e96c3772a624f07fcf7f7a0b3867eaeabd` of awesome-ai-contribution-policies: 101 projects, verified by that dataset on or before 2026-10-21. Its README gives their stances as ban 9, restricted 2, disclose-required 20, disclose-encouraged 3, neutral 17, encouraged 5 and no published policy 45. The tool parses the file at run time, numbers the projects D001 to D101 in file order and writes them to `frame.csv`. The frame is not a random sample: it leans towards AI and developer-tool projects and includes the dataset's own picks of well-known policies.

## What is read

For each project, once, by `docscope.py` 0.1.0, from one public machine:

1. From the project's GitHub repo (the dataset's `repo` field), at the default branch (`raw.githubusercontent.com/<repo>/HEAD/<path>`), these nine paths: `CONTRIBUTING.md`, `.github/CONTRIBUTING.md`, `docs/CONTRIBUTING.md`, `CONTRIBUTING.rst`, `AI_POLICY.md`, `.github/AI_POLICY.md`, `AGENTS.md`, `.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE.md`. Missing files (404) are recorded and skipped.
2. The dataset's own `source_url`, unless it is only the repo's home page (already covered by step 1) or another github.com page such as a commit (not read). GitHub file links are read as raw files. Press articles (theregister.com, infoq.com) are read but **never count as the project's own text**.
3. Up to 4 links found in those texts whose address or link text points to an AI policy (for example `AI_POLICY.md`, "AI tools", "use of AI"). One hop only.

From every text the tool keeps, word for word, each sentence that mentions AI (the capitalised token "AI", LLM, generative, Copilot, Claude, Codex, coding assistants or agents, agentic, vibe coding and similar). Each gets four first-pass flags (docs, code, generic, rule word) and each project gets a first-pass label (`classify()` in the tool). The first pass is a screen. **The primary coding below is done by reading every saved AI sentence**, and the saved page text where a sentence needs its context.

## Primary coding (one coder: an AI agent working in MV2's name)

**RULE** (yes/no). Yes if the project's own texts contain at least one sentence that sets terms for contributions made with AI: it permits, encourages, limits, requires disclosure or human review for, or bans them. Not a rule: AI as the project's product or topic, how to use the project's AI features, and workflow instructions to agents in AGENTS.md (commands, style, layout) that say nothing about whether or on what terms AI-made contributions are accepted. AGENTS.md text that does set such terms (disclose, do not open PRs, a human must review) is a rule.

**SCOPE**, for projects with RULE = yes, taking the first that applies:

1. **DOCS_DISTINCT**: a rule treats documentation differently from code (a different permission, limit or condition), or a rule applies to documentation alone.
2. **DOCS_NAMED**: a rule names documentation as covered, on the same terms as code.
3. **GENERIC**: the rules apply to contributions, pull/merge requests, changes, commits, submissions or content in general, and none names documentation.
4. **CODE_ONLY**: every rule is worded only in terms of code, patches or implementation.
5. **OTHER_ONLY**: the rules cover only issues, bug or security reports, review comments or other communication.

"Documentation" means docs, documentation, READMEs, tutorials, guides for users, manuals or man pages, website text, docstrings, translations or localisation of docs or UI text, changelogs and typo fixes. Code comments count as code. A translation rule about the contributor's own messages ("AI may translate your comments") is communication, not documentation.

Each coded project gets one short verbatim quote (at most 300 characters) for the sentence its code rests on, with its source address.

## Predictions

Let R be the projects with RULE = yes.

- **P1.** Fewer than half of R name documentation in a rule: (DOCS_DISTINCT + DOCS_NAMED) / |R| < 0.50.
- **P2.** At least 20% of R are CODE_ONLY.
- **P3.** At most 4 projects are DOCS_DISTINCT.
- **P4.** Of the projects the frame lists as having no published policy (`stance` = `no-policy`), fewer than 10 have RULE = yes in the texts read.
- **P5.** The first pass agrees with the primary scope for at least 70% of R, where `docs_named` matches DOCS_NAMED or DOCS_DISTINCT, `generic` matches GENERIC, and `code_only` matches CODE_ONLY. Any other first-pass label counts as a disagreement.

## Gates

- **G1.** At least 90 of the 101 projects have at least one own text read.
- **G2.** |R| ≥ 30.

If a gate fails, the counts are still published, but the predictions it affects (G1: all; G2: P1, P2, P3 and P5) are marked "not graded" with the reason.

## Known before registering

Before registering, the agents read the frame's README counts and its list of projects with their source links, but none of the frame's policy texts themselves. Search-result summaries quoted two of them: Kubernetes's guidance mentions AI tools "which generate code or documentation", and QEMU's policy declines "contributions which are believed to include or derive from AI generated content". The arXiv paper quotes policies outside this frame (NLnet Labs: "No output of LLMs in code or documentation"; Nextcloud; one Chromium change that "expand[ed] AI policy to include documentation updates"). Nothing else was read.

## Limits

- One coder, who is an AI agent. Borderline readings are listed in RESULT.md, with the quote each rests on.
- The texts are read at the default branch on the day of the run. A policy that lives only on a docs site not linked from these files, or in a discussion thread, is missed. The dataset's own source link reduces this but does not remove it.
- The frame is the dataset's 101 projects, not all of open source. Results describe this frame.
- Cues and coding are in English. Text that is not in English is coded only if its meaning is clear from the text read.

## What is published

Counts, per-project codes with one short quote each, the first-pass output (`DOCSCOPE_AUTO.md`, `frame.csv`) and the graded predictions. Full page texts are not republished.

Code Apache-2.0. Text and data CC BY 4.0. The frame is awesome-ai-contribution-policies (data CC BY 4.0), used with attribution. Quoted policy text belongs to each project.
