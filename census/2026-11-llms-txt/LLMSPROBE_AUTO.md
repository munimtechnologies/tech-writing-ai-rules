# Do projects with AI contribution rules serve their docs to AI readers? Automatic labels

llmsprobe.py 0.1.0. Frame: 56 projects from https://raw.githubusercontent.com/munimtechnologies/tech-writing-ai-rules/main/census/2026-11-llms-txt/frame.json. Fetched 2026-11-08T12:22:03Z to 2026-11-08T12:27:50Z UTC (432 requests). Pre-registration first committed: 2026-11-08T02:32:39Z.

These are the tool's labels before the hand check the pre-registration asks for.

| Group | Projects | Reached | Serve llms.txt or llms-full.txt | llms.txt | llms-full.txt | Markdown on request | robots.txt blocks a named AI crawler | Bot challenge | Refuses AI readers |
|---|---|---|---|---|---|---|---|---|---|
| BAN | 8 | 8 | 0 | 0 | 0 | 1 | 1 (0 unknown) | 0 | 1 |
| RESTRICTED | 2 | 2 | 0 | 0 | 0 | 1 | 0 (0 unknown) | 1 | 1 |
| OPEN | 46 | 46 | 27 | 27 | 20 | 18 | 1 (0 unknown) | 0 | 1 |
| ALL | 56 | 56 | 27 | 27 | 20 | 20 | 2 (0 unknown) | 1 | 3 |

## Gate and predictions (automatic labels)

| | Prediction | Value | Held |
|---|---|---|---|
| G1 | at least 50 of the 56 projects reached | 56 of 56 | yes |
| P1 | 14 to 33 of the 56 projects serve a valid llms.txt or llms-full.txt | 27 of 56 | yes |
| P2 | at most 1 of the 10 BAN or RESTRICTED projects serves one | 0 of 10 | yes |
| P3 | OPEN share minus BAN+RESTRICTED share is at least 25 points | 58.7 points | yes |
| P4 | at least half of the serving projects also serve llms-full.txt | 20 of 27 | yes |
| P5 | BAN+RESTRICTED share refusing AI readers is higher than the OPEN share | 20.0% vs 2.2% | yes |

## Projects

