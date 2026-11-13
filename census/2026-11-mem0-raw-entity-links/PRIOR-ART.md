# Study 17: prior-art check (completed 2026-11-13, before any result)

This note finishes the prior-art search promised in [PREREG.md](PREREG.md), which had read only the first 14 of 46 hits. It was written while the study's job (`mem0rawlink-v1`) was still waiting for compute, so no result is known yet. PREREG.md is unchanged.

Made with AI agents working for MV2 of Munim, Inc. Text: CC BY 4.0.

## Searches

| Query (GitHub issues and pull requests in mem0ai/mem0) | Hits | Read |
|---|---|---|
| `infer=False entity` | 46 | all 46 |
| `"entity boost"` | 92 | first 16 (most relevant by GitHub's ranking) |

## What was found

None of the 46 `infer=False entity` hits reports that memories added with `infer=False` are not entity-linked on add but are linked once their text is edited with `update()`, or that this changes their search ranking through the entity boost.

The closest items:

- **#4858** (merged 2026-04-16, "fix(oss): v3 entity cleanup, filter fixes, and QA hardening"). It wired entity cleanup into `_update_memory`, and its test table lists "Update cleanup (old entity unlinked, new entity linked)" for TypeScript and Python. The same PR fixed a different gap on the `infer:false` path ("`textLemmatized` missing on `infer:false` path"; "Memories added with `infer:false` had degraded BM25"), and its `infer:false` test row checks "0 LLM calls, textLemmatized populated". It does not mention entity linking on that path. So re-linking on update is designed and tested; whether raw adds were meant to skip linking is not stated there.
- **#6795** (open, TypeScript SDK) covers swallowed entity-embedding failures. It says the PR #6794 covers failures on the memory paths, including "raw writes (`infer: false`)", and that "Entity linking is deliberately not covered there, and this is that gap." That is about which failures get reported, not about whether raw adds should be linked.
- **#7535** (open) ran an `infer=False` ranking repro and says "Entity boosting is off here because spaCy is not installed."
- **#6177 / #6220 / #6170 / #6173 / #6202** are about scope ids (`user_id` and the like) being dropped on the TypeScript `infer:false` path, not entities.
- **#7277** covers the spaCy model being downloaded at runtime inside the first `add()`/`search()`.
- **#7561** (open) says metadata-only updates call the embedder needlessly; it states that "entity extraction and BM25 are not covered by this reproduction".

## What this means for the study

If predictions P1-P3 hold, the behaviour would not be a duplicate of an existing report. Any note to Mem0 will be phrased as a question (should raw memories be linked on add, or is it intended that only edited ones are?), will cite #4858 and #6795, and will say it was made with AI agents. If the predictions fail, nothing is sent and the result is published as it is.
