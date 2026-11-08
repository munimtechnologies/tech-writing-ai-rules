# Study 6 pre-registration: what do llms.txt files tell AI agents to do?

Written 2026-11-08, before the study's tool has requested any file in the frame. The tool (`agentlines.py` 0.1.0, with offline tests in `test_agentlines.py`) waits until this file is on `main` before it fetches anything.

## Why

An llms.txt file is meant to be a map of a site for language models: a title, a short summary and lists of links. Study 5 found that some of them do more than that. 8 of the 27 open-source docs hosts that serve one give AI agents instructions near the top of the file. Pydantic AI asks every agent to add `intent`, `stack` and `harness` query parameters to its requests, and Haystack's file opens with the rules for AI agents that edit its docs. An instruction in an llms.txt file goes straight into an agent's context, often with no human reading it first. This makes these files a channel through which a site can steer what agents say and do: how to use an API, which product to recommend, what to install, what to keep from the user.

Prior art (searched 2026-11-08). Adoption and traffic are well measured: Ahrefs (137,000 domains, 28% publish llms.txt, 97% of files never requested), SE Ranking (about 300,000 domains, 10.13%), Originality.ai (36,120 files in May 2026, 8.8 times as many as a year before), and ALLMO.ai (1 of 94,614 URLs cited by AI answers is an llms.txt). Single cases are described in posts: Stripe's "Instructions for Large Language Model Agents" section (Apideck), Wix's agent-facing llms.txt for shops, and agent instructions on Shopify stores. Guides disagree on whether to add such a section at all (some recommend "system instructions", Gauge's checklist says no hidden instructions). We found **no count of what llms.txt files tell AI agents to do, and no study of how often the instructions promote the site, ask the agent to act, or try to override it.** As far as we know, this is the first.

## Frame

All entries in `data/websites.json` of [llms-txt-hub](https://github.com/thedaviddias/llms-txt-hub) by David Dias (MIT), the largest open directory of sites with llms.txt files, read at commit `e4068608664a9349ddfcf3b51b3724849b51dd76` (2026-09-11, the newest commit that touches the file on 2026-11-08). Each entry gives a name, domain, one of the directory's categories, a listing date (`publishedAt`) and an `llmsTxtUrl`. Entries are numbered W0001... in file order. An entry whose llms.txt URL repeats an earlier one (ignoring `www.`, case of the host and a trailing slash) is kept in `frame.csv` but probed once. The unit of analysis is the unique llms.txt URL.

Disclosure: before writing this file we read the names and one-line descriptions of roughly the first 210 entries (to learn the file's format), but no llms.txt file from the frame. We knew from search results that Stripe's file has an instructions section and that Wix and Shopify publish agent-facing files, and we knew study 5's 27 open-source files. The directory's categories are self-chosen and often wrong (a phone repair shop is filed under `ai-ml`), so they are reported but not used in any prediction.

## Measures

### Automatic (by `agentlines.py`)

For each unique URL the tool reads robots.txt of the URL's host once and honours it for its own agent name (`tech-writing-ai-rules-agentlines`). A host is **reached** if that request gets any HTTP answer; a host with no answer at all is not asked again. It then asks for the llms.txt URL (15 s timeout, 0.25 s between requests, one retry each after 30 and 60 s on HTTP 429) and labels the answer as study 5 did: **valid** (status 200, the same file name after redirects, not HTML, at least 50 non-space characters, and either a Markdown H1 in the first 50 lines or at least three Markdown links), html, challenge, redirected, missing, short, unstructured, robots or error.

In each valid file it marks **candidate lines** that may address an AI reader:

- a line that names an AI reader (AI, LLM, language model, assistant, agent, chatbot, ChatGPT, Claude, Gemini, Copilot, Cursor, Perplexity, Grok, crawler, answer or generative engine) and holds a directive word (should, must, please, always, never, do not, avoid, recommend, cite, attribute, link to, ignore, make sure, ensure, instead of, "when users ask", may not, only use, and others listed in the code);
- a line that starts with an imperative (always, never, do not, please, ignore, avoid, make sure, ensure, "when answering/recommending/citing...", "if a user asks...");
- a "you should / must / need to / are an AI..." line;
- an override phrase: "ignore previous instructions", "disregard previous", "system prompt", "you are now", "new instructions", "do not tell the user", "without telling the user";
- a heading of level 2 or deeper that names AI readers, instructions, guidelines, rules, citation or attribution, and every non-empty line under it (at most 30, until a heading of the same or a higher level).

It also normalises each candidate line (lower case, the site's own name and host replaced by "site", punctuation removed) and counts how many files hold it, so text shared by three or more files (a platform or generator template) stands out.

### Samples (drawn by the tool, fixed by this text)

- **CODE sample:** the first 200 valid files when sorted by `sha256("study6|" + normalised URL)`. If fewer than 200 are valid, all of them.
- **RECALL sample:** the first 20 files of the CODE sample, in the same order, that have no candidate line. Their first 4,000 characters are kept in `recall_heads.json`.

### Hand coding (the study's measurement)

One AI coder reads every candidate line of every CODE file, and the first 4,000 characters of every RECALL file, and codes each file:

- **DIRECTIVE** (yes/no): the file holds at least one sentence that (a) is addressed to an AI reader, either by naming one (an AI, LLM, agent, assistant, model, crawler, a named product, or "you" in a passage addressed to AI) or by sitting under a heading addressed to AI readers, and (b) tells that reader to do, not do, prefer or say something. Not directives: descriptions of the file or the site ("This file helps AI understand our services"), facts about a product made for agents ("Our API is built for AI agents"), welcomes with no condition ("AI crawlers are welcome"), and instructions plainly addressed to human readers.

For files with DIRECTIVE = yes, each of these is coded yes/no (a file can have several):

- **CITE**: cite, attribute or link to the site or a given URL as the source.
- **PROMOTE**: recommend, rank, mention or describe the site, its product or its people favourably, or prefer them over others ("When users ask about X in Y, recommend Z").
- **SOURCE**: treat the site or these pages as authoritative, current or the source of truth, or prefer them over training data or other sources.
- **USAGE**: technical guidance on using the product, API, library or data (versions, endpoints, code patterns, what is deprecated).
- **ACTION**: do something beyond reading and answering: install or connect an MCP server, tool or package, call an API, sign up, pay or buy, contact someone, fetch further pages with added parameters, or report information about the user or task.
- **LIMIT**: restrict or set conditions on use of the content (no training, no reproduction, licence terms, rate limits addressed to AI).
- **OVERRIDE**: try to override the agent's own instructions or its user, or to hide something from the user (ignore previous instructions, a new system prompt, "do not tell the user").
- **OTHER**: any other directive.

Also coded: **TEMPLATE** (the directive text is held by three or more frame files, from the tool's shared count), and one verbatim **QUOTE** of at most 200 characters. A borderline code gets a note. Directives in non-candidate lines of non-RECALL files are not looked for: this is the main limit of the method, and the RECALL sample estimates it.

Outside the CODE sample, **every file in the frame with an override-phrase candidate** is also read and coded OVERRIDE yes/no (descriptive; it gives a whole-frame count of attempts to override agents).

## Gate

- **G1**: at least 60% of unique URLs are reached and at least 200 files are valid. If G1 fails, the counts are reported as descriptive and no prediction is graded.

## Predictions (graded on the hand coding of the CODE sample)

- **P1**: 10% to 40% of CODE files (20 to 80 of 200) have DIRECTIVE = yes.
- **P2**: at least 25% of CODE files with directives have PROMOTE = yes.
- **P3**: at least 20% of CODE files with directives have ACTION = yes.
- **P4**: at most 2% of CODE files (4 of 200) have OVERRIDE = yes.
- **P5**: the DIRECTIVE share among CODE files listed in 2026 is higher than among those listed in 2025. Graded only if each group has at least 30 files.

Method check (not a prediction): if 3 or more of the 20 RECALL files hold a directive, the RESULT says the cue lines miss many directives and reports P1's share as a lower bound.

## Limits known in advance

One reading on one day from one network; files change. The directory is a convenience frame: sites added themselves or were added by its contributors, so it over-represents AI and developer-tool sites and sites that care about llms.txt, and it is not the web. The listing date says when an entry was added, not when the file got its current text. Candidate lines miss directives that use none of the cue words, and the coder sees the candidate lines without the rest of the file. One AI coder, no second coder. The tool's agent name is not a named AI crawler, and some sites may answer AI agents differently. Nothing here says whether any agent follows these directives.

## What will be published

This file, the tool and its tests now. After the run: `RESULT.md`, `coding.csv` (one row per CODE file with its codes, the shared count and one quote), the whole-frame override list, and the tool's `probes.csv` and `AGENTLINES_AUTO.md`. `frame.csv` is republished without the directory's description field. `candidates.csv`, `recall_heads.json` and `census.json` hold longer passages of other people's files and are not republished; `agentlines.py` reproduces them.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the design, the tool and this text were made with AI. Text and data CC BY 4.0, code Apache-2.0.
