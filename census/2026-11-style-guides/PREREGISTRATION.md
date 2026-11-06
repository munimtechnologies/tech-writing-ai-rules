# Study 4 pre-registration: what do public documentation style guides say about AI?

Committed before any guide text is read by the study's tool. The study's job waits until this file is on `main`
(`--wait-prereg-minutes`), and its output records this file's first commit time.

Made by MV2 of Munim, Inc., with AI agents working in his name. Text and data CC BY 4.0, code Apache-2.0.

## Why

Writers, and more and more often AI agents, are told to "follow the Google style guide" or "follow the Microsoft
style guide". Studies 1 to 3 in this repository looked at paid writing programs and open-source contribution
policies. This study asks the style guides themselves. Do they say anything about AI at all, and if they do, is it
about **writing with AI** (using generative tools to draft or edit the content), **writing for AI** (content
that chatbots, AI search, LLMs or agents will read or speak), or only **writing about AI** (how to spell and use
terms such as "AI", "generative AI" or "machine learning")?

We found no earlier census of this. Searches on 2026-11-06 for surveys or comparisons of documentation style
guides' AI guidance found articles about Google Search's policy on AI content (not a style guide), marketing
posts about writing your own "AI style guide", and posts on feeding style guides to AI agents as instructions.

## Frame (frame.json, 19 guides)

The union of two independent public lists of recommended style guides:

- **Write the Docs, "Style Guides"** (read 2026-11-06): every whole style guide in the sections "Sample writing
  guides", "More enterprise software style guides", "Style guides from government and education" and "Style
  guides from open source projects" (13 guides).
  Left out, with reasons: AP Stylebook and Chicago Manual of Style (paywalled); the list's own link in the open
  source section, which points back to the list page itself; and the single-topic pages under "Developer
  documentation and APIs", "Command line resources", "API resources" and "Error messages" (they are not whole
  style guides, and two of them are sub-pages of the Google guide already in the frame).
- **Draft.dev, "10 Technical Writing Style Guides You Can Use in 2026"** (last updated 2026-02-06): all ten. Four
  overlap with Write the Docs (Apple, Microsoft, Google, SUSE), so six are added.

Each guide has seeds and a scope (URL prefixes) in frame.json, set from the guide's own structure before reading.
Two choices are ours and stated here: GOV.UK's entry includes the GOV.UK A to Z style guide on www.gov.uk next to
the "Writing to GOV.UK standards" pages the list links to, because those pages defer to it; Adobe's entry is
limited to Spectrum's content and writing pages, not its component pages.

Groups: **COMPANY** (G01-G12: guides a company or project writes for its own docs, UI and content),
**PUBLISHING** (G13-G15: guides for outside authors who submit articles to a publication),
**PUBLIC_EDU** (G16-G19: government, university and professional-body guides).

## Method

`guidescan.py` 0.1.0 (this repository; standard library; offline tests in `test_guidescan.py`) reads every HTML
page inside each guide's scope, breadth first from the seeds, up to the guide's `max_pages`, honouring robots.txt.
It keeps every sentence that mentions AI, word for word, with helper flags. The tool does not read PDFs and does
not run JavaScript; a guide it cannot read is coded UNREAD, never guessed.

Primary coding is done afterwards by one AI agent coder reading every saved AI sentence (and the surrounding saved
page text where needed) against the rubric below. Each non-SILENT code gets one quote of at most 300 characters
and its page URL. Site chrome (headers, footers, menus, site-wide AI assistant buttons) and text outside the
guide's own guidance (for example example sentences that merely contain the word "AI") does not count.

## Rubric (per guide)

- **UNREAD**: less than 1,000 characters of the guide's own text could be read.
- **BY** (writing with AI: using generative AI tools to write, draft, edit, translate or review the guide's kind
  of content):
  - BANS: forbids it.
  - LIMITS: allows it under conditions (human review, verification, disclosure, limits on some uses).
  - ALLOWS: allows or recommends it without conditions.
  - MENTIONS: talks about AI-written text or AI writing tools without a rule either way.
  - SILENT: none of these.
- **FOR** (writing for AI: guidance on content that AI systems will read, retrieve, answer from or speak, such as
  LLMs, AI search, llms.txt, chatbots, virtual agents or conversational interfaces): PRESENT or SILENT. Guidance
  on writing for machine translation does not count unless it names AI or LLMs.
- **ABOUT** (writing about AI: at least one entry or rule on how to write an AI-related term, for example "AI",
  "artificial intelligence", "machine learning", "generative AI", "LLM", "chatbot", "Copilot"): PRESENT or SILENT.

N is the number of guides not coded UNREAD. "Has BY guidance" means BY is BANS, LIMITS, ALLOWS or MENTIONS.

## Predictions

- **P1**: fewer than one third of the N guides have BY guidance.
- **P2**: more guides have ABOUT = PRESENT than have BY guidance.
- **P3**: no COMPANY guide is coded BANS.
- **P4**: every guide coded LIMITS names human review or verification of the AI output as a condition
  (not testable if no guide is coded LIMITS).
- **P5**: FOR = PRESENT in fewer than half of the N guides.
- **Gate G1**: N >= 12. Below that the study is reported as descriptive only and P1-P5 are not graded.

## What we already knew before reading (stated so it can be discounted)

From search-result summaries on 2026-11-06, before this file: the GitLab guide (G11) has an "AI-generated
content" section asking writers to check AI output carefully (so G11 is likely BY = LIMITS); Google's guide (G03)
lists word-list entries for "AI" and "generative AI" on its "What's new" page (likely ABOUT = PRESENT); Microsoft's
guide (G02) has guidance on content for chatbots and virtual agents (possibly FOR = PRESENT). Study 1 of this
repository read paid writing programs' "write for us" pages, which are different pages from G13-G15's style
guides. Nothing else about any guide's AI text was read.

## Limits

19 guides from two lists is a small, English-language, curated frame, not a sample of all style guides. A guide may
state an AI rule on a page outside its scope (for example a contributor agreement), which this study does not
count; such pages seen while coding are reported as limits, not codes. Pages are read once, on the day of the job.
The coder is one AI agent; every code has a public quote so anyone can re-check it.
