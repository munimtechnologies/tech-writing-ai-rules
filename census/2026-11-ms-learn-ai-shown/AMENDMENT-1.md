# Study 8, amendment 1: URL mapping and a rendered measure (2026-11-10)

Written 2026-11-10, after the first run and before any second run. No page has been rendered by the tool for this study. The [pre-registration](PREREGISTRATION.md) stands except for the two changes below. The tool, `learnshown.py` 0.2.0, waits until this file is on `main` before it reads anything.

## What the first run showed, and what we have seen since

The first run (`learnshown.py` 0.1.0, 2026-11-09 14:19 to 14:38 UTC) read 15 repos and drew 315 files, but nothing was graded:

- **Mapping.** Only 57 of the 315 files were confirmed as the source of the page fetched (all from `azure-docs` and `entra-docs`). 253 URLs gave HTTP 404, and 5 led to a page that names another source file. The tool built each URL from `docfx.json`'s `build.dest`, which is not Learn's URL path for most repos (for example `fabric-docs` where Learn uses `/fabric/`, `support1-docset` where it uses `/troubleshoot/`). So G1 failed: 40 labelled pages from 2 repos (needs 100 from 8).
- **G2 failed.** The served HTML of the Entra control page had no acknowledgement sentence, not even inside its scripts, although a rendering reader (r.jina.ai, which runs page scripts) had shown "The author created this article with assistance from AI." on the same page before the pre-registration. The sentence appears to be added by page scripts after loading, which is the case the pre-registration's G2 was written to catch. As pre-registered, P1 to P4 could not be graded.
- **Seen in the first run's output (57 counted pages):** no acknowledgement sentence in any served HTML or Markdown copy; every labelled page's Markdown copy and HTML carried its AI key; 49 of 49 pages whose source ends with "Next steps" or "Related content" lacked that heading in the Markdown copy. These are not grades.
- **Seen since, for this amendment only:** the `docfx.json` of 9 repos (Fabric, Cloud Adoption Framework, Architecture Center, Minecraft Creator, Power Apps and its breadcrumb file, SupportArticles, Dynamics 365 Customer Engagement, Dynamics 365 Finance and Operations, and Visual Studio), read through raw.githubusercontent.com, and the first run's own URLs and statuses. We fetched no sampled page. We confirmed that learn.microsoft.com/robots.txt does not disallow `/api/search`, and made one search request (not for a sampled title) to learn its JSON shape.

## Change 1: how each file's URL is found

The rule "a page counts only if a fetched form names this exact repo file as its source" is unchanged. Only the way candidate URLs are built changes. For each sampled file, the tool tries these in order and uses the first whose fetched form names the file (`source_path`, or the end of `original_content_git_url`, case ignored):

1. **Breadcrumb base:** the folder of the nearest `docfx.json`'s `globalMetadata.breadcrumb_path`, if that path starts with `/`, with a final folder named `breadcrumb`, `_breadcrumb`, `bread` or `_bread` dropped (`/fabric/breadcrumb/toc.json` gives `fabric`; `/azure/architecture/bread/toc.json` gives `azure/architecture`), then the content entry's `dest` and the path below its `src`, as before.
2. **Breadcrumb root:** the first segment of that base, if it differs (`/dynamics365/ops-bc/toc.json` gives `dynamics365`).
3. **The 0.1.0 rule** (`build.dest`, entry `dest`, path).
4. Each of 1 to 3 also in lower case, right after it, when that differs.
5. **Learn search:** if none of these is confirmed, the first 5 en-us page URLs that Learn's public search API (`learn.microsoft.com/api/search`) returns for the file's front matter `title`.

Each try is one Markdown request (one per second, robots.txt honoured). The answer names its source file whether Learn serves Markdown or HTML. Files that no candidate confirms are reported with the first candidate's statuses and are not counted, as before. `pages.csv` gains `url_rule` (which candidate was used) and `tried` (how many URLs were tried). The draw, the strata, the frame and the controls are unchanged; the draw is re-run on the repos as they are on the day of the second run.

## Change 2: the acknowledgement measure is read from the rendered page

With `--render`, after a page is counted, the tool also loads it in headless Chromium (Playwright). It waits for the load event and for the network to go quiet (at most 15 seconds), scrolls to the end, waits 2 more seconds, and reads `document.body.innerText`. Each line of that text is treated as a paragraph, and the same acknowledgement pattern as before is applied. The browser's User-Agent is Chromium's own followed by the tool's name and contact address.

- **G2 and P1 to P4 are graded on the rendered text** (`note_rendered`) instead of the served HTML. Their boundaries, minimum counts and the rule that G2 must pass before P1 to P4 are graded are unchanged. P4 compares the rendered page with the Markdown copy.
- The served-HTML measure (`note_html`) is still recorded and reported, as a descriptive result.
- If Playwright or its browser cannot start, the tool stops before it reads anything (exit code 5); it never falls back silently to the served HTML.
- G1, G3, P5, P6 and the hand checks are unchanged. The hand check of 10 counted A and B pages with no match is now read against the rendered text the tool saw, and those pages are also opened in a browser as before.

## Why this is not a change of question

The pre-registration asks whether readers are shown the acknowledgement. People read the page after its scripts have run. The pre-registration named this risk in G2 and in its limits ("The tool sees the HTML as served, not after scripts run"). This amendment replaces the measure with one that sees what people see, before any rendered result exists. If the rendered control still shows no sentence, G2 fails again and P1 to P4 stay ungraded.

## Limits added

- Rendering depends on Learn's scripts and on timing. A sentence added later than about 17 seconds after load, or only after a click, would be missed.
- Search results can change from day to day; the URL used for each page is recorded.
- The repos may have changed since the first run, so the second sample is not the same as the first.

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: this amendment, the tool and its tests were made with AI.
