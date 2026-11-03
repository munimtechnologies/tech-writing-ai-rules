# Result: what 43 paid technical-writing programs say about AI

Graded on 2026-11-03 (UTC) against [PREREGISTRATION.md](PREREGISTRATION.md). Made by MV2 of Munim, Inc., with AI agents working in his name. Text and data CC BY 4.0. Not legal advice, and not advice about any program: read the program's own page before pitching.

## Timing

- Pre-registration committed: **2026-11-02 12:14:12 UTC** (commit `47f0436`, recorded by `programs.py` in `census.json`).
- Pages fetched: **12:27:04 to 12:30:13 UTC**, after registration. This is the pre-registered census, not an exploratory one.
- Primary coding: done after the fetch by an AI agent, from the saved AI sentences and the saved page text around them, using the rubric as written. Every code and the sentence it rests on is in [coding.csv](coding.csv). Every quote was checked against the saved page text.

## Counts (primary coding)

| Code | Programs |
|---|---|
| BAN_ANY_USE | 0 |
| BAN_GENERATED | 7 |
| ALLOW_LIMITED | 0 |
| ALLOW_DISCLOSED | 0 |
| NO_ENTRY_RULE | 21 |
| SILENT | 10 |
| UNREADABLE | 5 |
| UNREACHABLE | 0 |
| **Total** | **43** |

Left out of every share below: Magic, MagicPod, Mem0, QuickNode and SitePoint (UNREADABLE). Their links go to Typeform forms or Notion pages that show 6 to 15 characters without JavaScript. That leaves **38 readable programs**.

The seven bans: Airbyte, Civo, Corellium, MSSQLTips, Simple Talk (Redgate), Stack Overflow (listed Paused) and Twilio (listed Paused). Every one bans AI-generated text, and none bans AI assistance. Simple Talk lists what it allows: "spell checking, basic grammar, brainstorming ideas, creating graphics and images, and other basic tasks". Stack Overflow has "no problems with you using AI to research, plan, or even outline articles. But the final result that you share with the world should be written by you."

## Predictions

| | Prediction | Result | Held? |
|---|---|---|---|
| P1 | At least 40% of readable programs are coded as a ban | 7 of 38 = **18.4%** | **not held** |
| P2 | At most one program is ALLOW_DISCLOSED | **0** | **held** |
| P3 | Fewer than half of the bans are BAN_ANY_USE | 0 of 7 = **0%** | **held** |
| P4 | At least 3 programs carry the DETECTOR flag | **2** (Civo, Simple Talk) | **not held** |
| P5 | At least 5 programs listed Active are GONE or CLOSED | **2** (Bugfender, WebWash) | **not held** |

Three of the five predictions failed. Paid technical-writing programs state a ban far less often than writing contests do (P1). Only two name AI-detection tools (P4). And on the rubric's narrow definition, few listed programs are plainly closed (P5).

## Readings that could change a result

- **P4.** Airbyte says "Authors will be banned from the program if we detect AI drafts." It names no tool or software, which the DETECTOR flag requires, so it is coded no. Counting it would make **3, and P4 would hold**. The primary coding keeps the registered wording.
- **P5.** GONE requires an HTTP 404 or 410 or a dead domain. Four more Active programs' listed pages now redirect away from any program page: LoginRadius and SaturnCloud to the company home page, Kestra to `/community` and Every Developer from `/join/` to `/about/`. These pages returned HTTP 200, so they are OPEN_OR_UNCLEAR. Counting them would make 6, and P5 would hold. Two more pages say they take no guest posts but still invite other pitches (Make Use Of: "we do not accept any guest posts at the moment", next to a contributor application; PHP Architect: "We do not accept applications for guest bloggers", but magazine and book concepts are welcome). They are not coded CLOSED.
- **Civo.** Its ban covers material "copied, paraphrased, translated, or generated from existing online sources, including AI tools". The primary reading is a ban on taking material from sources, AI tools among them (BAN_GENERATED). Read as a ban on AI paraphrasing of one's own text, it would be BAN_ANY_USE. P3 still holds (1 of 7).
- **TestMu AI.** Its editorial policy says AI is used for "producing first drafts of sections", with sign-off by a named human author and a visible note on "Every AI-assisted article". That describes the publisher's own process and sets no rule for guest writers, so it is NO_ENTRY_RULE. As ALLOW_DISCLOSED, P2 would still hold (1).
- **P1** fails under every reading: no reading of the other 31 programs' sentences turns them into bans.

## What this means for a writer using AI

No program among the 38 readable ones says it accepts AI-generated text, with or without disclosure. Seven refuse it in writing. Thirty-one say nothing about it on the pages read, which is not permission. The only program with a disclosure rule, Stack Overflow's (added October 2026), still asks that the final text be the writer's own. For articles made with AI agents and disclosed as such, this list holds no program that welcomes them.

## Exploratory (not tested)

