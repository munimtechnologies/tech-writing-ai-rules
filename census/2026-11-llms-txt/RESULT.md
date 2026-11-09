# Study 5 result: do projects with AI contribution rules serve their docs to AI readers?

Graded 2026-11-08 against the [pre-registration](PREREGISTRATION.md), which was first committed at 02:32:39 UTC (commit `a113718`). `llmsprobe.py` 0.1.0 read every docs base from 12:22:03 to 12:27:50 UTC the same day (432 requests), almost ten hours later. Nothing in the frame, the measures or the predictions was changed after the reading.

**Correction, 2026-11-09:** one label was corrected after a follow-up fetch. Home Assistant's docs page had been labelled a bot-check ("challenge") page, unconfirmed. A re-fetch with the same headers on 2026-11-09 got the normal documentation page, and the words that matched were Cloudflare's background script, not a bot check (see Hand check). The label is now "no". P5 becomes 1 of 10 against 1 of 46 and still holds; no other outcome changes.

Made by MV2 of Munim, Inc., with AI agents working in his name. The hand check was done by one AI agent coder. Text and data CC BY 4.0, code Apache-2.0.

## Short answer

**27 of the 56 projects (48%) serve a valid llms.txt or llms-full.txt for their docs. All 27 are among the 46 projects whose AI contribution rule allows AI-made work (59%). None of the 10 projects that ban or restrict it serves one** (GCC, Gentoo, Godot, NetBSD, OpenJDK, QEMU, SDL, SQLite, Home Assistant, Rust). 21 of the 27 also serve llms-full.txt, the whole documentation in one file. Only 2 projects refuse AI readers outright: Gentoo's wiki robots.txt disallows the whole site to 93 named crawlers, including all 20 we check, and Gitea's docs host blocks 11 of them in a Cloudflare-managed section. Home Assistant's docs page was first labelled a bot-check page by the tool; a re-fetch showed a normal page, and the label was corrected (see Hand check).

All five pre-registered predictions held, and the gate passed (56 of 56 projects reached). **The split by stance is real in this frame, but it should not be read as cause.** The projects that serve llms.txt are mostly young AI and JavaScript projects, while the ones that ban AI are long-established C and systems projects. Ten long-established projects that allow AI work also serve nothing: CPython, curl, Debian, Django, Fedora, Kubernetes, the Linux kernel, LLVM, Mesa and Firefox.

## Gate and predictions (hand-checked labels)

| | Prediction | Hand-checked | Automatic | |
|---|---|---|---|---|
| G1 | at least 50 of 56 projects reached | 56 of 56 | 56 of 56 | **Passed** |
| P1 | 14 to 33 of the 56 projects SERVE | 27 of 56 (48.2%) | 27 | **Held** |
| P2 | at most 1 of the 10 BAN or RESTRICTED projects SERVES | 0 of 10 | 0 | **Held** |
| P3 | OPEN share that SERVES is at least 25 points above the BAN+RESTRICTED share | 58.7% vs 0.0% (58.7 points) | 58.7 points | **Held** |
| P4 | at least half of the SERVING projects also SERVE_FULL | 21 of 27 (77.8%) | 20 of 27 | **Held** |
| P5 | BAN+RESTRICTED share that REFUSES_AI_READERS is above the OPEN share | 1 of 10 (10.0%) vs 1 of 46 (2.2%) | 2 of 10 (20.0%) vs 1 of 46 (2.2%) | **Held** |

The first version of this file (2026-11-08) gave P5 as 2 of 10 against 1 of 46, counting the unconfirmed Home Assistant label; the corrected value is above.

**Robustness.** Each of these changes leaves every outcome the same:

- Home Assistant's original challenge label kept (as the tool gave it): P5 is 2 of 10 (20.0%) vs 2.2%, and still holds.
- Counting hosts instead of projects (LangChain and LangGraph share docs.langchain.com, and PostHog and posthog-js share posthog.com; both pairs serve): 54 units, 25 serve (46.3%), OPEN 25 of 44 (56.8%), P3 difference 56.8 points, P4 19 of 25.
- Hono's llms-full.txt left as the tool labelled it (not valid): P4 is 20 of 27.

As a descriptive check that was not pre-registered, a one-sided Fisher exact test of 0 of 10 against 27 of 46 gives p ≈ 0.0006. That only says the split is unlikely to be chance in this frame. It does not separate stance from project age, language or docs platform.

## Hand check

The pre-registration asked for every valid file, every status-200 answer that was not valid, every challenge and every AI_BLOCK case to be read. All were read: the first 2,000 characters kept in `census.json` for each of the 52 valid answers (fewer distinct files, because LangChain and LangGraph, and PostHog and posthog-js, share URLs), the robots.txt files of the three hosts with named-agent rules (read live on 2026-11-08, about three hours after the run), and the redirect and HTML answers.

**Labels changed (2):**

