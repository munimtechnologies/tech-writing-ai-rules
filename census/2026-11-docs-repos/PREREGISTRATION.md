# Pre-registration: when a project keeps its docs in a separate repo, does that repo show the project's AI rule?

Registered 2026-11-06 by MV2 of Munim, Inc., with AI agents working in his name. This is study 3 in this repository. The job waits until this file is on `main` before it reads any text from the docs repos. This file is never edited after it is committed. Corrections go in a dated note in RESULT.md.

## Question

Study 2 ([census/2026-11-oss-docs](../2026-11-oss-docs/RESULT.md)) read the AI contribution rules of 101 open-source projects. 56 set terms for contributions made with AI. Those rules live in each project's main code repository, or on a page linked from it. But many projects keep their user documentation in a **separate repository** (for example `kubernetes/website`, `godotengine/godot-docs`, `rust-lang/book`). A technical writer, translator or docs contributor who opens a pull request there may never see the main repo's CONTRIBUTING file.

So, for each such docs repo: do its own contributor-facing files state an AI rule, link to one, or say nothing?

Prior work we found: Hora, Robbes and Zacchiroli (arXiv 2609.07542, 281 policies), arXiv 2605.16706 (118 policies in 1,000 repos), arXiv 2609.07919 and arXiv 2606.14594 study where AI policies are and what they say. Each reads policies one repository (or one project site) at a time. arXiv 2605.16706 notes that a policy can sit in a separate contributing document linked from CONTRIBUTING. We found no count of whether a project's AI rule reaches the separate repository that holds its documentation.

## Frame

Start from the 56 projects with RULE = yes in study 2's `coding.csv` (published 2026-11-05). Include a project when its main user documentation is built from a **separate, active GitHub repository** that is not the repository (or site) where its AI rule lives. Projects that share one docs repo count once. This gives 14 docs repos for 16 projects. They are listed in `frame.json` in this folder, which the job reads at run time. The tool numbers them D001 to D014 in file order:

| id | docs repo | project(s) | main project's rule (study 2: stance; scope) |
|---|---|---|---|
| D001 | Mintplex-Labs/anythingllm-docs | AnythingLLM | neutral; GENERIC |
| D002 | langgenius/dify-docs | Dify | neutral; GENERIC |
| D003 | ghostty-org/website | Ghostty | disclose-required; GENERIC |
| D004 | godotengine/godot-docs | Godot Engine | ban; GENERIC |
| D005 | home-assistant/home-assistant.io | Home Assistant | restricted; DOCS_NAMED |
| D006 | honojs/website | Hono | no-policy in the dataset, rule found; GENERIC |
| D007 | kubeflow/website | Kubeflow | disclose-required; DOCS_NAMED |
| D008 | kubernetes/website | Kubernetes | disclose-required; DOCS_NAMED |
| D009 | langchain-ai/docs | LangChain, LangGraph | neutral; GENERIC |
| D010 | OpenHands/docs | OpenHands | neutral; OTHER_ONLY |
| D011 | open-webui/docs | Open WebUI | neutral; CODE_ONLY |
| D012 | PostHog/posthog.com | PostHog, posthog-js | disclose-required; GENERIC |
| D013 | rust-lang/book | Rust | restricted; DOCS_DISTINCT |
| D014 | libsdl-org/sdlwiki | SDL | ban; GENERIC |

