# Study 10 pre-registration: do the Markdown copies docs sites serve to AI agents keep what the page shows people?

Written 2026-11-10, before any page in this study was read. The tool is `mdparity.py` 0.1.0 (in the repository root, with offline tests in `test_mdparity.py`). It waits for this file's first commit and records that commit's time.

## Why

Coding agents such as Claude Code, Cursor and OpenCode ask docs sites for Markdown (`Accept: text/markdown`), and the llms.txt convention offers a `<page>.md` copy of each page. [Study 9](../2026-11-vendor-docs-ai-labels/RESULT.md) found that 13 of 18 readable company docs sites in the Stack Overflow 2025 survey's cloud list serve such copies. The copy is a separate document. Nobody checks that it says what the page says, and an agent that gets a copy has no way to tell that something is missing. [Study 8](../2026-11-ms-learn-ai-shown/RESULT.md) found that Microsoft Learn's copies drop the article's AI note (0 of 131) and its final "Next steps" or "Related content" section (130 of 131).

The parts most likely to be lost matter most to agents: callouts (warnings, cautions, notes), which are often built from site components, and text pulled in from include files.

**Prior art (searched 2026-11-10).** AFDocs (afdocs.dev) has a `markdown-content-parity` check that scores the share of HTML content segments missing from a site's Markdown version, with pass, warn and fail thresholds of 5% and 20%. It is a tool for one site at a time, and it publishes no cross-site results and no counts by element type. Its issue tracker reports false positives on reference pages (agent-ecosystem/afdocs #106, #110). Single projects have reported and fixed lost or mangled callouts, tabs and cards in their own copies (for example graft PR #48, crisp-ui PR #10, holepunchto/pear-docs PR #431). A Hackmamba article (October 2026) showed one generated copy that dropped all four tab labels and commands. Checkly (February 2026) tested which agents ask for Markdown, not what they get. We found no count, across many docs sites, of how much of a page's content, and in particular how many of its warnings, are missing from the copy served to agents.

## Frame

1. **Vendor pages:** every row of study 9's published `census/2026-11-vendor-docs-ai-labels/pages.csv` (commit `af74d23`) that is not a control, was readable, and had a Markdown copy. The copy is asked for the way that worked in study 9: `Accept: text/markdown` at the page URL if that worked, otherwise the `<page>.md` address. By study 9's counts this is about 395 pages on 14 sites (Docker, AWS, Google Cloud, Cloudflare, Firebase, Ansible, DigitalOcean, Vercel, Datadog, Netlify, Supabase, Heroku, New Relic, Railway).
2. **Microsoft Learn:** 30 pages drawn with `random.Random("study10|learn")` from study 8's counted pages (strata A, B, C and U, mapped, Markdown copy served) in `census/2026-11-ms-learn-ai-shown/pages.csv` (same commit), asked for with `Accept: text/markdown`.

Both CSV files are read from that pinned commit and their SHA-256 is recorded. Pages are read once, in file order, with the tool's own User-Agent, robots.txt honoured, one second between requests and two requests per page.

## Measures

For each page the tool fetches the served HTML (page scripts are not run) and the Markdown copy, and takes the page's main content: `<main>`, else `role="main"`, else the largest `<article>`, else `<body>`; a large `<article>` inside `<main>` (at least half its words) is used instead. It drops `nav`, `header`, `footer`, `button`, `script`, `style`, `svg`, forms' inputs, `aria-hidden="true"` elements, non-callout `aside`s and elements whose class or id is common page chrome (table of contents, breadcrumbs, sidebar, feedback, pagination, copy buttons, heading anchors, screen-reader-only text). It then splits the content into blocks:

- **prose:** `p`, `li`, `td`, `th`, `dt`, `dd`, `figcaption`, `summary` with no such block inside, of at least 8 words;
- **heading:** `h2`, `h3`, `h4`;
- **code:** `pre`;
- **callout:** the outermost `div`, `aside`, `section`, `blockquote` or `p` whose class names an admonition, callout, alert, notice, warning, caution, danger, important, note or tip, whose role is `note` or `alert`, or that has a `data-*callout*` or `data-*admonition*` attribute, with at least 3 words after a leading kind word such as "Warning". A callout is in the **warning group** if its classes, data attributes or first two words name warning, caution, danger, important, error or critical, and in the **note group** otherwise.

