# Labelling AI-made docs pages so people and agents both see the label

A practical guide for docs teams, written from studies 7 to 10 in this repository (2026-11-11). Commands below run from the repository root. Text: CC BY 4.0. Code: Apache-2.0. This is not legal advice.

Some docs teams already use AI to draft or change pages, and some want to tell readers so. This guide covers how to make that note reach readers and stay attached when the page is copied. It does not tell you whether to label: that is your team's call, and the law rarely decides it for product docs (see [What the rules say](#what-the-rules-say)). If you do label, our studies found that the note fails silently far more often than you would expect.

## What we measured

| Finding | Number | Study |
| --- | --- | --- |
| Microsoft Learn articles carrying an AI label, in the 30 largest public MicrosoftDocs repos | 6,618 of 182,133 (3.63%); 7.73% of articles dated 2026 | [7](../census/2026-11-ms-learn-ai-labels/RESULT.md) |
| Learn pages labelled `ai-usage` that show the end-of-article note | 131 of 131 | [8](../census/2026-11-ms-learn-ai-shown/RESULT.md) |
| Learn pages whose label key is spelled `ms.ai-usage` or `ai.usage` that show it | 0 of 33 | 8 |
| Learn pages whose served HTML (before scripts run) contains the note | 0 of 263 | 8 |
| Labelled Learn Markdown copies (for agents) that keep the label / the note | 164 of 164 / 0 of 131 | 8 |
| Big developer-docs vendors that say AI drafts or helps write their docs | 4 of 20 | [9](../census/2026-11-vendor-docs-ai-labels/RESULT.md) |
| Sampled pages on 18 readable vendor sites that tell the reader | 0 of 536 | 9 |
| Callouts lost from Markdown copies served to agents (hand-checked) | 7 of 409, all where the export skipped a template or component | [10](../census/2026-11-md-copy-parity/RESULT.md) |

