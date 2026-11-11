# Study 11 pre-registration: does md-copy-check find broken Markdown copies, and how often does it cry wolf?

PREREG-ID: mdcheck-frame-2026-11

Written 2026-11-11, before any page for this study was read. The runner (`mdcheck_frame.py` 0.1.0) refuses to read a page until this file is on `main`.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name. Text CC BY 4.0, code Apache-2.0.

## Why

Study 10 found that most Markdown copies that docs sites serve to AI agents keep the page, but that a copy fails silently when the export skips a template or component. The failures it found by hand left traces in the copy: an exporter placeholder ("**Snippet** component (self-closing)"), an empty component tag (`<PriorityBoardingBanner />`), a heading with nothing under it, a copy that is only a title, a copy that is a line of MDX code. The agent skill `md-copy-check` 0.1.0 looks for such traces in a copy alone, without the page.

A checker like this is only useful if it finds most real failures and does not flag many good copies. Neither has been measured. This study measures both on study 10's frame, with predictions fixed now. It is a test of our own tool, so we write down in advance what would count against it.

Prior art: AFDocs and similar parity checkers compare a copy with its page; we found no published check that judges a copy alone, and no published false-alarm rate for one.

## Tool under test

`skills/md-copy-check/scripts/md_copy_check.py`, version 0.1.0, as on `main` when the run starts, with its default settings (`min_words` 20). The runner records its SHA-256 and stops if the version is not 0.1.0. It calls the checker's own `looks_like_markdown` and `check_text`; it changes nothing in it.

A page is **flagged** when the checker reports at least one error or warning. Info findings do not count.

## Frame

The 384 counted pages of study 10 (`census/2026-11-md-copy-parity/pages.csv`, `counted` = True), on 15 docs sites. Each page's Markdown copy is fetched again the way study 10 got it: `Accept: text/markdown` on the page URL when `method` is `accept`, or the recorded `md_url` (`Accept: text/markdown, text/plain;q=0.9, */*;q=0.1`) when it is `suffix`. One request per second; robots.txt is honoured. A page **has a copy** when the checker's `looks_like_markdown` accepts the answer.

Three groups:

- **K, known losses with a trace (7 pages).** Study 10's hand check found content lost from these copies, and the copy held a visible trace:
  - K1 Netlify, fix-a-failed-deploy (placeholder for a tip)
  - K2 Railway, networking/cdn (`<PriorityBoardingBanner />` for a beta notice)
  - K3 Docker, sbx/volume/create (copy is only a title)
  - K4 Docker, sbx/volume/rm (copy is only a title)
  - K5 New Relic, Diagnostics CLI release notes (copy is front matter and one MDX line)
  - K6 Google Cloud, ml-inference-t4 ("Project setup" heading with only `<br />` under it)
  - K7 Google Cloud, SQL Server failover cluster (a lead-in "you also need a Google Cloud project:" followed by unrelated text)
- **N, known losses without a trace (3 pages):** N1 Heroku, popsql (beta notice), N2 Datadog, path-traversal rule ("How to use this rule" section), N3 Vercel, sandbox drives (template cards).
- **O, all other counted pages (374).**

**Still broken.** For each K and N page a marker string fixed below is text that the page showed its readers and its copy lacked on 2026-11-11. A K or N page counts as still broken when its new copy is fetched and does not contain the marker (after curly quotes become straight quotes, Markdown escapes, `*`, `` ` ``, `[` and `]` are removed, and whitespace is collapsed). Pages fixed since 2026-11-11 are reported and left out of P1 to P3.

| Page | Marker |
|---|---|
| K1 | `control costs for Agent` |
| K2 | `This feature is in beta` |
| K3 | `The volume name must be unique per account` |
| K4 | `Volumes attached to active sandboxes` |
| K5 | `DotNet/Agent/Installed` |
| K6, K7 | `create a project instead of selecting an existing project` |
| N1 | `currently in beta` |
| N2 | `static-analysis.datadog.yml` |
| N3 | `Slack-based Contentful assistant` |

## Gate

- **G1:** at least 350 of the 384 pages have a copy. If G1 fails, the predictions are still graded and reported, marked as below the gate.

## Predictions

Written with the checker's known rules in mind: K7's trace is a dangling lead-in, which the checker reports only as info.

- **P1 (recall):** of the K pages still broken, the checker flags all but at most one.
- **P2 (a named blind spot):** if K7 is still broken, the checker does not flag it.
- **P3 (losses without a trace stay invisible):** of the N pages still broken, at most one is flagged.
- **P4 (noise level):** of the O pages with a copy, between 5% and 25% are flagged.
- **P5 (where the noise comes from):** among O pages, `empty-section` is the warning code on strictly the most pages.
- **P6 (warnings are mostly false alarms):** in the hand check below, fewer than half of the sampled warning-only O pages show a real loss.
- **P7 (errors are rare):** at most 5 O pages get an error.

P1 to P5 and P7 are computed by the runner. If no page in a prediction's group is still broken, that prediction is reported as not gradable.

## Hand check (for P6, and to describe errors)

The sample is every O page with an error, plus 20 O pages drawn from those with warnings but no error (Python `random.Random(20261111).sample` over those pages sorted by their row number in study 10's `pages.csv`; all of them if fewer than 20). The runner saves each sampled page's served HTML and, for each `empty-section` finding, the first 300 characters of page text after the matching heading.

One AI coder reads each error and warning on each sampled page against the live page (the saved HTML, or the page in a browser when its content is built by scripts) and codes it:

- **real:** text, a notice, a table, an image or a section that the page shows its readers at that point is missing from the copy;
- **harmless:** the page also shows nothing there (an empty API response heading, a heading for an interactive widget or a toggle), or what is missing is page furniture (feedback widgets, promotion cards, navigation).

A page counts as a real loss when at least one of its findings is real. Every code is published with a note in `hand_check.csv`. One coder, no second coder; borderline codes are marked as such.

## What is published

The runner's `pages.csv` (URL, status, word count, counts of errors, warnings and info, codes, group, marker check), `findings.csv` (code, line and at most 120 characters of the flagged line), `sample.csv`, `mdcheck_frame.json` and `MDCHECK_AUTO.md`, plus `hand_check.csv` and a RESULT.md. The copies and HTML the runner saves are the sites' text and are not republished; `context.csv` (up to 300 characters of page text per finding) is published only as far as needed to show a code.

## What would change the skill

If P4 fails above 25%, or P6 holds, the warning rules that make most false alarms get narrower or move to info in md-copy-check 0.2.0, and the SKILL.md says how noisy each code was here. If P1 fails, the trace rules missed real losses on the pages they were built from, and the skill says so plainly.
