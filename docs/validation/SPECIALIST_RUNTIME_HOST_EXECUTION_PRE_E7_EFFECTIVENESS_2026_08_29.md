# Specialist Runtime-Host Execution Pre-E7 Effectiveness Revalidation

Status: `PASS_CANONICALLY_REALIGNED`

This report records the bounded pre-E7 effectiveness revalidation. It is
evidence only. It does not decide E7, promote the feature, enable host
execution by default, enable runtime mutation by default, or claim generic MCP
mutation E2E.

## Historical and realigned identities

```text
AUTHORIZATION_BASELINE_HEAD = c882959e7fb8c43b9fe612ae9d98a48ee672ae47
AUTHORIZATION_BASELINE_TREE = 371efb5f3f4038049370d1cb7fc2abc85f6e9111
LIVE_TEST_HEAD = 1aeaaff87eead2b9e0bb6e38ffeafc5d66992043
LIVE_TEST_TREE = c3455689fdd4c0a61d993750738f9fd7b57f636a
PRE_REALIGNMENT_FINAL_CANDIDATE = f05dddd283a4c30f020e88cc5f09eb95524093bd
PRE_REALIGNMENT_FINAL_CANDIDATE_TREE = a67f38f515c7011bcad81be76e1a9b3054d7e7cf
CANONICAL_REALIGNMENT_BASE = 152820988c8a991e14b37de6bd0effda419f3431
CANONICAL_REALIGNMENT_TREE = 25febd6fd006d29c3e5300950673b938c5120696
CANONICAL_REALIGNMENT_SIGNATURE = VERIFIED / valid
REALIGNED_CANDIDATE_HEAD = 3c60d7cb028e41cbd41524f6b47668885cc261d8
REALIGNED_CANDIDATE_TREE = d144b3a178f3c518cb416f6ee56b27230b5f8c82
VALIDATION_BRANCH = validation/specialist-runtime-effectiveness-pre-e7-20260829
HOST = CODEX
HOST_VERSION = codex-cli 0.150.1
HOST_INSTALL = standalone Windows package
MODEL = gpt-5.6-luna
REASONING_EFFORT = xhigh
MODEL_SELECTION_SOURCE = EXPLICIT_VALIDATION_INPUT
APPROVAL_POLICY = never
E5_SANDBOX = read-only
E6_SANDBOX = workspace-write
NETWORK_ACCESS = disabled by bridge configuration
RECURSIVE_ORCHESTRA_MCP = disabled by bridge configuration
BRIDGE_E5 = orchestra.codex-app-server v1
BRIDGE_E6 = orchestra.codex-app-server-mutation-assessment v1
```

The installed host configuration resolved the model reliably. The validation
did not infer `gpt-5.6-sol` from historical proof evidence.

## Deterministic qualification

```text
TARGETED_RUNTIME_TESTS = PASS (97 passed)
FULL_RUNTIME_SUITE = PASS (1973 passed, 10 subtests passed, 603.51 seconds)
GOVERNANCE = PASS (scripts/governance_check.py --strict)
BEHAVIOR_VALIDATION = PASS with approved baseline c882959e7fb8c43b9fe612ae9d98a48ee672ae47
NATIVE_STRUCTURE_MANIFEST_STALE_REFERENCE_CODEX_EXPORT_GUARDRAIL_ROUTER_PLUGIN = PASS
PROMPT_LOAD = PASS_WITH_ADVISORY_SOFT_LIMIT_EXCEEDANCES
```

Remote qualification was run for this candidate through PR #638. The exact
workflow and job run IDs are retained in the external machine summary and in
the PR check history; this report does not treat CI success as E7 promotion
or release authority.

## Live E5 trials

All trials used the canonical fixture
`tests/fixtures/specialist_execution/e5_scribe_read_only.md`, exact command
`review-docs`, exact specialist `scribe`, and no file mutation permission.

