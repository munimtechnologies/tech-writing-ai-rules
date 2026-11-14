# Follow-up: four of the five unreadable programs, read in a browser

Added 2026-11-13 (UTC) to the census in [RESULT.md](RESULT.md); follow-up 2 added 2026-11-14. Made by MV2 of Munim, Inc., with AI agents working in his name. Text and data CC BY 4.0. Not legal advice, and not advice about any program: read the program's own page before pitching.

**This is not part of the pre-registered census.** It does not regrade P1-P5. The census fetched its pages without JavaScript on 2026-11-02, and five programs were coded UNREADABLE because their pages are forms or JavaScript-built Notion pages. On 2026-11-12, between 18:21 and 18:27 UTC, an AI agent working for MV2 opened four of them in an ordinary Chrome window, without signing in or submitting anything, and copied every AI sentence word for word. The codes below use the census's [pre-registered rubric](PREREGISTRATION.md) unchanged. Every code, quote and note is in [followup.csv](followup.csv).

## What the four pages say

| Program | Code (2026-11-02) | Code (follow-up) | Status | The sentence it rests on |
|---|---|---|---|---|
| MagicPod | UNREADABLE | SILENT | open or unclear | none (no AI sentence on the page) |
| Mem0 | UNREADABLE | NO_ENTRY_RULE | open or unclear | "If you can explain complex AI concepts without sounding like a ChatGPT prompt, you might be our person." |
| QuickNode | UNREADABLE | SILENT | **closed** | none ("At this time, we are not accepting new applications.") |
| SitePoint | UNREADABLE | **ALLOW_LIMITED** | open or unclear | "If you're planning to use it, make sure it's less than 50% of your total text." |
| Magic | UNREADABLE | UNREADABLE | open or unclear | not read again |

## What changes

- **SitePoint is the first program in the census that accepts some AI-generated text.** Its "Can I Use AI?" section says: "AI is fine to use as a tool to assist you in writing or editing content, but it should not constitute the bulk of your writing." It then sets a cap: "less than 50% of your total text". "Less than 50%" is the rubric's own example of ALLOW_LIMITED. It names no detector and asks for no disclosure ("You know best how much you've used it."), and it lists "The submission relied too heavily on generative AI." as a reason for rejection.
- **SitePoint is no longer a paid writing program in the usual sense.** Submitting is "an exclusive perk for SitePoint Premium subscribers", a paid subscription, and the page does not mention paying authors. The Typeform that the community list links is no longer on the page. Its status stays OPEN_OR_UNCLEAR under the rubric, which counts a program as CLOSED only if a page says it "no longer pays"; this page is just silent about pay.
- **The sentence in RESULT.md, "No program among the 38 readable ones says it accepts AI-generated text", still holds for those 38.** Among all 42 programs now read, one does, under a cap and behind a paywall.

Counts with the follow-up added (same 43 programs; codes from 2026-11-02 for the other 38):

| Code | 2026-11-02 | With follow-up |
|---|---|---|
| BAN_ANY_USE | 0 | 0 |
| BAN_GENERATED | 7 | 7 |
| ALLOW_LIMITED | 0 | **1** |
| ALLOW_DISCLOSED | 0 | 0 |
| NO_ENTRY_RULE | 21 | 22 |
| SILENT | 10 | 12 |
| UNREADABLE | 5 | 1 |
| **Readable** | **38** | **42** |

- Bans: 7 of 42 readable programs (16.7%), against 7 of 38 (18.4%) in the census. P1 (at least 40%) would still not hold.
- ALLOW_DISCLOSED is still 0, so P2 would still hold. P3 is unchanged (0 of 7 bans cover assistance).
- Listed Active and CLOSED: QuickNode joins Bugfender and WebWash, so 3. P5 (at least 5) would still not hold under the registered wording.
- Pay, exploratory as in RESULT.md: adding QuickNode ($350) to the higher-paid group and MagicPod (about $200), Mem0 (the writer names a rate) and SitePoint (none stated) to the other, 6 of 21 programs paying $300 or more ban AI-generated text, against 1 of 21. Fisher's exact p = 0.093 two-sided (0.047 one-sided). This was not a registered test, and these four were coded later and by a different method, so it adds little evidence.

## Two programs outside the frame

Baeldung and Real Python are not on the community list the census uses, so they are not counted above. They were read the same way on 2026-11-13, about 09:14-09:25 UTC.

- **Baeldung:** "Contributions are not currently open." Its writing guide, a Google Doc whose title marks it "(replaced)", says Grammarly "is only for correcting spelling/grammar errors, but NOT re-writing sentences using AI suggestions". That limits AI assistance itself, which is BAN_ANY_USE under the rubric. The page that replaced it is not public, so the current rule could not be read.
- **Real Python:** no AI sentence on the tutorial-writer page, its Workable posting or its Editorial Guidelines (SILENT). Applications are taken year-round into a pool.

