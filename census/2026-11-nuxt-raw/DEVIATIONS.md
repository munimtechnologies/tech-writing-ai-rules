# Study 15: deviations found while grading the first run

Written 2026-11-15, after the first run (`nuxtraw.py` 0.1.0) finished and before any re-run. Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: this note, the tool and its tests were made with AI. Licence: text CC BY 4.0, code Apache-2.0.

## The first run (0.1.0)

Read on 2026-11-15 between 12:57 and 13:07 UTC. Its unchanged output is in [`run-v1/`](run-v1/). The automatic grade it printed:

| | |
|---|---|
| Counted sites (G1 needs 4) | 7: nuxt.com, ui.nuxt.com, content.nuxt.com, docus.dev, i18n.nuxtjs.org, supabase.nuxtjs.org, directus.com/docs |
| Copies read | 193 |
| Copies with an empty component tag | 41 (21.2%) |
| P1 / P2 / P3 / P4 / P5 | holds / holds / holds / fails / holds |

**We are not reporting these as the study's result.** Grading turned up two errors in the tool. Both were ours, not the sites'.

## Error 1: wrappers around code counted as empty (affects P1 to P3)

The plan says tags are counted "outside fenced code". Version 0.1.0 did that by deleting fenced code before it tested whether a tag was empty. So a `<code-group>` that wraps two code blocks counted as an empty tag, even though the reader and the agent both get the code. One example, read on 2026-11-15: `content.nuxt.com/raw/docs/files/yaml.md` has a `<code-group>` around two YAML code blocks (`farnabaz.yml`, `larbish.yml`). 0.1.0 counted it as empty.

How much of the first run this touches, using its own `pages.csv`:

- 12 of the 41 flagged copies were flagged only for `<code-group>`.
- 5 more were flagged only for `tabs`, `tabs-item` or `code-preview`, which on these sites often wrap code.
- With the 12 removed, 29 of 193 copies (15.0%) remain. With all 17 removed, 24 of 193 (12.4%) remain, under P2's 15% line. So P2 depends on this error, and P3 may too (content.nuxt.com goes from 12 flagged copies to at most 7).

## Error 2: the "rendered page" was often Markdown (affects P4 and P5)

0.1.0 requested every address with `Accept: text/markdown, text/html;q=0.9`, including the live page it compared each copy with. It did not record what type came back. In 72 of the 193 rows, the ratio of copy words to "page" words is exactly 1.000, and in the rows we looked at the two word counts are identical (for example 1,166 and 1,166 on nuxt.com, 1,943 and 1,943 on ui.nuxt.com, 1,806 and 1,806 on content.nuxt.com). The likeliest explanation is that these sites negotiate content and sent Markdown to a client that asks for it first, so the tool compared the copy with Markdown, not with the rendered page. We have not confirmed this from the response headers, because 0.1.0 didn't save them. P4 and P5 from the first run measure nothing useful and are withdrawn.

## What changes in 0.2.0

The frame, sample (same seeds), eligibility, gate, predictions and hand check stay exactly as in [PREREG.md](PREREG.md). Only the measurement changes:

1. **Emptiness:** each fenced code block or inline code span inside a tag now counts as content (a placeholder word). Tags written inside code are still ignored. The 0.1.0 count is still reported per copy as `empty_tags_v1`, so the effect of the fix is visible copy by copy.
2. **The page:** the live page is now requested with `Accept: text/html,application/xhtml+xml;q=0.9,*/*;q=0.1`. Its `Content-Type` is recorded (`page_ctype`). A ratio is computed only when the answer is HTML; otherwise it's left blank. P5 now fails, rather than passing, if no ratio could be measured.
3. **Exploratory, not graded:** a third request asks the page address for `text/markdown` and records the status, the type and whether the text matches the `/raw/` copy. That shows which sites hand agents Markdown at the page's own address.

The re-run is `nuxtraw-v2`. Its results will be graded against the same predictions and published in RESULT.md, together with this note and the hand check.

## What this does to blinding

P1 to P3 are no longer blind. We saw the first run's tag names and counts before writing 0.2.0, and the fix changes which tags count. RESULT.md will say so next to each verdict. The rule we added (code inside a tag is content) follows from the plan's own definition of "empty" ("nothing but whitespace and other tags"), not from the counts. P4 and P5 were never really measured in the first run, so their 0.2.0 verdicts are the first real reading.
