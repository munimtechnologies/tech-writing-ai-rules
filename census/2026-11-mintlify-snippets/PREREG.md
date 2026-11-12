# Study 16: do Mintlify's Markdown copies for AI agents carry the content of `<Snippet file>` tags?

Pre-registered 2026-11-12, before the tool reads any repository or page in the frame. Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: this plan, the tool and its tests were made with AI.

## Background

Every Mintlify docs site serves a Markdown copy of each page to AI agents (`<page>.md`, or the page address with `Accept: text/markdown`). Mintlify's [Markdown export](https://www.mintlify.com/docs/ai/markdown-export) page (read 2026-11-12) says: "Snippets render the content of the imported file, not the tag such as `<Snippet file="path/to/snippet.mdx" />`", and "If a referenced snippet file isn't found, the Markdown export includes the tag." Its [reusable snippets](https://www.mintlify.com/docs/create/reusable-snippets) page says: "In Markdown page views, a `<Snippet>` tag is replaced by the snippet file, with `docs.json` variables filled in."

**Seen before this plan (disclosed):** on 2026-11-12, through a fetch tool, the Markdown copy of `https://docs.mem0.ai/open-source/python-quickstart` contained the bare tags `<Snippet file="star-on-github.mdx" />` and `<Snippet file="get-help.mdx" />`. Both files exist in [mem0ai/mem0](https://github.com/mem0ai/mem0) under `docs/_snippets/` (not `docs/snippets/`). `get-help.mdx` is a card group linking to Mem0's Discord, GitHub discussions and a call with the founders. A web search returned the HTML version of the same page with that card text ("Ask questions on GitHub", "Talk to founders") after "If you have any questions, please feel free to reach out:", so people reading the page appear to see the snippet while agents reading the copy see a tag. Mem0 also has `docs/_snippets/async-memory-add.mdx`, a notice that add requests are processed in the background for accounts created after 1 July 2025. We have not yet checked which pages use it. No other site in the frame was read.

**Our hypothesis (stated so it can fail):** the Markdown export resolves `<Snippet file="name.mdx">` in `snippets/` but not in the older `_snippets/` folder, which the web renderer still reads. A third-party re-implementation ([rustydocs PR #66](https://github.com/nrynss/rustydocs/pull/66)) describes the bare-name lookup order as `snippets/`, then `_snippets/`, then the root, then the page's folder; Mintlify's own pages do not mention `_snippets/`.

**Prior art (searched 2026-11-12):** Mintlify's docs describe the intended behaviour (above). mintlify/docs has PRs that document how Markdown export converts components and snippets (#7871, #7946) but, in what we read, no issue reporting snippets that stay as tags. rustydocs [#68](https://github.com/nrynss/rustydocs/issues/68) is about its own resolver, not Mintlify's output. We found no check, on any site, of whether `<Snippet file>` content reaches Mintlify's Markdown copies, and no cross-site count.

## Question

On open-source Mintlify docs sites, when a page uses `<Snippet file="...">`, does the page's Markdown copy carry the snippet's text, or the bare tag? Does it depend on whether the file lives in `snippets/` or `_snippets/`? Does the HTML page show the text?

## Frame

22 repositories with their docs folder and live base URL, fixed in `mintsnip.py` (`SITES`): mem0ai/mem0, crewAIInc/crewAI, browser-use/browser-use, Infisical/infisical, triggerdotdev/trigger.dev, ollama/ollama, mintlify/docs, pipecat-ai/docs, Helicone/helicone, novuhq/docs, firecrawl/firecrawl-docs, langgenius/dify-docs, cline/cline, continuedev/continue, supermemoryai/supermemory, agno-agi/docs, formbricks/formbricks, Unstructured-IO/docs, Portkey-AI/docs-core, lmnr-ai/docs, AgentOps-AI/agentops and openlit/openlit. They were chosen from memory as public repositories whose docs we believe are built with Mintlify; we did not check which of them use `<Snippet file>`. Some may have moved, may not use Mintlify any more, or may not use the tag, which the counting rules handle.

## Method

`mintsnip.py` 0.1.0, per repository:

1. Shallow, sparse clone of `main` (`.mdx`, `.md`, `docs.json`, `mint.json` only; a plain shallow clone if sparse checkout fails). The docs root is the given folder if it holds `docs.json` or `mint.json`, else the shallowest folder that does.
2. **Pages:** every `.mdx`/`.md` file under the docs root outside `snippets/` and `_snippets/` (README, AGENTS, CLAUDE, CONTRIBUTING and LICENSE files skipped). **Tags:** unique `file=` values of `<Snippet file="...">` outside fenced code and HTML comments.
3. **Where the file is:** a bare name is looked for in `snippets/`, `_snippets/`, the docs root, then the page's folder; `/x` is root-relative; `./x` and `../x` are page-relative. The location label is the top folder of the file found (`snippets`, `_snippets`, else `other`); `missing` if none is found; `variable` if the name has braces.
4. **Page URL:** the page's path without extension (`index` becomes the folder), mapped to the site's own `llms.txt` (`<base>/llms.txt`): a page is used only if `llms.txt` lists exactly `<base path>/<slug>` on the base host (a trailing `.md`, slash, query or fragment is dropped). Unlisted pages are counted but not read.
5. **Sample:** up to 15 mapped pages with a tag per site, drawn with `random.Random("study16:" + repo)` from the sorted list (all if 15 or fewer). **Controls:** up to 4 mapped pages per site that render an import-style snippet (`import Name from "....mdx"` and `<Name`), drawn the same way with key `repo + ":control"`; the first such import on each page is checked.
6. **Reading:** the Markdown copy is `<url>.md` with `Accept: text/markdown`; it is read if it answers 200 with a non-empty body that is not HTML. The HTML page is `<url>` with `Accept: text/html`. robots.txt is honoured (token `mintsnip`; a 4xx robots.txt allows all; an unreachable one disallows); one request at a time, one second apart; User-Agent names the tool, the repository and MV2's email. The tool checks that this file is on `main` before it reads anything.
7. **Snippet text ("needles"):** from the snippet file, front matter, comments, import/export lines and fence lines removed; tags, Markdown link syntax, `**`, `__` and backticks split the text into fragments; the 3 longest fragments of at least 15 characters without braces, plus the first 2 absolute link targets. Matching is case-insensitive after HTML-unescaping, removing `* _ \` and backticks and collapsing whitespace; a needle "is present" if any needle is a substring. HTML text is the visible text (script, style, template and noscript dropped) plus every `a[href]`.
8. **Status of each (page, tag):** `tag-kept` if the copy still contains `<Snippet file="...<name>">`; else `expanded` if a needle is present; else `lost` if the file has needles; else `no-text`.

## Gate and predictions

Computed by `mintsnip.grade()` over counted sites (a site is counted if at least one read page has a tag whose file was found) and printed in `MINTSNIP_AUTO.md`. Each prediction needs a minimum number of instances, otherwise it is reported as "too few".

- **G1:** at least 3 sites are counted. If G1 fails, P1 to P5 are reported as description and not graded.
- **P1 (Mem0):** of Mem0's instances in `_snippets/` that have needles (at least 5), at least 90% are `tag-kept` and at least 90% have a needle in the HTML page.
- **P2 (`_snippets/`):** pooled over counted sites, at least 80% of instances whose file is in `_snippets/` (at least 10) are `tag-kept`.
- **P3 (`snippets/`):** pooled over counted sites, at most 20% of instances whose file is in `snippets/` (at least 10) are `tag-kept`.
- **P4 (controls):** at least 80% of read control pages with needles (at least 5) have a needle of their imported snippet in the Markdown copy.
- **P5 (people see it):** at least 80% of instances with a found file and needles (at least 10) have a needle in the HTML page.

If P2 holds and P3 fails, the hypothesis is wrong in an informative way: the export would then keep `<Snippet file>` tags wherever the file is, not only in `_snippets/`. Exploratory, not graded: the share of `tag-kept` by location and by site, `lost` instances, `missing` files (a tag that is also broken for people), and sites whose llms.txt does not list their pages.

## Hand check

The tool writes up to 40 excerpt files (`handcheck/NN.txt`: the copy around the tag or needle, and the HTML text around the needle). We will open at least 10 of them across at least 3 sites, and the live copy and page for at least 5, and record in `hand_check.csv` whether each status is right. If more than 1 in 10 checked statuses is wrong, RESULT.md says so and reports which prediction verdicts rest on the wrong cases.

## What will be published

`sites.csv`, `instances.csv`, `controls.csv`, `mintsnip.json` and `MINTSNIP_AUTO.md` unchanged, plus `RESULT.md`, `hand_check.csv` and a test that recomputes the gate and predictions from the published CSVs. The handcheck excerpts quote the sites' own text and are not republished.

## Deviations

Any change to the frame, the tool or the rules after this file is on `main` will be listed in RESULT.md with its reason. If the run fails for a reason outside the tool (compute, network), it is re-run unchanged and the date of the reading is reported.

## Why it matters

Agents read the Markdown copy instead of the page. A bare `<Snippet file="get-help.mdx" />` costs an agent little, but the same mechanism carries shared notices (such as Mem0's note that `add` now runs in the background), install steps and warnings that docs teams write once and include on many pages. If the export ignores a folder that the web renderer still reads, every site that kept the older layout is sending agents tags where its people see content, and nobody checking the HTML page would notice.