- **Hono, `https://hono.dev/llms-full.txt`: html → valid.** It is served as `text/plain`, has 396 Markdown links and is Hono's full developer documentation. The tool called it HTML because its first character is `<`: the file opens with `<SYSTEM>This is the full developer documentation for Hono.</SYSTEM>` followed by `# Start of Hono documentation`. Effect: SERVES_FULL 20 → 21 (P4).
- **Home Assistant, `https://www.home-assistant.io/docs/`: challenge yes → no (corrected 2026-11-09).** The tool matched its bot-check pattern on the HTML of this page, which answered 200, and the saved data did not keep the page's text. A follow-up fetch on 2026-11-09 at about 09:24 UTC, with the same `Accept` headers and the tool's own User-Agent, got a 200 `text/html` page of 43,215 characters titled "Documentation - Home Assistant". The only match was the string `challenge-platform` near the end of the page, inside Cloudflare's background script (`/cdn-cgi/challenge-platform/scripts/precursor/main.js`), which Cloudflare adds to normal pages. It is not an interstitial: the page is the documentation itself. The Markdown request again got a 200 `text/markdown` copy of the docs page. Effect: CHALLENGE 1 → 0 and REFUSES_AI_READERS 3 → 2; P5 becomes 1 of 10 (10.0%) against 1 of 46 (2.2%) and still holds. **Known limit of `llmsprobe.py` 0.1.0** (not fixed here): its bot-check pattern includes `challenge-platform`, which also appears in Cloudflare's background script on normal pages. A later version should look for interstitial markers only (a "Just a moment" title, `_cf_chl_opt`) and keep the matched words.

**Labels kept, with notes:**

- **Node.js, AI_BLOCK = no.** nodejs.org's robots.txt has a single group, `User-Agent: *`, with `Disallow: /docs/`. Every agent, AI or not, is kept out of `/docs/latest/api/`, so this is not an AI block under the pre-registered definition, which requires an agent without a group of its own to be allowed. Our tool honoured it, so the docs-folder llms.txt files were not requested. Node.js serves a valid root `https://nodejs.org/llms.txt`, but **every API page it lists is under `/docs/latest/api/`, a path its own robots.txt disallows for all crawlers.**
- **Gentoo, AI_BLOCK = yes.** wiki.gentoo.org's robots.txt has one group of 93 named crawlers, including all 20 we check, with `Disallow: /`. The `*` group only excludes search and API paths. devmanual.gentoo.org has no robots.txt.
- **Gitea, AI_BLOCK = yes.** docs.gitea.com's robots.txt blocks 11 of our 20 agents (GPTBot, ClaudeBot, anthropic-ai, CCBot, Google-Extended and others) inside a block marked "BEGIN Cloudflare Managed content". It also declares `Content-Signal: search=yes,ai-train=no,use=reference`. Fetch-on-request agents such as ChatGPT-User and Claude-User are not blocked. The pre-registration's limits apply: a host's rules may be set by its platform rather than by the project.
- **Haystack, valid llms.txt but not an index.** `https://docs.haystack.deepset.ai/llms.txt` is 2.85 MB of concatenated docs source files. Its first file is the docs folder's `AGENTS.md`, the instructions for AI agents that **edit** the docs ("Edit `docs-website/docs/pipeline-components/` pages only for outdated, incorrect, or materially useful guidance..."). It meets the pre-registered test (it has links), and it is full documentation text.
- **Pydantic AI, valid without an H1.** Both files open with `## Querying This Documentation` (see below), then `# Pydantic AI`.
- **Redirects and HTML answers kept as not valid.** Django's and Gentoo's root requests redirect to the docs home page (HTML). The four developers.home-assistant.io requests redirect to the Markdown home page of contributors.home-assistant.io (not an llms.txt). Cal.com's root llms-full.txt is the site's HTML app shell. Its docs-folder llms-full.txt is valid, so Cal.com still serves both files.

**A side observation from the follow-up (not part of any prediction):** in the same follow-up, `www.home-assistant.io/robots.txt` answered our tool's own User-Agent with 200 (`User-agent: *` / `Disallow:`, which allows everything), but answered Python's default User-Agent (`Python-urllib`) with a 403 Cloudflare "Error 1010: Access denied" page, served as Markdown. So a client's User-Agent can decide whether it can read a site's robots.txt at all. That is why an earlier follow-up, which read robots.txt with Python's default agent, wrongly concluded it was disallowed and fetched nothing.

## Codes by group

| Group | Projects | SERVE | SERVE_FULL | Markdown on request | AI_BLOCK | Challenge | Refuses AI readers |
|---|---|---|---|---|---|---|---|
| BAN | 8 | 0 | 0 | 1 (Godot) | 1 (Gentoo) | 0 | 1 |
| RESTRICTED | 2 | 0 | 0 | 1 (Home Assistant) | 0 | 0 | 0 |
| OPEN | 46 | 27 | 21 | 18 | 1 (Gitea) | 0 | 1 |
| All | 56 | 27 | 21 | 20 | 2 | 0 | 2 |

Each project's row is in [`coding.csv`](coding.csv).

