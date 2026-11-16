# Study 15 result: empty component tags in Nuxt Content /raw/ copies

Graded 2026-11-16. Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the tool, the grading, the hand check and this text were made with AI. Licence: text and data CC BY 4.0, code Apache-2.0.

Plan: [PREREG.md](PREREG.md) (2026-11-12). Changes after the first run: [DEVIATIONS.md](DEVIATIONS.md). Data: [`run-v2/`](run-v2/) (the graded run, unchanged tool output), [`hand_check.csv`](hand_check.csv). [`test_study15_result.py`](../../test_study15_result.py) recomputes every number below from those files.

## Short answer

On 7 documentation sites that send AI agents to Nuxt Content's `/raw/*.md` copies, **22 of 193 sampled copies (11.4%) contain an empty component tag**: a tag with nothing inside, such as `<partial content="config-env-vars"></partial>`. That is fewer than the 15% predicted. And on most sites an empty tag is not a hole in the content. **In the hand check, only the two Directus copies lost text that the page shows people** (a callout and a JSON example). Elsewhere the empty tags were badges, buttons and feature cards whose text sits in an attribute (`label="Deprecated"`), or decorative icons.

## The run that was graded

`nuxtraw.py` 0.2.0 (job `nuxtraw-v2`), read on 2026-11-15 between 16:04 and 16:18 UTC. It used the same frame, sample and seeds as the plan, with the two fixes described in DEVIATIONS.md. The gate held: 7 sites counted (G1 needs 4): nuxt.com, ui.nuxt.com, content.nuxt.com, docus.dev, i18n.nuxtjs.org, supabase.nuxtjs.org and directus.com/docs, with 193 copies read.

## A third error, found by the hand check

Two of the ten hand-checked "empty" copies had no empty tag at all. ui.nuxt.com's copy of the Drawer page writes its warning callout as a Markdown blockquote, so the line that opens a Vue example reads `> ```vue [app.vue]`. Version 0.2.0 only recognised a code fence at the start of a line. It read the example as prose and counted `<NuxtPage />` as an empty component tag. nuxt.com's Icon bundles page was flagged the same way, for two `<Icon>` tags inside a code example in a tip callout. Both were the tool's error, not the sites'.

The verdicts below use the 0.2.0 output with these two copies corrected by hand. Version 0.3.0 recognises fences inside blockquotes and is re-running the same sample as `nuxtraw-v3`. Its counts will be added here when it finishes, whichever way they come out.

## Verdicts

P1 to P3 are not blind (see DEVIATIONS.md): we saw the first run's tag names before writing 0.2.0.

| | Prediction | Tool (0.2.0) | After hand check | Verdict |
|---|---|---|---|---|
| P1 | At least half the counted sites have a copy with an empty tag | 7 of 7 | 5 of 7 (nuxt.com and ui.nuxt.com drop to 0) | **holds** (not blind) |
| P2 | At least 15% of copies have an empty tag | 24/193 = 12.4% | 22/193 = 11.4% | **fails** (not blind) |
| P3 | At least 2 sites besides Directus have empty tags in at least 10% of copies | content.nuxt.com 23.3%, docus.dev 20.0% | unchanged | **holds** (not blind) |
| P4 | Copies with an empty tag have a lower median words ratio | 1.034 vs 1.029 | 1.0405 vs 1.0275 | **fails** |
| P5 | Every site's median words ratio is at least 0.5 | lowest ui.nuxt.com 0.781 | unchanged | **holds** |

The words ratio is the copy's word count divided by the words in the rendered page's `<main>`. In 0.2.0 every page was received as HTML (192 of 193; one nuxt.com page timed out). So P4 and P5 measured something this time, unlike in the first run.

Copies with an empty tag, by site, after the hand check: content.nuxt.com 7/30, directus.com/docs 7/30, docus.dev 6/30, supabase.nuxtjs.org 1/13, i18n.nuxtjs.org 1/30, nuxt.com 0/30, ui.nuxt.com 0/30.

## Hand check

