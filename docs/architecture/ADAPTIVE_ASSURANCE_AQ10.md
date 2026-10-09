# ADAPT-QA AQ10: Defect-Escape RCA Feedback Loop

## Status

`AQ10_DEFECT_ESCAPE_RCA` is a deterministic, evidence-only analysis layer. Its authority model is `EVIDENCE_ONLY_NON_AUTHORIZING`.

AQ10 does not alter an earlier gate after a defect escapes. It records what was missed, classifies the observed cause from explicit evidence signals, and emits bounded prevention actions for later human or governed implementation.

## Deterministic flow

```text
observed defect escape
        |
        v
DefectEscapeObservation
        |
        v
explicit evidence signals
        |
        v
fixed RCA taxonomy + precedence
        |
        v
DefectEscapeFinding
        |
        +--> prevention actions
        +--> confidence
        +--> human-review requirement
        |
        v
NO execution / policy / transition authority
```

The implementation surface is `orchestra_runtime/domain/adaptive/defect_escape_rca.py`.

## Taxonomy

AQ10 uses these exact root-cause categories:

- `COVERAGE_GAP`
- `ASSERTION_GAP`
- `ORACLE_GAP`
- `SCOPE_CLASSIFICATION_GAP`
- `DEPENDENCY_ENVIRONMENT_GAP`
- `ASSURANCE_TOOL_COMPATIBILITY`
- `PROCESS_GOVERNANCE_GAP`
- `UNKNOWN`

The taxonomy is intentionally descriptive rather than authorizing. A cause classification does not permit a threshold reduction, gate bypass, policy change, whitelist mutation, release, deployment, provider activation, telemetry, or production mutation.

## Fail-closed behavior

Unknown evidence signals are rejected rather than guessed. Duplicate defect, gate, signal, or evidence identities are rejected. An explicit `CAUSE_UNRESOLVED` signal produces `UNKNOWN`, adds `HUMAN_RCA_REVIEW_REQUIRED`, lowers confidence, and still grants no authority.

AQ10 also preserves a strict distinction between evidence and remediation. Prevention actions are recommendations only. They cannot mutate the system in the same classification operation.

## Reference defect escapes

The machine contract records bounded reference incidents from the AQ9/framework campaign, including:

- the AQ9 behavior-validator dependency/environment mismatch, classified as `DEPENDENCY_ENVIRONMENT_GAP`;
- the mutation-operator compatibility failure that remained invisible to earlier semantic gates and was caught by Cosmic Ray, classified as `ASSURANCE_TOOL_COMPATIBILITY`.

These incidents are regression fixtures, not permissions.

## Phase-separation boundary

The exact nine-path AQ10 implementation inventory is pre-registered under the human-approved reusable ADAPT-QA phase-separation policy. Exact AQ10 phase separation does not weaken historical assurance. Partial, mixed, expanded, duplicate, or unknown scopes remain fail closed.
