# Orchestra Pattern Catalog

This document is the governed human-readable projection of validated Artificer promotion records.

> [!IMPORTANT]
> Canonical authority remains with the validated Artificer JSON records. This Markdown file is manually synchronized and is never updated automatically by Artificer.
>
> Use `python scripts/validate_artificer_pattern_catalog.py --print-expected` to preview the canonical Catalog representation. The command writes only to standard output.

## Catalog Index

| ID | Pattern Name | Source Repository | Approval Date | Status | Assigned Specialist |
| --- | --- | --- | --- | --- | --- |
| agent\-lifecycle\-state\-machine | Lifecycle\-Gated Agent Completion | usestrix/strix | 2026\-07\-13 | APPROVED | clockwork |
| authority\-scope\-contract | Declared Scope Context | usestrix/strix | 2026\-07\-13 | APPROVED | arbiter |
| run\-scoped\-capability\-manifest | Run\-Wide Tool Extension Registry | usestrix/strix | 2026\-07\-13 | APPROVED | clockwork |
| specialist\-delegation\-contract | Validated Specialist Delegation | usestrix/strix | 2026\-07\-13 | APPROVED | overseer |

---

## Catalog Entries

### agent\-lifecycle\-state\-machine: Lifecycle\-Gated Agent Completion

- **Status**: APPROVED
- **Source Repository**: usestrix/strix
- **Source URL**: https://github\.com/usestrix/strix
- **Source Bundle**: usestrix\_\_strix\_\_09872744f5a9
- **Audited Commit**: 09872744f5a9d3ffad750478f823e656ac1a7c88
- **Source File**: strix/agents/factory\.py
- **Line Range**: 271\-321
- **Pattern Record**: internal/artificer/records/usestrix\_\_strix\_\_09872744f5a9/patterns/lifecycle\-gated\-agent\-completion\.json
- **Decision Record**: strix\-lifecycle\-gated\-agent\-completion\-decision
- **Proposal Record**: orchestra\-authority\-capability\-contract
- **Promotion Record**: promote\-agent\-lifecycle\-state\-machine
- **Promotion Record Path**: internal/artificer/promotions/agent\-lifecycle\-state\-machine\.json
- **Approval Date**: 2026\-07\-13
- **Original License**: Apache\-2\.0
- **Attribution Required**: true
- **Attribution Summary**: Preserve source provenance and Apache\-2\.0 attribution in governance and Catalog records\. This promotion authorizes conceptual Orchestra\-native design only and does not authorize reuse of source code, prompts, payloads, examples, media, or documentation expression\. Any later source adaptation or distribution requires applicable license, NOTICE, patent, modified\-file, attribution, trademark, and third\-party dependency review\.
- **Orchestra Specialist Owner**: clockwork
- **Pattern Classification**: REFERENCE\_ONLY
- **Pattern Description**: Examines tool results for explicit successful lifecycle signals and permits final output only after scan completion, child completion, or an interactive waiting transition\.

### authority\-scope\-contract: Declared Scope Context

- **Status**: APPROVED
- **Source Repository**: usestrix/strix
- **Source URL**: https://github\.com/usestrix/strix
- **Source Bundle**: usestrix\_\_strix\_\_09872744f5a9
- **Audited Commit**: 09872744f5a9d3ffad750478f823e656ac1a7c88
- **Source File**: strix/core/inputs\.py
- **Line Range**: 97\-122
- **Pattern Record**: internal/artificer/records/usestrix\_\_strix\_\_09872744f5a9/patterns/declared\-scope\-context\.json
- **Decision Record**: strix\-declared\-scope\-context\-decision
- **Proposal Record**: orchestra\-authority\-capability\-contract
- **Promotion Record**: promote\-authority\-scope\-contract
- **Promotion Record Path**: internal/artificer/promotions/authority\-scope\-contract\.json
- **Approval Date**: 2026\-07\-13
- **Original License**: Apache\-2\.0
- **Attribution Required**: true
- **Attribution Summary**: Preserve source provenance and Apache\-2\.0 attribution in governance and Catalog records\. This promotion authorizes conceptual Orchestra\-native design only and does not authorize reuse of source code, prompts, payloads, examples, media, or documentation expression\. Any later source adaptation or distribution requires applicable license, NOTICE, patent, modified\-file, attribution, trademark, and third\-party dependency review\.
- **Orchestra Specialist Owner**: arbiter
- **Pattern Classification**: REFERENCE\_ONLY
- **Pattern Description**: Builds structured authorization context from configured targets, identifies the declared scope and authorization sources, and states that user\-provided instructions do not expand the authorized target set\.

