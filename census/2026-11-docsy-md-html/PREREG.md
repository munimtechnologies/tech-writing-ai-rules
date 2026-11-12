# Study 14: how much shortcode HTML do Docsy sites' Markdown copies for AI agents carry?

Pre-registered 2026-11-12, before any page in the frame is read by the tool. Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: this plan, the tools and their tests were made with AI.

## Background

[Docsy](https://www.docsy.dev/) is a Hugo theme used by many open-source docs sites (Kubernetes, OpenTelemetry, gRPC, etcd and others). Docsy 0.15.0 added opt-in Markdown output for AI agents ([docsy/docsy#2597](https://github.com/docsy/docsy/pull/2597), merged 2026-04-05): each page gets an `index.md` copy built by `layouts/all.md`, which prints the title, the description, the page body through Hugo's `.RenderShortcodes`, and links to child pages. `.RenderShortcodes` renders each shortcode with its template for the current output format. Docsy's shortcodes (`tabpane`, `alert`, `card`, `imgproc`, `pageinfo`, `blocks/*`, `swaggerui`, `redoc`, `iframe` and others, in `theme/layouts/_shortcodes/`, read 2026-11-12) have only HTML templates, so we expect the copies to carry the HTML those templates emit. Docsy's tracking issue for agent-friendly output ([docsy/docsy#2614](https://github.com/docsy/docsy/issues/2614), milestone 0.19.0) lists "Initial work in creating md versions of shortcodes" as open phase 2 work.

**Seen before this plan (disclosed):** on 2026-11-12 we read one copy, `https://www.docsy.dev/docs/content/shortcodes/index.md`, through a fetch tool. It held Bootstrap tab lists (`<ul class="nav nav-tabs" ...>`), alert `<div>`s and a card group. That page documents the shortcodes, so it is an extreme case; this study measures ordinary pages. No other copy on any frame site was read before this plan.

**Prior art (searched 2026-11-12):** AFDocs ([agent-ecosystem/afdocs](https://github.com/agent-ecosystem/afdocs)) scores docs sites for agents and checks tab size, Markdown/HTML parity, code fences and link portability; none of its documented checks counts raw HTML in served Markdown copies. Docsy's golden tests cover its own site's output. We found no public count of shortcode HTML in Markdown copies across sites.

## Question

When a Docsy site serves Markdown copies of its pages, how often does a copy carry HTML from a Docsy shortcode, which shortcodes cause it, and how much of the copy is markup?

## Frame

The 26 sites listed on `https://www.docsy.dev/examples/` (read 2026-11-12), plus `https://www.docsy.dev/` itself: 27 sites, fixed in `docsyleak.py` (`SITES`).

## Eligibility

A site is **eligible** if (a) its home page is built with Docsy, judged by a Docsy class name (`td-home`, `td-section`, `td-page`, `td-navbar`, `td-main`, `td-outer`, `td-sidebar`, `td-content` or `td-default`) in a `class` attribute of the served HTML, and (b) it serves a Markdown copy of its home page: the URL in a `<link rel="alternate" type="text/markdown">` tag, or else `<home>/index.md`, answers 200 with a body that is not HTML (no `html` in the content type, does not start with `<!doctype html` or `<html`). An eligible site is **counted** if at least 10 of its sampled copies are read.

## Sample

For each eligible site: page URLs from its `sitemap.xml` (at the home path, then the host root; for a sitemap index, up to 30 child sitemaps, those under the home path first), kept if on the same host (ignoring `www.`), under the home path, ending in `/`, without a query, and not in `tags`, `categories`, `search`, `author(s)` or `page/<n>` paging folders. Language: if at least half of the kept URLs start with `en/`, only those are used; otherwise URLs whose first folder is a language code are dropped. If no sitemap gives pages, the `.md` links in `<home>/llms.txt` are used. 30 pages are drawn with `random.Random("study14:" + site_key)` from the sorted pool (all of them if 30 or fewer). Each page's copy is fetched at the home copy's pattern (`<page>/index.md`, or `<page>.md` if that is how the home copy is named). robots.txt is honoured (user agent token `docsyleak`; a 4xx robots.txt allows all; an unreachable one disallows) and requests are one second apart. The tool checks that this file is on `main` before it reads any site.

## Measurement

`skills/md-html-leak-check/scripts/md_html_leak.py` 0.1.0, unchanged, on each copy read. Outside fenced code, inline code and HTML comments it counts HTML tags (prose placeholders such as `<name>`, `List<String>` and `<path to file>` are not counted), structural tags (all but simple inline tags: `a`, `abbr`, `b`, `br`, `cite`, `code`, `del`, `em`, `i`, `img`, `ins`, `kbd`, `mark`, `q`, `s`, `samp`, `small`, `span`, `strong`, `sub`, `sup`, `u`, `var`, `wbr`), **markup share** (characters of the tags plus script and style bodies, divided by the copy's characters outside code and comments), and a source label per tag by signature: `docsy:tabpane`, `docsy:alert`, `docsy:card`, `docsy:imgproc`, `docsy:pageinfo`, `docsy:blocks`, `docsy:swaggerui`, `docsy:redoc`, `docsy:iframe`, `hugo:highlight`, `diagram:mermaid`, else `html:<element type>`. A tag with no signature of its own takes the label of the element it sits in. A copy has **Docsy shortcode markup** if at least one tag carries a `docsy:*` label.

## Gate and predictions

All are computed by `docsyleak.grade()` over counted sites and the copies read on them, and printed in `DOCSYLEAK_AUTO.md`.

- **G1:** at least 3 sites are counted. If G1 fails, P2 to P6 are reported as description and not graded.
- **P1:** at most 10 of the 27 frame sites are eligible (Markdown output is opt-in and recent; many example sites run older Docsy versions).
- **P2:** at least half of the counted sites have at least one copy with Docsy shortcode markup.
- **P3:** pooled over counted sites, at least 10% of copies read have Docsy shortcode markup.
- **P4:** the `docsy:*` label found on the most copies (pooled) is `docsy:alert` (held if it ties for the most).
- **P5:** among copies with Docsy shortcode markup, the median markup share is at least 5%.
- **P6:** every counted site has at least one copy with a structural tag (from any source).

Exploratory, not graded: `hugo:highlight` and plain-HTML labels, per-site medians, swagger/redoc copies that hold only an empty element and a script.

## Hand check

For each counted site, the first two copies in sample order with Docsy shortcode markup and the first copy without (`hand_check_sample.csv`): open the copy and the live HTML page and record (1) whether the counted markup is in the copy as reported, (2) whether each `docsy:*` label names the shortcode that produced it (by the page's rendered component and its source file where public), and (3) whether the copy without Docsy markup really has none. Results go in `hand_check.csv`. If the hand check finds a wrong `docsy:*` label on more than 1 in 5 checked copies, P2 to P5 are also reported with the hand-corrected labels for those copies, and RESULT.md says which verdict changes.

## What will be published

The tool's unchanged `sites.csv`, `pages.csv` (URLs, statuses, counts, labels and the first structural tag of each copy, cut at 120 characters), `labels.csv`, `hand_check_sample.csv`, `docsyleak.json` and `DOCSYLEAK_AUTO.md`, plus `RESULT.md`, `hand_check.csv` and a test that recomputes the gate and predictions from the published CSVs. The fetched copies (`copies/`) are the sites' text and are not republished.

## Deviations

Any change to the frame, the tools or the rules after this file is on `main` will be listed in RESULT.md with its reason. If the run fails for a reason outside the tool (compute, network), it is re-run unchanged and the date of the reading is reported.

## Why it matters

Agents read these copies in place of the page. If a copy holds the HTML of a tab set or an alert, the words are still there but wrapped in markup; if it holds an API explorer's empty element and script, the content is gone. Docsy plans Markdown templates for its shortcodes; a count of which shortcodes reach real sites' copies, and how often, tells where that work pays first. The checker is published as an agent skill so any docs team can run the same count on its own build.
