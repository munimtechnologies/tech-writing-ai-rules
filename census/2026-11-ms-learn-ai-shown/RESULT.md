# Study 8 result: does Microsoft Learn tell its readers, people and agents, that an article was made with AI?

Read 2026-11-10 13:46 to 14:36 UTC by `learnshown.py` 0.2.0 with `--render`, 22 minutes after [amendment 1](AMENDMENT-1.md) was committed (2026-11-10 13:24 UTC, commit `edd768a`). The [pre-registration](PREREGISTRATION.md) was committed on 2026-11-09. Graded 2026-11-10. The tool computed the gates and the six predictions as pre-registered; the hand check changed one automatic match (in stratum U) and no verdict.

## Summary

Microsoft's [principles for AI-generated content](https://learn.microsoft.com/en-us/principles-for-ai-generated-content) promise: "All articles that contain any AI-generated content include text acknowledging the role of AI. You'll see this text at the end of the article." Authors mark such articles in the source with a front matter label, `ai-usage: ai-assisted` or `ai-usage: ai-generated` ([study 7](../2026-11-ms-learn-ai-labels/RESULT.md) counted them).

- **Every sampled page labelled the standard way shows the note to people: 131 of 131.** Pages labelled `ai-assisted` end with "Note: The author created this article with assistance from AI." (99 of 99), and pages labelled `ai-generated` with "Note: This article contains content created with AI." (32 of 32).
- **No sampled page whose label is spelled differently shows it: 0 of 33.** These pages use `ms.ai-usage` (11) or `ai.usage` (22), all with the value `ai-assisted`, in Azure (mostly SRE Agent), Fabric, Dynamics 365 Customer Engagement, Visual Studio and the support articles. Their HTML carries the label in a `<meta>` tag with the same spelling (33 of 33), so the label reaches the page, but no note is shown. The Dev Box control page (`ms.ai-usage: ai-generated`, read before the pre-registration) shows none either, so the spelling, not the value, decides. Study 7 counted 169 articles with these spellings in the 30 largest repos; if the pattern holds for all of them, about 2.6% of labelled articles are shown to readers without the promised note.
- **The note is not in the page Learn serves: 0 of 263 counted pages have it in the served HTML**, not even inside scripts. It appears only after page scripts run (rendered in headless Chromium). A reader or tool that does not run scripts, such as a crawler or an agent that fetches the HTML, does not get it.
- **Agents that ask for Markdown get the label but not the note.** Learn served a Markdown copy for 263 of 263 counted pages. 164 of 164 labelled copies carry the AI key in their YAML header; 0 of 131 copies of pages that show the note to people carry the note.
- **The Markdown copy drops the article's last section.** Of 131 counted pages whose source ends with "Next steps", "Next step" or "Related content", 130 copies lack that heading.

**All three gates passed and all six predictions held.**

## Gates and predictions

| | Pre-registered | Result | Held |
|---|---|---|---|
| G1 | ≥ 100 labelled pages (A to C) counted, from ≥ 8 repos | 164 pages from 15 repos | passed |
| G2 | the Entra control page shows the note (rendered, amendment 1) | "Note: The author created this article with assistance from AI." | passed |
| G3 | Markdown copy served for ≥ 90% of counted pages | 263 / 263 = 100% | passed |
| P1 | ≥ 90% of A and B pages (key `ai-usage`) show the note | 131 / 131 = 100% | yes |
| P2 | ≤ 20% of C pages (another key spelling) show it | 0 / 33 = 0% | yes |
| P3 | ≤ 5% of U pages (no AI key) show it | 0 / 99 = 0% (tool: 1 / 99; one false positive) | yes |
| P4 | ≤ 20% of labelled pages that show the note carry it in the Markdown copy | 0 / 131 = 0% | yes |
| P5 | ≥ 90% of labelled Markdown copies carry an AI key in the header | 164 / 164 = 100% | yes |
| P6 | ≥ 80% of copies whose source ends with Next steps / Related content lack that heading | 130 / 131 = 99.2% | yes |