- **Pay.** Taking the top of each listed pay range, 6 of the 20 programs paying $300 or more ban AI-generated text (30%), against 1 of the 18 paying less or not stating pay (6%). Fisher's exact p = 0.093 two-sided (0.061 one-sided). The better-paying programs state a ban more often, but the difference is not significant at this size.
- **The four programs listed Paused.** Solace ("Submissions Paused – Program Under Construction") and Twilio ("We are not accepting new applications for the Developer Voices program at this time") are still paused. Stack Overflow's guidelines page, as read, has no pause notice and asks for pitches by email. TestMu AI's guest program is open, but the list notes it no longer pays cash.
- **Where the rule sits.** All 7 bans are stated on the page the list links to. In the companion contest census it was 13 of 24, and the rest sat one click away.
- **Other status notes.** Bugfender's notice ("POSITIONS FILLED: CURRENTLY, WE ARE NOT LOOKING FOR NEW WRITERS, BUT YOU CAN SUBMIT YOUR APPLICATION FOR FUTURE CONSIDERATION.") is in capitals, and `programs.py`'s status sentences missed it. It was found in the saved page text. In Plain English says "We do not pay writers for publishing content in our publications", with paid work offered only to its Discord community. Codiga's page says it "has joined Datadog!", but its write-for-us page is still up.
- **First pass vs primary coding.** Mapped to the rubric (ban/assisted to BAN_ANY_USE, ban/generated to BAN_GENERATED, other_mention to NO_ENTRY_RULE), `programs.py`'s labels agree with the primary coding for **37 of 43 programs (86%)**, and on ban vs no ban for 39 of 43 (91%). The six disagreements:
  - Civo and Simple Talk: auto said assisted. The word "tools" or "assist" appears, but assistance is not banned, and Simple Talk expressly allows it.
  - Corellium: auto said other mention, because its ban cue misses the curly apostrophe in "can’t".
  - In Plain English and Smashing Magazine: auto said ban, triggered by "no paywalls" and by an article title.
  - TestMu AI: auto said ban, triggered by "AI does not replace our editors".

## How this compares

- **Contests vs paid programs.** In this repository's companion census of 54 writing contests ([ai-writing-prize-rules](https://github.com/munimtechnologies/ai-writing-prize-rules), `census/2026-11/`), 24 of 51 readable contests (47%) ban AI, and 18 of those 24 also ban AI assistance such as editing, translation or grammar tools. Among paid technical-writing programs, 7 of 38 (18%) ban AI, and **none** bans assistance. Literary contests guard the act of writing itself. Technical programs guard only the finished text, and two of them spell out the help they allow.
- **Other counts.** Become a Writer Today's list (read 2026-11-02) found outright bans at 81 of 179 literary markets. Stingrai found that none of 53 bug-bounty programmes ban AI-assisted reports. Paid technical writing sits between the two.
- **What is new here.** We found no earlier count of AI rules across paid technical-writing programs. Community lists give pay and topics, and single programs' pages give their own rules. This census uses a frame not chosen for AI (a well-known community list pinned to one commit), publishes every coded sentence word for word, and graded predictions committed before any page was read.

## Limits

- One slice: 43 programs from one community list, leaning to developer-tool companies. Agencies and magazines that are not on the list are not covered.
- Rules can sit where the census does not look: a writer agreement sent after acceptance, a writer portal (Draft.dev), an application form (the five UNREADABLE programs) or an email. SILENT and NO_ENTRY_RULE mean no rule on the pages read, not no rule.
- Pages change. This records them as fetched on 2026-11-02 between 12:27 and 12:30 UTC.
- The primary coding was done by AI agents, not people. Every sentence it rests on is published so anyone can check or recode it.

## Files

- `coding.csv`: for every program, the primary code, flags and status, the quoted sentence and page, the status sentence when one decided the status, `programs.py`'s first-pass label, whether they agree, and a note on every borderline call.
- `sentences.csv`: every AI sentence `programs.py` 0.1.0 found, word for word, with two kinds of rows left out. Rows from personal author or contributor pages (one each at Simple Talk, Smashing Magazine and Stack Overflow) are left out, along with three more rows that name or describe a person. These are article titles and author biographies, and none of them holds a rule. 52 of 327 rows are omitted, so 275 remain; the omitted rows are described at the end of this file.
- `frame.csv` and `CENSUS_AUTO.md`: `programs.py` 0.1.0's output, unchanged.
- The run's `census.json` and `status.csv` (status and pay sentences, mostly terms-of-service text) and the saved page text are kept by the run that fetched them, not committed here. They repeat the omitted rows, and the page text names editors and authors. The run was `python programs.py --out-dir /out --save-text --pause 1 --wait-prereg-minutes 100`, after the offline tests passed. Running it again reads the pages as they stand on the new date.

Omitted from `sentences.csv`: the single row from Simple Talk's contributors page; the 26 rows from one Smashing Magazine author page, and the one row from its pitching article that names that author; the two rows of an author biography on Software Testing Help's editorial-policy page; and the 22 rows from one Stack Overflow author page.