### run\-scoped\-capability\-manifest: Run\-Wide Tool Extension Registry

- **Status**: APPROVED
- **Source Repository**: usestrix/strix
- **Source URL**: https://github\.com/usestrix/strix
- **Source Bundle**: usestrix\_\_strix\_\_09872744f5a9
- **Audited Commit**: 09872744f5a9d3ffad750478f823e656ac1a7c88
- **Source File**: strix/agents/factory\.py
- **Line Range**: 324\-477
- **Pattern Record**: internal/artificer/records/usestrix\_\_strix\_\_09872744f5a9/patterns/run\-wide\-tool\-extension\-registry\.json
- **Decision Record**: strix\-run\-wide\-tool\-extension\-registry\-decision
- **Proposal Record**: orchestra\-authority\-capability\-contract
- **Promotion Record**: promote\-run\-scoped\-capability\-manifest
- **Promotion Record Path**: internal/artificer/promotions/run\-scoped\-capability\-manifest\.json
- **Approval Date**: 2026\-07\-13
- **Original License**: Apache\-2\.0
- **Attribution Required**: true
- **Attribution Summary**: Preserve source provenance and Apache\-2\.0 attribution in governance and Catalog records\. This promotion authorizes conceptual Orchestra\-native design only and does not authorize reuse of source code, prompts, payloads, examples, media, or documentation expression\. Any later source adaptation or distribution requires applicable license, NOTICE, patent, modified\-file, attribution, trademark, and third\-party dependency review\.
- **Orchestra Specialist Owner**: clockwork
- **Pattern Classification**: REFERENCE\_ONLY
- **Pattern Description**: Combines a fixed base tool set with globally registered and per\-agent extensions, checks tool\-name uniqueness, and propagates the resulting capability set into root and child agent construction\.

### specialist\-delegation\-contract: Validated Specialist Delegation

- **Status**: APPROVED
- **Source Repository**: usestrix/strix
- **Source URL**: https://github\.com/usestrix/strix
- **Source Bundle**: usestrix\_\_strix\_\_09872744f5a9
- **Audited Commit**: 09872744f5a9d3ffad750478f823e656ac1a7c88
- **Source File**: strix/tools/agents\_graph/tools\.py
- **Line Range**: 350\-464
- **Pattern Record**: internal/artificer/records/usestrix\_\_strix\_\_09872744f5a9/patterns/validated\-specialist\-delegation\.json
- **Decision Record**: strix\-validated\-specialist\-delegation\-decision
- **Proposal Record**: orchestra\-authority\-capability\-contract
- **Promotion Record**: promote\-specialist\-delegation\-contract
- **Promotion Record Path**: internal/artificer/promotions/specialist\-delegation\-contract\.json
- **Approval Date**: 2026\-07\-13
- **Original License**: Apache\-2\.0
- **Attribution Required**: true
- **Attribution Summary**: Preserve source provenance and Apache\-2\.0 attribution in governance and Catalog records\. This promotion authorizes conceptual Orchestra\-native design only and does not authorize reuse of source code, prompts, payloads, examples, media, or documentation expression\. Any later source adaptation or distribution requires applicable license, NOTICE, patent, modified\-file, attribution, trademark, and third\-party dependency review\.
- **Orchestra Specialist Owner**: overseer
- **Pattern Classification**: REFERENCE\_ONLY
- **Pattern Description**: Validates requested specialist skills, resolves the coordinator and runner\-owned child spawner from context, optionally inherits parent turn history, delegates a focused task, and returns structured spawn results\.