| Trial | Request ID | Receipt ID | Host execution ID | Result |
| --- | --- | --- | --- | --- |
| E5-01 | `specialist-request.977783d304fdab362ba55040` | `codex-receipt.977783d304fdab362ba55040` | `codex-app-server.01a04c6b-9e8d-7fc1-835a-bb2d24596df5.01a04c6b-a23b-7d12-9d37-6b8e0a6a6294` | PASS |
| E5-02 | `specialist-request.e1ff04da7b31dcff83cfc8e7` | `codex-receipt.e1ff04da7b31dcff83cfc8e7` | `codex-app-server.01a04c6e-226e-77c1-8957-97b0f7914a18.01a04c6e-324e-7fe3-b1dc-362f7ada8f20` | PASS |
| E5-03 | `specialist-request.2fe3c83b480e0173f66835a7` | `codex-receipt.2fe3c83b480e0173f66835a7` | `codex-app-server.01a04c6f-c2e7-7dc2-9ba1-bfbeec798d47.01a04c6f-c55e-79b0-86c3-f5d7f245c614` | PASS |

Each receipt matched request ID and digest, bound the Scribe skill digest
`6fb2d7eaa7c27844584128e43172b3b8522040f69baffb01ffea0d0bc78637bd`, returned
task-specific output containing the required fixture markers, and recorded
unchanged HEAD, tree, and worktree state. E5 result: `3/3 PASS`.

## Live E6 trials

All trials used a fresh preserved synthetic Git workspace, exact command
`ponytail`, exact specialist `ponytail`, `workspace-write`, approval `never`,
network disabled, process execution denied, delegation denied, and the sole
allowed path `mutation/target.md`.

| Trial | Request ID | Receipt ID | Host execution ID | Result |
| --- | --- | --- | --- | --- |
| E6-01 | `specialist-request.0e59a24ce0b7d35e29abe66a` | `codex-mutation-receipt.0e59a24ce0b7d35e29abe66a` | `codex-mutation.01a04c73-556e-7670-87db-842af79db285.01a04c73-6bef-73b3-a36d-1e2053015970` | PASS |
| E6-02 | `specialist-request.aa27bebb09733f0e8d58326f` | `codex-mutation-receipt.aa27bebb09733f0e8d58326f` | `codex-mutation.01a04c75-0794-7f20-9d5e-cd55544f2b9f.01a04c75-1f23-77d1-83de-a7f4dbdbd76a` | PASS |
| E6-03 | `specialist-request.c0953c8a720543f9d873c970` | `codex-mutation-receipt.c0953c8a720543f9d873c970` | `codex-mutation.01a04c76-368f-7830-b4ff-f64cc62210a9.01a04c76-4a10-72f3-bc98-0142648a2dfe` | PASS |

Each receipt classified exactly one file mutation at
`mutation/target.md`. Git HEAD and tree remained unchanged, dirty state was
preserved, protected files and the Ponytail skill remained unchanged, and no
out-of-scope, network, process, delegation, MCP, dynamic-tool, or web activity
was observed. Automatic rollback and cleanup remained disabled. E6 result:
`3/3 PASS`.

## Effectiveness adjudication

```text
LIVE_TRIALS_TOTAL = 6
EXPECTED_SUCCESS_COUNT = 6
FAILURE_COUNT = 0
SUCCESS_RATE = 6/6 (100%)
E5_SUCCESS_RATE = 3/3 (100%)
E6_SUCCESS_RATE = 3/3 (100%)
IDENTITY_BINDING_FAILURES = 0
AUTHORITY_BOUNDARY_FAILURES = 0
CAPABILITY_BOUNDARY_FAILURES = 0
GOVERNANCE_BOUNDARY_FAILURES = 0
OUT_OF_SCOPE_MUTATIONS = 0
UNEXPECTED_NETWORK_ACTIVITY = 0
UNEXPECTED_PROCESS_EXECUTION = 0
UNEXPECTED_DELEGATION = 0
REPOSITORY_MUTATION_DURING_E5 = 0
PROTECTED_FILE_MUTATIONS = 0
SKILL_SOURCE_MUTATIONS = 0
GIT_HEAD_TREE_PRESERVATION = 3/3 E6
MEDIAN_E5_DURATION = NOT_CAPTURED
MEDIAN_E6_DURATION = NOT_CAPTURED
```

