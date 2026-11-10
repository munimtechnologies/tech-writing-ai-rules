# learnshown 0.2.0: does Microsoft Learn show readers that an article was made with AI? (automatic report)

First pass written by the tool. The graded result is in RESULT.md.

- Started 2026-11-10T13:46:25Z, finished 2026-11-10T14:36:39Z.
- Pre-registration (or amendment) file first committed: 2026-11-10T13:24:42Z.
- Acknowledgement measure for G2 and P1 to P4: note_rendered.
- Repos read: 15. Pages sampled: 315; mapped and fetched as HTML: 263; labelled (A-C): 164 from 15 repos; Markdown copy served: 263.
- Mapping: no 5, unknown 47, yes 263.
- URL rule of counted pages: breadcrumb 236, breadcrumb-root 16, search 11.
- Gates: G1 yes, G2 yes, G3 yes.

## Predictions (automatic; boundaries as pre-registered)

| | k | n | % | held |
|---|---|---|---|---|
| P1 | 131 | 131 | 100.0 | yes |
| P2 | 0 | 33 | 0.0 | yes |
| P3 | 1 | 99 | 1.01 | yes |
| P4 | 0 | 131 | 0.0 | yes |
| P5 | 164 | 164 | 100.0 | yes |
| P6 | 130 | 131 | 99.24 | yes |

## By stratum

| stratum | sampled | mapped | note in served HTML | note rendered | AI meta in HTML | MD served | note in MD | AI key in MD | last h2 missing in MD |
|---|---|---|---|---|---|---|---|---|---|
| A | 120 | 99 | 0 | 99 | 99 | 99 | 0 | 99 | 56 |
| B | 41 | 32 | 0 | 32 | 32 | 32 | 0 | 32 | 24 |
| C | 34 | 33 | 0 | 0 | 33 | 33 | 0 | 33 | 19 |
| D | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| U | 120 | 99 | 1 | 1 | 0 | 99 | 1 | 0 | 50 |

## Acknowledgement sentences seen (note_rendered)

- 99 x "Note: The author created this article with assistance from AI."
- 32 x "Note: This article contains content created with AI."
- 1 x "Content Safety An AI service that detects harmful user-generated and AI-generated content."

## Controls

- {"stratum": "control-positive", "url": "https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app", "url_rule": "given", "html_status": 200, "md_served": true, "mapped": "yes", "note_html": false, "note_html_text": "", "render_status": 200, "note_rendered": true, "note_rendered_text": "Note: The author created this article with assistance from AI.", "note_md": false, "md_ai_key": "ai-usage", "html_ai_key": "ai-usage", "last_h2_missing": ""}
- {"stratum": "control-seen", "url": "https://learn.microsoft.com/en-us/azure/dev-box/overview-what-is-dev-box-mcp-server", "url_rule": "given", "html_status": 200, "md_served": true, "mapped": "yes", "note_html": false, "note_html_text": "", "render_status": 200, "note_rendered": false, "note_rendered_text": "", "note_md": false, "md_ai_key": "ms.ai-usage", "html_ai_key": "ms.ai-usage", "last_h2_missing": ""}