| id | project | group | reached | llms.txt | llms-full.txt | H1 first | Markdown | AI crawlers blocked | challenge | policy mentions llms.txt |
|---|---|---|---|---|---|---|---|---|---|---|
| D003 | AnythingLLM | OPEN | yes | no | no |  | no | none | no | 0 |
| D004 | Apache Airflow | OPEN | yes | no | no |  | no | none | no | 0 |
| D006 | cal.diy (Cal.com) | OPEN | yes | yes | yes | yes | yes | none | no | 0 |
| D011 | Coder | OPEN | yes | yes | yes | yes | no | none | no | 0 |
| D012 | CPython | OPEN | yes | no | no |  | no | none | no | 0 |
| D014 | crewAI | OPEN | yes | yes | yes | yes | yes | none | no | 0 |
| D015 | curl | OPEN | yes | no | no |  | no | none | no | 0 |
| D016 | Debian | OPEN | yes | no | no |  | no | none | no | 0 |
| D018 | Dify | OPEN | yes | yes | yes | yes | yes | none | no | 0 |
| D019 | Django | OPEN | yes | no | no |  | no | none | no | 0 |
| D020 | Documenso | OPEN | yes | yes | yes | yes | no | none | no | 0 |
| D025 | Fedora | OPEN | yes | no | no |  | no | none | no | 0 |
| D027 | Formbricks | OPEN | yes | yes | yes | yes | yes | none | no | 0 |
| D028 | GCC | BAN | yes | no | no |  | no | none | no | 0 |
| D029 | Gemara | OPEN | yes | no | no |  | no | none | no | 0 |
| D030 | Gentoo | BAN | yes | no | no |  | no | Amazonbot, Applebot-Extended, Bytespider, CCBot, ChatGPT-User, Claude-SearchBot, Claude-User, ClaudeBot, Diffbot, GPTBot, Google-Extended, OAI-SearchBot, Omgilibot, Perplexity-User, PerplexityBot, Timpibot, YouBot, anthropic-ai, cohere-ai, meta-externalagent | no | 0 |
| D031 | Ghostty | OPEN | yes | no | no |  | no | none | no | 0 |
| D032 | Gitea | OPEN | yes | no | no |  | no | Amazonbot, Applebot-Extended, Bytespider, CCBot, ClaudeBot, Diffbot, GPTBot, Google-Extended, anthropic-ai, cohere-ai, meta-externalagent | no | 0 |
| D034 | Godot Engine | BAN | yes | no | no |  | yes | none | no | 0 |
| D035 | Haystack | OPEN | yes | yes | no | no | no | none | no | 0 |
| D036 | Home Assistant | RESTRICTED | yes | no | no |  | yes | none | yes | 0 |
| D037 | Hono | OPEN | yes | yes | no | yes | yes | none | no | 0 |
| D038 | Hugging Face Transformers | OPEN | yes | yes | yes | yes | yes | none | no | 0 |
| D041 | Inspect AI | OPEN | yes | yes | yes | yes | no | none | no | 0 |
| D042 | Instructor | OPEN | yes | yes | no | yes | no | none | no | 0 |
| D043 | Kubeflow | OPEN | yes | no | no |  | no | none | no | 0 |
| D044 | Kubernetes | OPEN | yes | no | no |  | no | none | no | 0 |
| D045 | LangChain | OPEN | yes | yes | yes | yes | yes | none | no | 1 |
| D048 | LangGraph | OPEN | yes | yes | yes | yes | yes | none | no | 1 |
| D049 | Linux Foundation | OPEN | yes | yes | yes | yes | yes | none | no | 0 |
| D050 | Linux kernel | OPEN | yes | no | no |  | no | none | no | 0 |
| D052 | LlamaIndex | OPEN | yes | yes | no | yes | no | none | no | 0 |
| D053 | LLVM | OPEN | yes | no | no |  | no | none | no | 0 |
| D056 | MCP Python SDK | OPEN | yes | yes | yes | yes | no | none | no | 0 |
| D058 | MCP TypeScript SDK | OPEN | yes | yes | yes | yes | no | none | no | 1 |
| D060 | Mesa | OPEN | yes | no | no |  | no | none | no | 0 |
| D062 | Model Context Protocol (spec) | OPEN | yes | yes | yes | yes | yes | none | no | 0 |
| D063 | Mozilla Firefox | OPEN | yes | no | no |  | no | none | no | 0 |
| D067 | NetBSD | BAN | yes | no | no |  | no | none | no | 0 |
| D068 | Next.js | OPEN | yes | yes | yes | yes | yes | none | no | 0 |
| D069 | Node.js | OPEN | yes | yes | no | yes | no | Amazonbot, Applebot-Extended, Bytespider, CCBot, ChatGPT-User, Claude-SearchBot, Claude-User, ClaudeBot, Diffbot, GPTBot, Google-Extended, OAI-SearchBot, Omgilibot, Perplexity-User, PerplexityBot, Timpibot, YouBot, anthropic-ai, cohere-ai, meta-externalagent | no | 0 |
| D072 | Open WebUI | OPEN | yes | yes | yes | yes | no | none | no | 0 |
| D074 | OpenHands | OPEN | yes | yes | yes | yes | yes | none | no | 0 |
| D075 | OpenJDK | BAN | yes | no | no |  | no | none | no | 0 |
| D076 | PostHog | OPEN | yes | yes | no | yes | no | none | no | 0 |
| D077 | posthog-js | OPEN | yes | yes | no | yes | yes | none | no | 0 |
| D080 | Pydantic AI | OPEN | yes | yes | yes | no | yes | none | no | 0 |
| D081 | pytest | OPEN | yes | no | no |  | yes | none | no | 0 |
| D082 | QEMU | BAN | yes | no | no |  | no | none | no | 0 |
| D087 | Rust | RESTRICTED | yes | no | no |  | no | none | no | 0 |
| D088 | SDL | BAN | yes | no | no |  | no | none | no | 0 |
| D089 | Shaka Player | OPEN | yes | no | no |  | no | none | no | 0 |
| D090 | SQLite | BAN | yes | no | no |  | no | none | no |  |
| D092 | Storybook | OPEN | yes | yes | yes | yes | yes | none | no | 0 |
| D097 | tRPC | OPEN | yes | yes | yes | yes | yes | none | no | 0 |
| D100 | vLLM | OPEN | yes | no | no |  | yes | none | no | 0 |

Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0, code Apache-2.0.