P1 to P4 are graded on the rendered page, as amendment 1 set out before any page was rendered. On the served HTML (the pre-registration's first measure, now descriptive) no page in any stratum shows the note, so P1 would have failed on it, which is why G2 failed in the first run. The one page that kept its last heading is `articles/durable-task/scheduler/quickstart-work-item-filtering-durable-task.md` in `azure-docs`.

## By stratum

| Stratum | Sampled | Counted | Note shown (rendered) | Note in served HTML | AI `<meta>` in HTML | Note in Markdown copy | AI key in Markdown header |
|---|---|---|---|---|---|---|---|
| A: `ai-usage: ai-assisted` | 120 | 99 | 99 | 0 | 99 | 0 | 99 |
| B: `ai-usage: ai-generated` | 41 | 32 | 32 | 0 | 32 | 0 | 32 |
| C: `ms.ai-usage` / `ai.usage` | 34 | 33 | 0 | 0 | 33 | 0 | 33 |
| D: other AI value | 0 | 0 | | | | | |
| U: no AI key | 120 | 99 | 0 (tool: 1) | 0 | 0 | 0 (tool: 1) | 0 |

Stratum C by repo (counted): `azure-docs` 8 (`ms.ai-usage`; 7 in SRE Agent, 1 in Container Apps), `fabric-docs` 8, `SupportArticles-docs` 8 and `dynamics-365-customer-engagement` 6 (all `ai.usage`), `visualstudio-docs` 3 (`ms.ai-usage`). No repo in the sample had stratum D articles.

## Hand check

As pre-registered (`hand_check.csv`):

- **Every matched sentence in C, D and U.** C and D had none. U had one: on the Architecture Center's "Data science and machine learning" guide, the tool matched "Content Safety An AI service that detects harmful user-generated and AI-generated content." It is a table row describing the Azure AI Content Safety service, not a note about how the page was written, so it is a **false positive**. P3 is graded on 0 of 99 (the tool's 1 of 99 also held). The same row was the one U match in the Markdown copy.
- **The first 10 matched pages in A and B** (sorted by repo and path, all in `SupportArticles-docs`): each matched sentence is Microsoft's standard note, which says how the article was made. All 10 are true positives. All 131 A and B matches are one of the two standard sentences, word for word.
- **10 counted A or B pages with no match, opened in a browser:** there were none, because all 131 matched.

Not pre-registered: we tried to confirm a few pages with a rendering reader service (r.jina.ai) on 2026-11-10. It showed the note on the Entra control page and on none of 3 C pages, but it also showed no note on 4 A and B pages that the tool's browser saw it on, because for most Learn pages it now returned the article without the page's end matter. So it cannot confirm or contradict the result, and we do not count it. A check of C pages in an ordinary desktop browser is planned and will be added here.

## URL mapping

Amendment 1's candidate rules confirmed 263 of 315 sampled files (breadcrumb base 236, breadcrumb root 16, Learn search 11). 52 were not confirmed and are not counted: for 47, no candidate was confirmed and the first gave HTTP 404 (19 in `powerapps-docs`, 14 in `sql-docs`, 14 in `azure-monitor-docs`; their Learn paths, such as `/sql/` and `/azure/azure-monitor/`, differ from the paths the rules built, and the title search did not confirm them), and 5 Microsoft 365 Copilot files led to pages that name a different source file (their old URLs redirect to other articles). Every one of the 15 repos still has labelled pages counted.

## What this means

- **For Microsoft:** the reader-facing note appears to follow the exact key name. A label written `ms.ai-usage` or `ai.usage` reaches the page's metadata, but readers see no note. Renaming the key to `ai-usage` in the affected articles would most likely bring the note back. That is our inference from the pattern; we did not read Learn's page scripts.
- **For agents and their users:** an agent that asks Learn for Markdown can tell from the header that an article was made with AI help (`ai-usage` or the variant key), but the sentence a person sees is not in the text it reads, and the article's "Next steps" or "Related content" links are usually gone too.
- **For other docs sites:** study 9 found no other company docs site that labels pages at all. Learn's system works for the canonical label, and fails silently for a spelling variant.

## Limits

- One sample, one day, en-us only. The sample leans towards the largest repos, as study 7's frame does, and 52 sampled files could not be mapped to live pages.
- All 33 C pages were `ai-assisted`; the only `ai-generated` page with a variant key is the Dev Box control, read before the pre-registration. That the value does not matter rests on that one page.
- Rendering depends on Learn's scripts and on timing (load, network quiet up to 15 seconds, scroll, 2 more seconds). A note added later, or only after a click, would be missed. The positive control and the 131 A and B pages show that the wait was long enough for the standard note.
- The 169 figure comes from study 7's snapshot of 2026-11-09; this study sampled 33 of them.
- A missing heading in the Markdown copy may be a deliberate choice, not a loss. We report what is missing, not why.
- Microsoft plans to retire most of these public repos by the end of December 2026, so the source side of this check may not be repeatable from the same repos.

## Files

- `RESULT.md` (this file), `PREREGISTRATION.md` and `AMENDMENT-1.md`.
- `pages.csv`: one row per sampled file and the two controls: repo, path, stratum, label, URL, the rule that found it, HTTP statuses, mapping, the label in each form, the matched note (at most 200 characters) in served HTML, rendered page and Markdown copy, and the heading checks. No article text and no author names.
- `frame.csv`: every eligible repo with its commit, its counts per stratum and how many files were sampled.
- `shown.json` and `LEARNSHOWN_AUTO.md`: the tool's own output, unchanged.
- `hand_check.csv`: the pre-registered hand check, one row per sentence read.
- `../../test_study8_result.py` recomputes the gates and predictions from `pages.csv` and `hand_check.csv`, checks them against `shown.json` and the table above, and checks that the hand check covers the pre-registered rows.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the tool, the hand check and this text were made with AI. Data CC BY 4.0, code Apache-2.0. The notes quoted are Microsoft's; no article text is republished.
