# Specialist Runtime Host Model Selection

**Status:** PRE-E7 REVIEW CANDIDATE
**Scope:** Codex host model selection only
**Authority:** No E7 promotion, merge, release, deployment, policy activation, or default-runtime mutation authority is created by this document.

## Purpose

The E5 and E6 live proofs were intentionally executed with `gpt-5.6-sol` as a frozen evidence identity. That tested model must not become Orchestra's permanent runtime model.

The supported model-selection rule for any later promoted Codex host-execution surface is:

```text
MODEL_HARDCODED_IN_PROMOTED_SURFACE = FALSE
MODEL_SELECTION_SOURCE = USER_CONFIG
MODEL_SELECTION_FROM_PROMPT = DENIED
MODEL_SELECTION_FROM_TASK_TEXT = DENIED
MODEL_SELECTION_FROM_MCP_META = DENIED
MODEL_SELECTION != EXECUTION_AUTHORITY
```

## Configuration contract

`internal/codex_user_model_selection.py` introduces an explicit `CodexUserModelSelection` configuration object.

- The caller supplies a non-empty model identifier.
- Optional reasoning effort is supplied through the same trusted configuration boundary.
- The selected model is bound into the existing Codex read-only or mutation-assessment configuration.
- Approval policy, sandbox mode, network policy, write scope, specialist scope, and command scope are not widened by model selection.
- Task input, specialist guidance, and MCP metadata do not select or override the model.

The configuration builders intentionally have no GPT model default. A future UI or adapter may populate this value from a host-provided model catalog, but the repository does not maintain a permanent static model list.

## Historical evidence boundary

The existing E5/E6 proof implementations retain their `gpt-5.6-sol` pin because those files describe and reproduce the exact historical verification environment.

```text
E5_TESTED_MODEL = gpt-5.6-sol
E6_TESTED_MODEL = gpt-5.6-sol
HISTORICAL_TEST_MODEL != ORCHESTRA_RUNTIME_DEFAULT
```

Changing the historical proof identity would weaken reproducibility and would incorrectly rewrite already-collected evidence.

## Review boundary

This correction is intentionally staged before the E7 human promotion decision.

```text
MODEL_SELECTION_CORRECTION = REVIEW_CANDIDATE
E7_PROMOTION = NOT_DECIDED_BY_THIS_CHANGE
DEFAULT_ROUTE_ONLY_BEHAVIOR = PRESERVED
DEFAULT_RUNTIME_MUTATION = NOT_ENABLED
MCP_MUTATION_E2E = NOT_CLAIMED
```

If accepted, E7 can evaluate the optional host-execution capability with the additional condition that model choice remains explicit user/host configuration rather than a model hard-coded by Orchestra.