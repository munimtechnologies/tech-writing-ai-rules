# Study 6, amendment 1: how the files are fetched (2026-11-09)

Written 2026-11-09, before any result of study 6 was seen. Nothing in the [pre-registration](PREREGISTRATION.md) changes except the scheduling described here.

## What happened

The first run of `agentlines.py` 0.1.0 (job `agentlines-v1`, started 2026-11-09 02:00 UTC) read the directory's hosts one after another. The job's 8-hour limit stopped it at 10:00 UTC, before it wrote any output file. It printed nothing on the way, so we do not know how far it got, and no answer from any llms.txt URL was saved or seen. The likely cause is slow servers: the tool's 15-second timeout applies to each network read, not to a whole request, so a server that sends its answer slowly can hold one request for minutes.

## What changes

The second run uses a new runner, `agentlines_run.py` 0.1.0 (offline tests in `test_agentlines_run.py`). It imports `agentlines.py` 0.1.0 unchanged and replaces only two functions while it runs:

- **Hosts in parallel.** Unique llms.txt URLs are grouped by host. Each host's requests (robots.txt first, then each llms.txt URL on that host) stay in order in one worker, with the same 0.25 s pause before each request and the same retries after 30 and 60 s on HTTP 429. Up to 8 hosts are read at the same time. No host gets more requests, or gets them faster, than in a one-by-one run.
- **A limit on each request.** Each request is cut off after 60 seconds in all (600 seconds for the directory file itself). A cut-off answer is recorded as an error with no HTTP status, as a timeout already was. One known effect: a host whose robots.txt takes longer than 60 seconds is recorded as not reached.
- An unexpected error while probing one URL is recorded as that URL's error instead of stopping the run.

Results keep the frame's order, so the samples, the counts and the output files are what a one-by-one run would give for the same answers (a test checks this). The tool's agent name, User-Agent, robots.txt handling, labels, candidate lines, CODE and RECALL samples, hand coding rubric, gate, predictions and `grade_study6.py` are all unchanged. The automatic report names the runner next to the tool version.

The fetch date moves from 2026-11-09 to the day the second run takes place; the frame stays the directory at commit `e406860`.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: this text and the runner were made with AI. Text CC BY 4.0, code Apache-2.0.