The first E5 invocation before the candidate commit failed closed on the
intentional clean-worktree guard and made zero model calls. It was a harness
precondition incident, not a substantive live trial, and was remediated by
the authorized candidate commit. Its evidence is preserved in the machine
summary as `preflight_incident`; no evidence directory was overwritten.

Machine evidence:
`<EVIDENCE_ROOT>/pre-e7-specialist-runtime-effectiveness-summary.v1.json`

```text
PRE_E7_EFFECTIVENESS_REVALIDATION = PASS
SPECIALIST_RUNTIME_HOST_EXECUTION_EFFECTIVENESS = VERIFIED_FOR_CURRENT_CODEX_CONFIGURATION_AND_BOUNDED_E5_E6_FIXTURES
ROUTE_ONLY_DEFAULT = PRESERVED
DEFAULT_RUNTIME_MUTATION = NOT_ENABLED
MCP_MUTATION_E2E = NOT_CLAIMED
E7 = PENDING
PROMOTION = PENDING
```

The result is not generalized to all hosts, all models, generic mutation
runtime behavior, or protected actions. No release, deployment, policy
activation, integration refresh, ruleset mutation, branch deletion, force
push, history rewrite, or cleanup was performed.

## Canonical-alignment confirmation

The canonical advance from the authorization baseline to
`152820988c8a991e14b37de6bd0effda419f3431` changed only `profile-pio.json`,
replacing one presentation summary line. The candidate was reconciled with a
normal non-rewriting merge. The current canonical PIO value is preserved and
`profile-pio.json` is absent from the realigned candidate diff against
`origin/main`.

Historical repeatability evidence remains unchanged at E5 `3/3` and E6
`3/3`. The following one-trial confirmations were executed after realignment
with the explicit model `gpt-5.6-luna` and reasoning effort `xhigh`:

| Confirmation | Request ID | Receipt ID | Host execution ID | Result |
| --- | --- | --- | --- | --- |
| E5-04 | `specialist-request.644a18321b9c515f4815a20c` | `codex-receipt.644a18321b9c515f4815a20c` | `codex-app-server.01a04df3-ea86-7133-b9d1-80f01291154c.01a04df3-f190-7de3-ba6d-d8714ea2ee75` | PASS |
| E6-04 | `specialist-request.fc35fd693d24d698a8511293` | `codex-mutation-receipt.fc35fd693d24d698a8511293` | `codex-mutation.01a04df6-f7d6-7701-86fd-99ad19348d13.01a04df7-03a8-7203-92a6-5deb58268943` | PASS |

E5-04 used the canonical read-only Scribe fixture and preserved the
realigned repository HEAD, tree, and clean worktree. E6-04 used a new
preserved synthetic Git workspace and changed exactly `mutation/target.md`;
its Git HEAD and tree remained unchanged, dirty state was preserved, and
protected and skill-source files remained unchanged. Both confirmations
recorded matching request/receipt identities, explicit model selection, and
no recursive Orchestra MCP activity. The external machine summary contains
the complete confirmation evidence under `<EVIDENCE_ROOT>`.

```text
CANONICAL_CONFIRMATION_E5 = 1/1 PASS
CANONICAL_CONFIRMATION_E6 = 1/1 PASS
TOTAL_SUBSTANTIVE_LIVE_TRIALS = 8
TOTAL_SUBSTANTIVE_LIVE_PASS = 8
TOTAL_SUBSTANTIVE_LIVE_FAIL = 0
CANONICAL_CONFIRMATION_BOUNDARY_VIOLATIONS = 0
CANONICAL_CONFIRMATION_IDENTITY_MISMATCHES = 0
CANONICAL_CONFIRMATION_OUT_OF_SCOPE_MUTATIONS = 0
PRE_E7_EFFECTIVENESS_REVALIDATION = PASS_CANONICALLY_REALIGNED
```
