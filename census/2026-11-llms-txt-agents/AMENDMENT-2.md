# Study 6, amendment 2: how a stuck run is prevented (2026-11-09)

Written 2026-11-09, before any result of study 6 was seen. Nothing in the [pre-registration](PREREGISTRATION.md) or in [amendment 1](AMENDMENT-1.md) changes except what is described here.

## What happened

The second run (job `agentlines-v2`, runner `agentlines_run.py` 0.1.0, 8 hosts at a time, one CPU) started on 2026-11-09 at 15:56 UTC. It read 800 of the 1,512 unique llms.txt URLs in about four minutes, printing a progress line every 100 URLs. Then it printed nothing more for three hours. At 19:00 UTC the job runner stopped it from outside, together with another field's job on the same machine, so the job's own 10-hour limit was not what ended it. It wrote no output file, and no answer from any llms.txt URL was saved or seen.

We cannot tell from the log which host stalled the run. The pattern (all eight workers silent at once) points to one of two causes:

1. **A robots.txt rule that makes the matcher backtrack.** `agentlines.py` 0.1.0 turns each robots.txt rule into a regular expression (`*` becomes `.*`). A rule with many `*` wildcards can make Python's regular expression engine try a huge number of ways to match before it fails. That engine holds the interpreter lock while it runs, so one such rule freezes every worker at once.
2. **Servers that answer too slowly to finish but never time out**, for example by sending headers a byte at a time. Runner 0.1.0 limits the whole body to 60 seconds, but not the wait for the headers.

## What changes

The third run uses `agentlines_run.py` 0.2.0 (offline tests in `test_agentlines_run.py`). It still imports `agentlines.py` 0.1.0 unchanged and replaces only functions while it runs:

- **A linear-time robots.txt matcher.** `wildcard_match` gives the same answer as `agentlines.py`'s `pattern_match` for every rule and path (a test compares them on all 1,365 rules of up to five characters over `a`, `.`, `*` and `$` against all 121 paths of up to four characters), but it never backtracks. Which URLs robots.txt allows does not change.
- **A host that does not finish is given up.** If a host's requests have not all finished after 600 seconds per URL, its unfinished URLs are recorded as errors with the note "given up", and the run goes on. A URL is counted as not reached if its host's robots.txt never answered, and as reached with no answer otherwise, as a timeout already was. A host that answers normally needs far less: robots.txt and the llms.txt file, each cut off after 60 seconds and retried at most twice (after 30 and 60 seconds) on HTTP 429.
- **A diagnosis if it stalls again.** If no host finishes for 15 minutes, the stack of every thread is written to the job's error log.

Everything amendment 1 kept unchanged is still unchanged: the frame (the directory at commit `e406860`), the agent name, User-Agent, robots.txt handling, labels, candidate lines, CODE and RECALL samples, hand coding rubric, gate, predictions and `grade_study6.py`. The automatic report names the runner version and both limits. The fetch date moves to the day the third run takes place.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: this text and the runner were made with AI. Text CC BY 4.0, code Apache-2.0.
