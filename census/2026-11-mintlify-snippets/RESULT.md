# Study 16 result: `<Snippet file>` tags in Mintlify's Markdown copies for AI agents

Graded 2026-11-16. Made by MV2 of Munim, Inc. (mv2@munimtech.com), with AI agents working in his name: the tool, the grading, the hand check and this text were made with AI. Licence: text and data CC BY 4.0, code Apache-2.0.

Plan: [PREREG.md](PREREG.md) (2026-11-12). Tool: [`mintsnip.py`](../../mintsnip.py) 0.1.0, unchanged. Unchanged output: [`sites.csv`](sites.csv), [`instances.csv`](instances.csv), [`controls.csv`](controls.csv), [`mintsnip.json`](mintsnip.json), [`MINTSNIP_AUTO.md`](MINTSNIP_AUTO.md). Hand check: [`hand_check.csv`](hand_check.csv). [`test_study16_result.py`](../../test_study16_result.py) recomputes the numbers below from those files.

## Short answer

Mintlify's documentation says the Markdown copy of a page, which is the version served to AI agents, contains "the content of the imported file, not the tag such as `<Snippet file="path/to/snippet.mdx" />`". **On three of the four sites we could count, the copy contained the bare tag instead**: Mem0 (15 of 15 sampled uses), Helicone (1 of 1) and Supermemory (1 of 1). On Mem0, the web page shows people the snippet's text in all 15 cases. On Agno, all 20 sampled uses reached the copy as text.

**Our hypothesis was wrong.** We expected the folder to decide it: tags kept for files in the older `_snippets/` folder, expanded for files in `snippets/`. But Agno keeps its files in `_snippets/` and its snippets were expanded, while Helicone and Supermemory keep theirs in `snippets/` and their tags were kept.

On the same sites, snippets included the other way (`import X from "/snippets/x.mdx"` and then `<X />`) reached the copy as text in all 25 control pages, across 7 sites, Helicone and Supermemory among them.

## The run

`mintsnip-v1`, run on 2026-11-15 between 18:51 and 19:01 UTC. The tool's own tests passed. Of the 22 repositories in the frame:

- 3 had no `docs.json` or `mint.json`, or couldn't be cloned.
- 13 have no `<Snippet file>` tag on any page, or none that their `llms.txt` lists.
- mintlify/docs has one, but it is not a real tag (see the hand check), so the site isn't counted.
- **4 sites are counted** (G1 needs 3): Mem0, Helicone, Supermemory and Agno, with 37 sampled uses of the tag.

## Verdicts

| | Prediction | Result | Verdict |
|---|---|---|---|
| G1 | At least 3 sites counted | 4 | **holds** |
| P1 | Mem0's `_snippets/` uses: at least 90% tag kept and at least 90% shown on the HTML page | 15/15 kept, 15/15 shown | **holds** |
| P2 | `_snippets/` uses, pooled: at least 80% tag kept | 15/35 = 42.9% (Mem0 15/15, Agno 0/20) | **fails** |
| P3 | `snippets/` uses, pooled: at most 20% tag kept (needs 10) | 2 uses, both kept | **too few** (opposite direction) |
| P4 | Import-style controls: at least 80% reach the copy | 25/25 | **holds** |
| P5 | Uses with a found file: at least 80% shown on the HTML page | 34/37 = 91.9% | **holds** |

The plan says that if P2 fails, the folder hypothesis is wrong. It is. P3 can't be graded with 2 uses. Both were kept, which also goes against the hypothesis.

## Hand check

We read 11 of the tool's excerpts across 5 repositories, and re-read 5 of the copies live on 2026-11-16. The plan asks for at least 10 excerpts across at least 3 sites, and at least 5 live reads. We used a fetch tool that summarises pages and quotes at most about 125 characters.

- **Right:** 9 of 11. The bare tag is really in the Mem0, Helicone and Supermemory copies, and Agno's copies have the snippet text and no tag.
- **Wrong:** 1. mintlify/docs' `cli/commands` page mentions `<Snippet file="...">` inside inline code in a table. It is an example, not a tag. The tool skipped fenced code but not inline code. That site is not counted and the case has no snippet text, so no verdict uses it.
- **Uncertain:** 1. On one Agno page the live copy has no `<Snippet` tag, but our re-read didn't find the first line of the snippet's text. The "expanded" status may rest on a link alone. This doesn't affect P2, which counts only whether the tag is kept.

1 wrong in 11 is under the plan's line of 1 in 10. Counting the uncertain case as wrong would make it 2 in 11, and P2 would still fail: Agno's copies contain no `<Snippet` tag.

Two things we couldn't confirm:

- Whether people see Helicone's snippet on the web page. The tool found none of its text in the HTML.
- Whether people see Supermemory's snippet. The tool's HTML match may rest on a link only.

On Mem0, people see the text: the HTML shows "Star us on GitHub to help more developers discover memory for AI apps" and the Discord, GitHub and founders contact cards.

## What separates the sites

We can't say. Two observations, neither tested:

- **Agno's Markdown copies have a different format** from the other three. Each starts with `# Title (/path)`, headings carry `[#anchor]` ids, and code tabs are `<CodeBlockTabs>`. Mintlify's footer ("This documentation is built and hosted on Mintlify") is missing. Agno's repository README still says the site is "built with Mintlify". So the two formats may come from different versions or settings of Mintlify's export, but we have not confirmed it.
- **The same sites expand import-style snippets** but keep `<Snippet file>` tags (Helicone, Supermemory). So the two include mechanisms behave differently in the export on those sites.

## Prior art

Mintlify's own pages describe the expansion as current behaviour: [Markdown export](https://www.mintlify.com/docs/ai/markdown-export) and [Reusable snippets](https://www.mintlify.com/docs/create/reusable-snippets). Searches on 2026-11-12 and 2026-11-16 found PRs in mintlify/docs that document the export (#7871, #7946, #7962, #8359). They found no report that `<Snippet file>` tags stay as tags, and no cross-site count.

## What this means

- **For docs teams on Mintlify:** check your own `.md` copies for `<Snippet file=`. If the tag is there, agents get the tag and not the text. On these sites, the import style reached the copy every time, so it is a workaround to try.
- **For Mem0:** every sampled page that ends with the star-on-GitHub or get-help snippet sends agents a bare tag. Pages that use shared notices this way would lose them the same way.
- **For anyone measuring this:** a site can look right in the browser and still send agents a tag. Only reading the `.md` copy shows it.

## Limits

- The frame of 22 repositories was chosen from memory, and only 4 sites use the tag on pages their `llms.txt` lists. Mem0 and Agno supply 35 of the 37 uses. This describes these sites on 2026-11-15, not Mintlify in general.
- Each copy and page was read once. Mintlify can change its export at any time.
- The hand check covers 11 of 37 uses plus the false case, read through a summarising fetch tool.