Microsoft Learn is the only docs site we have seen label pages. Its [principles page](https://learn.microsoft.com/en-us/principles-for-ai-generated-content) promises that "All articles that contain any AI-generated content include text acknowledging the role of AI" at the end of the article. That promise holds when the label is spelled exactly as documented. It fails without any warning when the key is misspelled, when a reader's tool doesn't run page scripts, or when an agent reads the Markdown copy.

## The one rule behind all the failures

**A note that a template or script adds is lost wherever the template or script doesn't run.** That covers crawlers and agents that read the served HTML without running scripts, Markdown copies (`Accept: text/markdown`, `<page>.md`, `llms-full.txt`), RSS, print and offline exports, and copy-paste. Study 10 found the same mechanism with tips, warnings and setup steps: the copies kept almost everything written in the page's own text and lost what a component added.

So decide where the note lives:

| Where the note comes from | Rendered page | Served HTML | Markdown copy for agents | Risk |
| --- | --- | --- | --- | --- |
| A script adds it after load (Learn today) | yes | no | no | invisible to anything that doesn't run scripts |
| The site template adds it at build time | yes | yes | only if your exporter runs the same template | the copy needs its own step |
| A sentence in the page's own Markdown | yes | yes | yes | the sentence and the metadata can drift apart; lint both |

## Checklist

1. **Keep one machine-readable label in the source front matter.** Use one key and a closed set of values. Microsoft's is a top-level `ai-usage:` with `ai-assisted` or `ai-generated`. Keep the key at the top level (study 7 found 23 Learn labels nested under `ms.custom` or commented out, where no parser reads them).
2. **Lint the key in CI**, so a misspelled key fails the build instead of hiding the note. For Learn-style repos our checker does this (Python standard library only):
   ```
   python skills/docs-ai-label-check/scripts/ai_label_check.py docs/ --json
   ```
   It reports variant keys, misspelled values, duplicate, nested and commented labels. It was built for DocFX/Learn repos; for other generators, reject any front matter key that contains `ai` and `usage` but isn't exactly yours.
3. **Render the note at build time, not with a script**, so it is in the served HTML. In Docusaurus 3, wrap the doc footer (`npm run swizzle @docusaurus/theme-classic DocItem/Footer -- --wrap`) and read the front matter. This is a sketch; check it against your version:
   ```jsx
   import React from 'react';
   import Footer from '@theme-original/DocItem/Footer';
   import {useDoc} from '@docusaurus/plugin-content-docs/client';

   const NOTES = {
     'ai-assisted': 'This page was written with help from AI tools and reviewed by our docs team.',
     'ai-generated': 'Parts of this page were generated with AI and reviewed by our docs team.',
   };

   export default function FooterWrapper(props) {
     const {frontMatter} = useDoc();
     const note = NOTES[frontMatter['ai-usage']];
     return (
       <>
         {note && <p className="ai-usage-note">{note}</p>}
         <Footer {...props} />
       </>
     );
   }
   ```
   Write only what is true for your process. Don't claim review that didn't happen.
4. **Put the note in the Markdown copy as text, not only in its front matter.** Learn's copies keep the `ai-usage` key in their header, but an agent that strips the header, or quotes the body, loses it. Add the same sentence as the copy's last paragraph, or as its first line under the title. If your copies come from a plugin or an exporter, add the step there.
5. **Test the outputs, not the source.** After the build, check that every labelled page's HTML (as served, before scripts) and its Markdown copy contain the note. A one-line check per page is enough (`curl -s <url> | grep -c "written with help from AI"`, and the same with `-H "Accept: text/markdown"` or the `.md` address). Our `md-copy-check` skill finds the other ways copies break (exporter placeholders, empty components, MDX code):
   ```
   python skills/md-copy-check/scripts/md_copy_check.py --url https://docs.example.com/some/page/
   ```
6. **Make the note readable by assistive technology.** Plain text in the page flow is enough; an icon alone is not (the EU's own icon set is optional, and Smashing Magazine's summary quotes the Commission: an icon "does not establish legal compliance by itself").
7. **Keep the label when a page changes.** Decide in advance what happens when a person rewrites an AI-assisted page, or when AI rewrites a page with no label. Learn's labels are almost all from 2025 and 2026, so most teams will face this soon.
8. **Say where AI is used, not only that it is.** Study 9's four vendor statements (AWS, Cloudflare, Datadog, IBM Cloud) say that AI drafts or helps write docs. None of their 88 sampled pages (AWS, Cloudflare, Datadog) tells the reader which ones.

## What the rules say

- **EU AI Act, Article 50(4), second subparagraph.** It applies from 2 August 2026. Deployers of an AI system that generates or manipulates text "published with the purpose of informing the public on matters of public interest" must disclose that the text is AI-generated. That duty does not apply where the content "has undergone a process of human review or editorial control" and a person or company holds editorial responsibility. Article 50(5) asks for the information "in a clear and distinguishable manner at the latest at the time of the first interaction or exposure", meeting accessibility requirements. Most product docs are probably not "matters of public interest", and most docs teams review before publishing, so for many teams labelling is a choice, not a duty. Ask your own counsel.
- **The Commission's Code of Practice on transparency of AI-generated content** (published 10 June 2026) offers an optional EU icon in three variants and guidance on the placement of labels. Its [FAQ](https://digital-strategy.ec.europa.eu/en/faqs/code-practice-transparency-ai-generated-content) gives a transition until 2 December 2026 for systems already on the market. Smashing Magazine's [summary of the guidelines](https://www.smashingmagazine.com/2026/08/eu-guidelines-ai-labelling/) is a readable overview for web teams.
- **Microsoft Learn's own promise** goes further than the law: every article with any AI-generated content gets the note, although Microsoft says its authors review and test all AI-generated content before publishing.

## Limits

The numbers come from one docs site that labels (Microsoft Learn) and 20 that don't, read in November 2026, English pages only. Study 8's browser check used one desktop browser on 8 pages. The Docusaurus snippet is a sketch, not tested code. The tools named here are tested in this repository (`python -m unittest -v test_ai_label_check test_md_copy_check`).

Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the studies, the tools and this guide were made with AI.
