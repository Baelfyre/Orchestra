# Specialist Runtime-Host Execution E7 Promotion Decision

Date: 2026-08-30

Decision owner: Baelfyre maintainer

Disposition: `ADOPT_OPTIONAL`

## Decision

E7 adopts Specialist Runtime-Host Execution as a supported optional capability. It does not replace the route-only default and does not make runtime mutation a default capability.

```text
SPECIALIST_RUNTIME_HOST_EXECUTION = SUPPORTED_OPTIONAL
ROUTE_ONLY_DEFAULT = PRESERVED
DEFAULT_RUNTIME_MUTATION = NOT_ENABLED
MCP_MUTATION_E2E = NOT_CLAIMED
MODEL_SELECTION = EXPLICIT_USER_CONFIG
```

## Evidence basis

The promotion decision is grounded in the canonical pre-E7 validation package merged by PR #638 at commit `fbcacf3c7c48c4471fde220954a8515d2c3decf0`, tree `976ebc314438a830751a179cc321a538f3b22112`.

Measured evidence:

- E5 Scribe read-only repeatability: 3/3 PASS.
- E6 Ponytail isolated single-file mutation repeatability: 3/3 PASS.
- Canonical-alignment E5 confirmation: 1/1 PASS.
- Canonical-alignment E6 confirmation: 1/1 PASS.
- Total substantive live trials: 8/8 PASS.
- Boundary violations: 0.
- Identity mismatches: 0.
- Out-of-scope mutations: 0.
- Current validation host: Codex App Server / codex-cli 0.150.1.
- Explicit validation model: `gpt-5.6-luna`.
- Reasoning effort: `xhigh`.
- Post-merge Governance, validate/runtime, Required Analysis Compatibility, CodeQL, and Windows/macOS/Ubuntu validation passed.

Detailed evidence remains in `docs/validation/SPECIALIST_RUNTIME_HOST_EXECUTION_PRE_E7_EFFECTIVENESS_2026_08_29.md` and PR #638.

## Why ADOPT_OPTIONAL

The capability produced measurable value beyond route acknowledgement: bounded installed-host executions returned substantive specialist output and enforced the tested execution boundaries repeatedly. The feature is reversible and can remain disabled unless explicitly configured.

`ADOPT` as a default capability is not supported by the present evidence. Validation remains bounded to one host family and the E5/E6 fixtures. Generic MCP mutation E2E has not been demonstrated, and write-scope enforcement is not equivalent to full read isolation.

## Claims intentionally not made

```text
ALL_HOSTS_VERIFIED = FALSE
ALL_MODELS_VERIFIED = FALSE
GENERAL_MUTATION_RUNTIME_VERIFIED = FALSE
MCP_MUTATION_E2E_VERIFIED = FALSE
DEFAULT_RUNTIME_MUTATION = FALSE
HOST_CAPABILITY_GRANTS_AUTHORITY = FALSE
```

The E7 decision grants no merge, release, deployment, policy activation, destructive-operation, or installed-integration-refresh authority.

## Track closeout

E0-E7 are complete once this decision reaches verified canonical `main`. No new post-E7 implementation campaign is implied by this decision. Any newly identified productization, multi-host, model-discovery, isolation, or MCP mutation work must be proposed separately and explicitly approved before implementation.
