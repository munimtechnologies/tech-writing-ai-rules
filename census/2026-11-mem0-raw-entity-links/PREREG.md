# Study 17 (pre-registration): do verbatim Mem0 memories get the entity boost only after an edit?

*Pre-registered 2026-11-13 ~02:10 UTC, before any run. Made with AI agents working in the name of MV2 of Munim, Inc. (mv2@munimtech.com). Text CC BY 4.0; code Apache-2.0.*

## Why

Documentation teams and docs-review agents increasingly keep style rules in an agent memory such as Mem0. A rule should be stored exactly as the team wrote it, which in Mem0 means `add(..., infer=False)`. Reading the source of Mem0 OSS 2.2.1 (`mem0/memory/main.py`, tag `v2.2.1`):

- the `infer=False` branch of `_add_to_vector_store` stores each message with `_create_memory` and returns before the extraction pipeline, so it never calls `extract_entities`, `_link_entities_for_memory` or `_upsert_entity`;
- `_update_memory` calls `_link_entities_for_memory` whenever the text changes;
- `search()` adds an entity boost (`_compute_entity_boosts`, entity matches with similarity >= 0.5) only to memories linked in the entity store.

If that reading is right, a verbatim rule gets no entity boost until someone edits it, after which it does, so editing a rule changes how it ranks for reasons unrelated to its wording. This study checks the reading on a running install. It does not judge whether the behaviour is intended.

Prior art (checked 2026-11-13 in mem0ai/mem0 issues and PRs): #7535 notes the entity boost was off in its `infer=False` repro because spaCy was not installed; #6794/#6795 cover swallowed entity-embedding failures; #7277 covers spaCy's runtime model download. None reports that `infer=False` memories are linked on update but not on add (search covered the first 14 of 46 hits for "infer=False entity"; the full list will be re-checked before any report).

## Method

Tool: `rawlink.py` 0.1.0 (Apache-2.0), job `mem0rawlink-v1`. mem0ai[nlp] 2.2.1, spaCy `en_core_web_sm`, FastEmbed `BAAI/bge-small-en-v1.5` (384 dims), local Qdrant folder, local history DB, telemetry off, no LLM (a placeholder client that fails loudly if called; calls counted).

- 20 one-sentence style rules, each naming one product or tool (GitHub, PyPI, Kubernetes, ...).
- Team A: all 20 stored with `infer=False`. Then the 10 even-numbered rules are edited with `update(id, text=original + " Reviewers check this on every page.")`.
- Team B (same collection): the same 20 *final* texts stored with `infer=False`, never edited. So both teams hold identical texts; the only difference is the edit history.
- Query per rule: "What is our rule for <entity>?", `search(..., filters={"user_id": team}, top_k=20, threshold=0.0)`. Delta = score of the rule in team A minus score of its identical twin in team B.

## Gate

The study is graded only if spaCy's model loads in Mem0 (`get_nlp_full()` is not None) and `extract_entities` finds at least one entity in at least 15 of the 20 queries. Otherwise: "not graded", reported as such.

## Predictions

- **P1:** after the 40 `infer=False` adds, the entity store links none of the 40 memories (0).
- **P2:** after the edits, at least 8 of team A's 10 edited rules are linked in the entity store, none of its 10 untouched rules, and none of team B's 20.
- **P3:** for at least 8 of the 10 edited rules, delta > 0.001 (the edited copy outscores its never-edited twin).
- **P4:** for at least 9 of the 10 untouched rules, |delta| < 0.001.

Also recorded, not graded: scores before the edit, ranks in each team, result keys, top-1 counts per team, LLM call count (expected 0).

## What would follow

- All hold: a short, disclosed note to Mem0 (after re-checking the full issue list), asking whether raw memories should be linked on add or left unlinked on update; and a section in MV2's docs-memory write-up.
- P1 or P2 fails: the source reading was wrong or version-specific; reported here as a negative result.
- Gate fails: environment problem; fix and re-run as v2.

Results will be added as `RESULT.md` in this folder, whatever they show.
