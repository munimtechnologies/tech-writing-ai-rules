# docs-ai-label-check on nine Microsoft Learn docs repos (tool check, read 2026-11-11)

This is a check of our own agent skill, [`skills/docs-ai-label-check/`](../../skills/docs-ai-label-check/SKILL.md), on real repos. It is **not a pre-registered study**: nothing was predicted in advance, and nothing here is graded. It asks two things: does the checker run cleanly on large public Learn repos, and are the hidden AI labels that studies 7 and 8 found still there two days later?

`labelcheck_repos.py` ran `scripts/ai_label_check.py` 0.1.0 unchanged over shallow, sparse clones (Markdown files and `docfx.json` only) of nine repos on 2026-11-11 from 17:06:33 to 17:07:28 UTC. Each repo's commit is in `repos.csv` and `labelcheck.json`. For `MicrosoftDocs/azure-docs` only two folders were read, `articles/sre-agent` and `articles/container-apps`, where study 7 found almost all of that repo's variant labels. The other eight repos were read whole.

## What it found

| Repo | Markdown files | `ai-usage: ai-assisted` | `ai-usage: ai-generated` | Variant key (error) | Label in an include file (info) | Other value (info) |
|---|---|---|---|---|---|---|
| MicrosoftDocs/azure-docs (two folders) | 386 | 5 | 3 | 119 `ms.ai-usage` | 0 | 0 |
| MicrosoftDocs/fabric-docs | 3,258 | 1,181 | 39 | 9 `ai.usage` | 213 | 0 |
| MicrosoftDocs/SupportArticles-docs | 7,944 | 505 | 5 | 31 `ai.usage` | 0 | 0 |
| MicrosoftDocs/dynamics-365-customer-engagement | 6,899 | 227 | 1 | 6 `ai.usage` | 0 | 0 |
| MicrosoftDocs/visualstudio-docs | 5,685 | 40 | 0 | 3 `ms.ai-usage` | 0 | 0 |
| MicrosoftDocs/entra-docs | 5,027 | 640 | 22 | 0 | 14 | 1 |
| dotnet/docs | 13,960 | 983 | 70 | 0 | 2 | 0 |
| dotnet/AspNetCore.Docs | 1,666 | 416 | 1 | 0 | 33 | 0 |
| MicrosoftDocs/PowerShell-Docs | 3,097 | 0 | 0 | 0 | 0 | 0 |
| **Total** | **47,922** | **3,997** | **141** | **168** | **262** | **1** |

- **168 articles in five repos carry an AI label under a key Learn does not act on** (122 `ms.ai-usage`, 46 `ai.usage`). Study 8 found that Learn shows its end-of-article AI note for the standard key `ai-usage` (131 of 131 sampled pages) and for neither variant (0 of 33). So these 168 articles say in their source that they were made with AI help, and their readers are not told. Every one is a one-line fix: rename the key to `ai-usage`. The checker's `--fix --write` does exactly that and nothing else.
- **No hidden label of the other kinds** turned up in these nine repos: no nested or commented label, no duplicate key, no misspelled or empty value and no stray AI token. Study 7's 23 labels that YAML cannot see were not found here; this check does not say where they are now.
- **262 labels sit in include files** (files under an `includes` folder that are pulled into articles). Learn's note is set per article, and we have not tested whether a label in an include file shows anything. The checker reports these as info, not errors.
- **One article uses a value Microsoft's instructions do not name**: `ai-usage: human-only` in entra-docs' SSH server administration article. Reported as info only.
- The checker ran on 47,922 Markdown files in 55 seconds and every repo was read.

## Two days after study 7

Study 7 read the same repos on 2026-11-09. Compared with it:

- **No variant label was corrected.** fabric-docs (9), SupportArticles-docs (31), dynamics-365-customer-engagement (6) and visualstudio-docs (3) have the same counts, and the same three visualstudio-docs files. In azure-docs' two folders, `sre-agent` still has 114.
- **Two new articles repeat the mistake.** `articles/container-apps/migrate-overview.md` and `articles/container-apps/migrate-azure-migrate.md` are not in study 7's list of every Markdown file in the repo, and both are labelled `ms.ai-usage: ai-assisted` (the first is dated 11/09/2026). So `azure-docs`' two folders went from 117 to 119. The spelling is still being copied into new articles, most likely from neighbouring files.

Counts were compared per repo and, for `container-apps` and `visualstudio-docs`, file by file; other files were not matched one by one.

## Hand check

Eight findings were read by hand on 2026-11-11 in the raw files at the commits the checker read (two also in Learn's live Markdown copy): one or two per repo with an error, plus the one `other-value`. All eight agree with the checker on key and value, and the seven whose line we counted agree on the line too. See `hand_check.csv`.

## Limits

- A tool check, not a study: no predictions, one reader (the checker), one moment.
- `azure-docs` was read in two folders only; study 7 also counted two variant labels in its `dev-box` folder and one in another repo, which this check did not read.
- The claim that readers see no note rests on study 8's sample of 33 variant-key pages (rendered in headless Chromium, and 5 more in a desktop browser), not on rendering these 168 pages again.
- Whether a label in an include file should show a note is Microsoft's call; we only report where the labels are.
- Microsoft plans to retire most public product-documentation repos by the end of December 2026, so this check may soon be impossible to repeat from outside.

## Files

- `repos.csv`, `findings.csv` (paths, line numbers, keys and values only; no article text), `labelcheck.json` and `LABELCHECK_AUTO.md`: the script's unchanged output.
- `hand_check.csv`: the eight findings read by hand.
- `../../test_labelcheck_result.py` recomputes every count in this file from `findings.csv` and `repos.csv` and checks the hand check against `findings.csv` (`python -m unittest -v test_labelcheck_result`).

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the checker, the run, the hand check and this text were made with AI. Data CC BY 4.0, code Apache-2.0.
