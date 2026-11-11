# Study 12 (pre-registration): how fast do AI-use labels change in Microsoft Learn's docs repos, before the repos go private?

Pre-registered 2026-11-11, before any data for this study was read. Made by MV2 of Munim, Inc., with AI agents working in his name. Code Apache-2.0, text and data CC BY 4.0.

## Why now

Microsoft Learn asks authors to mark Markdown made with AI help with front matter: `ai-usage: ai-assisted` or `ai-usage: ai-generated`. [Study 7](../2026-11-ms-learn-ai-labels/RESULT.md) counted those labels in the 30 largest active MicrosoftDocs repos on 2026-11-09: 6,618 of 182,133 articles (3.63%). It published every labelled file and each repo's commit. [Study 8](../2026-11-ms-learn-ai-shown/RESULT.md) found that labels with a variant key (`ms.ai-usage`, `ai.usage`) never show readers the AI note.

Microsoft [announced](https://techcommunity.microsoft.com/blog/skills-hub-blog/changes-to-microsoft-learn%e2%80%99s-public-documentation-repositories/4554909) in September 2026 that it is retiring most public product-documentation repos. It expects to finish by the end of December 2026, and retired repos "will no longer be publicly viewable". After that, nobody outside Microsoft can count these labels from source. Study 7 was one snapshot. This study adds two more while the repos are still public. That gives a measured rate at which AI-use labels are added, removed and corrected in a large docs corpus, plus a record of which repos close and when. We found no earlier measurement of either.

## Design

Tool: `learnsnap.py` 0.1.0 (this repository), built on study 7's `learnlabels.py` 0.1.0. It reuses that tool's front matter reader, label categories, org listing, frame rules and shallow, blob-filtered sparse clones, and it reads front matter only. No author names are recorded.

- **Snapshot A** is study 7's published data: `frame.csv` (129 eligible repos and each read repo's commit) and `labelled.csv`, read on 2026-11-09 at about 11:21 UTC.
- **Wave 1** runs as soon as this file is committed and a compute slot is free (expected 2026-11-11 to 11-13). **Wave 2** runs on or after 2026-12-14; the tool refuses to start it earlier.
- **Panel:** study 7's 30 read repos. Each one that is still listed (public or archived) is cloned again. For each Markdown file labelled now or labelled in A, the tool records one change: `kept`, `key-fixed` (a variant key became `ai-usage`), `label-changed`, `new-label-existing-file` (the path existed in A's commit, unlabelled), `new-label-new-file` (the path did not exist in A's commit), `label-removed` (the file is still there without an AI label) or `file-gone`. Whether a path existed in A's commit comes from `git ls-tree` of that commit, fetched without file contents. If that commit can't be fetched, new labels in that repo are `new-label-unknown-file`.
- **Breadth:** every other repo that passes study 7's frame rules today (public, not archived, not a fork or localized copy, pushed since 2026-05-01) is read once, and its articles and labels are counted. Study 7 read only the 30 largest of 129.
- **Retirement:** each of study 7's 129 eligible repos is classed `public`, `archived`, `not public` (absent from the org listing and HTTP 404 from the API: private or deleted) or `renamed to ...`.
- "Article" and "AI-labelled" mean exactly what they meant in study 7. A label counts if its key matches `(ms.)ai[-_.]usage` and its value is `ai-assisted`, `ai-generated` or another value that mentions AI.

## Gate and predictions

Every prediction is computed by `summarise()` in `learnsnap.py`. "Days" means days from 2026-11-09T11:21Z to the job's start. New labels are all three `new-label-*` kinds.

**Wave 1**

- **G1 (gate):** at least 25 of the 30 panel repos are read again, and A's commit is fetched for at least 25. If the gate fails, the predictions are reported but not graded.
- **P1:** new labels in the panel are between 5 and 60 per day (inclusive). *Pre-run estimate: about 10 to 25 a day. Study 7 found 4,641 AI-labelled articles whose `ms.date` is in 2026, about 15 for each day of the year up to 11-09. `ms.date` is the last review, so this is only a rough guide.*
- **P2:** at least half of the new labels whose file's history is known are on files that already existed in A. *Estimate: about 60%. Labels are added when existing articles are revised with AI help.*
- **P3:** labels removed (file still there, label gone) are fewer than 10% of new labels.
- **P4:** at most 10 of the files that had a variant key in A have the standard `ai-usage` key now. *No one has asked Microsoft to fix them. Study 8's note to Microsoft is drafted but has not been sent.*
- **P5:** at most 15 of study 7's 129 eligible repos are `not public` or `archived`.
- **P6:** among the non-panel repos read with at least 20 articles (at least 10 such repos needed), between 30% and 80% have at least one AI-labelled article.
- **P7:** across all non-panel repos read (at least 1,000 articles needed), between 2% and 15% of articles are AI-labelled. *Estimate: about 5 to 8%. Most smaller repos are product docs, not generated API reference, and study 7 found 8.05% without the reference repos.*

**Wave 2** (on or after 2026-12-14; compared with A, not with wave 1)

- **W2-P1:** between 25% and 95% of study 7's 129 eligible repos are `not public` or `archived`.
- **W2-P2:** new labels in the panel repos still readable are between 5 and 60 per day (graded only if at least 10 panel repos are read).
- **W2-P3:** at most 20 of the variant-key files read in wave 2 have been fixed (same condition).

## Hand check (both waves)

- 20 random `new-label-existing-file` rows and 10 random `new-label-new-file` rows: open the file at the wave's commit and at A's commit on GitHub, and confirm the label and whether the path existed.
- Every `key-fixed` and `label-removed` row if there are 30 or fewer, otherwise 30 random rows: confirm both versions.
- Every panel repo that was not read: confirm why.
- Any tool error found by the hand check is reported. A prediction whose grade changes because of it is graded on the corrected count, and the change is stated.

## Publication

`frame.csv`, `labelled.csv`, `changes.csv`, `snapshot.json` and `LEARNSNAP_AUTO.md` for each wave (in `wave1/` and `wave2/`), a hand check CSV, `RESULT.md` with every prediction graded, and a test that recomputes every grade from the published files.

## Limits known in advance

- A label is a statement, not a measurement. This study counts statements.
- A moved or renamed file shows up as `file-gone` plus a new label. The hand check estimates how often.
- A label added and then removed between two snapshots is invisible.
- Wave 2 can only read the repos that are still public. Its per-day rate covers those repos, and they may not be typical.
- The public repos may differ from what Learn publishes (study 7).
- Days are measured to the job's start, and one job reads for about 30 minutes.
