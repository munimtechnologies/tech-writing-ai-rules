# Study 9: do company docs sites tell readers, people and agents, which pages were made with AI? (pre-registration)

Written 2026-11-09, before any page of the 20 sites below was fetched for this study. The tool, `vendordocs.py` 0.1.0, waits until this file is on `main` before it reads anything.

## Why this study

Microsoft Learn labels articles made with AI. Authors set `ai-usage: ai-assisted` or `ai-generated` in the source (study 7 counts these labels), and Microsoft promises readers a sentence acknowledging AI at the end of each such article (study 8 checks whether it appears). Microsoft's developer blogs show a top-of-post note: "AI-assisted content. This article was partially created with the help of AI."

Other big vendors also write docs that developers use every day. Many of them now also write for AI readers, with an `llms.txt` file or a Markdown copy of each page for agents. We want to know whether those vendors tell their readers, people or agents, which pages were made with AI.

**Prior art (searched 2026-11-09):** we found no count of AI-authorship labels on vendor documentation sites. Pew Research Center (2026-08-20) estimated how much of the web *shows signs* of AI authorship; it measured detection, not disclosure. Minuttia (2026-10) counted whether vendor-written "best tools" lists disclose who wrote them, not whether AI did. Datadab (2026-10-23) counted machine-readable docs indexes for 11 vendors in one category. Studies of `llms.txt` adoption count files, not authorship labels. Google's Ads and Merchant Center rules require AI labels on ads and product data, not on documentation.

## What we had seen before writing the predictions

- We have **not** fetched any page of the 20 sites for this study.
- From earlier work and general knowledge, we expect several of these sites to serve `llms.txt`: our study 5 found it common on docs sites, and Cloudflare, Vercel and Supabase are widely reported to serve it. We have not checked any of the 20 for this study. P4 and P5 are written with that expectation in mind and are the least surprising predictions here.
- We know of no vendor besides Microsoft that labels docs pages made with AI. That absence of knowledge is the basis for P1 to P3, and the study tests it.

## Frame

The **Stack Overflow 2025 Developer Survey**, "Cloud development" question (all respondents; 42 entries), read on 2026-11-09 at https://survey.stackoverflow.co/2025/technology. An entry is **in** if its docs are run by a company that sells the product or a paid tier of the same product. Entries that share a docs site are counted once. Open-source projects run by a foundation or community are out, as are build tools whose company sells a different product.

| Survey entry | Decision | Docs site (root used) |
|---|---|---|
| Docker | in | https://docs.docker.com/ |
| npm | in (GitHub/npm sells paid tiers) | https://docs.npmjs.com/ |
| Amazon Web Services (AWS) | in | https://docs.aws.amazon.com/ |
| Pip | out (PyPA, community) | |
| Kubernetes | out (CNCF) | |
| Microsoft Azure | reference, not counted (learn.microsoft.com, studies 7-8) | |
| Homebrew | out (community) | |
| Vite | out (community project) | |
| Google Cloud | in | https://cloud.google.com/docs (paths containing /docs) |
| Make | out (GNU) | |
| Yarn | out (community) | |
| Cloudflare | in | https://developers.cloudflare.com/ |
| NuGet | reference (learn.microsoft.com) | |
| APT | out (Debian) | |
| Webpack | out (OpenJS) | |
| Terraform | in (HashiCorp, an IBM company, sells HCP Terraform) | https://developer.hashicorp.com/terraform |
| Maven (build tool) | out (Apache) | |
| Cargo | out (Rust project) | |
| Gradle | out (the build tool is free; Gradle Inc. sells a separate product) | |
| pnpm | out (community) | |
| Firebase | in (Google) | https://firebase.google.com/docs |
| Prometheus | out (CNCF) | |
| Ansible | in (Red Hat sells Ansible Automation Platform; docs.ansible.com is Red Hat-run) | https://docs.ansible.com/ |
| Podman | out (community) | |
| Chocolatey | in (Chocolatey Software sells Chocolatey for Business) | https://docs.chocolatey.org/ |
| Composer | out (community) | |
| MSBuild | reference (learn.microsoft.com) | |
| Digital Ocean | in | https://docs.digitalocean.com/ |
| Vercel | in | https://vercel.com/docs |
| Poetry | out (community) | |
| Datadog | in | https://docs.datadoghq.com/ |
| Pacman | out (Arch Linux) | |
| Netlify | in | https://docs.netlify.com/ |
| Bun | out (open-source runtime, no paid tier) | |
| Supabase | in | https://supabase.com/docs |
| Heroku | in (Salesforce) | https://devcenter.heroku.com/ (paths under /articles/) |
| Ninja | out (community) | |
| Splunk | in (Cisco) | https://help.splunk.com/ |
| New Relic | in | https://docs.newrelic.com/ (paths under /docs/) |
| Railway | in | https://docs.railway.com/ |
| IBM Cloud | in | https://cloud.ibm.com/docs |
| Yandex Cloud | in | https://yandex.cloud/en/docs |

That gives **20 sites**. The hosts and path rules for each are in `SITES` in `vendordocs.py`.

## Sample

For each site, `vendordocs.py`:

1. reads `robots.txt` with its own User-Agent and never fetches a disallowed URL (an unreadable robots.txt allows everything);
2. collects page URLs from the site's sitemaps: the `Sitemap:` lines in robots.txt, then `/sitemap.xml`, `<docs root>/sitemap.xml` and `/sitemap_index.xml`. Sitemap indexes are expanded with children whose path contains "doc" first, then the rest, each group in a seeded shuffle. It stops after 25 sitemap files or 2,000 in-scope URLs;
3. keeps a URL only if it is in scope: the site's host and path rule, no query string, not a file type such as `.pdf` or `.xml`, and no language code (`ja`, `fr-fr`, `zh_cn` and so on) in the first two path segments;
4. crawls if the sitemaps give fewer than 30 URLs: the docs root's links, then the links of up to 10 of those pages;
5. draws **30 pages** with `random.Random("study9|<site id>").sample` over the sorted URLs (all of them if there are fewer).

