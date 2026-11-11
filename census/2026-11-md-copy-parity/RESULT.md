# Study 10 result: do the Markdown copies docs sites serve to AI agents keep what the page shows people?

Read 2026-11-11 00:05 to 00:25 UTC by `mdparity.py` 0.1.0, six hours after the [pre-registration](PREREGISTRATION.md) was committed (2026-11-10 18:02 UTC, commit `06301e8`). Hand check and grading on 2026-11-11. The frame files were read from commit `af74d23`, as pre-registered (SHA-256 in `mdparity.json`).

## In short

- **Most copies keep most of the page.** Across 384 counted pages on 15 sites, the median page keeps 100% of its prose blocks. Pooled, 95.5% of prose blocks are in the copy, and 97.5% once three bits of page furniture are set aside (AWS's feedback widget, Microsoft Learn's hidden sign-in notice and Ask Learn prompt, Google Cloud's free-trial cards).
- **Warnings almost always survive.** The tool found 17 of 410 callouts missing. Every one was read by hand: 9 are in the copy in a form the matcher missed, 1 is page chrome, and **7 are really lost (7 of 409, 1.7%)**. Only one of them is a warning: **1 of 92** warning-group callouts is lost.
- **When a copy fails, it fails silently and often completely.** The real losses come from templates and components that the Markdown export does not render:
  - **Google Cloud:** the shared "project setup" block (sign in, choose or create a project, the roles you need, check that billing is on, and a note about using a throwaway project) is missing from the copy. One copy keeps the lead-in "To complete the guide, you also need a Google Cloud project:" and then goes straight on; another has a "Project setup" heading with nothing under it.
  - **Netlify:** where the page shows a tip on limiting Agent Runners' costs, the copy says "**Snippet** component (self-closing)".
  - **Railway:** where the page says "This feature is in beta.", the copy holds the unrendered tag `<PriorityBoardingBanner />`.
  - **Heroku:** the copy of the PopSQL add-on page never says the add-on is in beta.
  - **Docker:** the copies of two `sbx` CLI reference pages are the page title and nothing else, with no description and no options.
  - **New Relic:** the copy of the Diagnostics CLI release notes is its front matter plus one line of MDX code (`export const _frontmatter = ...`), and none of the page's 41 prose blocks.
  - **Datadog:** the copy of a static-analysis rule page drops the whole "How to use this rule" section (the ruleset snippet and the steps to enable it).
- An agent that gets one of these copies cannot tell that anything is missing.

## Predictions

Gates: **G1 passed** (14 sites with at least 15 counted pages, 384 counted pages in all) and **G2 passed** (410 callouts on 14 sites). **2 of 6 predictions held.**

| | Prediction | Value | Verdict |
|---|---|---|---|
| P1 | The median page coverage is at least 90%. | 100% | **held** |
| P2 | At least 2 sites (with at least 15 counted pages) have a median page coverage below 80%. | 1 site (AWS, 73.2%) | **failed** |
| P3 | At least 5% of callouts are missing from the Markdown copy. | 7 of 409 lost (1.7%), hand-checked; tool 17 of 410 (4.1%) | **failed** |
| P4 | At least one site with at least 5 callouts is missing at least 25% of them. | none, hand-checked (highest: Google Cloud, 4 of 47); tool: Firebase, 2 of 5 | **failed** |
| P5 | At least 95% of code blocks are present. | 1,697 of 1,869 (90.8%) | **failed** |
| P6 | At least 95% of headings are present. | 3,500 of 3,624 (96.6%) | **held** |

P3 and P4 are graded on the hand-checked counts, because every missing callout was read (pre-registered rule). **P4 changed verdict in the hand check:** the tool's count passed it through Firebase (2 of 5 callouts missing), but both are in Firebase's copy, where method names are replaced by raw URLs and the word match fails. P1, P2, P5 and P6 are graded on the tool's numbers, as pre-registered.

**What the misses mean.** We expected copies to lose more than they do. P2, P3 and P4 were genuine guesses about how often copies drop content, and all three were too pessimistic. P5 failed for a reason we did not foresee, explained below.

## The hand check

`hand_check.csv` holds every hand-coded row: **lost** (the content is not in the copy in any form), **variant** (it is there in a form the matcher missed) or **chrome** (not article content).

**1. All 17 missing callouts** were read against the saved copies: 7 lost, 9 variant, 1 chrome.

| Site | Lost | Variant | Chrome |
|---|---|---|---|
| Google Cloud | 4 (the shared project-setup note, twice on each of two pages) | | |
| Netlify | 1 (the Agent Runners tip, replaced by a placeholder) | 3 (glossary tooltip text inside the HTML sentence) | |
| Heroku | 1 (PopSQL beta notice) | 3 (`<your-image-name>` placeholders) | |
| Railway | 1 (beta banner left as a component tag) | | |
| Firebase | | 2 (method names replaced by URLs) | |
| Vercel | | 1 | 1 (an instruction for the page's interactive endpoint browser) |

The Heroku beta notice may be added by the page template rather than written in the article; either way the copy does not carry it.

**2. The first 10 missing prose blocks of the two counted pages with the lowest coverage on each site** (25 pages; Supabase and Railway have none, DigitalOcean one): **22 of 89 lost, 45 of 89 variant, 22 of 89 chrome.**

- Lost: the two Docker `sbx` pages (6), New Relic's release notes (10), Datadog's "How to use this rule" steps (3), and three card descriptions on Vercel pages (3).
- Variant: mostly the matcher's own limits. It strips anything in angle brackets as if it were an HTML tag, so `<your-image-name>`, `<ipv4 address>/<mask>` and `<color>` placeholders break the match (Heroku, Ansible, Cloudflare, DigitalOcean, New Relic). Netlify's HTML puts glossary tooltip text inside sentences. Firebase's copies replace type and method names with raw URLs (the text is there, but harder to read). Vercel's Marketplace API reference serves a longer, differently worded document as its copy; its points are there in other words.
- Chrome: AWS's feedback widget ("Thanks for letting us know ..."), Learn's hidden "Access to this page requires authorization" notices and "Ask Learn" prompt, Google Cloud's free-trial cards, and Datadog's IDE plugin promotions.

**Does the hand check change P1 or P2?** No. The tool's coverage errs both ways: it counts some chrome and variants as missing and cannot see a copy that is a different document. AWS's low median is page chrome: its feedback widget's four lines are missing on every one of its 28 pages (112 blocks), and on 26 of 28 pages they are the only missing blocks. Without them AWS keeps 99.3% of its prose and its median page is 100%, so P2 would still fail (no site below 80%). The same holds for Microsoft Learn (96.7% without its three template lines; on 18 of 30 pages they are the only missing blocks). These adjusted figures were not pre-registered; `test_study10_result.py` recomputes them.

## Why P5 failed: Datadog's hidden code

151 of the 172 missing code blocks are on Datadog. 104 of them are the same API call repeated for each Datadog region (`DD_SITE="datadoghq.eu" ...`, `DD_SITE="ap1.datadoghq.com" ...`); the page holds every region's version for a site picker, and the copy keeps one. Almost all of the other 47 are two small blocks (a line-number column and a `rulesets:` snippet) from a "How to use this rule" template that Datadog's served HTML carries on most pages. Most Datadog pages (all but the API reference) have no `<main>` element, so the tool read the whole body. On pages that are not rules the snippet reads `rulesets: - %!s(<nil>) # Rules to enforce .`, which is Go's mark for a missing template value. Without Datadog, 98.6% of code blocks are in the copies. P5 is graded on the tool's numbers, as pre-registered, and failed; the failure says more about how much hidden code Datadog's pages hold than about lost examples.

## Other figures (reported without a prediction)

- **Tabs:** all 173 prose blocks inside tab panels are in the copies. Sites that render only the active tab are not measured (see Limits).
- **Callout markers:** the copies of only six sites use a callout marker of the kinds the tool counts (`> [!NOTE]`, `:::warning`, `<Callout>`, `!!! tip` and the like): Google Cloud 99, Docker 38, Firebase 7, New Relic 5, Netlify 4, Heroku 1. Elsewhere a warning survives as plain text, bold text or a quote block, so an agent sees its words but may not see that it is a warning. Heroku's copy of the PopSQL page writes the literal word "callout" on a quote line.
- **Microsoft Learn against the vendors:** Learn's median page keeps 89.5% of its prose by the tool's count (96.7% without its template lines) and 83% of its headings (256 of 307); the vendor sites keep 97.8% of theirs (3,244 of 3,317). Study 8 found that Learn's copies drop the final "Next steps" or "Related content" section, which likely accounts for many of the missing headings (not checked by hand here).
- **Size:** the median copy has more words than the page's prose on every site except Datadog (0.19), whose pages hold every region's code.
- Full per-site figures are in `sites.csv` and `MDPARITY_AUTO.md`; every missing block (with at most 160 characters of its text) is in `missing.csv`.

## What this means

- **For docs teams that serve Markdown to agents:** check the copy, not just the page. The losses we found come from includes, components and generated reference pages, which an export can skip without an error. `mdparity.py` flagged all seven lost callouts and the empty reference pages above; run on your own page and copy pairs, a check like it finds such gaps, though its flags need a human look (see the hand check).
- **For agent builders:** a copy that is much shorter than the page, has empty sections, or holds component tags (`<PriorityBoardingBanner />`, "**Snippet** component") is a sign to read the HTML instead.
- **The overall picture is reassuring.** On these 15 sites, an agent that reads the copy gets almost all of what people see, and nearly every warning.

## Prior art and what is new

AFDocs (afdocs.dev) has a per-site `markdown-content-parity` check but publishes no cross-site results or counts by element type. Single projects have reported lost callouts and tabs in their own copies (see the pre-registration). As far as we found, this is the first pre-registered count across many company docs sites of how much of a page, and in particular how many of its warnings, is missing from the Markdown copy served to agents, with every missing callout read by hand.

## Limits

- Served HTML only: page scripts were not run. Content added by scripts, and inactive tab panels rendered on click, are not measured.
- The block rules and the word matcher are heuristics. The hand check shows the matcher misses many blocks that are present (placeholders in angle brackets, tooltip text, URLs for names), so the tool's missing counts are upper bounds for prose; it can also miss a loss that a callout's other words cover.
- One reader coded the hand check (an AI agent working in MV2's name), with no second coder. "Lost" against "chrome" is a judgment for notices such as Heroku's beta line.
- One read on one day, English pages only, and only the sites and pages of studies 8 and 9. Supabase has 10 counted pages, fewer than the 15 needed for P2.
- The evidence (each page's Markdown copy and block list) is not republished, because it holds the sites' text.

## Files

- `PREREGISTRATION.md`: the plan, committed before any page was read.
- `pages.csv`, `sites.csv`, `missing.csv`, `mdparity.json`, `MDPARITY_AUTO.md`: the tool's unchanged output (missing block texts are cut at 160 characters).
- `hand_check.csv`: every hand-coded row, with a note.
- `../../test_study10_result.py`: recomputes the gates and predictions from these files, checks that the hand check covers exactly the pre-registered rows, and recomputes every figure quoted above (`python -m unittest -v test_study10_result`).

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the tool, the hand check and this text were made with AI. Data CC BY 4.0, code Apache-2.0. Quoted page text belongs to each site.
