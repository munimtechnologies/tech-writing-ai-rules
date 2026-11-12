# Study 15: what do Nuxt Content's /raw/ Markdown copies lose when they reach AI agents?

Pre-registered 2026-11-12, before the tool reads any copy in the frame. Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: this plan, the tool and its tests were made with AI.

## Background

Sites built with [Nuxt Content](https://content.nuxt.com/) 3 and [nuxt-llms](https://github.com/nuxt-content/nuxt-llms) publish an `llms.txt` whose links point AI agents to a Markdown copy of each page at `/raw/<path>.md`. That route is `src/features/llms/runtime/server/routes/raw/[...slug].md.get.ts` in nuxt/content (read on `main`, 2026-11-12). It takes the page's stored body, adds the title and description if the body has no `h1`, and returns `stringify(body, { format: 'markdown/html' })` from `minimark`. The body is stored before the page is rendered, so we expect a component whose content exists only at render time (a Vue component that builds a props table or a live example, a partial that pulls in another file) to come out as a tag with nothing inside it, for example `<partial content="config-options"></partial>`.

**Seen before this plan (disclosed):**
- directus.com/docs: MV2's issue [directus/docs#865](https://github.com/directus/docs/issues/865) (2026-11-12) reports that its llms.txt points agents to `/raw/` copies in which shared partials come out empty. Directus is in the frame as a known positive and is left out of P3.
- On 2026-11-12 we read the link lists of `nuxt.com/llms.txt` (about 430 links, nearly all `/raw/`), `ui.nuxt.com/llms.txt` (about 200) and `content.nuxt.com/llms.txt` (about 63) through a fetch tool, and one copy, `ui.nuxt.com/raw/docs/components/button.md`. The fetch tool summarized it as plain Vue code blocks with no component tags; we did not see the raw bytes. No other copy in the frame was read.

**Prior art (searched 2026-11-12):** nuxt-llms issues [#25](https://github.com/nuxt-content/nuxt-llms/issues/25) (KaTeX rendered to HTML in `llms-full.txt`, closed as duplicate), [#50](https://github.com/nuxt-content/nuxt-llms/issues/50) (LaTeX, open) and [#17](https://github.com/nuxt-content/nuxt-llms/issues/17) (an empty list item crashes the stringifier, open) are about `llms-full.txt` and single pages. nuxt/content [#3724](https://github.com/nuxt/content/pull/3724) added related links to the raw route. We found no count, on any site, of components that reach `/raw/` copies empty, and no cross-site comparison of `/raw/` copies with the rendered pages.

## Question

On sites whose llms.txt links Nuxt Content `/raw/` copies, how often does a copy contain a component tag with no text inside, which components are they, and how many words does a copy have compared with the main content of its rendered page?

## Frame

20 candidate `llms.txt` addresses, fixed in `nuxtraw.py` (`SITES`): nuxt.com, ui.nuxt.com, content.nuxt.com, hub.nuxt.com, image.nuxt.com, eslint.nuxt.com, devtools.nuxt.com, fonts.nuxt.com, scripts.nuxt.com, test-utils.nuxt.com, nuxt.studio, docus.dev, i18n.nuxtjs.org, color-mode.nuxtjs.org, supabase.nuxtjs.org, tailwindcss.nuxtjs.org, nuxtseo.com, unhead.unjs.io, motion.vueuse.org and directus.com/docs. They were chosen as Nuxt-ecosystem docs sites and one known non-Nuxt-team user; some may not exist or may not use the raw route, which the eligibility rule handles.

## Eligibility and counting

A site is **eligible** if its llms.txt answers 200 with a body that is not HTML and contains at least 10 unique same-host links whose path contains `/raw/` and ends in `.md` (fragments and queries dropped). An eligible site is **counted** if at least 10 of its sampled copies are read. A copy is **read** if it answers 200 with a non-empty body that is not HTML.

## Sample

Per eligible site, 30 links drawn with `random.Random("study15:" + site_key)` from the sorted unique `/raw/` links (all of them if 30 or fewer), where `site_key` is the host plus the llms.txt folder (for example `directus.com/docs`). Each copy's rendered page is the same address with the first `/raw/` segment and `.md` removed (`/index` becomes the folder). robots.txt is honoured (user agent token `nuxtraw`; a 4xx robots.txt allows all; an unreachable one disallows), and requests are one at a time, one second apart. The tool checks that this file is on `main` before it reads any site.

## Measurement

`nuxtraw.py` 0.1.0, outside fenced code, inline code and HTML comments:

- **Component tag:** an opening tag whose name has a hyphen or is not a standard HTML element (so `partial`, `callout`, `field` count; `div`, `br` do not).
- **Empty:** self-closing, or nothing but whitespace and other tags between the opening tag and its matching closing tag. A tag with no closing tag (a prose placeholder such as `<your-token>`) is not empty.
- **What an empty tag still carries:** `text-attr` if it has an attribute named title, label, description, text, alt, summary, caption, heading or message; else `link-attr` if it has to, href or src; else `bare`.
- **Words:** words of the copy (comments and tags removed, code kept) and words of the rendered page's `<main>` or `<article>` (whole body if neither; script, style, nav, header, footer and aside dropped). **Ratio** = copy words / page words.

## Gate and predictions

All are computed by `nuxtraw.grade()` over counted sites and the copies read on them, and printed in `NUXTRAW_AUTO.md`.

- **G1:** at least 4 sites are counted. If G1 fails, P1 to P5 are reported as description and not graded.
- **P1:** at least half of the counted sites have at least one copy with an empty component tag.
- **P2:** pooled over counted sites, at least 15% of copies read have an empty component tag.
- **P3:** at least 2 counted sites other than directus.com/docs have an empty component tag in at least 10% of their copies.
- **P4:** the median ratio of copies with an empty component tag is lower than the median ratio of copies without one (pooled).
- **P5:** every counted site's median ratio is at least 0.5 (losses are local, not whole pages).

Exploratory, not graded: the empty tags by name and kind per site (`tags.csv`), sites whose llms.txt does not use `/raw/`, and copies whose ratio is above 1 (navigation or duplicated text in the copy).

## Hand check

For each counted site, the first two copies in sample order with an empty component tag and the first copy without one (`hand_check_sample.csv`): open the copy and the rendered page and record (1) whether each counted empty tag is in the copy as reported, (2) whether the rendered page shows content at that spot (text, a table, code or an example) that the copy lacks, and (3) whether the copy without an empty tag really has none. Results go in `hand_check.csv`. If on more than 1 in 5 checked copies an empty tag stands for nothing the page shows (a decoration or icon), RESULT.md reports P1 to P3 again with `bare` tags only and says which verdict changes.

## What will be published

The tool's unchanged `sites.csv`, `pages.csv` (URLs, statuses, counts, tag names and the first empty tag of each copy), `tags.csv`, `hand_check_sample.csv`, `nuxtraw.json` and `NUXTRAW_AUTO.md`, plus `RESULT.md`, `hand_check.csv` and a test that recomputes the gate and predictions from the published CSVs. The copies themselves are the sites' text and are not republished.

## Deviations

Any change to the frame, the tool or the rules after this file is on `main` will be listed in RESULT.md with its reason. If the run fails for a reason outside the tool (compute, network), it is re-run unchanged and the date of the reading is reported.

## Why it matters

Agents read these copies instead of the page. An empty `<component-props>` or `<partial>` looks like a finished page to an agent, but the table or the shared text a reader would see is gone. Nuxt Content's raw route is on by default wherever nuxt-llms is used, so a count across sites shows whether this is one site's setup (Directus) or a property of the route that every Nuxt Content site inherits, and which components a fix would have to render first.