Each page is fetched three times, at most one request per second: as HTML (`Accept: text/html`), with `Accept: text/markdown`, and at the `.md` address the llms.txt proposal uses (`<path>.md`). The site's `/llms.txt` and `/llms-full.txt` are checked at the host root and the docs root.

## Measures

- **Readable page:** HTTP 200, HTML, not a bot-check page (statuses 401, 403, 429 and 503, and challenge pages under 30 KB, count as blocked).
- **Machine-readable AI label:** an HTML `<meta>` tag, or a key in a Markdown copy's front matter, whose name is an AI-authorship key (`ai-usage`, `ms.ai-usage`, `ai-generated`, `ai-assisted`, `ai-disclosure`, `ai-content` and similar), or whose value says `ai-generated` or `ai-assisted` (not in title, description, keywords or tag fields), or names IPTC's `trainedAlgorithmicMedia`.
- **Acknowledgement sentence:** the same pattern as study 8 (created, written, generated, produced, drafted, authored or prepared ... with, by, using or from ... AI, naming the page, article, content, document, documentation, topic, post or guide; or "AI-assisted content" / "AI-generated content"), in the visible HTML text or a Markdown copy's body.
- **Markdown copy:** HTTP 200, not HTML, and either a Markdown content type, or plain text that starts with front matter or a heading.
- **llms.txt:** HTTP 200, not HTML, first non-empty line starts with `# `.
- Recorded, not graded: `Content-Signal` lines in robots.txt, AI phrases anywhere in the raw HTML (including scripts), and the front matter keys of Markdown copies.

**Readable site:** at least 20 readable sampled pages.

## Controls and gates

- **Control-md:** the Learn article `entra/identity-platform/quickstart-register-app`, whose Markdown copy carried `ai-usage: ai-assisted` when we read it for study 8.
- **Control-note:** the Microsoft DevBlogs post "Introducing WinDbg MCP: Debug with natural language, grounded in evidence", listed by a web search as carrying the "AI-assisted content" note. We have not fetched it.
- **G1:** at least 15 of the 20 sites are readable. If not, P1, P2, P3 and P5 are not graded.
- **G2:** the tool finds the AI label on control-md. If not, P1 and P3 are not graded.
- **G3:** the tool finds the acknowledgement sentence on control-note. If not, P2 and P3 are not graded.

## Predictions

Boundaries are inclusive and computed by `summarise` in `vendordocs.py` (offline tests in `test_vendordocs.py`). P1 to P3 and P5 count readable sites only.

- **P1:** at most 2 readable sites have any sampled page with a machine-readable AI label.
- **P2:** at most 2 readable sites have any sampled page with an acknowledgement sentence that the hand check confirms describes how the page was made.
- **P3:** at most 1% of counted pages (readable pages on readable sites) carry a confirmed AI label or acknowledgement sentence.
- **P4:** at least 10 of the 20 sites serve a valid `llms.txt` at the host root or the docs root.
- **P5:** at least 6 readable sites serve a Markdown copy (either way) for at least half of their readable sampled pages.
- **P6 (by hand):** at most 3 of the 20 vendors publish a statement, findable by the procedure below, telling readers whether or how AI is used to write or edit their documentation.

**P6 procedure, fixed now.** For each vendor: (a) a web search for `"<vendor>" documentation "AI-generated" OR "AI-assisted" OR "written with AI" OR "created with AI"`; (b) a web search for `site:<docs host> "AI-generated content" OR "with the help of AI" OR "AI-assisted content"`; (c) if the docs source is public on GitHub (found from an "Edit this page" link or the vendor's GitHub organisation), read its root `README`, `CONTRIBUTING` and `AGENTS.md` / `CLAUDE.md` if present. A **statement** is the vendor's own text telling readers whether or how AI is used to write or edit its docs. A rule for *contributors* about AI-made changes counts separately (descriptive, not graded). We read the first 10 results of each search.

## Hand check

The tool decides each measure. Then we will read the matched label or sentence of **every** page where the tool finds one. A sentence is a false positive if it describes something other than how the page was made (for example a product feature that generates content, which is common in AI product docs). We will also open **2 readable pages per readable site** (the first two by URL) through a rendering reader, to look for a note that only appears after scripts run. P2 and P3 use the hand-checked values. Both the automatic and the checked values are published.

## What will be published

`RESULT.md`, `sites.csv`, `pages.csv` (URL, statuses, measures, matched label value and sentence; no page text), `vendordocs.json` and `VENDORDOCS_AUTO.md`, plus the P6 reading notes with links. Data are CC BY 4.0; the code is Apache-2.0.

## Limits, stated in advance

- One reading, en pages only, 30 pages per site, on one day. The sample is clustered by the sitemap files read (at most 25 per site), so it is not a simple random sample of each site.
- The tool sees HTML as served, not after scripts run; the per-site rendered check and G3 address this in part.
- A label in a form we did not anticipate (a badge image, a JSON-LD field with another name) is missed. The raw-HTML search and the rendered check help estimate how often.
- No label is not the same as no AI use. This study measures what readers are told, not how the pages were written.
- The frame is one survey's list of cloud and tooling entries; it leans toward infrastructure products.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: this pre-registration, the tool and its tests were made with AI.
