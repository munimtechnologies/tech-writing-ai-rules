# Study 9 result: do company docs sites tell readers which pages were made with AI?

Read 2026-11-09 15:34 to 16:23 UTC by `vendordocs.py` 0.1.0, about six hours after the [pre-registration](PREREGISTRATION.md) was first committed (09:43 UTC). Hand checks done and P1 to P5 graded on 2026-11-09. **P6 (the hand search for vendor statements) is not graded yet**; it follows in a later update with its reading notes.

## Short answer

**None of the 18 readable company docs sites labels any sampled page as made with AI, or says so on the page, for people or for agents.** Microsoft remains the only vendor we have seen do it (studies 7 and 8). Yet the same sites already write for AI readers: **14 of the 20 serve an `llms.txt` file**, and **13 of the 18 readable sites serve a Markdown copy** of at least half of their sampled pages.

## Frame and sample

The 20 company-run docs sites of the Stack Overflow 2025 Developer Survey's "Cloud development" list (see the pre-registration for every in/out decision). For each, the tool drew 30 pages by a seeded draw from its sitemaps (or a short crawl), and fetched each page as HTML, with `Accept: text/markdown`, and at its `.md` address.

- 571 pages sampled, 537 readable. **18 of 20 sites are readable** (at least 20 readable pages). Splunk (`help.splunk.com`) answered every sampled page with HTTP 403 to the tool. IBM Cloud's docs are a script-built app: the crawl found only one page.
- Counted pages (readable pages on readable sites): **536**.

## Gates

| Gate | Needed | Found | |
|---|---|---|---|
| G1 | at least 15 of 20 sites readable | 18 | passed |
| G2 | the tool finds the AI label on the Learn control page | `ai-usage: ai-assisted` in the Markdown copy and an `ai-usage` meta tag in the HTML | passed |
| G3 | the tool finds the acknowledgement on the DevBlogs control post | "AI-assisted content." | passed |

## Predictions

| | Prediction | Result | |
|---|---|---|---|
| P1 | at most 2 readable sites have any page with a machine-readable AI label | 0 of 18 | **held** |
| P2 | at most 2 readable sites have any page with a confirmed acknowledgement sentence | 0 of 18 | **held** |
| P3 | at most 1% of counted pages carry a confirmed label or sentence | 0 of 536 (0%) | **held** |
| P4 | at least 10 of 20 sites serve a valid `llms.txt` | 14 of 20 | **held** |
| P5 | at least 6 readable sites serve a Markdown copy for at least half of their readable pages | 13 of 18 | **held** |
| P6 | at most 3 of 20 vendors publish a statement on AI use in their docs | | **not graded yet** |

## Hand check

- **Tool hits:** the tool found no AI label and no acknowledgement sentence on any sampled page, in HTML or in a Markdown copy, and no AI phrase anywhere in the raw HTML (scripts included). There was nothing to confirm or reject.
- **Rendered check (pre-registered):** we opened the first two readable pages by URL of each of the 18 readable sites (36 pages) through a rendering reader (r.jina.ai), which runs the page's scripts, and read each for any note, badge or sentence saying the page was made with AI. **None of the 36 has one.** Two Docker pages were longer than the reader's first window; we read the rest of each, and the end of the page has no note either.
- **Front matter keys:** we searched every Markdown copy's front matter keys for any AI-like key the tool's list might miss (`ai`, `llm`, `generated`, `assisted`, `machine`, `translated`). Only the Learn control page has one.

So the checked values equal the automatic values.

## Who writes for AI readers

| Site | llms.txt | llms-full.txt | Markdown copy (of readable pages) | By `Accept` | At `.md` | `Content-Signal` in robots.txt |
|---|---|---|---|---|---|---|
| Docker | yes | yes | 30 of 30 | 30 | 30 | ai-train=yes, search=yes, ai-input=yes |
| npm | no | no | 0 of 30 | 0 | 0 | |
| Amazon Web Services | yes | yes | 28 of 28 | 28 | 28 | |
| Google Cloud | no | no | 30 of 30 | 30 | 30 | |
| Cloudflare | yes | no | 30 of 30 | 30 | 0 | ai-train=yes, search=yes, ai-input=yes |
| Terraform (HashiCorp) | no | no | 0 of 30 | 0 | 0 | |
| Firebase | yes | no | 28 of 28 | 28 | 28 | |
| Ansible | no | no | 30 of 30 | 30 | 0 | |
| Chocolatey | no | no | 0 of 30 | 0 | 0 | search=yes, ai-train=no, use=reference |
| DigitalOcean | yes | yes | 29 of 30 | 0 | 29 | ai-train=yes, search=yes, ai-input=yes |
| Vercel | yes | yes | 30 of 30 | 30 | 30 | |
| Datadog | yes | no | 30 of 30 | 30 | 30 | |
| Netlify | yes | no | 30 of 30 | 30 | 30 | search=yes, ai-input=yes, ai-train=yes |
| Supabase | yes | yes | 11 of 30 | 11 | 11 | ai-train=yes, search=yes, ai-input=yes |
| Heroku | yes | no | 30 of 30 | 0 | 30 | |
| Splunk (not readable) | no | no | | | | |
| New Relic | yes | no | 29 of 30 | 0 | 29 | |
| Railway | yes | yes | 30 of 30 | 30 | 30 | search=yes, ai-input=yes, ai-train=yes |
| IBM Cloud (not readable) | yes | no | 0 of 1 | 0 | 0 | ai-train=yes, search=yes, ai-input=yes |
| Yandex Cloud | yes | no | 0 of 30 | 0 | 0 | |

- **The two ways of asking for Markdown are not interchangeable.** Cloudflare and Ansible answer only `Accept: text/markdown`; DigitalOcean, Heroku and New Relic answer only the `.md` address. An agent that tries one way misses the copy on those five sites.
- **8 sites publish Cloudflare-style `Content-Signal` lines** in robots.txt. Seven allow AI training; Chocolatey alone says `ai-train=no`.
- Markdown and llms.txt answers are the tool's automatic labels; we did not hand-check them.

## What this means

Writing for AI readers is now normal on vendor docs sites; telling any reader, person or agent, which pages were made with AI is not. Agents that read these Markdown copies get no signal about how a page was written, and neither do people. Microsoft's `ai-usage` label and its end-of-article note are, among the sites we have looked at, the only such signal. A label is also not proof of how a page was written, and its absence is not proof that AI was not used: this study measures what readers are told, not how the pages were made.

## Limits

- One reading on one day, English pages only, 30 pages per site. The sample is clustered by the sitemap files the tool read (at most 25 per site), so it is not a simple random sample of each site; on Datadog, New Relic and DigitalOcean it leans towards generated reference and release-note pages.
- The tool reads HTML as served. The rendered check covers 2 pages per site, not all 536.
- Splunk could not be read by the tool and IBM Cloud gave one page, so 2 of the 20 vendors are judged on their `llms.txt` only.
- A label in a form neither the tool nor the hand checks anticipated (for example a badge image without text) would be missed.

## Files

- `sites.csv`, `pages.csv`, `vendordocs.json`, `VENDORDOCS_AUTO.md`: the tool's unchanged output (URLs, statuses, measures and front matter key names; no page text).

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the tool, the checks and this text were made with AI. Data and text CC BY 4.0. Each site's pages belong to its owner.
