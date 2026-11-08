# Changelog

## Unreleased (2026-11-08): study 5 pre-registered, agent skill added

- **New agent skill, `skills/oss-ai-contribution-rules/` 0.1.0.** A `SKILL.md` (Agent Skills format) tells coding agents such as Claude Code, Codex and Cursor to check a project's AI contribution rule before they write, edit or open a pull request or issue for it. It puts documentation first and covers the trap studies 2 and 3 found: a separate docs repo whose contributor files never repeat the main rule. `scripts/ai_rules_lookup.py` (standard library only, no network) looks a project up by GitHub URL, `owner/repo` or name. It prints the coded rule, a verbatim quote, the source link, any separate docs repo and what to do, with exit codes 0 (matched), 1 (no row; same-owner rows are listed as hints) and 2 (error). Its data in `assets/` are unchanged copies of study 2's and study 3's `coding.csv`, plus `repo_slugs.csv`, which maps each study 2 row to GitHub slugs for lookup and is not part of the studies' coding. Offline tests: `python -m unittest -v test_ai_rules_skill`. The skill's text says plainly that it is a snapshot (texts read 2026-11-04 and 2026-11-07) and that the live files win.
- **New tool, `llmsprobe.py` 0.1.0**, with offline tests in `test_llmsprobe.py` (standard library only). For each documentation base in a frame it reads the base page (noting bot-check pages), asks for it again as Markdown, asks for `llms.txt` and `llms-full.txt` in the base's folder and at the host root, and labels each answer (valid, html, challenge, redirected, missing, short, unstructured, error, robots). It reads robots.txt of the host the docs land on and records which of 20 named AI crawlers may not fetch the docs page while an agent without a group of its own may, using RFC 9309 / Google-style matching (own group else `*`, longest rule, Allow wins a tie), plus any Content-Signal lines. It honours robots.txt for its own fetches and computes the pre-registered gate and predictions from its labels.
- **Study 5 is pre-registered** in `census/2026-11-llms-txt/` (frame of 56 projects from study 2, grouped BAN / RESTRICTED / OPEN by the dataset's stance; five predictions and a gate). The tool waits until the pre-registration is on `main`. Not graded yet.
- No other tool changed: `programs.py` stays at 0.1.1, and `docscope.py` and `guidescan.py` at 0.1.0.

## 0.5.0 (2026-11-07): study 4 graded

- **Result of study 4** in `census/2026-11-style-guides/RESULT.md`. Of 19 public documentation style guides, 14 could be read. Only 3 say anything about writing with AI: GitLab and Intuit allow it with a check, Microsoft's word list recommends learning to prompt, and none bans it. 4 give advice on writing for AI (LLMs, AI search, AI crawlers, chatbots), and 7 have a rule on writing AI terms. All five predictions held, and the gate passed (N = 14). The release adds `coding.csv` (BY, FOR and ABOUT per guide, first-pass agreement, borderline flags, verbatim quotes of at most 300 characters with URLs) and the tool's unchanged `frame.csv`, `pages.csv` and `GUIDESCAN_AUTO.md`.
- The tool's `sentences.csv` is not republished, because some rows come from event-programme pages that name individual speakers. `guidescan.py` reproduces it.
- **Known first-pass limits in `guidescan.py` 0.1.0** (not fixed here; the primary coding was done by reading). Site menus and footers count as AI sentences, which gave three false `ai_text` labels (Draft.dev, Princeton, DigitalOcean). A page that is only a table of contents passes the 1,000-character check (Apple). The breadth-first crawl can spend its page cap on a word list before it reaches topic sections (Microsoft). A later version should drop repeated navigation text and visit section index pages before word-list entries.
- No tool code changed. `programs.py` stays at 0.1.1, and `docscope.py` and `guidescan.py` at 0.1.0.

## 0.4.0 (2026-11-07): study 3 graded, study 4 pre-registered

- **Result of study 3** in `census/2026-11-docs-repos/RESULT.md`. It covers 14 separate documentation repos of projects whose main repos have AI contribution rules. Only 3 state an AI rule in their own contributor files, and none has a link that points to an AI policy. Four main rules name documentation, and only Home Assistant's appears in its docs repo. P1, P2 and P3 held; P4 failed on one borderline code (PostHog's website repo drops the disclosure its main policy requires). The release adds `coding.csv` (REACH, TERMS, first-pass agreement, borderline flag, one quote of at most 300 characters and its source per repo) and the tool's unchanged `frame.csv`, `sentences.csv` and `DOCSCOPE_AUTO.md`.
- **A known first-pass gap in `docscope.py` 0.1.0** (not fixed here; the primary coding was done by reading): its AI cues do not match "agent" on its own, so a rule addressed to "you, an agent" in an AGENTS.md file is missed. This happened in PostHog's website repo.
- **Study 4 is pre-registered** in `census/2026-11-style-guides/`, with `guidescan.py` 0.1.0 and its offline tests (committed 2026-11-06). It has not been graded yet.
- No tool code changed in this release. `programs.py` stays at 0.1.1 and `docscope.py` at 0.1.0.

## 0.3.0 (2026-11-05): study 2 graded

- **Result of study 2** in `census/2026-11-oss-docs/RESULT.md`, with `coding.csv` (one row per project: RULE, SCOPE, first-pass label and agreement, borderline flag, one quote of at most 300 characters and its source), plus the tool's unchanged `frame.csv` and `DOCSCOPE_AUTO.md`. Both gates passed (93 of 101 projects read; 56 with AI rules). P1, P3 and P4 held; P2 and P5 failed. Of the 56 projects with AI rules, 14 name documentation, and only Rust treats it differently from code.
- **Known first-pass issues in `docscope.py` 0.1.0** (not fixed in this release; the primary coding was done by reading and did not rely on them): the docs flag only looks inside the AI sentence itself, so documentation named in a neighbouring sentence or list item is missed; the sentence splitter breaks at "e.g."; and the docs cues match "manual", "README.md" in other senses and site names such as "Source Docs". A later version should look at a window around each AI sentence.
- No tool code changed. `programs.py` stays at 0.1.1 and `docscope.py` at 0.1.0.

## 0.2.0 (2026-11-04): docscope.py 0.1.0, a second study

- **New tool, `docscope.py` 0.1.0**, with offline tests in `test_docscope.py`. It asks whether open-source projects' AI contribution policies say they cover documentation. The frame is the 101 projects of the open dataset awesome-ai-contribution-policies (data CC BY 4.0) at a pinned commit. For each project it reads the repo's standard policy files at the default branch, the dataset's own source link and up to four AI-policy links from those texts, then keeps every AI sentence word for word with first-pass flags (docs, code, generic, rule word). Raw Markdown and reST are read with hard-wrapped lines joined, so a sentence that spans lines stays whole. The text inside HTML comments is kept, because pull request templates put their instructions there. A rate-limited fetch (HTTP 429) is retried after 60, 120 and 240 seconds, and each page records whether it was retried.
- **Pre-registration** in `census/2026-11-oss-docs/PREREGISTRATION.md`, with a rubric, five predictions and two gates. It was committed before any policy text was read, and the tool waits for it.
- `programs.py` is unchanged (0.1.1).

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
