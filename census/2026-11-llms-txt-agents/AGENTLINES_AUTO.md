# What do llms.txt files tell AI agents to do? Automatic counts

agentlines.py 0.1.0, run by agentlines_run.py 0.2.0 (8 workers, 60 s per request, 600 s per URL). Frame: 1515 entries of llms-txt-hub data/websites.json at commit e4068608664a9349ddfcf3b51b3724849b51dd76 (3 repeat an earlier llms.txt URL, 0 have no http(s) URL), so 1512 unique URLs. Fetched 2026-11-09T22:08:27Z to 2026-11-09T22:17:46Z UTC (2908 requests). Pre-registration first committed: 2026-11-08T16:57:34Z.

Candidate lines are not directives: the pre-registered hand coding decides that.

Labels: challenge 4, error 122, html 15, missing 93, redirected 19, robots 13, unstructured 13, valid 1233

| Group | Unique URLs | Reached | Valid llms.txt | With a candidate line | With an AI heading | With an override phrase |
|---|---|---|---|---|---|---|
| ALL | 1512 | 1416 | 1233 | 623 | 322 | 27 |
| category ai-ml | 573 | 529 | 456 | 243 | 138 | 14 |
| category data-analytics | 202 | 192 | 180 | 71 | 26 | 2 |
| category developer-tools | 609 | 577 | 494 | 252 | 126 | 11 |
| category infrastructure-cloud | 65 | 61 | 49 | 30 | 16 | 0 |
| category security-identity | 63 | 57 | 54 | 27 | 16 | 0 |
| listed 2024 | 2 | 2 | 2 | 2 | 1 | 0 |
| listed 2025 | 594 | 557 | 468 | 221 | 108 | 20 |
| listed 2026 | 916 | 857 | 763 | 400 | 213 | 7 |
| CODE sample | 200 | 200 | 200 | 98 | 55 | 2 |

CODE sample: 200 files. RECALL sample: 20 files.

## Candidate lines shared by 3 or more files (normalised; site names replaced by 'site')

| Files | Line |
|---|---|
| 11 | rate limits back off on 429 responses and respect retry after when provided |
| 11 | interaction guidelines |
| 11 | buyer context use the buyer s country and currency where supported by the tool schemas for accurate pricing and availability |
| 11 | buyer authorization place orders and submit payment only with the buyer s authorization follow required review and approval steps |
| 11 | browser interactions agents must use the provided webmcp tools for all agent initiated shopping actions and updates if the tools are unavailable or cannot perform the required action yield and ask the |
| 11 | agent traffic agents must identify their requests as agent initiated server to server requests and hosted or remote browsers must use web bot auth https shopify dev docs api storefront identifying bot |
| 6 | instructions for ai agents |
| 4 | for section specific indexes append llms txt to any section url |
| 4 | for clean markdown of any page append md to the page url |
| 4 | content type application json |
| 3 | notes for ai assistants |

Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0, code Apache-2.0. Frame: llms-txt-hub by David Dias (MIT).
