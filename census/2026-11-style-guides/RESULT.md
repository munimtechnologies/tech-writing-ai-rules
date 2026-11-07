# Study 4 result: what do public documentation style guides say about AI?

Graded 2026-11-07 against the [pre-registration](PREREGISTRATION.md), which was first committed on 2026-11-06 at 23:06:34 UTC. `guidescan.py` 0.1.0 read the guides' pages on 2026-11-07 from 08:37 to 09:02 UTC, more than nine hours later. Nothing in the rubric, the predictions or the frame was changed after the pages were read.

Made by MV2 of Munim, Inc., with AI agents working in his name. The coding was done by one AI agent coder. Text and data CC BY 4.0, code Apache-2.0.

## Short answer

Of 14 style guides that could be read, **only 3 say anything about writing with AI**, and only 2 of them set conditions: GitLab and Intuit. Both conditions involve checking the output: GitLab tells writers to "check the output carefully before you submit it for review". **No guide bans it.** Half of the guides (7 of 14) have a word-list entry on how to write "AI" or a related term. **4 of 14 give advice on writing for AI**, meaning content that chatbots, LLMs, AI search or AI crawlers will read or speak. Red Hat's supplementary guide tells writers: "Write for AI and search." **The guides for outside authors (Draft.dev, A List Apart) and the public-sector and university guides say nothing about AI use, apart from GOV.UK's A to Z entry.**

All five pre-registered predictions held, and the gate passed (N = 14).

## Frame and reading

The frame is the 19 guides in [`frame.json`](frame.json): the union of Write the Docs' "Style Guides" list and Draft.dev's "10 Technical Writing Style Guides You Can Use in 2026". The tool read each guide's in-scope HTML pages breadth first, up to a per-guide cap, honouring robots.txt (see `pages.csv`, one row per URL tried).

