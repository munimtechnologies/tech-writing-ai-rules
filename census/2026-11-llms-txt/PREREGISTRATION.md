# Study 5 pre-registration: do projects with AI contribution rules serve their docs to AI readers?

Written 2026-11-08 before the study's tool has requested any llms.txt file, robots.txt or docs page. The tool (`llmsprobe.py` 0.1.0, with offline tests in `test_llmsprobe.py`) waits until this file is on `main` before it fetches anything.

## Why

Studies 2 to 4 asked what projects and style guides say about writing **with** AI. Study 4 found that 4 of 14 style guides now give advice on writing **for** AI readers (LLMs, AI search, crawlers). This study asks the same question of practice: do the 56 open-source projects that set terms for AI-made contributions also serve their documentation to AI readers, and does that depend on how strict their contribution rule is?

Prior art (searched 2026-11-08). Many studies count llms.txt adoption across the web: SE Ranking (about 300,000 domains, 10.13%), Ahrefs (137,000 domains, 28%, and 97% of files never read), Rankability (top 1,000 and 10,000 domains, about 8-9%), an HTTP Archive analysis (5.61% of the top 10,000 in June 2026), and a meta-review that explains why the figures disagree (sampling, and root-only crawls that miss `/docs/llms.txt`). Robots.txt blocking of AI crawlers has been measured for news and top sites. We found no count of either one for open-source projects grouped by their own rule on AI-made contributions. This study is the first we know of that puts a project's rule on AI writing **into** its docs next to how it treats AI **readers** of those docs.

## Frame

All 56 projects that study 2 coded as setting terms for AI-made contributions (`census/2026-11-oss-docs/coding.csv`, rule = yes; release v0.3.0). Groups come from the stance label in the open dataset awesome-ai-contribution-policies (commit `6cd258e`), not from our coding:

- **BAN** (stance `ban`), 8 projects: GCC, Gentoo, Godot Engine, NetBSD, OpenJDK, QEMU, SDL, SQLite.
- **RESTRICTED** (stance `restricted`), 2 projects: Home Assistant, Rust.
- **OPEN** (every other stance), 46 projects.

`frame.json` gives each project one or two documentation base URLs (its docs home page), chosen by hand on 2026-11-08 from the project's own links and the docs sites study 2 and study 3 read, plus the policy page study 2 quoted. Disclosure: while checking three docs addresses, web search results showed in passing that LlamaIndex's docs serve an llms.txt and that the MCP TypeScript SDK serves Markdown copies of pages. No other llms.txt answer was seen before this file was written. Unit of analysis: the project. LangChain and LangGraph share one docs site, and PostHog and posthog-js share one host; a host-level count is reported next to the project count.

## Measures (automatic, by `llmsprobe.py`)

For each base the tool reads the base page, the same page with `Accept: text/markdown`, robots.txt of the host the base page lands on, and `llms.txt` and `llms-full.txt` both in the base's own folder and at the host root. It honours robots.txt for its own agent name (`tech-writing-ai-rules-llmsprobe`) on every fetch, waits 0.5 s between requests and retries an HTTP 429 after 60, 120 and 240 s.

- **SERVES** (per project): at least one requested llms.txt or llms-full.txt answer is **valid**: status 200, the same file name after redirects, not HTML, at least 50 non-space characters, and either a Markdown H1 (`# ...`) in its first 50 lines or at least three Markdown links. Other labels: html (an app shell or a 200 error page), challenge (a bot-check page such as Anubis or a Cloudflare "Just a moment..."), redirected, missing, short, unstructured, error, robots.
- **SERVES_FULL**: a valid llms-full.txt.
- **SPEC_H1**: a valid file's first non-empty line is an H1, as the llms.txt proposal asks (descriptive).
- **MARKDOWN**: the base page comes back as `text/markdown` when asked for it (descriptive).
- **AI_BLOCK**: robots.txt of the base's host disallows the base page for at least one of 20 named AI crawlers and fetchers (GPTBot, ChatGPT-User, OAI-SearchBot, ClaudeBot, Claude-User, Claude-SearchBot, anthropic-ai, CCBot, Google-Extended, PerplexityBot, Perplexity-User, Bytespider, Applebot-Extended, meta-externalagent, Amazonbot, cohere-ai, Diffbot, Omgilibot, Timpibot, YouBot), while an agent without a group of its own may fetch it. Matching follows RFC 9309 and Google's rules: the agent's own group if it has one, else `*`; the longest matching rule wins, and Allow wins a tie. A robots.txt that is missing (404/410) blocks nothing. Any other answer (5xx, HTML, unreachable) is **unknown**. Content-Signal lines are recorded (descriptive).
- **CHALLENGE**: the base page or a requested file answers with a bot-check page.
- **REFUSES_AI_READERS** = AI_BLOCK or CHALLENGE.
- **POLICY_MENTION**: how often "llms.txt" or "llms-full.txt" appears on the project's policy page (descriptive; robots.txt is honoured, so some raw GitHub files may not be read).

## Hand check

Every valid file is checked by reading its first 2,000 characters (kept in `census.json`): it must be an llms.txt-style index or full text of that project's documentation. Every status-200 answer that is not valid (html, short, unstructured) and every challenge and AI_BLOCK case is read too. A label is changed only with a stated reason, and the RESULT lists every change. **Predictions are graded on the hand-checked labels**, and the automatic values are shown next to them.

## Gate

- **G1**: at least 50 of the 56 projects are reached (some HTTP answer from a base or a requested file). If G1 fails, the counts are reported as descriptive and no prediction is graded.

## Predictions

- **P1**: 14 to 33 of the 56 projects (25% to 59%) SERVE.
- **P2**: at most 1 of the 10 BAN or RESTRICTED projects SERVES.
- **P3**: the OPEN share that SERVES is at least 25 percentage points higher than the BAN+RESTRICTED share.
- **P4**: at least half of the projects that SERVE also SERVE_FULL.
- **P5**: the BAN+RESTRICTED share that REFUSES_AI_READERS is higher than the OPEN share.

`llmsprobe.py` computes the gate and all five predictions from its automatic labels in `LLMSPROBE_AUTO.md`; the RESULT grades them again after the hand check.

## Limits known in advance

One reading on one day from one network; sites change. The base URLs are our choice of each project's docs home, and a project may serve llms.txt at a path we do not request (only the base folder and the host root are tried). robots.txt rules on AI crawlers express a wish, not what crawlers do, and a host's rules may be set by its hosting platform rather than the project. The BAN+RESTRICTED group is small (10), so P2, P3 and P5 are weak tests. Serving llms.txt says nothing about whether any AI reader uses it.

## What will be published

`frame.json`, this file, the tool and tests now. After the run: `RESULT.md`, `coding.csv` (one row per project with the hand-checked labels), and the tool's `frame.csv`, `bases.csv`, `probes.csv`, `projects.csv` and `LLMSPROBE_AUTO.md`. `census.json`, which holds the first 2,000 characters of each file, is not republished.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the design, the tool and this text were made with AI. Text and data CC BY 4.0, code Apache-2.0.
