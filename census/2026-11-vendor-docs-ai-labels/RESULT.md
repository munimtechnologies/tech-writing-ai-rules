# Study 9 result: do company docs sites tell readers which pages were made with AI?

Read 2026-11-09 15:34 to 16:23 UTC by `vendordocs.py` 0.1.0, about six hours after the [pre-registration](PREREGISTRATION.md) was first committed (09:43 UTC). Hand checks done and P1 to P5 graded on 2026-11-09. **P6, the hand search for vendor statements, was done and graded on 2026-11-10** (see [P6](#p6-do-vendors-say-how-ai-is-used-in-their-docs) and `p6_notes.csv`).

## Short answer

**None of the 18 readable company docs sites labels any sampled page as made with AI, or says so on the page, for people or for agents.** Microsoft remains the only vendor we have seen do it (studies 7 and 8). Yet the same sites already write for AI readers: **14 of the 20 serve an `llms.txt` file**, and **13 of the 18 readable sites serve a Markdown copy** of at least half of their sampled pages.

**And 4 of the 20 vendors say elsewhere, in public, that AI drafts or helps write their docs**: AWS (a blog post by its documentation lead), Cloudflare (its docs style guide), Datadog (its docs repo's README) and IBM Cloud (a site-wide notice). For the three of them whose sites we could sample (88 pages), no sampled page tells its reader. The statements sit in a style guide, a blog post, a repo and a notices page, not on the pages they describe.

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
| P6 | at most 3 of 20 vendors publish a statement on AI use in their docs | 4 of 20 | **failed** |

## Hand check

- **Tool hits:** the tool found no AI label and no acknowledgement sentence on any sampled page, in HTML or in a Markdown copy, and no AI phrase anywhere in the raw HTML (scripts included). There was nothing to confirm or reject.
- **Rendered check (pre-registered):** we opened the first two readable pages by URL of each of the 18 readable sites (36 pages) through a rendering reader (r.jina.ai), which runs the page's scripts, and read each for any note, badge or sentence saying the page was made with AI. **None of the 36 has one.** Two Docker pages were longer than the reader's first window; we read the rest of each, and the end of the page has no note either.
- **Front matter keys:** we searched every Markdown copy's front matter keys for any AI-like key the tool's list might miss (`ai`, `llm`, `generated`, `assisted`, `machine`, `translated`). Only the Learn control page has one.

So the checked values equal the automatic values.

## P6: do vendors say how AI is used in their docs?

Done on 2026-11-10 by the procedure fixed in the pre-registration, for all 20 vendors: (a) a web search for `"<vendor>" documentation "AI-generated" OR "AI-assisted" OR "written with AI" OR "created with AI"`, (b) a web search for `site:<docs host> "AI-generated content" OR "with the help of AI" OR "AI-assisted content"`, first 10 results of each, and (c) the root `README`, `CONTRIBUTING`, `AGENTS.md` and `CLAUDE.md` of the docs source where it is public on GitHub. Every hit was then opened live and quoted from the vendor's own page. One row per vendor, with links and quotes of at most 200 characters, is in [`p6_notes.csv`](p6_notes.csv).

**4 of 20 vendors publish a statement**, so **P6 failed** (at most 3 predicted):

| Vendor | Where | What it says |
|---|---|---|
| Amazon Web Services | [AWS Insights blog](https://aws.amazon.com/blogs/aws-insights/aws-documentation-update-progress-challenges-and-whats-next-for-2025/), by the head of the AWS Documentation, SDK and CLI teams, 2025-02-13 | "Most of the guides began with AI-generated first drafts through some clever prompting" (the AWS Decision Guides), then tested and revised. AI content shown without that review "will always be clearly labeled as such". |
| Cloudflare | [Style guide, "When we use AI"](https://developers.cloudflare.com/style-guide/how-we-docs/how-we-ai/when-we-use-ai/), on the docs site, updated 2026-04-24 | "We are optimistic about asking stakeholders to use AI to create initial drafts of documentation". The section also has prompt templates. The docs repo README says AI tools may help review documentation and pull requests. |
| Datadog | [README of DataDog/documentation](https://github.com/DataDog/documentation/blob/master/README.md), note "AI and content quality" | "The docs team are huge fans of AI tools like Claude Code and use them to generate content all the time." It adds that the team will always rely on human review. |
| IBM Cloud | [IBM Cloud Notices](https://cloud.ibm.com/docs/overview?topic=overview-notices), updated 2026-10-26 | "Portions of IBM Cloud documentation may be generated with the assistance of IBM AI technologies." |

- **None of the four marks which pages.** AWS, Cloudflare and Datadog were readable in P1 to P5. None of their 88 sampled pages (28, 30 and 30) carries a label or a note, in HTML, in Markdown copies or in the rendered check. IBM Cloud's notice covers the whole docs site, and its pages could not be sampled. AWS's promise is about AI content shown *without* review, so unlabelled reviewed pages do not break it. The statements tell readers that AI is used somewhere, not where.
- **Where the verdict is fragile.** Datadog's statement is in its docs repository, not on its docs site. The pre-registered procedure reads that repository, and the sentence describes the docs team's own practice, so it counts. **If only statements on a docs site or a vendor blog counted, the count would be 3 and P6 would hold at its boundary.** Two more items were found and not counted. Supabase's docs `CONTRIBUTING.md` tells contributors how to write with agent skills ("If you write with an agent, use our AI agent skills for docs authoring") but does not say how Supabase's own docs are written, so it is coded a contributor rule. Google Cloud's translated pages say that Google uses AI technology to translate the content into the reader's language ("Google menggunakan teknologi AI untuk menerjemahkan konten ke dalam bahasa pilihan Anda", on the Indonesian docs home), which is about translation, not the English text this study samples. Counting both would give 6.
- **Contributor rules, recorded separately (not graded):** 5 of the 20 set terms for AI-made docs contributions: Docker (links Moby's AI policy, which asks for disclosure), Terraform/HashiCorp ("These guidelines apply whether you write the change yourself or use an AI assistant."), Ansible (the community's AI-assisted contribution policy, with an `Assisted-by` line), Datadog (note AI use in the PR template) and Supabase (agent skills plus human review). All five are among the 11 vendors whose docs source is public on GitHub. 7 of those 11 have an `AGENTS.md`-style file for coding agents.
- **No public docs source** for 9 vendors: AWS (most awsdocs repos archived in June 2023), Google Cloud, Firebase, DigitalOcean, Vercel, Netlify, Heroku, Splunk (its public Observability docs repo was archived in September 2025) and Railway. For these, only searches (a) and (b) apply.
- **Common false leads, not counted:** many docs sites label their AI chatbot's answers ("AI-generated responses may be inaccurate" on Datadog, the "AI-generated content disclaimer" for Ask Netlify, New Relic AI, Firebase's Gemini features). These describe a product's output, not how the docs are written. Chocolatey's command reference says it was "automatically generated from choco --help", which is not AI.

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

Writing for AI readers is now normal on vendor docs sites; telling any reader, person or agent, which pages were made with AI is not. At least four of these vendors say in public that AI drafts or helps write their docs, yet their pages carry no label and no note. A reader, or an agent reading the Markdown copy, gets no signal about how a given page was written. Among the sites we have looked at, Microsoft's `ai-usage` label and its end-of-article note are still the only per-page signal. A label is also not proof of how a page was written, and its absence is not proof that AI was not used: this study measures what readers are told, not how the pages were made.

## Limits

- One reading on one day, English pages only, 30 pages per site. The sample is clustered by the sitemap files the tool read (at most 25 per site), so it is not a simple random sample of each site; on Datadog, New Relic and DigitalOcean it leans towards generated reference and release-note pages.
- The tool reads HTML as served. The rendered check covers 2 pages per site, not all 536.
- Splunk could not be read by the tool and IBM Cloud gave one page, so 2 of the 20 vendors are judged on their `llms.txt` only for P1 to P5.
- A label in a form neither the tool nor the hand checks anticipated (for example a badge image without text) would be missed.
- **P6:** the web search tool returns a summary of its top results, and several site-restricted searches also returned pages from other sites, so a statement that ranks low or uses other wording (for example "machine learning" or a non-English page) could be missed. The rule that a statement must describe the vendor's own use, not set terms for contributors, was applied while reading; the sensitivity above shows how the verdict moves with it. One reader, no second reader. A statement can also exist on a page that is not indexed, such as a footer, a terms page or a private wiki.

## Files

- `sites.csv`, `pages.csv`, `vendordocs.json`, `VENDORDOCS_AUTO.md`: the tool's unchanged output (URLs, statuses, measures and front matter key names; no page text).
- `p6_notes.csv`: P6 reading notes, one row per vendor: statement (yes/no), where it is (site, blog or repo), link, quote (at most 200 characters), which search found it, contributor rule with link and quote, AI translation notice, the docs repo read, and notes. `test_study9_p6.py` recounts it and checks this file's P6 row.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the tool, the checks, the P6 reading and this text were made with AI. Data and text CC BY 4.0. Each site's pages belong to its owner.