Prose inside tab panels (`role="tabpanel"` or a `tab-pane`/`tab-panel`/`tab-content` class) is flagged.

A block is **present** in the Markdown copy if its words (lower case, letters and digits only) appear there: a block of fewer than 5 words as an exact word sequence, a longer block if at least 80% of its 5-word shingles do. Before matching, link targets, reference definitions, HTML and MDX tags, template tags (`{{< >}}`, `{% %}`) and comments are removed from the Markdown outside code fences; code inside fences is kept.

A page is **counted** if its HTML was read (status 200, HTML, not a bot wall), its Markdown copy was served (study 9's rule) and it has at least 3 prose blocks. A page's **coverage** is the share of its prose blocks that are present.

## Gates

- **G1:** at least 10 sites with at least 15 counted pages each, and at least 250 counted pages in all. If G1 fails, nothing is graded.
- **G2:** at least 40 callouts found in counted pages, on at least 5 sites. If G2 fails, P3 and P4 are not graded.

## Predictions

All pooled over counted pages unless stated. Bounds are inclusive.

| | Prediction |
|---|---|
| P1 | The median page coverage is at least 90%. |
| P2 | At least 2 sites (with at least 15 counted pages) have a median page coverage below 80%. |
| P3 | At least 5% of callouts are missing from the Markdown copy. |
| P4 | At least one site with at least 5 callouts is missing at least 25% of them. |
| P5 | At least 95% of code blocks are present (graded only if there are at least 50). |
| P6 | At least 95% of headings are present (graded only if there are at least 50). |

Reported without a prediction: missing shares for warning-group and note-group callouts, prose coverage inside and outside tab panels, Microsoft Learn against the vendor sites, the median ratio of Markdown words to HTML prose words per site, and the number of callout markers (`> [!NOTE]`, `:::warning`, `<Callout>`, `!!! tip` and the like) in each site's copies.

## Hand check

The tool saves each counted page's Markdown copy and its block list (marked present or missing) in `evidence/`. These are not republished, because they hold the sites' text.

1. **Every missing callout** (if there are more than 60, a sample of 60 drawn with `random.Random("study10|hand")`) is read against the saved copy and coded **lost** (its content is not in the copy in any form), **variant** (it is there in a form the matcher missed, such as a substituted variable or a re-flowed list) or **chrome** (not article content: a site banner, version notice, cookie note or feedback widget). **P3 and P4 are graded on the hand-checked counts** if every missing callout was read: variant and chrome callouts are removed from the missing count, and chrome ones also from the total. If a sample was read, they are graded on the tool's counts and the sample's rates are reported next to them.
2. **For each site, the two counted pages with the lowest coverage:** the first 10 missing prose blocks of each are coded the same way. P1 and P2 are graded on the tool's numbers; the hand check's rates of variant and chrome blocks are reported next to them, and if they show the tool's coverage is off by enough to change a verdict, the result says so.

## Limits, stated before the run

- Served HTML only. A page whose content is added by scripts shows fewer blocks than a reader sees, and such a page may not be counted. Inactive tab panels that a site renders only on click are not in the HTML at all.
- The block rules are heuristics. They will miss some callouts (a site whose callout classes use other words) and find some false ones (a class like `release-note` on non-callout text). The hand check measures this.
- Word matching ignores formatting, so a callout that survives as plain text with no marker counts as present. The marker counts are reported separately for that reason.
- Markdown copies can also contain more than the page (front matter, text for agents). Extra text is not measured except through the word ratio.
- One read, one day, English pages, the sites and pages of studies 8 and 9.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the tool, this pre-registration and the coding were made with AI. Data CC BY 4.0, code Apache-2.0.