As planned, we checked the first two flagged copies and the first clean copy on each counted site: 10 flagged and 7 clean. We read each copy and its page once, on 2026-11-16, through a fetch tool that summarises pages and quotes at most about 125 characters. So the checks rest on short quotes, not on byte-level reads. The fence prefix was confirmed character by character only on the ui.nuxt.com copy; on the nuxt.com copy it is inferred from the same callout markup.

| What the flagged tag turned out to be | Copies | Where |
|---|---|---|
| Not an empty tag: code inside a blockquoted callout (tool error) | 2 | nuxt.com, ui.nuxt.com |
| Visible text kept in an attribute (badge, button, feature-card labels) | 5 | content.nuxt.com ×2, docus.dev, i18n.nuxtjs.org, supabase.nuxtjs.org |
| Decoration (an icon) | 1 | docus.dev |
| **Content the page shows that the copy lacks** | **2** | **directus.com/docs** |

The two real losses:

- `configuration/logging`: `<partial content="config-env-vars"> </partial>` stands where the page shows an "Environment Variables" callout ("Environment variables are configurable for Directus Enterprise Cloud projects via our Customer Success team.").
- `guides/auth/email-login`: `<partial content="snippet-auth-token">` stands where the page shows a JSON example of the login response, with `expires`, `access_token` and `refresh_token`.

All 7 clean copies were confirmed clean. The plan's decoration rule says to recount P1 to P3 on `bare` tags only if more than 1 in 5 checked copies are decoration. Here 1 in 10 was, so the rule was not triggered. As a sensitivity check only, a bare-only count gives 11/193 copies (5.7%) on 3 of 7 sites, and under it P1 and P3 would fail.

## Exploratory: asking the page address for Markdown

This part is not graded. For each copy, the tool also asked the page's own address for `Accept: text/markdown`. 6 of the 7 sites answered with Markdown (163 of 193 copies). i18n.nuxtjs.org sent HTML. On five sites the Markdown matched the `/raw/` copy (133 copies). Directus answered with Markdown on all 30 pages, but none of them matched its `/raw/` copy.

This kind of content negotiation is already documented. It is described by [Vercel](https://vercel.com/docs/agent-resources/markdown-access) and [Cloudflare](https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents), the [nuxt-agent-discovery](https://github.com/benjamincanac/nuxt-agent-discovery) module and [Nuxt AI Ready](https://nuxtseo.com/docs/ai-ready/guides/markdown). So we report the counts as confirmation, not as a finding. One open question is about Directus. MV2's report [directus/docs#865](https://github.com/directus/docs/issues/865) noted that Directus's `/docs/<path>.md` copies fill partials in, while its llms.txt links the `/raw/` copies, which don't. If the Markdown served at the page address is the filled-in version, then agents that send `Accept: text/markdown` to the page get the full text, and only agents that follow llms.txt get the holes. Version 0.3.0 records the empty tags in the negotiated Markdown, its `Vary` and `x-markdown-tokens` headers and its word count, to test this.

## What this means for docs teams

- **Nuxt Content sites that use partials or snippets** (Directus here) give agents a `/raw/` copy with a hole where the partial goes. The fix could go in the raw route, which could expand partials before it prints the copy, or in which copies llms.txt links to. This matches what MV2 reported to Directus in [directus/docs#865](https://github.com/directus/docs/issues/865), which is still open with no maintainer reply.
- **Badge and button components** (`<u-badge label="Deprecated">`) keep their text in an attribute. An agent that reads attributes gets it. One that strips tags loses words like "Deprecated" or "removed". This is smaller than a missing partial, but on i18n.nuxtjs.org's migration guide it covers 19 status labels.
- **Anyone measuring Markdown copies** should treat `>`-prefixed code fences as code. GitHub-style callouts (`> [!NOTE]`) put fenced code inside blockquotes, and a line-start fence rule will count that code as prose. This was our third tool error in this study. Both earlier ones are in DEVIATIONS.md.

## Limits

- 7 sites, all from one ecosystem, read once. Copies change as sites redeploy.
- P1 to P3 are not blind. The hand check covers 17 of 193 copies, and we read them through a summarising fetch tool.
- The verdicts correct two copies by hand. The machine re-run (0.3.0) may find other copies affected by the same fence error, which would lower the 11.4% further.
