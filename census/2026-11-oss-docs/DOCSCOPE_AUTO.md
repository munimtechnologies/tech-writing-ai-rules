# Do AI contribution policies cover documentation? Automatic first pass

docscope.py 0.1.0. Frame: 101 projects from https://raw.githubusercontent.com/ahmad-punch/awesome-ai-contribution-policies/6cd258e96c3772a624f07fcf7f7a0b3867eaeabd/policies.json. Texts fetched 2026-11-04T14:45:28Z to 2026-11-04T14:56:33Z UTC. Pre-registration first committed: 2026-11-04T14:39:13Z.

This is the deterministic first pass, not the study's primary coding (see the pre-registration). Every AI sentence is in sentences.csv with its flags, word for word.

| Auto label | Projects |
|---|---|
| docs_named | 15 |
| generic | 36 |
| code_only | 2 |
| other | 12 |
| ai_text_no_rule_cue | 19 |
| no_ai_text | 9 |
| unreachable | 8 |

| id | project | dataset stance | own texts read | followed | AI sentences | rule-word | docs | auto label |
|---|---|---|---|---|---|---|---|---|
| D001 | Anthropic SDK (Python) | no-policy | 1 | 0 | 1 | 0 | 0 | ai_text_no_rule_cue |
| D002 | Anthropic SDK (TypeScript) | no-policy | 1 | 0 | 1 | 0 | 0 | ai_text_no_rule_cue |
| D003 | AnythingLLM | neutral | 1 | 0 | 16 | 7 | 0 | generic |
| D004 | Apache Airflow | disclose-required | 3 | 0 | 5 | 1 | 0 | other |
| D005 | browser-use | no-policy | 2 | 0 | 33 | 1 | 0 | other |
| D006 | cal.diy (Cal.com) | neutral | 3 | 0 | 3 | 0 | 0 | ai_text_no_rule_cue |
| D007 | Claude Agent SDK (Python) | no-policy | 0 | 0 | 0 | 0 | 0 | unreachable |
| D008 | Claude Agent SDK (TypeScript) | no-policy | 0 | 0 | 0 | 0 | 0 | unreachable |
| D009 | Claude Code | no-policy | 0 | 0 | 0 | 0 | 0 | unreachable |
| D010 | Cloudflare Agents | no-policy | 1 | 0 | 5 | 1 | 0 | other |
| D011 | Coder | disclose-required | 8 | 4 | 22 | 7 | 2 | docs_named |
| D012 | CPython | disclose-encouraged | 5 | 2 | 28 | 16 | 0 | generic |
| D013 | Crawl4AI | no-policy | 2 | 0 | 1 | 0 | 0 | ai_text_no_rule_cue |
| D014 | crewAI | disclose-required | 3 | 0 | 5 | 3 | 0 | generic |
| D015 | curl | neutral | 3 | 0 | 4 | 4 | 0 | other |
| D016 | Debian | disclose-encouraged | 1 | 0 | 135 | 64 | 0 | generic |
| D017 | DeepEval | no-policy | 1 | 0 | 1 | 0 | 0 | ai_text_no_rule_cue |
| D018 | Dify | neutral | 3 | 0 | 5 | 1 | 0 | generic |
| D019 | Django | disclose-required | 3 | 0 | 25 | 6 | 0 | generic |
| D020 | Documenso | neutral | 3 | 0 | 7 | 1 | 0 | generic |
| D021 | Drizzle ORM | no-policy | 1 | 0 | 0 | 0 | 0 | no_ai_text |
| D022 | E2B | no-policy | 2 | 0 | 1 | 0 | 0 | ai_text_no_rule_cue |
| D023 | FastAPI | no-policy | 0 | 0 | 0 | 0 | 0 | unreachable |
| D024 | FastMCP (TypeScript) | no-policy | 0 | 0 | 0 | 0 | 0 | unreachable |
| D025 | Fedora | disclose-encouraged | 3 | 2 | 41 | 31 | 6 | docs_named |
| D026 | Firecrawl | no-policy | 2 | 0 | 1 | 1 | 0 | other |
| D027 | Formbricks | no-policy | 3 | 0 | 3 | 1 | 1 | docs_named |
| D028 | GCC | ban | 1 | 0 | 10 | 6 | 0 | generic |
| D029 | Gemara | encouraged | 3 | 1 | 14 | 8 | 0 | generic |
| D030 | Gentoo | ban | 5 | 4 | 22 | 13 | 0 | generic |
| D031 | Ghostty | disclose-required | 4 | 0 | 31 | 16 | 0 | generic |
| D032 | Gitea | encouraged | 3 | 0 | 11 | 8 | 0 | generic |
| D033 | Go | no-policy | 2 | 0 | 0 | 0 | 0 | no_ai_text |
| D034 | Godot Engine | ban | 3 | 0 | 14 | 7 | 0 | generic |
| D035 | Haystack | disclose-required | 3 | 0 | 8 | 1 | 0 | generic |
| D036 | Home Assistant | restricted | 6 | 1 | 62 | 33 | 0 | generic |
| D037 | Hono | no-policy | 2 | 0 | 3 | 3 | 0 | generic |
| D038 | Hugging Face Transformers | disclose-required | 3 | 0 | 5 | 3 | 0 | generic |
| D039 | Infisical | no-policy | 3 | 0 | 1 | 0 | 0 | ai_text_no_rule_cue |
| D040 | Inngest JS SDK | no-policy | 3 | 0 | 2 | 0 | 0 | ai_text_no_rule_cue |
| D041 | Inspect AI | no-policy | 3 | 0 | 12 | 1 | 0 | generic |
| D042 | Instructor | encouraged | 1 | 0 | 6 | 1 | 0 | other |
| D043 | Kubeflow | disclose-required | 4 | 3 | 26 | 17 | 4 | docs_named |
| D044 | Kubernetes | disclose-required | 4 | 0 | 15 | 9 | 0 | generic |
| D045 | LangChain | neutral | 3 | 0 | 10 | 3 | 1 | docs_named |
| D046 | LangChain.js | no-policy | 3 | 0 | 8 | 1 | 0 | other |
| D047 | Langfuse | no-policy | 3 | 0 | 24 | 2 | 0 | generic |
| D048 | LangGraph | neutral | 3 | 0 | 7 | 3 | 1 | docs_named |
| D049 | Linux Foundation | neutral | 1 | 0 | 11 | 7 | 0 | generic |
| D050 | Linux kernel | disclose-required | 4 | 2 | 18 | 6 | 0 | other |
| D051 | LiteLLM | neutral | 2 | 0 | 15 | 5 | 0 | generic |
| D052 | LlamaIndex | neutral | 2 | 0 | 10 | 3 | 0 | generic |
| D053 | LLVM | disclose-required | 6 | 4 | 83 | 36 | 2 | docs_named |
| D054 | Mastra | no-policy | 4 | 0 | 4 | 0 | 0 | ai_text_no_rule_cue |
| D055 | MCP Inspector | no-policy | 3 | 0 | 20 | 11 | 2 | docs_named |
| D056 | MCP Python SDK | disclose-required | 4 | 1 | 21 | 9 | 1 | docs_named |
| D057 | MCP servers | no-policy | 4 | 0 | 21 | 8 | 0 | generic |
| D058 | MCP TypeScript SDK | neutral | 1 | 0 | 2 | 0 | 0 | ai_text_no_rule_cue |
| D059 | MCP-Nest | no-policy | 0 | 0 | 0 | 0 | 0 | unreachable |
| D060 | Mesa | disclose-required | 1 | 0 | 12 | 3 | 0 | other |
| D061 | MLflow | no-policy | 3 | 0 | 3 | 0 | 0 | ai_text_no_rule_cue |
| D062 | Model Context Protocol (spec) | disclose-required | 4 | 0 | 19 | 10 | 1 | docs_named |
| D063 | Mozilla Firefox | neutral | 4 | 2 | 20 | 10 | 1 | docs_named |
| D064 | NestJS | no-policy | 2 | 0 | 0 | 0 | 0 | no_ai_text |
| D065 | NestJS GraphQL | no-policy | 2 | 0 | 0 | 0 | 0 | no_ai_text |
| D066 | NestJS Swagger | no-policy | 2 | 0 | 0 | 0 | 0 | no_ai_text |
| D067 | NetBSD | ban | 1 | 0 | 2 | 0 | 0 | ai_text_no_rule_cue |
| D068 | Next.js | neutral | 3 | 0 | 4 | 1 | 0 | generic |
| D069 | Node.js | disclose-required | 5 | 1 | 64 | 49 | 1 | docs_named |
| D070 | Novu | no-policy | 3 | 0 | 1 | 0 | 0 | ai_text_no_rule_cue |
| D071 | Ollama | no-policy | 2 | 0 | 1 | 0 | 0 | ai_text_no_rule_cue |
| D072 | Open WebUI | neutral | 1 | 0 | 1 | 0 | 0 | ai_text_no_rule_cue |
| D073 | OpenAI Agents SDK (JS) | no-policy | 2 | 0 | 4 | 2 | 1 | docs_named |
| D074 | OpenHands | neutral | 2 | 0 | 3 | 2 | 0 | other |
| D075 | OpenJDK | ban | 3 | 1 | 65 | 14 | 0 | generic |
| D076 | PostHog | disclose-required | 5 | 0 | 35 | 15 | 0 | generic |
| D077 | posthog-js | disclose-required | 5 | 0 | 17 | 10 | 0 | generic |
| D078 | promptfoo | neutral | 2 | 0 | 8 | 1 | 0 | generic |
| D079 | Pydantic | neutral | 3 | 0 | 0 | 0 | 0 | no_ai_text |
| D080 | Pydantic AI | no-policy | 3 | 0 | 17 | 8 | 1 | docs_named |
| D081 | pytest | disclose-required | 2 | 0 | 17 | 9 | 0 | generic |
| D082 | QEMU | ban | 1 | 0 | 16 | 5 | 0 | generic |
| D083 | Ragas | encouraged | 2 | 0 | 12 | 1 | 0 | code_only |
| D084 | RAGFlow | no-policy | 2 | 0 | 3 | 1 | 0 | other |
| D085 | React Email | no-policy | 2 | 0 | 0 | 0 | 0 | no_ai_text |
| D086 | Ruby | no-policy | 1 | 0 | 0 | 0 | 0 | no_ai_text |
| D087 | Rust | restricted | 5 | 1 | 95 | 58 | 4 | docs_named |
| D088 | SDL | ban | 4 | 1 | 23 | 14 | 0 | generic |
| D089 | Shaka Player | encouraged | 2 | 0 | 4 | 2 | 0 | generic |
| D090 | SQLite | ban | 1 | 0 | 3 | 2 | 0 | code_only |
| D091 | Stagehand | no-policy | 2 | 0 | 1 | 0 | 0 | ai_text_no_rule_cue |
| D092 | Storybook | disclose-required | 4 | 0 | 12 | 7 | 0 | generic |
| D093 | Supabase | no-policy | 3 | 0 | 0 | 0 | 0 | no_ai_text |
| D094 | Supabase Edge Runtime | no-policy | 0 | 0 | 0 | 0 | 0 | unreachable |
| D095 | supabase-js | no-policy | 4 | 1 | 13 | 0 | 0 | ai_text_no_rule_cue |
| D096 | Trigger.dev | no-policy | 4 | 0 | 4 | 1 | 0 | other |
| D097 | tRPC | no-policy | 2 | 0 | 2 | 0 | 0 | ai_text_no_rule_cue |
| D098 | Twenty | no-policy | 2 | 0 | 1 | 0 | 0 | ai_text_no_rule_cue |
| D099 | Vercel AI SDK | no-policy | 4 | 0 | 17 | 2 | 0 | generic |
| D100 | vLLM | disclose-required | 3 | 0 | 5 | 1 | 0 | generic |
| D101 | Zig | ban | 0 | 0 | 42 | 6 | 0 | unreachable |

Frame: awesome-ai-contribution-policies (data CC BY 4.0), commit 6cd258e96c3772a624f07fcf7f7a0b3867eaeabd.
Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0, code Apache-2.0.
