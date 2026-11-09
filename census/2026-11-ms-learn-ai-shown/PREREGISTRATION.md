# Study 8: does Microsoft Learn tell its readers, people and agents, that an article was made with AI? (pre-registration)

Written 2026-11-09, before any page in the sample was drawn or fetched. The tool, `learnshown.py` 0.1.0, waits until this file is on `main` before it reads anything.

## Why this study

Study 7 counts the AI-use labels (`ai-usage: ai-assisted` or `ai-generated`) in the front matter of Microsoft's public documentation repos. A label in a source file is not the same as telling a reader. Microsoft's [principles for AI-generated content](https://learn.microsoft.com/en-us/principles-for-ai-generated-content) promise readers more than a label:

> "All articles that contain any AI-generated content include text acknowledging the role of AI. You'll see this text at the end of the article."

Learn now has two kinds of reader. People get the HTML page. Agents that ask for Markdown get a Markdown copy of the same URL. Copilot Chat in VS Code, Copilot CLI, Microsoft Copilot and Claude Code all send `Accept: text/markdown` ([acceptmarkdown.com/status](https://acceptmarkdown.com/status), verified there 2026-06-22). When we fetched Learn pages with a client that asks for Markdown, Learn returned a Markdown copy with a YAML header that includes the AI label and the source file's path.

So this study asks, for a seeded sample of labelled articles: does the HTML page show the acknowledgement text, does the Markdown copy carry it, and does the Markdown copy carry the label?

**Prior art (searched 2026-11-09):** we found no check of whether Learn's AI labels reach readers. Daniel Bradley ([ourcloudnetwork.com, 2026-09-30](https://ourcloudnetwork.com/microsoft-makes-repos-for-learn-documentation-private-now-what/)) counted labels in the Entra repo, not on pages. A Microsoft Q&A thread notes "Authored with AI" marks on Learn training modules, which are outside this study. Microsoft's developer blogs use a different, top-of-page notice ("AI-assisted content. This article was partially created with the help of AI."). We found no study of Learn's Markdown copies for agents.

## What we had seen before writing the predictions

We read exactly two pages by hand. Both are excluded from the sample and kept as controls.

1. **Entra, "How to Register an App in Microsoft Entra ID"** (`MicrosoftDocs/entra-docs`, `docs/identity-platform/quickstart-register-app.md`; front matter `ai-usage: ai-assisted`). The HTML page, rendered by a reader service, shows a note near the end: "The author created this article with assistance from AI." followed by "Learn more". The Markdown copy has `ai-usage: ai-assisted` and `source_path: docs/identity-platform/quickstart-register-app.md` in its header. Its body does not contain the note, and it ends inside the "Grant admin consent" section, without the "Related content" section that the HTML page lists.
2. **Dev Box, "What is Microsoft Dev Box MCP Server?"** (`MicrosoftDocs/azure-docs`, `articles/dev-box/overview-what-is-dev-box-mcp-server.md`; the published page's header reads `ms.ai-usage: ai-generated`). Neither the HTML page nor the Markdown copy shows any sentence about AI's role in writing it. The only AI text near the article is the site-wide footer link "AI Disclaimer". The Markdown copy ends after "Authentication", without the "Next steps" section the HTML page has.

Two pages cannot separate the possible reasons for the difference: the key spelling (`ai-usage` against `ms.ai-usage`) or the value (`ai-assisted` against `ai-generated`). The strata below are drawn to separate them. We had also seen study 7's pre-registration and its frame rule, but no result of study 7 (its job had not run).

## Frame and sample

- **Repos:** study 7's frame rule, applied at run time by `learnlabels.py` 0.1.0: every public repo of the MicrosoftDocs organisation except forks, archived repos, localized copies and repos not pushed since 2026-05-01, ranked by size (largest first). Repos are read in that order (shallow, Markdown-only sparse clone) until **15 repos with at least 10 AI-labelled articles** have been read, or 30 repos have been tried. Article, AI key and category are defined as in study 7.
- **Strata** (articles only):
  - **A:** key exactly `ai-usage`, value `ai-assisted`.
  - **B:** key exactly `ai-usage`, value `ai-generated`.
  - **C:** another AI key spelling (`ms.ai-usage`, `ai.usage`, `ai_usage`, `aiusage`, any case), value `ai-assisted` or `ai-generated`.
  - **D:** an AI key whose value names AI in another form (study 7's `other-ai`). Descriptive only.
  - **U:** no AI key.
  - Articles with a non-AI value such as `human-only` are not sampled.
- **Draw:** from each read repo, up to **8 articles per stratum**. Within a stratum the pool is sorted by path, and `random.Random("study8|<repo>|<stratum>").sample` picks 8 when there are more. The two hand-read pages above are never drawn.
- **URL:** each article's en-us URL is derived from the repo's `docfx.json`: the nearest `docfx.json` above the file, the content entry with the longest matching `src`, then `build.dest` / entry `dest` / the path below `src` without `.md` (`index.md` maps to its folder). **A page counts only if a fetched form names this exact repo file as its source** (`source_path`, or the end of `original_content_git_url`, case ignored). Pages that fail that check are reported, not counted.
- **Fetching:** each page is fetched twice from learn.microsoft.com, at most one request per second, with the tool's own User-Agent and robots.txt honoured. The first request sends `Accept: text/markdown`; the second sends `Accept: text/html,application/xhtml+xml`.

## Measures

- **Acknowledgement sentence:** a sentence that matches `(created|written|generated|produced|drafted|authored|prepared) … (with|by|using|from) … (AI|artificial intelligence)` and names the article, page, content, document, documentation or topic, or one that says "AI-assisted content" or "AI-generated content". Sentences longer than 400 characters are skipped. In HTML the search runs over the visible text (scripts and styles removed, block elements split into paragraphs). In the Markdown copy it runs over the body below the header. The tool keeps only the matched sentence (at most 200 characters).
- **Label in each form:** an AI key in the Markdown copy's header, and a `<meta>` tag with an AI key name in the HTML.
- **Sections:** the level-2 headings of the source file (outside code fences), compared with the Markdown copy's level-2 headings after normalising case and punctuation.
- **Markdown served:** HTTP 200 with a `text/markdown` content type, or a body that starts with a YAML header and is not HTML.

## Gates

- **G1:** at least 100 labelled pages (strata A, B and C) counted, from at least 8 repos. If G1 fails, nothing is graded.
- **G2 (positive control):** the Entra control page's HTML, fetched by the tool, contains an acknowledgement sentence. If G2 fails, the text may be added by scripts after loading, which this tool cannot see, so P1 to P4 are not graded.
- **G3:** the Markdown copy is served for at least 90% of counted pages. If G3 fails, P4 to P6 are not graded.

## Predictions

All boundaries are inclusive and computed in integer arithmetic by `summarise` in `learnshown.py` (offline tests in `test_learnshown.py`). Each prediction also needs a minimum number of pages, or it is not graded.

- **P1:** at least 90% of counted A and B pages (key `ai-usage`) show an acknowledgement sentence in the HTML. (Needs 20.)
- **P2:** at most 20% of counted C pages (another key spelling) show one. (Needs 10.)
- **P3:** at most 5% of counted U pages (no AI key) show one. (Needs 20.)
- **P4:** of counted labelled pages (A to C) whose HTML shows the sentence and whose Markdown copy was served, at most 20% have the sentence in the Markdown copy. So agents who ask for Markdown mostly do not get the sentence people see. (Needs 20.)
- **P5:** at least 90% of counted labelled pages whose Markdown copy was served carry an AI key in its header. (Needs 20.)
- **P6:** of counted pages (any stratum) with a Markdown copy whose source file's last level-2 heading is "Next steps", "Next step" or "Related content", at least 80% lack that heading in the Markdown copy. (Needs 20.)

Descriptive, not graded: A and B separately (assisted against generated), stratum D, every acknowledgement wording found, whether the sentence appears anywhere in the raw HTML including scripts, AI `<meta>` tags in HTML, the source's last headings, and pages that could not be mapped.

## Hand check

The tool decides each measure. Afterwards we will read the matched sentence of **every** counted page that shows one in strata C, D and U, and of the first 10 in A and B (sorted by repo and path). A match is a false positive if the sentence describes something other than how the page was written (for example, a product feature that generates content). We will also open 10 counted pages with no match in A or B in a browser, to look for an acknowledgement worded in a way the pattern misses. Grades use the hand-checked values, and both the automatic and the checked values are published.

## What will be published

`RESULT.md`, the tool's `frame.csv`, `pages.csv` (repo, path, stratum, label, URL, HTTP statuses, the measures and the matched sentence; no article text, no author names), `shown.json` and `LEARNSHOWN_AUTO.md`. Data are CC BY 4.0; the code is Apache-2.0.

## Limits, stated in advance

- The tool sees the HTML as served, not after scripts run. G2 checks this on a page where a reader service showed the sentence.
- The sample comes from repos that are still public, and Microsoft plans to retire most of them by the end of December 2026. It leans towards large product documentation, as study 7 does.
- A repo file and its live page can differ, because the public repos mirror private ones. Only pages whose live source path matches are counted.
- A missing heading in the Markdown copy may be a deliberate choice (for example, moving "Next steps" to page navigation), not a loss. The study reports what is missing, not why.
- An acknowledgement worded unlike the pattern is missed. The hand check of 10 unmatched A and B pages estimates how often.
- en-us only, one fetch per form, on one day.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: this pre-registration, the tool and its tests were made with AI.
