# learnlabels 0.1.0: AI-use labels in Microsoft Learn's public docs repos (automatic report)

First pass written by the tool. The graded result is in RESULT.md.

- Started 2026-11-09T11:18:36Z, finished 2026-11-09T11:23:50Z.
- Pre-registration first committed: 2026-11-09T01:24:41Z.
- Org repos listed: 711; eligible: 129; excluded: archived 399, fork 10, localized copy 29, not pushed since 2026-05-01 144.
- Repos read: 30 (gate needs 15); articles: 182133 (gate needs 20000); gate PASSED.
- AI-labelled articles: 6618 (3.63%). Categories: unlabelled 175511, ai-assisted 6362, ai-generated 256, non-ai 4.
- Keys: AI_Usage 3, ai-usage 6450, ai.usage 47, ms.ai-usage 122. Other AI tokens: ai-gen-docs-bap 457, ai-gen-description 220, ai-gen-desc 183, ai-gen-title 102, ai-assisted 27, ai-gen-diyeditor 6, ai-generated 2.

## Predictions (automatic; boundaries as pre-registered)

| | value | held |
|---|---|---|
| P1 | {"value_pct": 3.63} | no |
| P2 | {"ai_assisted": 6362, "ai_generated": 256, "ratio": 24.85} | yes |
| P3 | {"value_pct": 99.0, "known_year": 6618} | yes |
| P4 | {"share_2026_pct": 7.73, "n_2026": 60046, "share_le2024_pct": 0.07, "n_le2024": 96009, "ratio": 112.43} | yes |
| P5 | {"repos_with_label": 21, "repos_read": 30, "value_pct": 70.0} | no |
| P6 | {"noncanonical": 169, "value_pct": 2.55} | yes |

## By ms.date year

| year | articles | AI-labelled | % |
|---|---|---|---|
| 2007 | 1 | 0 | 0.0 |
| 2008 | 1 | 0 | 0.0 |
| 2011 | 12 | 0 | 0.0 |
| 2012 | 21 | 0 | 0.0 |
| 2013 | 8 | 0 | 0.0 |
| 2015 | 3 | 0 | 0.0 |
| 2016 | 3029 | 0 | 0.0 |
| 2017 | 6824 | 2 | 0.03 |
| 2018 | 53446 | 2 | 0.0 |
| 2019 | 3156 | 0 | 0.0 |
| 2020 | 2182 | 1 | 0.05 |
| 2021 | 2615 | 2 | 0.08 |
| 2022 | 7060 | 4 | 0.06 |
| 2023 | 7720 | 16 | 0.21 |
| 2024 | 9931 | 39 | 0.39 |
| 2025 | 21443 | 1911 | 8.91 |
| 2026 | 60046 | 4641 | 7.73 |
| none | 4635 | 0 | 0.0 |

## Repos

| rank | repo | status | articles | AI-labelled | assisted | generated |
|---|---|---|---|---|---|---|
| 1 | MicrosoftDocs/azure-docs | read | 13715 | 852 | 832 | 20 |
| 2 | MicrosoftDocs/learn | too few articles | 0 | 0 | 0 | 0 |
| 3 | MicrosoftDocs/fabric-docs | read | 2822 | 1015 | 976 | 39 |
| 4 | MicrosoftDocs/azure-docs-sdk-java | read | 1426 | 0 | 0 | 0 |
| 5 | MicrosoftDocs/microsoftgraph-docs-powershell | read | 27344 | 0 | 0 | 0 |
| 6 | MicrosoftDocs/azure-docs-sdk-dotnet | read | 1872 | 0 | 0 | 0 |
| 7 | MicrosoftDocs/entra-docs | read | 4428 | 646 | 624 | 22 |
| 8 | MicrosoftDocs/microsoft-365-docs | read | 1246 | 56 | 55 | 1 |
| 9 | MicrosoftDocs/dynamics-365-customer-engagement | read | 4893 | 234 | 233 | 1 |
| 10 | MicrosoftDocs/msteams-docs | read | 330 | 0 | 0 | 0 |
| 11 | MicrosoftDocs/powerapps-docs | read | 2881 | 103 | 97 | 6 |
| 12 | MicrosoftDocs/dynamics-365-unified-operations-public | read | 6351 | 154 | 154 | 0 |
| 13 | MicrosoftDocs/dynamics-365-mixed-reality | read | 248 | 0 | 0 | 0 |
| 14 | MicrosoftDocs/architecture-center | read | 313 | 105 | 104 | 1 |
| 15 | MicrosoftDocs/windows-dev-docs | read | 2160 | 1 | 1 | 0 |
| 16 | MicrosoftDocs/visualstudio-docs | read | 5440 | 43 | 43 | 0 |
| 17 | MicrosoftDocs/azure-docs-sdk-python | read | 1718 | 0 | 0 | 0 |
| 18 | MicrosoftDocs/sql-docs | read | 13624 | 459 | 456 | 3 |
| 19 | MicrosoftDocs/azure-monitor-docs | read | 2735 | 286 | 286 | 0 |
| 20 | MicrosoftDocs/azure-stack-docs | read | 1217 | 40 | 40 | 0 |
| 21 | MicrosoftDocs/edge-developer | read | 709 | 0 | 0 | 0 |
| 22 | MicrosoftDocs/minecraft-creator | read | 4251 | 1542 | 1542 | 0 |
| 23 | MicrosoftDocs/SupportArticles-docs | read | 7823 | 519 | 513 | 6 |
| 24 | MicrosoftDocs/sdk-api | read | 65890 | 0 | 0 | 0 |
| 25 | MicrosoftDocs/cloud-adoption-framework | read | 215 | 26 | 26 | 0 |
| 26 | MicrosoftDocs/windowsserverdocs | read | 2568 | 118 | 110 | 8 |
| 27 | MicrosoftDocs/power-platform | read | 1317 | 60 | 60 | 0 |
| 28 | MicrosoftDocs/azure-compute-docs | read | 1407 | 117 | 116 | 1 |
| 29 | MicrosoftDocs/azure-docs-sdk-node | read | 1659 | 0 | 0 | 0 |
| 30 | MicrosoftDocs/power-automate-docs | read | 728 | 1 | 1 | 0 |
| 31 | MicrosoftDocs/azure-dev-docs | read | 803 | 241 | 93 | 148 |
