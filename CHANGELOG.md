# Changelog

## 0.1.1 (2026-11-04)

Fixes to `programs.py`'s automatic first pass, found while grading the 2026-11 census by hand. The census in `census/2026-11/` was made with 0.1.0. Its files, its primary coding and its graded result are unchanged: the primary coding was done by reading every saved sentence and never relied on these cues. The next census will use 0.1.1.

- **Curly apostrophes.** 0.1.0's ban cue knew "can't", "won't" and "don't" only with a straight apostrophe, so Corellium's "can’t" was missed and its first-pass label was other_mention, not ban. Cues are now matched on a copy of each sentence with curly apostrophes made straight. Sentences are still saved exactly as found.
- **Missed closed notices.** Bugfender's notice ("POSITIONS FILLED: CURRENTLY, WE ARE NOT LOOKING FOR NEW WRITERS ...") was not caught as a status sentence. The cues were already case-insensitive, but none covered "not looking for (new) writers" or "positions filled". Both are now cues, along with "not hiring/seeking writers, authors, contributors or submissions".
- **Redirects.** Each page now records `redirect`: `home` when the listed page lands on a home page, `elsewhere` when it lands on another path or site, and empty otherwise (scheme, `www.` and a trailing slash are ignored). Each program records `main_redirect`. In the 2026-11 census, four Active programs' links redirected away from any program page, and this was only found by hand (see `census/2026-11/RESULT.md`, P5).
- **Detector flag.** 0.1.0 set `mentions_detector` for any AI sentence containing a "detect" word, so privacy-policy text about detecting fraud counted. It now needs detection of AI writing ("if we detect AI drafts", "AI detection", a named tool). A new flag, `names_detector_tool`, records whether a tool is named (Originality.ai, GPTZero, Copyleaks, ZeroGPT, Turnitin, "AI detector"), which is what the 2026-11 rubric's DETECTOR flag asks for.
- `CENSUS_AUTO.md` gains a redirect column and redirect counts. In its detector column, `tool` means a tool is named and `yes` means detection is mentioned without naming one.

Not changed: the frame (the pinned list commit), the pages followed, the sentence splitter, the label set and the ban/assist/allow cues apart from the apostrophe fix. Two 0.1.0 false bans noted in RESULT.md ("no paywalls" at In Plain English, "AI does not replace our editors" at TestMu AI) are still possible in 0.1.1. The first pass is a screen, and the primary coding is done by reading.

## 0.1.0 (2026-11-02)

First release, used for the pre-registered census in `census/2026-11/`.

Made by MV2 of Munim, Inc., with AI agents working in his name. Apache-2.0.
