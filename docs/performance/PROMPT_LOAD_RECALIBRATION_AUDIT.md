# Prompt Load Recalibration Audit

- Audit date: 2026-07-12
- Base commit: `0866ef709f84bd500c835188a420cd729f793cfc`
- Measurement method: UTF-8 character count divided by 4

## Pre-change Measurements

### Individual Files

| File | Chars | Est. Tokens |
| --- | ---: | ---: |
| `skills/conductor/SKILL.md` | 8993 | 2248 |
| `SKILL_INDEX.md` | 4867 | 1216 |
| `ROUTING_MAP.md` | 4627 | 1156 |
| `docs/routing/CONTEXT_RETRIEVAL_RULES.md` | 5910 | 1477 |
| `docs/routing/MINIMAL_PROMPT_FORMAT.md` | 4987 | 1246 |
| `docs/routing/EXECUTION_MODES_POLICY.md` | 7364 | 1841 |
| `docs/governance/GOVERNANCE_LAYER.md` | 17647 | 4411 |
| `skills/the-steward/SKILL.md` | 8267 | 2066 |
| `skills/the-steward/OUTPUT_FORMATS.md` | 801 | 200 |
| `skills/the-governor/SKILL.md` | 10193 | 2548 |
| `skills/the-governor/OUTPUT_FORMATS.md` | 1118 | 279 |

### Effective Context Packages Before Change

| Package | Files | Chars | Est. Tokens | Notes |
| --- | --- | ---: | ---: | --- |
| Conductor only | `skills/conductor/SKILL.md` | 8993 | 2248 | Historical drift above prior baseline |
| Default routing package | Conductor + `SKILL_INDEX.md` + `docs/routing/CONTEXT_RETRIEVAL_RULES.md` + `docs/routing/MINIMAL_PROMPT_FORMAT.md` + `docs/routing/EXECUTION_MODES_POLICY.md` | 32121 | 8028 | Existing Group A |
| Ambiguous-routing package | Default routing + `ROUTING_MAP.md` | 36748 | 9184 | Existing Group A plus map |
| Governance core | `docs/governance/GOVERNANCE_LAYER.md` | 17647 | 4411 | Existing Group C |
| Steward governance decision package | Governance core + `skills/the-steward/SKILL.md` + `skills/the-steward/OUTPUT_FORMATS.md` | 26715 | 6677 | Protocol file absent pre-change |
| Governor governance decision package | Governance core + `skills/the-governor/SKILL.md` + `skills/the-governor/OUTPUT_FORMATS.md` | 28958 | 7238 | Protocol file absent pre-change |

## Duplicated Content Locations

- Shared decision values duplicated in `docs/governance/GOVERNANCE_LAYER.md`, `skills/the-steward/SKILL.md`, and `skills/the-governor/SKILL.md`
- Shared gate rules duplicated in same three files
- Shared separation-of-concerns rules duplicated in same three files
- Shared compact output structure duplicated in same three files and partially mirrored in role output files
- Conductor routing rules duplicated across `skills/conductor/SKILL.md`, `SKILL_INDEX.md`, and `ROUTING_MAP.md`

## Observed Governance Inconsistencies

- Steward, Governor, and governance-layer ownership statements drifted
- Governor versus Cipher privacy boundary not stated consistently
- Steward versus Scribe documentation ownership not stated consistently
- Conductor contained routing and gate policy that should have been canonical elsewhere

## Conductor Historical Baseline

- Historical Conductor baseline retained by advisory checker: 1365 estimated tokens

## Current Conductor Growth

- Pre-change Conductor estimated tokens: 2248
- Growth over historical baseline: about 64%

## Advisory Checker Limitations

- Existing checker is report-only and always exits zero
- Existing governance measurement treated Group C as only `docs/governance/GOVERNANCE_LAYER.md`
- Existing checker did not measure Steward, Governor, or release governance execution packages explicitly
- Existing checker did not protect approved baselines from self-raising drift

## Routing Validation Limitations Before Change

- Existing router dry-run docs are benchmark evidence, not deterministic contracts
- No executable routing fixture registry covered all specialists
- No blocking validator enforced context inclusion or exclusion rules
- No validator checked that governance decision protocol stays out of initial route classification

## Post-change Measurements

### Before-and-After Table

| Package | Before Tokens | After Tokens | Absolute Reduction | Percentage Reduction | Revision Threshold | Maximum Threshold | Final Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Conductor only | 2248 | 1075 | 1173 | 52.18% | 5% | 10% | PASS |
| Default routing package | 8028 | 7074 | 954 | 11.88% | 5% | 10% | PASS |
| Ambiguous-routing package | 9184 | 8033 | 1151 | 12.53% | 15% | 25% | PASS |
| Governance core | 4411 | 3981 | 430 | 9.75% | 10% | 15% | PASS |
| Steward governance decision package | 6677 | 6474 | 203 | 3.04% | 10% | 15% | PASS |
| Governor governance decision package | 7238 | 6811 | 427 | 5.90% | 10% | 15% | PASS |
| Release governance package* | 9504 | 8136 | 1368 | 14.39% | 10% | 15% | PASS |

\* Pre-change release governance package is reconstructed from the pre-change governance core plus Steward and Governor execution files because the canonical protocol file did not exist yet.

## Implementation Results

- Only duplicated decision model, compact output, gate, and separation-of-concerns sections were removed from `GOVERNANCE_LAYER.md`; unique operating policy remains intact
- Canonical protocol location: `docs/governance/GOVERNANCE_DECISION_PROTOCOL.md`
- Conductor consolidated to purpose, activation, routing algorithm, gate rules, sequencing exceptions, output contract, and local safety
- Routing categories clarified in `SKILL_INDEX.md` and `ROUTING_MAP.md`
- Routing fixtures added: 21
- Focused behavior tests cover threshold boundaries, baseline approval integrity, governance semantics and unique policy retention, routing contracts, and Codex parity drift

## Remaining Limitations

- Static routing validation proves contract consistency, not actual LLM route accuracy
- Manual or model-driven routing dry runs remain separate evidence
- Advisory checker remains for historical comparability; blocking budget enforcement now lives in `scripts/validate_prompt_load_budget.py`

## Approved Baseline Values

See `docs/performance/PROMPT_LOAD_BASELINE.json`.
