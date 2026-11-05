# Result: do open-source AI contribution policies say whether they cover documentation?

Graded 2026-11-05 by MV2 of Munim, Inc., with AI agents working in his name. The pre-registration is [`PREREGISTRATION.md`](PREREGISTRATION.md). It was first committed at 2026-11-04 14:39:13 UTC, and `docscope.py` 0.1.0 read the policy texts from 14:45:28 to 14:56:33 UTC the same day. The pre-registration has not been edited since.

## In one paragraph

Of the 93 projects whose own texts could be read, 56 set terms for contributions made with AI. **Only 14 of those 56 (25%) name documentation anywhere in their rules. Only one, Rust, treats documentation differently from code.** 32 (57%) speak of "contributions", "changes" or "PRs" in general and never say whether a docs fix or a translation counts. 7 are worded for code only and 3 cover only issues or PR text. So a technical writer or translator who wants to send an AI-assisted docs PR usually has to infer whether the rule applies. The keyword first pass agreed with the hand coding for just 30 of the 56. Most misses were documentation mentions in sentences with no AI word, which only a human-style reading of the surrounding text finds.

## Gates

- **G1 (at least 90 of 101 projects with an own text read): passed, 93.** No own text was read for 8 projects: Claude Agent SDK (Python and TypeScript), Claude Code, FastAPI, FastMCP (TypeScript), MCP-Nest and Supabase Edge Runtime (the tool saved no text from their repos or source links; see `DOCSCOPE_AUTO.md`), and Zig, for which only a press article was read, and press never counts.
- **G2 (|R| ≥ 30): passed, |R| = 56.**

## Counts

| Code | Projects | Share of R |
|---|---|---|
| DOCS_DISTINCT | 1 | 2% |
| DOCS_NAMED | 13 | 23% |
| GENERIC | 32 | 57% |
| CODE_ONLY | 7 | 13% |
| OTHER_ONLY | 3 | 5% |
| **R (RULE = yes)** | **56** | |
| RULE = no (own text read, no AI rule found) | 37 | |
| Not read | 8 | |

- **DOCS_DISTINCT (1):** Rust. Its AGENTS.md tells agents: "Never generate or rewrite non-trivial PR descriptions, issue bodies, public comments, user-facing documentation, diagnostic messages, or source comments." LLM-made code changes, by contrast, are allowed with a named reviewer and tests, and a typo fix counts as "trivial". The project blog's summary of the policy says "LLM output isn't allowed in public docs, PR descriptions, or GitHub comments unless it's clearly marked".
- **DOCS_NAMED (13):** CPython, crewAI, Debian, Django, Fedora, Home Assistant, Instructor, Kubeflow, Kubernetes, LLVM, MCP Python SDK, Model Context Protocol (spec), OpenJDK.
- **GENERIC (32):** AnythingLLM, Apache Airflow, Coder, curl, Dify, Formbricks, GCC, Gemara, Gentoo, Ghostty, Gitea, Godot Engine, Haystack, Hono, Hugging Face Transformers, Inspect AI, LangChain, LangGraph, Linux Foundation, LlamaIndex, Next.js, Node.js, PostHog, posthog-js, Pydantic AI, pytest, QEMU, SDL, Shaka Player, Storybook, tRPC, vLLM.
- **CODE_ONLY (7):** Documenso, Linux kernel, Mesa, Mozilla Firefox, NetBSD, Open WebUI, SQLite.
- **OTHER_ONLY (3):** cal.diy (AI-written PR summaries), MCP TypeScript SDK (issues), OpenHands (the human section of a PR description).

Every coded project has one verbatim quote and its source in [`coding.csv`](coding.csv).

## Predictions

- **P1. Fewer than half of R name documentation: HELD.** (1 + 13) / 56 = 25%.
- **P2. At least 20% of R are CODE_ONLY: FAILED.** 7 / 56 = 12.5%. Code-only wording is rarer than expected: most policies say "contributions" or "PRs" and leave the scope open, rather than speaking of code.
- **P3. At most 4 projects are DOCS_DISTINCT: HELD.** One project (Rust).
- **P4. Fewer than 10 of the frame's "no published policy" projects have RULE = yes: HELD.** Five of the 45 do: Hono and Inspect AI have AI sections in their contributing guides, Formbricks and tRPC ask for the AI model used in their PR templates, and Pydantic AI's AGENTS.md tells agents how to handle AI-made contributions. The frame's labels date from 2026-10-21 or earlier, so some of these may be new.
- **P5. The first pass agrees with the primary scope for at least 70% of R: FAILED.** 30 / 56 = 54%.

## Why the first pass missed so much (P5)

The first pass flags a sentence as "docs" only if that same sentence mentions AI. Documentation is usually named next to the AI sentence, not in it:

