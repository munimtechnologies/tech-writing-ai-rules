# Result: when a project keeps its docs in a separate repo, does that repo show the project's AI rule?

Study 3 in this repository. Graded 2026-11-07 by MV2 of Munim, Inc., with AI agents working in his name. The coding and this text were made with AI. One coder, who is an AI agent.

- Pre-registration: [PREREGISTRATION.md](PREREGISTRATION.md), first committed 2026-11-06 17:25:10 UTC (commit `09dd95b9`).
- Texts read: 2026-11-07 00:12:16 to 00:13:40 UTC, by `docscope.py` 0.1.0, unchanged from study 2 and fetched from commit `44981fa`. Its offline tests passed first. The job waited 0 seconds because the pre-registration was already on `main`.
- Files: `coding.csv` (one row per docs repo: REACH, TERMS, first-pass label, borderline flag, a note and one quote of at most 300 characters with its source), plus the tool's unchanged output (`DOCSCOPE_AUTO.md`, `frame.csv`, `sentences.csv`). Page texts are not republished.

## Headline

**Only 3 of 14 separate documentation repos show an AI rule in their own contributor files, and none has a link that points to an AI policy.** Some link to a general contributor guide (see Limits). Four of the main projects' rules name documentation (Home Assistant, Kubeflow, Kubernetes and Rust). Only Home Assistant's rule appears in its docs repo, as a copy of the organisation's policy. Kubernetes and Kubeflow require AI disclosure in their main repos, but `kubernetes/website` and `kubeflow/website` never mention AI. Rust is the only project in study 2 whose rule treats documentation differently from code (agents must not write non-trivial user-facing documentation), and that rule does not appear in the Rust book's repo.

A docs contributor who reads only the docs repo's own files would not meet the AI rule in 11 of 14 cases.

## Codes

| REACH | Docs repos |
|---|---|
| STATES | 3: Home Assistant (D005), LangChain/LangGraph (D009), PostHog (D012) |
| LINKS | 0 |
| SILENT, no files | 3: AnythingLLM (D001), Hono (D006), SDL (D014) |
| SILENT, files but no rule | 8: Dify (D002), Ghostty (D003), Godot (D004), Kubeflow (D007), Kubernetes (D008), OpenHands (D010), Open WebUI (D011), Rust book (D013) |
| UNREAD | 0 |

| TERMS (STATES and LINKS only) | Docs repo | Compared with the main rule |
|---|---|---|
| SAME | Home Assistant (D005) | The repo carries the Open Home Foundation AI policy. It has the same human-in-the-loop condition and the same ban on autonomous agents as the published policy. |
| STRICTER | LangChain/LangGraph (D009) | The main rule allows AI help when every change is verified and asks for no disclosure. The docs repo also asks for a one-sentence disclosure and forbids AI attribution badges and trailers. |
| LOOSER (borderline) | PostHog (D012) | The main policy requires AI disclosure through the PR template's Agent context section. The website repo's own agent rules, which call themselves non-negotiable, do not ask for disclosure, and its PR template has no such section. |

Quotes, word for word from the saved texts:

- Home Assistant docs, `AI_POLICY.md`: "AI can be a helpful tool for writing code and documentation. However, due to the foundational open source nature of our projects, we require a human in the loop who understands the work produced by AI."
- LangChain docs, pull request template: "If an AI agent helped, say so in one plain sentence here, for example "Prepared with Claude Code." Do not add a "Generated with" badge."
- PostHog website, `AGENTS.md`: "You MAY NOT, under any circumstances, reply to a human reviewer in the stead of your user. This will result in the PR being closed."
- Ghostty website, `CONTRIBUTING.md` (the main Ghostty project requires AI disclosure): "**Note, Ghostty.org has different contributing guidelines than the Ghostty project.** They are simpler."

## Predictions

N = 14 docs repos not UNREAD.

| | Prediction | Result | |
|---|---|---|---|
| **G1** | N ≥ 12 | N = 14 | passed |
| **P1** | (STATES + LINKS) / N < 0.50 | 3 / 14 = 21% | **held** |
| **P2** | at least 3 SILENT with no files | 3 (D001, D006, D014) | **held**, at the threshold (see Limits) |
| **P3** | at least one of D005, D007, D008, D013 is SILENT | 3 of 4 (D007, D008, D013) | **held** |
| **P4** | no docs repo is LOOSER | 1 (D012, borderline) | **failed** |

**3 of 4 predictions held.** P4 failed on one borderline code. PostHog's website repo has a rule of its own for AI agents, but that rule leaves out the disclosure the main policy requires. The rubric names "drops a requirement (disclosure, human review) that the main rule sets" as LOOSER, so that is the code. If silence is read as not dropping, D012 would be UNCLEAR and P4 would hold. Both readings are reported, and the pre-registered rubric decides the grade.

## What the automatic first pass got right and wrong

The first pass agrees with the hand coding for 12 of 14 repos when STATES is matched to any rule label and SILENT to `no_ai_text`, `ai_text_no_rule_cue` or `unreachable` (all 404). It missed two:

- **D012 PostHog**: labelled `no_ai_text`. Its AI cues do not match "agent" on its own, so a rule addressed to "you, an agent" is invisible to it. This is a gap for any study of AGENTS.md files.
- **D002 Dify**: labelled `code_only` from a sentence that tells agents how to load a skill file. That is a workflow instruction and sets no terms.

The `unreachable` label means every path returned 404 (no network errors occurred). Under the rubric that is SILENT with no files, not UNREAD.

## Limits

- **14 repos, hand-built frame**, drawn from a dataset that leans towards AI and developer-tool projects. These results describe this frame only.
- **Fixed paths.** Only the nine standard paths, three named pages and AI-policy links were read. A GitHub API listing made after grading shows that **AnythingLLM's docs repo has a `pull_request_template.md` at its root**, which is outside the nine paths. Read separately, it has no AI sentence, so D001's REACH stays SILENT. It would move from *no files* to *files, no rule*, and P2 would then be 2 and fail. P2 is graded on the pre-registered definition (step 1 paths only) and held. Hono's and SDL's `.github` folders hold only workflows and build files.
- **Links not followed.** Godot's pull request template points to a content-guidelines page on contributing.godotengine.org. LangChain's CONTRIBUTING.md and Kubeflow's point to their main contributor guides. These general links were not followed, as pre-registered, because they do not point to an AI policy. A contributor who follows them may meet the main rule. So SILENT means the docs repo's own files are silent, not that the rule is out of reach.
- **Godot's step 2 page returned 404.** The pre-registered address was named before reading and was not checked beforehand.
- **Kubeflow** hosts its AI policy page on the site this repo builds, but the repo's contributor files neither name nor link it.
- **One coder, an AI agent.** Two codes are flagged borderline in `coding.csv` (D009 and D012), each with its quote and the effect of the other reading.
- **Snapshot.** Files can change at any time. Each code describes the default branch on 2026-11-07.

## What this adds

Studies of AI contribution policies (arXiv 2609.07542, 2605.16706, 2609.07919, 2606.14594) read policies one repository or one project site at a time. This is, as far as we found, the first count of whether a project's AI rule reaches the separate repository that holds its documentation. In this frame it mostly does not. In 11 of 14 docs repos, a docs or translation contributor who reads only that repo's files does not meet the rule. And where the docs repo does have its own rule, it differs from the main rule in 2 of 3 cases, once stricter and once looser.

Code Apache-2.0. Text and data CC BY 4.0. Quoted text belongs to each project.