The 16 candidate repos were checked on 2026-11-06 through the GitHub API with repository metadata only (name, description, archived flag, default branch, last push), not their files. Two candidates were dropped: `go-gitea/docs` (archived since 2017; Gitea's docs now live on gitea.com, outside GitHub) and `deepset-ai/haystack-home` (Haystack's docs are built from the `docs-website/` folder of the main repo, checked by listing that repo's top level).

For Rust, the book is chosen because it is the first item on rust-lang.org's Learn page. For Kubeflow, the AI policy page is on kubeflow.org, which this repo builds, but the question here is whether the repo's contributor-facing files show it.

**Excluded (40 projects), with the reason.** Docs in the same repository as the rule: Apache Airflow, Coder, CPython, crewAI, curl, Django, Documenso, Formbricks, Haystack, Hugging Face Transformers, Inspect AI, Instructor, LlamaIndex, LLVM, MCP Python SDK, MCP TypeScript SDK, Model Context Protocol (spec), Next.js, Node.js, Pydantic AI, pytest, Shaka Player, Storybook, tRPC, vLLM. Developed outside GitHub (docs in-tree there), or docs kept outside GitHub (Gitea): Debian, Fedora, GCC, Gentoo, Gitea, Linux kernel, Mesa, Mozilla Firefox, NetBSD, OpenJDK, QEMU, SQLite. No separate user-docs repo identified: cal.diy, Gemara. Umbrella body with no docs repo: Linux Foundation. These calls were made from the agents' knowledge of each project's layout. Only the 16 candidates above were checked through the API. A project wrongly excluded is a limit of this frame.

## What is read

`docscope.py` 0.1.0 does the reading. It is unchanged from study 2 and fetched by the job from commit `44981fa2bc1bdfacb3e629b80d4cecdfb476eb3a` of this repository, together with its offline tests, which run first. For each docs repo, once, from one public machine:

1. From the docs repo's default branch, the same nine paths as study 2: `CONTRIBUTING.md`, `.github/CONTRIBUTING.md`, `docs/CONTRIBUTING.md`, `CONTRIBUTING.rst`, `AI_POLICY.md`, `.github/AI_POLICY.md`, `AGENTS.md`, `.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE.md`. Missing files (404) are recorded.
2. For three repos whose docs have a well-known contributor guide page, that page as `source_url`. The addresses below were named before reading anything and were not opened beforehand, so a 404 is recorded as is:
   - D004: `https://docs.godotengine.org/en/latest/contributing/documentation/contributing_to_the_documentation.html`
   - D005: `https://developers.home-assistant.io/docs/documenting/`
   - D008: `https://kubernetes.io/docs/contribute/`
3. Up to 4 links in those texts whose address or link text points to an AI policy (one hop), as in study 2.

The tool's report reuses study 2's wording in two places: its last line names study 2's frame, and its ids are D001 to D014 in this frame's order. The frame actually read is the `--frame-url` recorded in `census.json`.

## Primary coding (one coder: an AI agent working in MV2's name)

RULE has the meaning it has in study 2's pre-registration: a sentence that sets terms for contributions made with AI (permits, encourages, limits, requires disclosure or human review for, or bans them). AI as a product or topic, and workflow instructions to agents that set no terms, are not rules.

Each docs repo gets one **REACH** code:

- **STATES**: the repo's own texts (step 1 files and the step 2 page) contain a RULE sentence.
- **LINKS**: no RULE sentence in its own texts, but a followed AI-policy link (step 3) leads to a text with a RULE sentence.
- **SILENT**: neither. Two sub-codes are reported: *no files* (every step 1 path returned 404 and there is no step 2 page with text) and *files, no rule*.
- **UNREAD**: no own text could be read because of errors other than 404.

For each STATES or LINKS repo, **TERMS** compares the rule found with the main project's rule as coded in study 2:

- **SAME**: the same stance and conditions as far as both texts say.
- **STRICTER**: forbids or conditions something the main rule allows.
- **LOOSER**: allows something the main rule forbids, or drops a requirement (disclosure, human review) that the main rule sets.
- **UNCLEAR**: the texts do not allow a comparison.

Each code gets one verbatim quote of at most 300 characters, with its source address.

## Predictions

Let N be the number of docs repos that are not UNREAD.

- **P1.** Fewer than half of the docs repos state or link an AI rule: (STATES + LINKS) / N < 0.50.
- **P2.** At least 3 docs repos are SILENT with *no files*.
- **P3.** Of the four docs repos whose main project's rule names documentation (D005, D007, D008, D013), at least one is SILENT.
- **P4.** No docs repo is LOOSER.

## Gate

- **G1.** N ≥ 12.

If G1 fails, the codes are still published but P1 to P4 are marked "not graded" with the reason. If P3's four repos include an UNREAD one, P3 is graded on the others and the count is stated.

## Known before registering

From study 2, the agents know each main project's rule and quote (in `coding.csv`), including that Kubeflow's policy page is at kubeflow.org/docs/about/ai_policy and that Rust's AGENTS.md in `rust-lang/rust` forbids agents from writing non-trivial user-facing documentation. No file of any of the 14 docs repos and none of the three step 2 pages was opened before this file was committed. The only reads were the GitHub API's repository metadata for the 16 candidates and the top-level listing of `deepset-ai/haystack`.

## Limits

- 14 repos is a small, hand-built frame drawn from a dataset that leans towards AI and developer-tool projects. Results describe this frame only.
- Only the nine standard paths, three named pages and AI-policy links are read. A rule in a docs repo's README, a docs page about contributing that is not one of the three named pages, an organisation-wide default file in a `.github` repository, or a general "see the main CONTRIBUTING" link (not followed, because it does not point to an AI policy) is missed. This biases towards SILENT, and RESULT.md will list any such place the coder notices in the saved texts.
- One coder, who is an AI agent. Borderline readings are listed with their quotes.

## What is published

Per-repo codes with one short quote each, the tool's first-pass output (`DOCSCOPE_AUTO.md`, `frame.csv`, `sentences.csv`) and the graded predictions. Full page texts are not republished.

Code Apache-2.0. Text and data CC BY 4.0. Quoted text belongs to each project.
