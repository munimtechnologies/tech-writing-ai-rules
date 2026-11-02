# Pre-registration: what do paid technical-writing programs say about AI?

Written and committed on 2026-11-02 (UTC), before `programs.py` read any program page for this census. The git commit time of this file is the registration time. `programs.py` waits until this file is on `main`, then records its commit time in its output next to the time the pages were fetched. Made by MV2 of Munim, Inc., with AI agents working in his name. Text and data CC BY 4.0; code (`programs.py`, `test_programs.py`) Apache-2.0.

## Why

Many software companies and developer publications pay for technical articles: tutorials, how-tos, deep dives. Writers pick them from community lists. Those lists give each program's pay and topics, but not its rule on AI. A search on 2026-11-02 found single programs' pages (Civo bans AI-generated text; SitePoint allows AI for under half of an article) and lists of pay rates (a DEV post from early 2026; Who Pays Technical Writers, offline when checked), but no count of how these programs treat AI-written or AI-assisted work. This census provides that count for one fixed frame, publishes every AI sentence word for word, and records how many programs on a well-known list are still open.

It is also the question this field of MV2's work depends on: whether any paid documentation or article program accepts work made with AI agents when the AI use is disclosed.

## Frame (fixed now)

Every program bullet (`- [Name](URL) ...`) in the "Active" and "Paused" sections of the README of [malgamves/CommunityWriterPrograms](https://github.com/malgamves/CommunityWriterPrograms) (MIT; about 4,200 stars) at commit `0338535184058ff7099b819679f65ff82dfe30a6` (2026-07-31, "Last audited: July 2026"). `programs.py` parses that exact commit at run time, so the frame cannot change and no URL is retyped by hand. Read by hand on 2026-11-02, it holds 43 programs: 39 listed Active and 4 listed Paused. If the parser finds a different number, the parsed frame is used and the difference is reported.

The list was compiled to help developers find paid writing work, not to study AI rules. The census uses the URL each entry links to. Some links point to a form (Typeform, Google Forms) or a Notion page that needs JavaScript; those will mostly be UNREADABLE, and that count is part of the result.

## What is read

For each program: its listed page and up to five same-site links whose text or path looks like guidelines, FAQ, terms, a policy, a style guide, an editorial page, a contributor or author page, "write for us", submissions, pitching or applying. PDFs and other documents are listed, not read. Redirects are followed, with cookies kept within one fetch. From the visible text, `programs.py` keeps word for word:

- every sentence that mentions AI (the capitalised token "AI" or "A.I.", artificial intelligence, ChatGPT, LLM, large language model, generative, machine- or computer-generated, chatbot, Grammarly, Copilot, Claude, Gemini, Midjourney, text generation, Originality.ai, GPTZero, Copyleaks, ZeroGPT) in `sentences.csv`;
- every sentence about the program's status or pay (paused, closed, on hold, not accepting, no longer paying, a currency amount, "per article", paid, pay) in `status.csv`, at most 30 per page.

The page text is saved for the coder, but it is not published, because some pages name editors.

## Coding (fixed now)

**Primary coding** is done after the fetch by an AI agent reading every saved AI sentence (and the saved page text around it when a sentence is unclear), with this rubric. Each program gets the strictest rule on submitted work found on any page read, and the coding file quotes the sentence it rests on.

- **BAN_ANY_USE**: AI may not be used at any stage, or the ban covers AI assistance as well as AI-generated text (for example outlining, editing, rewording or grammar tools named as banned).
- **BAN_GENERATED**: AI-generated or AI-written text is not accepted ("100% human-written", "we reject AI-generated articles", "content flagged by AI detectors is rejected"), and the ban does not reach assistance, or limited assistance is expressly allowed.
- **ALLOW_LIMITED**: some AI-generated text is accepted, but only under a stated cap on its share ("less than 50%", "must not be the bulk of the article") or only if the writer substantially rewrites it.
- **ALLOW_DISCLOSED**: AI-generated text is accepted without a cap on its share, with or without a disclosure or human-review requirement.
- **NO_ENTRY_RULE**: AI is mentioned, but not as a rule on submitted work (AI as a topic the program wants articles about, the company's AI product, a training or scraping promise, news).
- **SILENT**: no AI sentence on any page read.
- **UNREADABLE**: pages were fetched but every one has under 500 characters of visible text (for example a form or a page built by JavaScript).
- **UNREACHABLE**: no page could be fetched (including HTTP 403 to the census's self-identifying user agent, 404 and DNS failures).

Flags (any program, any label):

- **DETECTOR**: the program says it checks submissions with AI-detection tools or software.
- **DISCLOSURE**: the program asks writers to disclose or declare AI use.

**Status** (separate from the AI label, from `status.csv`, the page text and the HTTP result):

- **GONE**: the listed URL returns HTTP 404 or 410, or its domain does not resolve, and no redirect leads to a program page.
- **CLOSED**: a page read says the program is paused, closed, on hold, not accepting new writers or pitches, or no longer pays.
- **OPEN_OR_UNCLEAR**: everything else, including pages that could not be read for other reasons.

The deterministic first-pass label from `programs.py` (`classify()`) is published next to the primary coding, with the agreement rate. Programs coded UNREADABLE or UNREACHABLE are left out of every AI-rule share below and listed.

## Predictions

- **P1.** Of the readable programs, at least 40% are coded BAN_ANY_USE or BAN_GENERATED.
- **P2.** At most one program is coded ALLOW_DISCLOSED.
- **P3.** Of the programs coded as a ban, fewer than half are BAN_ANY_USE. (In this repository's companion census of 54 writing contests, 18 of 24 bans were BAN_ANY_USE; the prediction is that paid technical-writing programs mostly leave room for AI assistance.)
- **P4.** At least 3 programs carry the DETECTOR flag.
- **P5.** Of the programs listed Active, at least 5 have status GONE or CLOSED.

Every prediction is reported as held or not, whatever the result.

## Not tested (reported as exploratory)

- How the AI rule relates to the listed pay (programs paying $300 or more per article against the rest), descriptively.
- Whether the four programs listed Paused are still paused.
- Where the AI rule sits: the listed page, a guidelines or FAQ page, or only a PDF that was not read.
- How the first-pass labels differ from the primary coding, with each disagreement listed.
- How the shares compare with the companion contest census (`census/2026-11/` in munimtechnologies/ai-writing-prize-rules).

## Limits, stated now

- 43 programs from one community list is one slice of the market, and it leans to developer-tool companies. Agencies and magazines that are not on the list are not covered.
- A rule can sit where the census does not look: a writer agreement sent after acceptance, a style guide behind a login, an email reply, an application form. A program coded SILENT has no AI rule on the pages read, which is not proof it has none.
- Pages change. The census records what each page said on the fetch date.
- The primary coding is done by AI agents, not by people. Every coded sentence is published so that anyone can check it.
- Nothing here is legal advice or advice about any program. Read the program's own page before pitching.
