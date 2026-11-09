# Study 7 result: how much of Microsoft Learn's documentation is labelled as made with AI?

Read 2026-11-09 11:18 to 11:24 UTC by `learnlabels.py` 0.1.0, almost ten hours after the [pre-registration](PREREGISTRATION.md) was first committed (2026-11-09 01:24 UTC, commit `33c984e`). Graded 2026-11-09. The tool computed the gate and the six predictions exactly as pre-registered. We checked 20 rows by hand, as the pre-registration says.

## Summary

- **3.63% of the articles read carry an AI label: 6,618 of 182,133** articles in 30 of Microsoft's largest public documentation repos (snapshot of 2026-11-09).
- **Almost all labels are `ai-assisted`**: 6,362 against 256 `ai-generated` (25 to 1). Four articles carry a key with another value: one says `human-only`, three have an empty value.
- **The labels are new.** 99.0% of labelled articles have an `ms.date` in 2025 or 2026. Among articles dated 2026, 7.73% are labelled; among articles dated 2024 or earlier, 0.07% are (66 of 96,009).
- **Nine of the 30 repos have no label at all.** Six of them are generated API reference (the Win32 `sdk-api` repo alone has 65,890 articles, the Microsoft Graph PowerShell reference 27,344). Together the nine hold 101,196 articles, 56% of everything read.
- **A few repos carry most labels.** Minecraft Creator (1,542 labelled, 36% of its articles), Fabric (1,015, 36%) and Azure (852, 6%) hold 52% of all labels. `azure-dev-docs` holds 148 of the 256 `ai-generated` articles (58%).
- **169 labelled articles (2.6%) use another key name than `ai-usage`**: `ms.ai-usage` (122, of which about 114 are in Azure SRE Agent's docs) and `ai.usage` (47, mostly support articles). Study 8 checks whether the spelling changes what readers see.
- **23 articles state AI use in the wrong place** and so count as unlabelled: 22 hold `ai-assisted` and one `ai-generated` somewhere other than a top-level key. We read two: one nests `ai-usage: ai-assisted` as a list item under `ms.custom`, the other has `# ai-usage: ai-generated` as a YAML comment. A YAML parser sees neither.

**Gate G1 passed** (30 repos, 182,133 articles). **Predictions: P2, P3, P4 and P6 held; P1 and P5 did not.**

## Predictions

| | Pre-registered | Result | Held |
|---|---|---|---|
| G1 | ≥ 15 repos read and ≥ 20,000 articles | 30 repos, 182,133 articles | passed |
| P1 | 5% to 35% of articles are AI-labelled | 6,618 / 182,133 = 3.63% | **no** |
| P2 | `ai-assisted` ≥ 3 × `ai-generated` | 6,362 vs 256 (24.9 ×) | yes |
| P3 | ≥ 75% of labelled articles with a year are dated 2025 or later | 6,552 / 6,618 = 99.0% | yes |
| P4 | labelled share among 2026 articles ≥ 3 × share among ≤ 2024 articles | 7.73% (n = 60,046) vs 0.07% (n = 96,009), 112 × | yes |
| P5 | ≥ 80% of read repos have a labelled article | 21 / 30 = 70.0% | **no** |
| P6 | < 10% of labelled articles are non-canonical | 169 / 6,618 = 2.55% | yes |

**Why P1 and P5 failed.** We did not expect so much of the frame to be generated reference. The frame ranks repos by size, and the largest include API reference produced from source code (Win32, Graph PowerShell, and the Java, .NET, Python and Node.js SDK references). These six repos hold 99,909 articles and no label. Microsoft's instruction covers Markdown "created or substantially modified with AI assistance"; text generated from code by other tools is outside it, so these zeros are expected under the rule, not a sign that it is ignored. The other three repos with no label are Microsoft Teams developer docs (330 articles), Dynamics 365 Mixed Reality (248) and Microsoft Edge developer docs (709).

**Not a grade, added after seeing the data:** leaving out the six generated-reference repos, 8.05% of the remaining 82,224 articles are labelled and 21 of 24 repos (88%) have a label. This is post hoc and does not change the grades above.

## By `ms.date` year

| Year | Articles | AI-labelled | % |
|---|---|---|---|
| 2016 and earlier | 3,075 | 0 | 0.00 |
| 2017 | 6,824 | 2 | 0.03 |
| 2018 | 53,446 | 2 | 0.00 |
| 2019 | 3,156 | 0 | 0.00 |
| 2020 | 2,182 | 1 | 0.05 |
| 2021 | 2,615 | 2 | 0.08 |
| 2022 | 7,060 | 4 | 0.06 |
| 2023 | 7,720 | 16 | 0.21 |
| 2024 | 9,931 | 39 | 0.39 |
| 2025 | 21,443 | 1,911 | 8.91 |
| 2026 | 60,046 | 4,641 | 7.73 |
| no date | 4,635 | 0 | 0.00 |

`ms.date` is the date of the last substantial edit or review, not the date an article was first written. 2018's large count is mostly the Win32 reference. The few labelled articles with old dates are most likely articles whose `ms.date` was not updated when the label was added.

## By repo (all 31 tried)

| Repo | Articles | AI-labelled | % | assisted | generated |
|---|---|---|---|---|---|
| azure-docs | 13,715 | 852 | 6.2 | 832 | 20 |
| learn | (too few articles: its 14,650 Markdown files have no `title`) | | | | |
| fabric-docs | 2,822 | 1,015 | 36.0 | 976 | 39 |
| azure-docs-sdk-java | 1,426 | 0 | 0 | 0 | 0 |
| microsoftgraph-docs-powershell | 27,344 | 0 | 0 | 0 | 0 |
| azure-docs-sdk-dotnet | 1,872 | 0 | 0 | 0 | 0 |
| entra-docs | 4,428 | 646 | 14.6 | 624 | 22 |
| microsoft-365-docs | 1,246 | 56 | 4.5 | 55 | 1 |
| dynamics-365-customer-engagement | 4,893 | 234 | 4.8 | 233 | 1 |
| msteams-docs | 330 | 0 | 0 | 0 | 0 |
| powerapps-docs | 2,881 | 103 | 3.6 | 97 | 6 |
| dynamics-365-unified-operations-public | 6,351 | 154 | 2.4 | 154 | 0 |
| dynamics-365-mixed-reality | 248 | 0 | 0 | 0 | 0 |
| architecture-center | 313 | 105 | 33.5 | 104 | 1 |
| windows-dev-docs | 2,160 | 1 | 0.0 | 1 | 0 |
| visualstudio-docs | 5,440 | 43 | 0.8 | 43 | 0 |
| azure-docs-sdk-python | 1,718 | 0 | 0 | 0 | 0 |
| sql-docs | 13,624 | 459 | 3.4 | 456 | 3 |
| azure-monitor-docs | 2,735 | 286 | 10.5 | 286 | 0 |
| azure-stack-docs | 1,217 | 40 | 3.3 | 40 | 0 |
| edge-developer | 709 | 0 | 0 | 0 | 0 |
| minecraft-creator | 4,251 | 1,542 | 36.3 | 1,542 | 0 |
| SupportArticles-docs | 7,823 | 519 | 6.6 | 513 | 6 |
| sdk-api | 65,890 | 0 | 0 | 0 | 0 |
| cloud-adoption-framework | 215 | 26 | 12.1 | 26 | 0 |
| windowsserverdocs | 2,568 | 118 | 4.6 | 110 | 8 |
| power-platform | 1,317 | 60 | 4.6 | 60 | 0 |
| azure-compute-docs | 1,407 | 117 | 8.3 | 116 | 1 |
| azure-docs-sdk-node | 1,659 | 0 | 0 | 0 | 0 |
| power-automate-docs | 728 | 1 | 0.1 | 1 | 0 |
| azure-dev-docs | 803 | 241 | 30.0 | 93 | 148 |

All repos are under `github.com/MicrosoftDocs/`. `frame.csv` gives each repo's commit, so every count can be checked against the exact tree read.

**Frame:** the organisation listed 711 public repos on 2026-11-09. 399 are archived, 144 were not pushed since 2026-05-01, 29 are localized copies and 10 are forks, which leaves 129 eligible. The 31 largest were read until 30 had at least 200 articles. No repo set the label for many files at once in `docfx.json` (`docfx_ai.csv` is empty).

## By article type (`ms.topic`, at least 1,000 articles)

| ms.topic | Articles | AI-labelled | % |
|---|---|---|---|
| quickstart | 1,334 | 152 | 11.4 |
| tutorial | 2,048 | 221 | 10.8 |
| concept-article | 10,014 | 1,059 | 10.6 |
| overview | 3,925 | 366 | 9.3 |
| how-to | 25,163 | 2,014 | 8.0 |
| troubleshooting | 5,349 | 379 | 7.1 |
| article | 4,764 | 112 | 2.4 |
| (none) | 98,699 | 1,699 | 1.7 |
| reference | 20,935 | 260 | 1.2 |
| generated-reference | 4,245 | 1 | 0.0 |

Smaller types with high shares: best-practice 15.9% (73 of 460), get-started 9.2%, sample 8.6%. Learning and task content is labelled most often, reference least.

## Other AI marks in the front matter (descriptive)

- **`ms.custom` tokens starting `ai-gen`** appear in 465 articles: `ai-gen-docs-bap` (457 files in all), `ai-gen-description` (220), `ai-gen-desc` (183) and `ai-gen-title` (102). **366 of these articles have no AI label.** 150 are in Dynamics 365 Customer Engagement and 50 in Azure. We found no public definition of these tokens. Their names suggest that AI wrote the article's title or description metadata, which Microsoft's rule may or may not count as "content". We report them and do not count them as labels.
- **Misplaced labels:** 22 articles without a top-level AI key hold `ai-assisted`, and one holds `ai-generated`, elsewhere in the front matter. The two we read are described in the summary.
- **Include files** (fragments reused across articles) carry 270 labels. They are counted separately and are not in the article totals.

## Hand check

As pre-registered, we opened the first 10 AI-labelled rows of `labelled.csv` and the first 10 unlabelled articles of `files.csv` (both sorted by repo and path, all in `azure-docs`) on GitHub on 2026-11-09. **All 20 match the tool**: the AI key and value, or its absence, the `ms.date` year and the `ms.topic`. The labelled rows were nine `ai-assisted` articles in API Center, API Management and Azure AD B2C, and one `ai-generated` one (`articles/api-management/secure-api-management.md`). The unlabelled rows were Azure AD B2C articles dated 2023 to 2025. No misreads.

## How this compares

The only earlier count we found is Daniel Bradley's for one repo ([ourcloudnetwork.com, 2026-09-30](https://ourcloudnetwork.com/microsoft-makes-repos-for-learn-documentation-private-now-what/)): in the Entra docs, 568 articles "substantially modified with AI", 12 "completely AI generated" and one marked human-only. We count 624 `ai-assisted` and 22 `ai-generated` Entra articles on 2026-11-09. His method is not stated, so the two numbers may not be comparable.

## Limits

- **A label is a statement, not a measurement.** It records what authors declared. Unlabelled articles may have been written with AI, because legacy content is exempt and labels can be forgotten or misplaced (23 were). Labelled articles may be mostly human work.
- The frame is the largest active repos, so it leans towards big product docs and generated reference. It is not all of Microsoft Learn, and repos outside the MicrosoftDocs organisation (such as `dotnet/docs`) are out of scope.
- The public repos mirror Microsoft's private repos and may lag behind or differ from what is published.
- `ms.date` is a last-reviewed date, not a creation date.
- This study does not check whether the published page tells readers. Study 8 does.
- One snapshot on one day. Microsoft plans to retire most of these repos by the end of December 2026, so this count may not be repeatable from the same source.

## Files

- `RESULT.md` (this file) and `PREREGISTRATION.md`.
- `frame.csv`: every eligible repo with its status, commit and counts.
- `labelled.csv`: one row per AI-labelled Markdown file (repo, path, key, value, category, year, `ms.topic`, other tokens). No author names.
- `docfx_ai.csv`: `docfx.json` AI entries (none were found).
- `LEARNLABELS_AUTO.md` and `census.json`: the tool's own output, unchanged (counts only).
- `files.csv` (every Markdown file, about 199,000 rows) is not published. The pre-registration publishes it only if it is under 20 MB, and at roughly 100 bytes a row it is about that size, so we could not confirm it is under. `learnlabels.py` reproduces it while the repos stay public; the per-repo counts are in `frame.csv`.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the tool, the hand check and this text were made with AI. Data CC BY 4.0, code Apache-2.0. Front matter values belong to Microsoft's documentation; no article text is republished.
