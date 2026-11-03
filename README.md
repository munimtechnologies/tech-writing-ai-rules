# tech-writing-ai-rules

What do the companies that pay developers to write technical articles say about AI?

Many software companies and developer publications pay $100 to $900 per tutorial or how-to. Community lists give each program's pay and topics, but not its rule on AI-written or AI-assisted work. This repository counts those rules. It reads each program's own pages, keeps every AI sentence word for word, and codes them against a rubric fixed in advance.

## Result (census of 2026-11-02, graded 2026-11-03)

The frame is all 43 programs (39 listed Active, 4 Paused) in commit `0338535` of [malgamves/CommunityWriterPrograms](https://github.com/malgamves/CommunityWriterPrograms) (MIT). Their pages were read on 2026-11-02, 13 minutes after the [pre-registration](census/2026-11/PREREGISTRATION.md) was committed. Full write-up: [`census/2026-11/RESULT.md`](census/2026-11/RESULT.md).

- **7 of 38 readable programs (18%) ban AI-generated text.** They are Airbyte, Civo, Corellium, MSSQLTips, Simple Talk, Stack Overflow and Twilio. **None bans AI assistance**, and Simple Talk and Stack Overflow name the help they allow (grammar, brainstorming, research, outlining).
- **None says it accepts AI-generated text**, with or without disclosure. 21 mention AI only as a topic or a product, and 10 never mention it. Five could not be read: they are Typeform forms or Notion pages.
- Stack Overflow added a rule in October 2026: writers must disclose their AI use, and the final text "should be written by you".
- Two programs name AI-detection tools (Civo, Simple Talk). Airbyte bans authors "if we detect AI drafts".
- Two programs listed Active now say they take no new writers (Bugfender, WebWash). Four more Active links redirect away from any program page.
- Predictions: **P2 and P3 held; P1, P4 and P5 did not.** Paid technical programs ban AI far less often than the 40% predicted, and fewer name detectors or are plainly closed than predicted.

Compared with writing contests ([companion census](https://github.com/munimtechnologies/ai-writing-prize-rules)): 47% of contests ban AI, and three in four of those bans reach editing and grammar tools. Paid technical programs ban less often, and they guard only the finished text.

## Files

- `programs.py`: the census tool (Python standard library only). It parses the pinned list, waits until the pre-registration is on `main`, then fetches each program's page and up to five same-site guideline, FAQ or policy pages. It writes `census.json`, `sentences.csv` (AI sentences), `status.csv` (status and pay sentences), `frame.csv` and `CENSUS_AUTO.md` (a deterministic first-pass label).
- `test_programs.py`: offline tests (`python -m unittest -v test_programs`).
- `census/2026-11/PREREGISTRATION.md`: the frame, rubric and predictions, committed before any page was read.
- `census/2026-11/RESULT.md`: the graded result, borderline readings and exploratory notes.
- `census/2026-11/coding.csv`: one row per program, giving the code, flags, status and the sentence it rests on.
- `census/2026-11/sentences.csv`: the AI sentences found, word for word (rows from personal author pages are left out; see RESULT.md).
- `census/2026-11/frame.csv`, `census/2026-11/CENSUS_AUTO.md`: the tool's frame and first-pass output, unchanged.

Run it yourself: `python programs.py --out-dir out --no-prereg-check`

## Licence and disclosure

Code: Apache-2.0 (see `LICENSE`). Text and data: CC BY 4.0. The program list it reads is malgamves/CommunityWriterPrograms (MIT); only names, links and pay text are parsed from it.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the tool, the coding and this text were made with AI. Nothing here is legal advice or advice about any program. Read the program's own page before pitching.