**5 guides are UNREAD** (less than 1,000 characters of the guide's own text):

| Guide | Why |
|---|---|
| G01 Apple Style Guide | Only the table of contents and Apple's site chrome came back. Every guide page the tool followed returned HTTP 404 to a plain fetch. |
| G05 Salesforce | 21 characters. The page is built with JavaScript. |
| G09 SUSE | The single-page HTML seed returned HTTP 404. |
| G15 DigitalOcean | Only DigitalOcean's menus and footer came back (3.8k characters), with no guideline text. Its four "AI" sentences are menu items. |
| G19 IET | The guide is a PDF, which the tool does not read. |

Two of these are judgement calls, both stated here. The tool's first pass labelled G01 `no_ai_text` and G15 `ai_text`, because each had more than 1,000 characters of page text, but none of that text is guidance. The pre-registration expected Salesforce and IET to be unread. Apple, SUSE and DigitalOcean were not expected.

**N = 14.** Gate G1 (N ≥ 12) passed.

## Codes

Each non-SILENT code has one verbatim quote (300 characters at most) and its URL in [`coding.csv`](coding.csv).

| id | Guide | Group | BY (writing with AI) | FOR (writing for AI) | ABOUT (AI terms) |
|---|---|---|---|---|---|
| G02 | Microsoft Writing Style Guide | COMPANY | ALLOWS (borderline) | PRESENT | PRESENT |
| G03 | Google developer documentation style guide | COMPANY | SILENT | SILENT | PRESENT |
| G04 | Red Hat supplementary style guide | COMPANY | SILENT | PRESENT | PRESENT (borderline) |
| G06 | Mailchimp Content Style Guide | COMPANY | SILENT | SILENT | SILENT |
| G07 | Intuit Content Design | COMPANY | LIMITS | PRESENT | PRESENT |
| G08 | Adobe Spectrum content guidelines | COMPANY | SILENT | SILENT | SILENT |
| G10 | GNOME developer documentation guidelines | COMPANY | SILENT | SILENT | SILENT |
| G11 | GitLab Documentation Style Guide | COMPANY | LIMITS | PRESENT | PRESENT |
| G12 | Red Hat Technical Writing Style Guide (stylepedia) | COMPANY | SILENT | SILENT | PRESENT |
| G13 | Draft.dev Technical Blogging Style Guide | PUBLISHING | SILENT | SILENT | SILENT |
| G14 | A List Apart style guide | PUBLISHING | SILENT | SILENT | SILENT |
| G16 | GOV.UK (Writing to GOV.UK standards + A to Z) | PUBLIC_EDU | SILENT | SILENT | PRESENT |
| G17 | Princeton Editorial Style Guide | PUBLIC_EDU | SILENT | SILENT | SILENT |
| G18 | Federal plain language guidelines (digital.gov) | PUBLIC_EDU | SILENT | SILENT | SILENT |

Totals (N = 14): BY guidance 3 (LIMITS 2, ALLOWS 1, BANS 0, MENTIONS 0); FOR = PRESENT 4; ABOUT = PRESENT 7; all three SILENT 7.

### Writing with AI (BY)

- **GitLab (LIMITS).** Its main style guide page has a section headed "AI-generated content": "When you use AI tools to generate or assist with documentation, check the output carefully before you submit it for review." It then lists the problems to look for (repetition, vague or unverifiable claims, wrong scope) and says: "Only include information you can ground in the existing codebase, linked documentation, or content already on the page."
- **Intuit (LIMITS).** Intuit's content design system has an "AI" section. Its "Using AI" page points writers to an AI plugin that "handles most content tasks including drafting, reviewing, and iterating either in your AI tool of choice, or in Figma". It sets a quality bar ("Generated content should be at the same level of quality—or at least a consistent quality—as content written by humans") and a human step ("After a prompt is given to an LLM and the model begins generating content, humans step in again to help evaluate the model’s output."). Because Intuit's product UI text is itself increasingly written by an LLM at run time, much of this section is about generated product content, not only about writers' own drafts. Both readings give LIMITS.
- **Microsoft (ALLOWS, borderline).** The word-list entry "prompt, prompting" says: "If you want quality outputs, you need fine-tuned prompts. To start becoming a prompting pro, check out this prompt crafting guide (for marketing content) from Writer.com." This recommends learning to prompt for marketing content and sets no conditions. A second coder could call it MENTIONS, because it is advice rather than a rule. Either code counts as BY guidance, so no prediction changes.

### Writing for AI (FOR)

- **Red Hat's supplementary style guide** requires a short description for every module and says: "Write for AI and search. High-quality short descriptions are a primary source of metadata for large language models (LLMs) and search engine link previews." Its 2026 notes say the guide itself is now also generated in Markdown, which "optimizes the SSG for AI consumption and machine reading."
- **GitLab** asks writers who remove a page to redirect it to "a file that has relevant context for users and for AI crawlers". Its localization section adds that "The increasing use of machine translation, GitLab Duo Chat, and other AI tools means that consistency is even more important."
- **Intuit** has voice-and-tone rules, UX patterns and "conversational maxims" for AI responses, for example: "For conversational interfaces, a welcome message should break the ice and guide customers through the experience."
- **Microsoft**'s AI and bot term collection points to the guide's own chatbot writing guidance: "Learn more See Chatbots and virtual agents for guidelines for creating a new chatbot." See Limits: the tool did not reach that section.

### Writing about AI (ABOUT)

Seven guides tell writers how to write AI terms. Most say the abbreviation needs no spelling out:

- Microsoft: "To refer to the technology itself, use AI for all audiences and in most content". Its AI and bot terms entry also says "Don't spell out artificial intelligence."
- Google: "In general, you can use AI without spelling out artificial intelligence."
- GitLab: "Do not spell out artificial intelligence."
- Red Hat stylepedia: "AI" is understood and suffices.
- GOV.UK: "Write first as artificial intelligence (AI) then AI throughout."
- Intuit (AI assistant, AI-powered, generative AI, LLM and others, with rules against implying that AI "thinks").
- Red Hat SSG (borderline): its "inference (noun, verb)" glossary entry defines AI inference.

So GOV.UK alone asks for the long form first.

## Predictions

| | Prediction | Result | |
|---|---|---|---|
| P1 | Fewer than one third of the N guides have BY guidance | 3 of 14 (21.4%) | **Held** |
| P2 | More guides have ABOUT = PRESENT than have BY guidance | 7 vs 3 | **Held** |
| P3 | No COMPANY guide is coded BANS | 0 of 10 readable COMPANY guides | **Held** |
| P4 | Every LIMITS guide names human review or verification of the AI output | GitLab ("check the output carefully before you submit it for review"); Intuit ("humans step in again to help evaluate the model’s output") | **Held** (2 of 2) |
| P5 | FOR = PRESENT in fewer than half of the N guides | 4 of 14 (28.6%) | **Held** |
| G1 | N ≥ 12 | N = 14 | **Passed** |

**Robustness.** Each of the following changes leaves every prediction's outcome the same:

- G01 counted as read and SILENT (N = 15): P1 3/15, P5 4/15.
- Microsoft BY coded MENTIONS.
- Microsoft FOR coded SILENT because the section itself was not read: P5 3/14.
- Red Hat SSG ABOUT coded SILENT: P2 6 vs 3.

P4 is the weakest. It rests on two guides, and Intuit's human-evaluation sentence describes evaluating LLM output in general, not a rule for a writer's own draft.

## First pass vs reading

The tool's deterministic label (`ai_text` / `no_ai_text` / `unread`, in [`GUIDESCAN_AUTO.md`](GUIDESCAN_AUTO.md)) matched the reading for 15 of 19 guides. The four misses were all caused by site chrome or an empty shell: Draft.dev and Princeton (`ai_text` from footer and menu links), DigitalOcean (`ai_text` from menus on a page with no guide text) and Apple (`no_ai_text` on a page that was only a table of contents). A keyword screen cannot code this; the words "AI" or "generative AI" in a page's navigation say nothing about its guidance.

## What this adds

Studies 1 to 3 in this repository found that paid writing programs ban AI-written articles more often than they allow them (study 1). Open-source AI policies rarely say whether they cover documentation (study 2), and separate docs repos rarely carry their project's AI rule (study 3). The style guides that writers and agents are told to follow mostly say nothing about writing with AI. The two that do (GitLab and Intuit) allow it with a check, and none bans it. In the same guides, the newer topic is writing *for* AI: Red Hat, GitLab, Intuit and Microsoft now give advice on content that LLMs, AI search or crawlers will read, and the outside-author and public-sector guides have none.

We found no earlier census of AI guidance in documentation style guides (searches on 2026-11-06, listed in the pre-registration).

## Limits

- **Small, curated, English-language frame.** 19 guides from two recommendation lists, 14 of them readable. This is not a sample of all style guides.
- **Cap hits.** Microsoft (900 pages) and Intuit (600 URLs, 71 distinct pages) reached their caps. Microsoft's breadth-first crawl spent its cap on the A to Z word list. Its "Chatbots and virtual agents" section is inside the guide's scope and was live on 2026-11-07, but it was not reached, so Microsoft's FOR code rests on the guide's own pointer to it. A pointer cannot add a BAN to Microsoft, but unread pages could hold more BY text.
- **Adobe** yielded only two distinct in-scope pages (voice and tone; grammar and mechanics). The **Mailchimp** word list page gave 3k characters.
- **Pages outside scope.** Princeton's site menu links to a separate "Generative AI Guidelines" page, and GitLab's footer links to a legal "Use of generative AI" page. Both are outside the guides' scopes, so they were not read and do not count. Draft.dev's own writer rules live in a portal (noted in study 1), and its public style guide was last updated 2025-11-21.
- **One coder.** One AI agent coded every guide. Every code has a public quote and URL, so anyone can re-check it. Two codes are marked borderline in `coding.csv`.
- **Read once.** Pages were read once, on 2026-11-07. Guides change, and Microsoft and Intuit both note AI changes in 2025-2026.

## Files

- [`PREREGISTRATION.md`](PREREGISTRATION.md), [`frame.json`](frame.json): fixed before reading.
- [`coding.csv`](coding.csv): one row per guide with BY, FOR and ABOUT, the first-pass label and whether it agrees, borderline flags, verbatim quotes with URLs, and notes.
- [`GUIDESCAN_AUTO.md`](GUIDESCAN_AUTO.md), [`frame.csv`](frame.csv), [`pages.csv`](pages.csv): the tool's unchanged output (first-pass table, frame as read, every URL tried with status and character count).
- The tool's full `sentences.csv` (430 AI sentences) is not republished. Some rows come from event-programme pages that name individual speakers, and this repository does not republish people's names. Every code's evidence is quoted in `coding.csv`, and `guidescan.py` 0.1.0 reproduces the file: `python guidescan.py --out-dir out --no-prereg-check`. Page texts are not republished.

Nothing here is legal advice or a judgement on any guide. Read each guide's own pages before relying on them.
