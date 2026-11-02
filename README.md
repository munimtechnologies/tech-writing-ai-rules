# tech-writing-ai-rules

What do the companies that pay developers to write technical articles say about AI?

Many software companies and developer publications pay $100 to $900 per tutorial or how-to. Community lists give each program's pay and topics, but not its rule on AI-written or AI-assisted work. This repository counts those rules. It reads each program's own pages, keeps every AI sentence word for word, and codes it against a rubric fixed in advance.

## Status (2026-11-02)

**Pre-registered, not yet run.** [`census/2026-11/PREREGISTRATION.md`](census/2026-11/PREREGISTRATION.md) fixes the frame, the coding rubric and five predictions before any program page is read. The frame is all 43 programs (39 listed Active, 4 Paused) in commit `0338535` of [malgamves/CommunityWriterPrograms](https://github.com/malgamves/CommunityWriterPrograms) (MIT). The results will be added to `census/2026-11/` with every coded sentence quoted, and graded against the predictions whatever they show.

## Files

- `programs.py`: the census tool (Python standard library only). It parses the pinned list, waits until the pre-registration is on `main`, fetches each program's page and up to five same-site guideline, FAQ or policy pages, and writes `census.json`, `sentences.csv` (AI sentences), `status.csv` (status and pay sentences), `frame.csv` and `CENSUS_AUTO.md` (a deterministic first-pass label).
- `test_programs.py`: offline tests (`python -m unittest -v test_programs`).
- `census/2026-11/PREREGISTRATION.md`: the frame, rubric and predictions.

Run it yourself: `python programs.py --out-dir out --no-prereg-check`

## Companion

[munimtechnologies/ai-writing-prize-rules](https://github.com/munimtechnologies/ai-writing-prize-rules) does the same for writing contests: in its pre-registered census of 54 contests closing in late 2026, 24 of 51 readable contests ban AI and one accepts disclosed AI-generated text.

## Licence and disclosure

Code: Apache-2.0 (see `LICENSE`). Text and data: CC BY 4.0. The program list it reads is malgamves/CommunityWriterPrograms (MIT); only names, links and pay text are parsed from it.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the tool, the coding and this text were made with AI. Nothing here is legal advice or advice about any program. Read the program's own page before pitching.
