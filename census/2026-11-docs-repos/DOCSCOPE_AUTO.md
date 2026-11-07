# Do AI contribution policies cover documentation? Automatic first pass

docscope.py 0.1.0. Frame: 14 projects from https://raw.githubusercontent.com/munimtechnologies/tech-writing-ai-rules/main/census/2026-11-docs-repos/frame.json. Texts fetched 2026-11-07T00:12:16Z to 2026-11-07T00:13:40Z UTC. Pre-registration first committed: 2026-11-06T17:25:10Z.

This is the deterministic first pass, not the study's primary coding (see the pre-registration). Every AI sentence is in sentences.csv with its flags, word for word.

| Auto label | Projects |
|---|---|
| docs_named | 1 |
| generic | 1 |
| code_only | 1 |
| other | 0 |
| ai_text_no_rule_cue | 1 |
| no_ai_text | 7 |
| unreachable | 3 |

| id | project | dataset stance | own texts read | followed | AI sentences | rule-word | docs | auto label |
|---|---|---|---|---|---|---|---|---|
| D001 | AnythingLLM docs | neutral; main rule GENERIC | 0 | 0 | 0 | 0 | 0 | unreachable |
| D002 | Dify docs | neutral; main rule GENERIC | 1 | 0 | 4 | 1 | 0 | code_only |
| D003 | Ghostty website and docs | disclose-required; main rule GENERIC | 2 | 0 | 0 | 0 | 0 | no_ai_text |
| D004 | Godot docs | ban; main rule GENERIC | 1 | 0 | 0 | 0 | 0 | no_ai_text |
| D005 | Home Assistant user docs | restricted; main rule DOCS_NAMED | 6 | 2 | 100 | 36 | 1 | docs_named |
| D006 | Hono website and docs | no-policy in dataset; main rule GENERIC | 0 | 0 | 0 | 0 | 0 | unreachable |
| D007 | Kubeflow website and docs | disclose-required; main rule DOCS_NAMED | 2 | 0 | 0 | 0 | 0 | no_ai_text |
| D008 | Kubernetes website and docs | disclose-required; main rule DOCS_NAMED | 3 | 0 | 0 | 0 | 0 | no_ai_text |
| D009 | LangChain and LangGraph docs | neutral; main rule GENERIC | 3 | 0 | 18 | 6 | 0 | generic |
| D010 | OpenHands docs | neutral; main rule OTHER_ONLY | 2 | 0 | 17 | 0 | 0 | ai_text_no_rule_cue |
| D011 | Open WebUI docs | neutral; main rule CODE_ONLY | 1 | 0 | 0 | 0 | 0 | no_ai_text |
| D012 | PostHog website, docs and handbook | disclose-required; main rule GENERIC | 2 | 0 | 0 | 0 | 0 | no_ai_text |
| D013 | The Rust Programming Language (book) | restricted; main rule DOCS_DISTINCT | 1 | 0 | 0 | 0 | 0 | no_ai_text |
| D014 | SDL wiki | ban; main rule GENERIC | 0 | 0 | 0 | 0 | 0 | unreachable |

Frame: awesome-ai-contribution-policies (data CC BY 4.0), commit 6cd258e96c3772a624f07fcf7f7a0b3867eaeabd.
Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0, code Apache-2.0.
