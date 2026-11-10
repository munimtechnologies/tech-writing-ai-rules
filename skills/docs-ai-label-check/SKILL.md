---
name: docs-ai-label-check
description: Check the AI-usage label in Microsoft Learn style (DocFX) Markdown front matter before you commit docs that AI helped write or edit. Microsoft asks for a top-level `ai-usage` entry with the value `ai-assisted` or `ai-generated`, and Learn then shows readers a note at the end of the article. A 2026 study found that pages labelled with another spelling (`ms.ai-usage`, `ai.usage`) show no note at all, and labels nested under `ms.custom` or left in a YAML comment are never read. Use when you create or edit articles in a MicrosoftDocs, dotnet/docs or other Learn-published repo, review such a pull request, or audit a docs repo's AI labels. Ships an offline checker that finds variant keys, nested or commented labels, odd values and (with --require) unlabelled articles, and can fix the safe cases.
license: Apache-2.0
metadata:
  author: MV2 of Munim, Inc.
  version: "0.1.0"
  source: https://github.com/munimtechnologies/tech-writing-ai-rules
---

# Docs AI label check (Microsoft Learn front matter)

Microsoft Learn promises readers: "All articles that contain any AI-generated content include text acknowledging the role of AI. You'll see this text at the end of the article." ([principles for AI-generated content](https://learn.microsoft.com/en-us/principles-for-ai-generated-content)). The Copilot instructions shipped in Microsoft's public docs repos (for example [`MicrosoftDocs/entra-docs/.github/copilot-instructions.md`](https://github.com/MicrosoftDocs/entra-docs/blob/main/.github/copilot-instructions.md)) say how: "All Markdown content created or substantially modified with AI assistance must include an `ai-usage` front matter entry", with the value `ai-generated` ("AI produced the initial draft with minimal human authorship") or `ai-assisted` ("Human-directed, reviewed, and edited with AI support").

The note follows the exact key. What two pre-registered studies in [tech-writing-ai-rules](https://github.com/munimtechnologies/tech-writing-ai-rules) found:

- **Study 8** (read 2026-11-10, [result](https://github.com/munimtechnologies/tech-writing-ai-rules/blob/main/census/2026-11-ms-learn-ai-shown/RESULT.md)): 131 of 131 sampled pages labelled `ai-usage` showed readers the note ("The author created this article with assistance from AI." or "This article contains content created with AI."). **0 of 33 pages labelled `ms.ai-usage` or `ai.usage` showed it**, although the label reached each page's `<meta>` tags. A desktop browser check of 8 pages agreed.
- **Study 7** (read 2026-11-09, [result](https://github.com/munimtechnologies/tech-writing-ai-rules/blob/main/census/2026-11-ms-learn-ai-labels/RESULT.md)): in 30 large MicrosoftDocs repos, 169 of 6,618 labelled articles used a variant key, and 23 more put the label where YAML does not read it as a key (nested under `ms.custom`, or in a `#` comment).

So a label that is spelled or placed slightly wrong fails silently: the build passes, and readers never see the note.

## Steps

1. **If AI helped write or substantially edit an article, label it** at the top level of its front matter, with exactly one of the two values (lower case):

   ```yaml
   ---
   title: ...
   ms.date: 11/10/2026
   ai-usage: ai-assisted
   ---
   ```

   Pick `ai-generated` only if AI produced the first draft with little human authorship. Follow the repo's own instructions (`.github/copilot-instructions.md`, contributor guide) where they say more.
2. **Run the checker** on the files you changed (or the whole repo):

   ```
   python scripts/ai_label_check.py articles/my-article.md --require
   python scripts/ai_label_check.py . --json
   ```

   `--require` also reports changed articles that have no label at all. Without it, unlabelled files are not reported (most human-written articles have none, and that is correct).
3. **Fix what it reports.** `--fix` shows the safe fixes (rename a variant key to `ai-usage`, correct the case or spacing of a value), and `--fix --write` applies them, changing nothing else in the file. Nested and commented labels are never fixed automatically: ask the user whether the label is meant, then move it to a top-level `ai-usage:` line.
4. **Do not touch other people's labels without asking.** In a repo you do not own, report variant keys to the user or in the pull request; do not mass-rename them in an unrelated change.
5. **After publishing, check the live page** (optional, network):

   ```
   python scripts/ai_label_check.py --url https://learn.microsoft.com/en-us/<path>
   ```

   This asks the page for its Markdown copy (`Accept: text/markdown`), whose YAML header carries the label as authored. The note itself is added by the page's scripts. It is in neither the served HTML nor the Markdown copy, so to see it, open the page in a browser and scroll to just above "Additional resources".

## Findings

| Code | Severity | Meaning |
|---|---|---|
| `variant-key` | error | An AI key spelled other than `ai-usage` (`ms.ai-usage`, `ai.usage`, `AI-usage`, `ai_usage`, ...). Fixable when the value is valid. |
| `bad-value` | error / warning | `ai-usage` with a value that is not exactly `ai-assisted` or `ai-generated`. An error with a fix when only case or spacing is off (`AI-Assisted`, `ai generated`); a warning otherwise. |
| `empty-value` | warning | The key with no value. |
| `other-value` | info | A non-AI value such as `human-only`. No note is expected. |
| `duplicate-key` | warning | Both `ai-usage` and a variant are set. Remove the variant. |
| `nested` | warning | An AI key that is not top level (indented, or a list item under `ms.custom`). |
| `commented` | warning | An AI key inside a YAML `#` comment. |
| `stray-token` | warning | `ai-assisted` or `ai-generated` elsewhere in the front matter (outside title, description and keywords) with no top-level label. |
| `missing` | error | With `--require`: an article with no label. |
| `include-label` | info | A label in an include file. Learn labels articles, so label the articles that use it (not tested). |

`docfx.json` files are checked too: AI keys set in `globalMetadata` or `fileMetadata` get the same key and value checks. Exit codes: `0` no error or warning, `1` at least one, `2` usage error. `--json` prints every finding with path, line, key, value and fix. Python 3 standard library only, and no network unless `--url` is given.

## Limits

- **Measured on Microsoft Learn only, on one day.** Study 8 tested `ms.ai-usage` and `ai.usage`, all with the value `ai-assisted` (plus one `ai-generated` control page). Other variant spellings, odd values, nested and commented labels and include files were not tested on rendered pages. The checker flags them because they are not the documented form, not because their failure was observed.
- Learn's behaviour can change. If Microsoft starts reading the variant keys, the `variant-key` finding becomes advice to follow the documented spelling, nothing more.
- Only Markdown front matter and `docfx.json` are read. YAML pages (`.yml`, which hold metadata under a `metadata:` block) are skipped.
- Microsoft said in September 2026 that it will retire most public docs repos by the end of December 2026. The rule and the checker still apply wherever Learn articles are written.

## Licence

Code Apache-2.0. Quoted text belongs to Microsoft. Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the studies, this skill and its code were made with AI.
