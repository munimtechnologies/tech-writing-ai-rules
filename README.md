# tech-writing-ai-rules

What do the people who pay for or accept technical writing say about AI?

This repository holds two pre-registered studies. Each reads its sources' own pages, keeps every AI sentence word for word, and codes them against a rubric fixed in advance.

1. **Paid technical-writing programs** (graded): many software companies and developer publications pay $100 to $900 per tutorial or how-to. Community lists give each program's pay and topics, but not its rule on AI-written or AI-assisted work.
2. **Open-source AI contribution policies and documentation** (registered 2026-11-04, not yet run): do projects' AI rules say whether they cover docs, READMEs, tutorials and translations, or only code?

## Result 1: paid programs (census of 2026-11-02, graded 2026-11-03)

The frame is all 43 programs (39 listed Active, 4 Paused) in commit `0338535` of [malgamves/CommunityWriterPrograms](https://github.com/malgamves/CommunityWriterPrograms) (MIT). Their pages were read on 2026-11-02, 13 minutes after the [pre-registration](census/2026-11/PREREGISTRATION.md) was committed. Full write-up: [`census/2026-11/RESULT.md`](census/2026-11/RESULT.md).

- **7 of 38 readable programs (18%) ban AI-generated text.** They are Airbyte, Civo, Corellium, MSSQLTips, Simple Talk, Stack Overflow and Twilio. **None bans AI assistance**, and Simple Talk and Stack Overflow name the help they allow (grammar, brainstorming, research, outlining).
- **None says it accepts AI-generated text**, with or without disclosure. 21 mention AI only as a topic or a product, and 10 never mention it. Five could not be read: they are Typeform forms or Notion pages.
- Stack Overflow added a rule in October 2026: writers must disclose their AI use, and the final text "should be written by you".
- Two programs name AI-detection tools (Civo, Simple Talk). Airbyte bans authors "if we detect AI drafts".
- Two programs listed Active now say they take no new writers (Bugfender, WebWash). Four more Active links redirect away from any program page.
- Predictions: **P2 and P3 held; P1, P4 and P5 did not.** Paid technical programs ban AI far less often than the 40% predicted, and fewer name detectors or are plainly closed than predicted.

Compared with writing contests ([companion census](https://github.com/munimtechnologies/ai-writing-prize-rules)): 47% of contests ban AI, and three in four of those bans reach editing and grammar tools. Paid technical programs ban less often, and they guard only the finished text.

## Study 2: do AI contribution policies cover documentation? (pre-registered 2026-11-04)

The largest study of open-source AI policies so far ([arXiv 2609.07542](https://arxiv.org/abs/2609.07542), 281 policies) counts documentation together with code, and the open datasets record stance but not scope. This study reads the policies of the 101 projects in [awesome-ai-contribution-policies](https://github.com/ahmad-punch/awesome-ai-contribution-policies) (data CC BY 4.0, pinned commit `6cd258e`). For each one it codes whether the rules name documentation, treat it differently from code, speak of contributions in general, or are worded for code only. The rubric, five predictions and two gates are in [`census/2026-11-oss-docs/PREREGISTRATION.md`](census/2026-11-oss-docs/PREREGISTRATION.md), committed before any policy text was read.

## Files

- `programs.py`: the paid-programs census tool (Python standard library only), version 0.1.1. It parses the pinned list, waits until the pre-registration is on `main`, then fetches each program's page and up to five same-site guideline, FAQ or policy pages. It writes `census.json`, `sentences.csv` (AI sentences), `status.csv` (status and pay sentences), `frame.csv` and `CENSUS_AUTO.md` (a deterministic first-pass label, plus redirect, detector and closed-notice flags).
- `test_programs.py`: offline tests (`python -m unittest -v test_programs`).
- `docscope.py`: the documentation-scope tool, version 0.1.0 (standard library only). It reads each frame project's CONTRIBUTING, AI_POLICY, AGENTS.md and pull request template files, the dataset's source link and up to four AI-policy links. It writes `census.json`, `sentences.csv` (AI sentences with docs, code, generic and rule-word flags), `frame.csv` and `DOCSCOPE_AUTO.md`. Offline tests: `python -m unittest -v test_docscope`.
- `CHANGELOG.md`: what changed in each version.
- `census/2026-11/PREREGISTRATION.md`: the frame, rubric and predictions, committed before any page was read.
- `census/2026-11/RESULT.md`: the graded result, borderline readings and exploratory notes.
- `census/2026-11/coding.csv`: one row per program, giving the code, flags, status and the sentence it rests on.
- `census/2026-11/sentences.csv`: the AI sentences found, word for word (rows from personal author pages are left out; see RESULT.md).
- `census/2026-11/frame.csv`, `census/2026-11/CENSUS_AUTO.md`: the 0.1.0 tool's frame and first-pass output, unchanged.
- `census/2026-11-oss-docs/PREREGISTRATION.md`: study 2's frame, rubric, predictions and gates.

Run them yourself: `python programs.py --out-dir out --no-prereg-check` or `python docscope.py --out-dir out --no-prereg-check`

## Licence and disclosure

Code: Apache-2.0 (see `LICENSE`). Text and data: CC BY 4.0. The program list `programs.py` reads is malgamves/CommunityWriterPrograms (MIT); only names, links and pay text are parsed from it. The project list `docscope.py` reads is awesome-ai-contribution-policies (data CC BY 4.0), used with attribution. Quoted policy text belongs to each project.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the tools, the coding and this text were made with AI. Nothing here is legal advice or advice about any program or project. Read the program's or project's own page before pitching or contributing.