- **In a list or the next sentence.** CPython lists "Supplementing contributor knowledge for code, tests, and documentation" under "acceptable uses of generative AI". crewAI follows its label rule with "This applies to code, documentation, and issues alike." Kubernetes lists "AI tools (...) which generate code or documentation" under "Large or Automatic Edits".
- **Cut by the sentence splitter.** Django's "(e.g., generating code, drafting commit messages, writing documentation)" was split off at "e.g.,". Hard-wrapped HTML text split OpenJDK's and Debian's sentences.
- **False docs hits.** "manual verification" (Coder) matched the "manual" cue, "as listed in the README.md" (Node.js) matched README, and Firefox's page title "Firefox Source Docs" and LangChain's "check facts against ... official provider docs" also matched.
- **Rules with no rule word.** NetBSD's "presumed to be tainted code, and must not be committed" and Open WebUI's "I reviewed any AI-generated code" checkbox were both labelled as having no rule cue.

A keyword screen is not enough for scope questions. A later docscope version should flag documentation words in a window around each AI sentence and should not split at "e.g.".

## Borderline readings (each marked in `coding.csv`)

Changing any of these does not change a graded outcome:

- **Whether it is a rule.** cal.diy, Formbricks, tRPC, OpenHands and Pydantic AI were coded RULE = yes. If all five are read as not rules, R = 51: 14 / 51 = 27% name docs (P1 still holds), and 7 / 51 = 14% are CODE_ONLY (P2 still fails). The AGENTS.md attribution instructions at LiteLLM and promptfoo ("no Claude co-author trailer") were read as style instructions, as were Langfuse's instructions for its own cloud agents. Counting all three as rules gives R = 59, with 24% DOCS and 12% CODE_ONLY.
- **"Documentation comments".** The Model Context Protocol org policy asks contributors to state "the extent to which AI assistance was used (e.g., documentation comments vs. code generation)". This was read as naming docs (docstrings). If it is read as code comments, MCP Python SDK and the MCP spec become GENERIC. Instructor (a Cursor rule "for writing documentation") would become GENERIC too, giving 11 / 56 = 20% DOCS (P1 still holds).
- **CODE_ONLY or GENERIC.** The Linux kernel ("AI agents MUST NOT add Signed-off-by tags"; the linked generated-content.rst was not read), Mesa, Firefox (its scope is "production code for the browser") and SQLite (code, plus a separate rule on bug reports) were read as CODE_ONLY. Read as GENERIC, CODE_ONLY falls to 3 / 56 and P2 fails more clearly.
- **Fedora.** Fedora's disclosure takes a different form for documents and translations ("document preambles, design file metadata, translation notes, or wiki page categories"), but the obligation is the same, so it was coded DOCS_NAMED. Read as DOCS_DISTINCT, the count is 2 and P3 still holds.
- **Debian.** Debian's own text is the 2026 general resolution's vote page, which lists eight options. Debian was coded from the winning one, Option 5 ("Responsible Use of Generative AI"), the only member of the Schwartz set. Its first sentence names documentation.

## What a docs contributor can take from this (exploratory)

These are the projects whose rules, in the texts read, explicitly cover documentation and allow AI help under conditions. Read the project's current page before contributing:

- **Kubeflow:** "The use of AI to generate code or documentation is permitted", with disclosure (an `Assisted-by:` trailer or a note in the PR).
- **LLVM:** an LLM-generated documentation PR "which a contributor manually reviews for correctness, edits, and then posts as a PR, is an approved use", and tool-generated content is labelled.
- **Fedora, Debian, CPython, Django, Kubernetes, Home Assistant, crewAI, Model Context Protocol:** AI help is allowed with human review. Disclosure is required at Django, Kubernetes, MCP and Fedora (for substantial unchanged output), encouraged at Debian and CPython, and done with a label at crewAI.
- **Where documentation is explicitly closed to AI text:** OpenJDK (an interim ban on "source code, text, and images", with an FAQ that allows AI to review JavaDoc you wrote yourself) and Rust (agents may not write non-trivial user-facing docs).

## Limits

- One coder, who is an AI agent. Every code rests on a public quote, and the borderline readings are listed above.
- Texts were read once, at the default branch, on 2026-11-04. Policies on docs sites not linked from the nine standard files, or from the dataset's source link, were missed. For the Linux kernel, the linked `generated-content.rst` was not read.
- The frame is the dataset's 101 projects. It leans towards AI and developer tools and is not a random sample of open source.
- Prior work: Hora, Robbes and Zacchiroli ([arXiv 2609.07542](https://arxiv.org/abs/2609.07542)) count documentation together with code. As far as we found, no earlier study reports how many policies name documentation.

## Files

- `coding.csv`: one row per project, giving the stance in the frame, RULE, SCOPE, the first-pass label and whether it agrees, a borderline flag, a note, one quote of at most 300 characters, and its source.
- `frame.csv`, `DOCSCOPE_AUTO.md`: the tool's frame and first-pass output, unchanged.
- The tool's `census.json`, `sentences.csv` and saved page texts are not republished (see the pre-registration). Anyone can regenerate them with `python docscope.py --out-dir out --no-prereg-check`, but pages change over time.

Frame: [awesome-ai-contribution-policies](https://github.com/ahmad-punch/awesome-ai-contribution-policies) (data CC BY 4.0), commit `6cd258e96c3772a624f07fcf7f7a0b3867eaeabd`. Quoted policy text belongs to each project. This text and `coding.csv` are CC BY 4.0. Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the coding and this text were made with AI. This is not legal advice.
