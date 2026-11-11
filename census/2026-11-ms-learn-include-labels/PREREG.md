# Study 13 (pre-registered): do AI labels in include files reach the readers of the articles that use them?

Pre-registered on 2026-11-11, before any data for this study was read. Tool: [`includereach.py`](../../includereach.py) 0.1.0, offline tests in [`test_includereach.py`](../../test_includereach.py). It reuses study 7's `learnlabels.py` 0.1.0 (front matter, clones) and study 8's `learnshown.py` 0.2.0 (finding a page on Learn, reading it as Markdown and HTML, rendering it in headless Chromium) unchanged.

## Why

Microsoft Learn articles pull shared passages in from **include files** (`[!INCLUDE [title](path)]`). Microsoft's [principles for AI-generated content](https://learn.microsoft.com/en-us/principles-for-ai-generated-content) say that every article containing AI-generated content ends with text acknowledging AI's role, and authors mark such articles with `ai-usage: ai-assisted` or `ai-usage: ai-generated` in the article's front matter. Study 8 found that Learn shows this note for the documented key (131 of 131 sampled pages) and not for misspelled keys (0 of 33).

Some authors also put the label on **include files**. Our label check of 2026-11-11 ([census/2026-11-labelcheck](../2026-11-labelcheck/RESULT.md)) counted 262 labelled include files in four repos: `MicrosoftDocs/fabric-docs` (213), `dotnet/AspNetCore.Docs` (33), `MicrosoftDocs/entra-docs` (14) and `dotnet/docs` (2). Our own checker tells authors that such a label probably does nothing and that they should label the articles instead, but we marked that advice "not tested". This study tests it: when an article pulls in an AI-labelled include and has no label of its own, does the published page tell readers anything about AI?

We found no published test of this. Microsoft's [metadata guide](https://learn.microsoft.com/en-us/contribute/content/metadata) says metadata is set in an article's front matter or in `docfx.json`. We found no statement on whether metadata in an include file's front matter is used. Include files commonly carry their own front matter (`ms.topic: include`, author, date), so a label there looks natural to authors.

## Design

1. **Source.** Shallow, sparse clones (Markdown and `docfx.json` only) of the four repos' `main` branches. Every Markdown file's front matter is read with `learnlabels.describe_file`. Every `[!INCLUDE [..](path)]` reference (any case, with or without a space) is resolved to a repo path: relative to the including file, `~/` from the folder of the nearest `docfx.json` above it, and a leading `/` from the repo root. Anchors and queries are dropped. A target that matches a file only when case is ignored is matched to it. Nested includes are followed up to 6 levels, and cycles are cut.
2. **Labelled include:** a file under an `includes`, `include` or `_includes` folder whose front matter has an AI key with the value `ai-assisted` or `ai-generated`.
3. **Hosts:** articles (front matter with a `title`, not under an include folder) that reach at least one labelled include.
   - **H0:** the article has no AI key at all.
   - **H1:** the article has `ai-usage: ai-assisted` or `ai-usage: ai-generated` itself.
   - **HX:** any other AI key or value. Counted, not sampled.
4. **Sample.** A seeded random draw (`random.Random("study13|<repo>|<group>")`) of up to 15 H0 and 5 H1 hosts per repo. Each is found on Learn and read with `learnshown.check_page`: candidate URLs from `docfx.json`, then Learn's search API, confirmed only when the fetched page names this exact repo file as its source. It is read as Markdown (`Accept: text/markdown`), as served HTML, and rendered in headless Chromium, so text that page scripts add is seen. Study 8's positive control (the Entra quickstart "Register an application", which is labelled `ai-usage: ai-assisted`) is read the same way. Delays and robots.txt are as in study 8.
5. **Counted pages:** confirmed (`mapped = yes`), HTML status 200 and render status 200. **AI note:** study 8's sentence test (`learnshown.rendered_note`) on the rendered page text.

## Gates

- **G1:** the positive control shows the AI note when rendered. If not, P1 and P2 are not graded (the note test is broken).
- **G2:** at least 20 counted H0 pages. If not, P1 is not graded and we report the counts.

P2 needs at least 8 counted H1 pages, and P3 needs at least 20 counted H0 pages with a Markdown copy served. Otherwise they are not graded.

## Predictions

- **P1.** At most 5% of counted H0 pages show an AI note when rendered. We expect Learn to set the note from the article's own metadata only, so a label in an include file reaches no reader.
- **P2.** At least 90% of counted H1 pages show the AI note. This replicates study 8 on these repos, so a failure of P1 cannot be blamed on these repos rendering the note differently.
- **P3.** At most 5% of the Markdown copies of counted H0 pages carry an AI key in their YAML header (study 8 found the copy carries the article's own label as written), so agents reading the copy are not told either.

Not predicted, reported only: how many hosts there are, how many labelled includes no article uses, how H0 and H1 split, and how deep the include chains go. We have no published numbers to base a prediction on.

## Hand check (fixed now, done before grading)

- Every counted H0 page that **shows** a note, plus 5 counted H0 pages that do not (the first 5 in `pages.csv` order). For each, the raw article and include file are read at the commit the tool read, to confirm the article has no AI key, that the INCLUDE reference resolves to the labelled include, and that the include carries the label. Any page with a note is opened in a desktop browser.
- 5 random hosts from `hosts.csv` (seed `study13-hand`) are traced the same way, and 3 labelled includes that the tool says no article uses are searched for by file name in their repo.
- Every disagreement is reported in `RESULT.md` and `hand_check.csv`. It changes the grade only if it changes a page's counted status or note.

## Limits (known now)

- Four repos and one moment. Microsoft plans to retire most public Learn docs repos by the end of December 2026, so this may soon be impossible to repeat from outside.
- Only `[!INCLUDE]` references in Markdown are followed (not YAML or `.yml` landing pages, and not includes pulled in from other repos).
- Rendering uses headless Chromium with one user agent, in en-us.
- A missing note on an H0 page is reported as a fact about what readers see. Whether Microsoft wants such articles labelled is Microsoft's call.

## Files the run will add

`hosts.csv` (every host: repo, path, group, its own key and value, labelled includes reached, the first one and its depth; no article text), `pages.csv`, `includereach.json`, `INCLUDEREACH_AUTO.md`; then `RESULT.md`, `hand_check.csv` and a test that recomputes every figure.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the design, code and this text were made with AI. Data CC BY 4.0, code Apache-2.0.