**Serving projects (27):** Cal.com (cal.diy), Coder, crewAI, Dify, Documenso, Formbricks, Haystack, Hono, Hugging Face Transformers, Inspect AI, Instructor, LangChain, LangGraph, Linux Foundation (its LFX docs), LlamaIndex, MCP Python SDK, MCP TypeScript SDK, Model Context Protocol (spec), Next.js, Node.js, Open WebUI, OpenHands, PostHog, posthog-js, Pydantic AI, Storybook and tRPC. Haystack, Instructor, LlamaIndex, Node.js, PostHog and posthog-js serve llms.txt only.

**OPEN projects serving nothing (19):** AnythingLLM, Apache Airflow, CPython, curl, Debian, Django, Fedora, Gemara, Ghostty, Gitea, Kubeflow, Kubernetes, Linux kernel, LLVM, Mesa, Mozilla Firefox, pytest, Shaka Player and vLLM. Three of them did something else for or about AI readers: pytest and vLLM serve Markdown on request, and Gitea's host blocks named AI crawlers. So "no llms.txt" does not always mean "no thought for AI readers".

**Policies that mention llms.txt:** 3. LangChain and LangGraph (one shared contributing page) and the MCP TypeScript SDK's CONTRIBUTING mention it once each. No BAN or RESTRICTED policy mentions it. SQLite's policy page was not read because robots.txt disallowed it.

## What else the files say (descriptive, not pre-registered)

These come from the first 2,000 characters of each valid file only.

- **Many llms.txt files talk to AI agents directly.** 8 hosts (9 projects) put instructions to agents near the top. Cal.com's llms-full.txt opens with an agent quickstart and "Instructions for the agent". LlamaIndex has "Instructions for AI agents", and PostHog "Instructions for AI Coding Assistants". Next.js tells agents to "use this site as the source of truth" and to cite the canonical URL, and Open WebUI asks agents to cite canonical HTML URLs. The Linux Foundation's GitBook file has "Agent Instructions", and Haystack's opens with its docs AGENTS.md. **Pydantic AI asks every agent to add `intent`, `stack` and `harness` query parameters to each request**, "so the pages where agents get stuck ... get fixed first". This is a direct request to AI readers to report what they are doing, and it tells them never to include personal or confidential information.
- **The writing rule and the reading rule can sit in the same file.** Haystack's llms.txt opens with the rules for AI agents that edit its docs, so an AI reader gets the docs writers' AI rules first. In study 3, we found that most separate docs repos never show their project's AI contribution rule at all.
- **Content-Signal lines** appear on 9 hosts. Two say `ai-train=no` (Cal.com and Gitea). The other seven allow AI training (`ai-train=yes`) for at least one group: crewAI, Dify, docs.langchain.com, the Linux Foundation's docs, modelcontextprotocol.io, OpenHands and pydantic.dev.
- **Markdown on request without llms.txt.** Godot (BAN), Home Assistant (RESTRICTED), pytest and vLLM answer `Accept: text/markdown` with Markdown, but serve no llms.txt.

## What this adds

Web-wide counts of llms.txt adoption range from about 5% to 28% of domains, depending on the sample. Their differences come from sampling and from root-only crawls that miss `/docs/llms.txt`; the sources are in the pre-registration. Among open-source projects that have set rules for AI contributions, adoption is much higher (48%) and is concentrated entirely among the projects that allow AI-made work. We found no earlier count that puts a project's rule on AI **writing** next to how its docs treat AI **readers**. Projects that ban AI-made contributions here do not refuse AI readers much more: one of eight does, by robots.txt. They simply do not prepare anything for them.

## Limits

- **Confounded groups.** Stance comes with age, language, ecosystem and docs platform. Most serving projects are on hosted docs platforms that can generate llms.txt automatically, and the BAN group is all long-established, self-hosted projects. This study cannot separate these factors.
- **Small groups.** BAN+RESTRICTED has 10 projects, so P2, P3 and P5 are weak tests, as the pre-registration said. P5 now rests on one project in each group.
- **Paths tried.** Only the base's folder and the host root were tried. A project may serve llms.txt at another path, such as a different docs version or language. The tool honours robots.txt, so Node.js's docs-folder files were not requested.
- **One reading, one coder.** Everything was read once, on 2026-11-08, from one network, and hand-checked by one AI agent coder (the Home Assistant label was re-fetched once more on 2026-11-09). Every label can be re-checked from the published URLs.
- **robots.txt is a wish.** It expresses what a site asks of crawlers, not what crawlers do, and serving llms.txt says nothing about whether any AI reader uses it.

## Files

- [`PREREGISTRATION.md`](PREREGISTRATION.md), [`frame.json`](frame.json): fixed before reading.
- [`coding.csv`](coding.csv): one row per project with the hand-checked labels, the automatic labels where they differ, and notes.
- [`LLMSPROBE_AUTO.md`](LLMSPROBE_AUTO.md), [`frame.csv`](frame.csv), [`bases.csv`](bases.csv), [`probes.csv`](probes.csv), [`projects.csv`](projects.csv): the tool's unchanged output (they still show Home Assistant's original challenge label).
- `census.json`, which holds the first 2,000 characters of each file, is not republished. `python llmsprobe.py --out-dir out --no-prereg-check` reproduces a fresh reading.

Nothing here is legal advice or a judgement on any project. Read each project's own pages before relying on them.
