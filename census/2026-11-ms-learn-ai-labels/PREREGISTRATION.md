# Study 7: how much of Microsoft Learn's documentation is labelled as made with AI? (pre-registration)

Written 2026-11-09, before any repository in the frame was read or counted. The tool, `learnlabels.py` 0.1.0, waits until this file is on `main` before it reads anything.

## Why this study, and why now

Microsoft publishes its product documentation on Microsoft Learn and has kept the Markdown sources in public GitHub repos under the MicrosoftDocs organisation. Two public texts make a census possible:

- Microsoft's [principles for AI-generated content](https://learn.microsoft.com/en-us/principles-for-ai-generated-content) (ms.date 2025-03-05): "All articles that contain any AI-generated content include text acknowledging the role of AI."
- The Learn-wide Copilot instructions shipped in public docs repos (for example [`MicrosoftDocs/entra-docs/.github/copilot-instructions.md`](https://github.com/MicrosoftDocs/entra-docs/blob/main/.github/copilot-instructions.md), read 2026-11-09): "All Markdown content created or substantially modified with AI assistance must include an `ai-usage` front matter entry". Its values are `ai-generated` ("AI produced the initial draft with minimal human authorship") and `ai-assisted` ("Human-directed, reviewed, and edited with AI support"), and authors should "Omit only for purely human-authored legacy content".

So every Markdown article carries, or should carry, a machine-readable statement of whether AI helped write it. The label is visible in the published page's metadata too (for example `ms.ai-usage: ai-generated` on the Dev Box MCP Server overview).

**Why now:** on 2026-09-23 Microsoft Learn [announced](https://techcommunity.microsoft.com/blog/skills-hub-blog/changes-to-microsoft-learn%e2%80%99s-public-documentation-repositories/4554909) that it "will retire most public repositories associated with product documentation" and "expects to retire the relevant repositories by the end of December 2026". Once retired, a repo "will no longer be publicly accessible or visible". This census is a dated snapshot while the sources can still be read.

**Prior art (searched 2026-11-09):** we found no count of AI labels across Microsoft's docs. The closest is a partial count for one repo: Daniel Bradley ([ourcloudnetwork.com, 2026-09-30](https://ourcloudnetwork.com/microsoft-makes-repos-for-learn-documentation-private-now-what/)) reports for the Entra docs that "568 articles have been substantially modified with AI", "12 articles are completely AI generated" and one is marked human-only, without a total or a method. Coverage of the repo closures (Office365ITPros, IT-Connect) does not count labels. Virtualization Review (January 2024) found one AI-labelled post on Microsoft's developer blogs.

**What we had seen before writing the predictions:** the Entra figures above; web-search snippets showing single files labelled `ai-generated` or `ai-assisted` in azure-docs, azure-ai-docs, azure-dev-docs, fabric-docs, cpp-docs, SupportArticles-docs, dotnet/docs and NuGet's docs; and two key variants, `ms.ai-usage` and `ai.usage`. We had also seen the first page of the organisation's repo list (names, sizes, push dates; 711 public repos on 2026-11-09). We had not counted or sampled labels in any repo.

## Questions

1. What share of Microsoft's documentation articles carries an AI label?
2. How do `ai-assisted` and `ai-generated` compare?
3. How does the labelled share change with the article's `ms.date` (the date the article was last substantially edited or reviewed)?
4. How many repos use the label at all?
5. How consistently is the convention written (key name and value)?

## Frame

All repos returned by the GitHub REST API for `orgs/MicrosoftDocs/repos?type=public` at run time, except:

- forks, archived repos and repos that are not public;
- localized copies (name ends in a locale suffix such as `.de-de`, `.zh-tw` or `.sr-latn-rs`);
- repos not pushed since 2026-05-01.

The rest are ranked by the API's `size` (largest first, ties by name). The tool reads them in that order until **30 repos with at least 200 articles each** have been read, or 50 repos have been tried. A repo with fewer than 200 articles is recorded as "too few articles" and left out of the pooled counts. A repo that cannot be cloned is recorded with its error. All eligible repos and their status go into `frame.csv`, which also records how many repos the organisation still has public on the run date.

Each repo is cloned at its default branch with `git clone --depth 1 --filter=blob:none --sparse`, with only `*.md` files and `docfx.json` checked out. Only the first 16 KB of each Markdown file are read, and only its YAML front matter is parsed. No clone is kept, and no author names are recorded.

## Definitions

- **Markdown file:** any `*.md` file outside folders whose name starts with a dot.
- **Article:** a Markdown file whose front matter has a `title` key and which is not under a folder named `includes`, `include` or `_includes`. Include files (fragments reused in articles) are counted separately.
- **AI key:** the first top-level front matter key matching `ai-usage`, `ms.ai-usage`, `ai.usage`, `ai_usage` or `aiusage` (case ignored).
- **Category** of an article: `ai-assisted` or `ai-generated` when the AI key's value is exactly that (case ignored); `other-ai` when the value contains the word "ai" in another form; `non-ai` when the key is present with any other value (such as `human-only`); unlabelled when there is no AI key.
- **AI-labelled:** `ai-assisted`, `ai-generated` or `other-ai`.
- **Year:** the year of the article's `ms.date` (MM/DD/YYYY or YYYY-MM-DD). Articles without a parsable `ms.date` get no year.
- **Canonical:** the key is exactly `ai-usage` and the category is `ai-assisted` or `ai-generated`.
- AI labels set for many files at once in `docfx.json` (`globalMetadata` or `fileMetadata`) are listed in `docfx_ai.csv` and reported, but not applied to single files.

## Gate

**G1:** at least 15 repos read and at least 20,000 articles in total. If G1 fails, the result is descriptive only and no prediction is graded.

## Predictions

All boundaries are inclusive unless stated otherwise. `learnlabels.py` computes each one exactly as written here, in its `summarise` function (offline tests in `test_learnlabels.py`).

- **P1:** between 5% and 35% of all articles in the read repos are AI-labelled.
- **P2:** `ai-assisted` articles are at least three times as many as `ai-generated` articles.
- **P3:** at least 75% of AI-labelled articles with a year have an `ms.date` in 2025 or later.
- **P4:** the AI-labelled share among articles dated 2026 is at least three times the share among articles dated 2024 or earlier (both groups need at least 100 articles; otherwise P4 is not graded). If no article dated 2024 or earlier is labelled, P4 holds when at least one 2026 article is.
- **P5:** at least 80% of the read repos have at least one AI-labelled article.
- **P6:** fewer than 10% of AI-labelled articles are non-canonical (another key name, or a value other than `ai-assisted` / `ai-generated`).

Descriptive, not graded: labelled shares by `ms.topic` (topics with at least 100 articles) and by repo; labelled include files; other AI tokens in the front matter, such as `ms.custom` values starting `ai-gen`; `docfx.json` entries; and the number of eligible and excluded repos on the run date.

## Hand check

The tool does the counting, so there is no hand coding. We will open 10 AI-labelled and 10 unlabelled rows, picked by the first rows of `labelled.csv` and `files.csv` after sorting by repo and path, on GitHub to confirm the tool read each front matter correctly, and report any misreads.

## What will be published

`RESULT.md`, the tool's `frame.csv`, `labelled.csv` (repo, path, key, value, category, year, ms.topic, other tokens; no author names), `docfx_ai.csv`, `LEARNLABELS_AUTO.md` and `census.json` (counts only). `files.csv` (every Markdown file) is published if it is under 20 MB; otherwise per-repo counts only. Data are CC BY 4.0; the code is Apache-2.0.

## Limits, stated in advance

- **A label is a statement, not a measurement.** It records what the authors declared. An unlabelled article may still have been written with AI, because legacy content is exempt and labels can be forgotten. A labelled article may be mostly human work.
- The public repos are mirrors of Microsoft's private `-pr` repos, and some may lag behind or differ from what is published.
- Microsoft has already retired smaller repos, so the frame leans towards large product documentation.
- `ms.date` is the date of the last substantial edit or review, not the creation date.
- We do not check whether the published page shows the disclosure text to readers.
- Repos outside the MicrosoftDocs organisation (for example `dotnet/docs`) are out of scope.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: this pre-registration, the tool and its tests were made with AI.