Apify's content program (also outside the frame; read 2026-11-12, about 15:32 UTC) is paused until Q1 2027. Its guide says "Don't use AI to generate content you haven't personally validated" and asks that "My authentic voice is present (not AI-generated patterns)". The closest code is ALLOW_DISCLOSED: AI text is allowed once a person has checked it, with no cap. If "authentic voice" is read as a requirement to rewrite AI text, the code would be ALLOW_LIMITED. The program also says it gives writers "AI writing assistance".

## Follow-up 2: seven "Active" programs from a second community list

Added 2026-11-14. Also not pre-registered, and also outside the census frame, so none of the counts above change. [Technical-writing-platforms](https://github.com/Roy-Wanyoike/Technical-writing-platforms) is a second community list of paid writing programs, marked "Last audited: October 2026". Seven programs in its Active table are not on the list the census uses. On 2026-11-14, between about 00:41 and 00:46 UTC, an AI agent working for MV2 opened each program's page in Chrome, signed in nowhere, declined non-essential cookies, filled no form, and copied every AI sentence and the status sentence word for word. The codes use the same [rubric](PREREGISTRATION.md). Rows T01-T07 in [followup.csv](followup.csv) hold every quote.

| Program | AI code | Detector | Status | What the page says |
|---|---|---|---|---|
| Better Stack | NO_ENTRY_RULE | no | **closed** | "We are temporarily closed to new writers but you can register your interest here." (still describes $300 per article) |
| Postmark | NO_ENTRY_RULE | no | open or unclear | takes ideas, but no payment on the page; it offers an interview-based draft and promotion instead |
| A List Apart | SILENT | no | open or unclear | "We're always looking for new authors." (no payment on the page) |
| DigitalOcean (Write for DOnations) | NO_ENTRY_RULE | no | **closed** | "paused for new topics until 2025" (still says "$400 per tutorial") |
| Permit.io | UNREACHABLE | n/a | **gone** | "Page not found" |
| Semaphore | UNREACHABLE | n/a | **gone** | "Oops! That page can't be found." |
| Percona Community | **BAN_GENERATED** | **yes** | open or unclear | "One firm rule: no AI-generated content." "We run every submission through GPTZero and it has to come back clean." ($350 per post) |

What this adds:

- **Of seven programs listed as Active a month after an audit, none is an open, paying program that accepts AI-generated text.** Two pages are gone, two say they are closed or paused, two are open but do not mention payment, and the one open paying program bans AI-generated text.
- **Percona Community is the first program read in any part of this study that names its AI detector.** The census's two DETECTOR flags (Civo, Simple Talk) and Airbyte's "if we detect AI drafts" do not name a tool. Percona's page names GPTZero and requires a clean result. It also expressly allows AI help with drafting ("If you used AI to help draft, that's fine — but the post needs to read as yours and pass the check."), so it is BAN_GENERATED, not BAN_ANY_USE.
- **The four NO_ENTRY_RULE and SILENT codes say nothing about AI rules on submitted work.** On these pages, AI appears only in product links, banners and news.
- Three programs that are in the census frame were read again in the same session. QuickNode, Bugfender and WebWash still show the status sentences recorded before ("At this time, we are not accepting new applications."; "POSITIONS FILLED: CURRENTLY, WE ARE NOT LOOKING FOR NEW WRITERS, BUT YOU CAN SUBMIT YOUR APPLICATION FOR FUTURE CONSIDERATION."; "We're no longer accepting writers."). Their codes are unchanged.
- These statuses were reported to the list's maintainer in [an issue](https://github.com/Roy-Wanyoike/Technical-writing-platforms/issues/4). The three re-read statuses were also proposed for the census's own source list in [malgamves/CommunityWriterPrograms#243](https://github.com/malgamves/CommunityWriterPrograms/pull/243).

## Limits

- One reader, one day, a different method from the census (a browser read by an AI agent, not `programs.py`), and no pre-registration. The page text was saved by the run that read it and is not committed here, because it names authors and staff.
- Coding was done by AI agents. Every quote it rests on is in [followup.csv](followup.csv), so anyone can check or recode it.
- Conflict of interest: MV2 is preparing an application to Mem0's writer program. Mem0's code (NO_ENTRY_RULE) depends on reading one sentence as a wish about style rather than a rule; [followup.csv](followup.csv) says so.
- SitePoint's page refuses automated requests (HTTP 403 on 2026-11-13), so it could only be read in a browser.
- Follow-up 2: the seven programs were chosen because they are on the second list and not on the census's list, not at random. Permit.io and Semaphore are coded GONE from the page text ("Page not found"); the browser read did not record the HTTP status code. Codes that rest on a product link (Better Stack, Postmark, DigitalOcean) follow the rubric's NO_ENTRY_RULE definition; reading those links as no AI sentence would make them SILENT, which also means no rule.
