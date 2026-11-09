# vendordocs 0.1.0: do company docs sites tell readers which pages were made with AI? (automatic report)

First pass written by the tool. The graded result is in RESULT.md.

- Started 2026-11-09T15:34:39Z, finished 2026-11-09T16:23:39Z.
- Pre-registration first committed: 2026-11-09T09:43:25Z.
- Sites: 20; readable (at least 20 pages): 18. Pages sampled 571, readable 537, counted 536.
- Gates: G1 yes, G2 yes, G3 yes.

## Predictions (automatic, before the hand check)

| | k | n | % | held |
|---|---|---|---|---|
| P1 | 0 | 18 | 0.0 | yes |
| P2 | 0 | 18 | 0.0 | yes |
| P3 | 0 | 536 | 0.0 | yes |
| P4 | 14 | 20 | 70.0 | yes |
| P5 | 13 | 18 | 72.22 | yes |
| P6 | None | 20 | None | n/a |

## Sites

| site | method | pool | sampled | readable | blocked | llms.txt | MD copy | AI label | AI note |
|---|---|---|---|---|---|---|---|---|---|
| Docker | sitemap | 2176 | 30 | 30 | 0 | yes | 30 | 0 | 0 |
| npm | crawl | 216 | 30 | 30 | 0 | no | 0 | 0 | 0 |
| Amazon Web Services | sitemap | 678 | 30 | 28 | 0 | yes | 28 | 0 | 0 |
| Google Cloud | crawl | 1103 | 30 | 30 | 0 | no | 30 | 0 | 0 |
| Cloudflare | sitemap | 9044 | 30 | 30 | 0 | yes | 30 | 0 | 0 |
| Terraform (HashiCorp) | sitemap | 1864 | 30 | 30 | 0 | no | 0 | 0 | 0 |
| Firebase | crawl | 6361 | 30 | 28 | 0 | yes | 28 | 0 | 0 |
| Ansible | sitemap | 11545 | 30 | 30 | 0 | no | 30 | 0 | 0 |
| Chocolatey | crawl | 456 | 30 | 30 | 0 | no | 0 | 0 | 0 |
| DigitalOcean | sitemap | 7186 | 30 | 30 | 0 | yes | 29 | 0 | 0 |
| Vercel | sitemap | 2505 | 30 | 30 | 0 | yes | 30 | 0 | 0 |
| Datadog | sitemap | 16281 | 30 | 30 | 0 | yes | 30 | 0 | 0 |
| Netlify | sitemap | 424 | 30 | 30 | 0 | yes | 30 | 0 | 0 |
| Supabase | sitemap | 2548 | 30 | 30 | 0 | yes | 11 | 0 | 0 |
| Heroku | sitemap | 821 | 30 | 30 | 0 | yes | 30 | 0 | 0 |
| Splunk | sitemap | 7005 | 30 | 0 | 30 | no | 0 | 0 | 0 |
| New Relic | sitemap | 7778 | 30 | 30 | 0 | yes | 29 | 0 | 0 |
| Railway | sitemap | 288 | 30 | 30 | 0 | yes | 30 | 0 | 0 |
| IBM Cloud | crawl | 1 | 1 | 1 | 0 | yes | 0 | 0 | 0 |
| Yandex Cloud | sitemap | 13945 | 30 | 30 | 0 | yes | 0 | 0 | 0 |

## AI labels found

- none

## Acknowledgement sentences found (to be hand-checked)

- none

## Controls

- {"control": "control-md", "url": "https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app", "html_status": 200, "readable": true, "md_accept": true, "md_ai_key": "ai-usage", "note_html": false, "note_html_text": ""}
- {"control": "control-note", "url": "https://devblogs.microsoft.com/performance-diagnostics/introducing-windbg-mcp-debug-with-natural-language-grounded-in-evidence/", "html_status": 200, "readable": true, "md_accept": false, "md_ai_key": "", "note_html": true, "note_html_text": "AI-assisted content."}
