# README Direct-Main Governance Reconciliation

## Status

`FORWARD_ONLY_REMEDIATION_PREPARED`

This record documents the August 10, 2026 Orchestra README direct-main governance incident and the evidence required for forward-only remediation.

## Incident identity

```text
INCIDENT_SHA=807bda608d65cb10bf65cdf313916d9d0fd62320
INCIDENT_PARENT=4f5dd94687f8ee5d33a1c08a34ae5bf920b69233
INCIDENT_CHANGED_PATH=README.md
PRESERVE_CURRENT_CANONICAL_HISTORY=true
HISTORY_REWRITE=false
FORCE_PUSH=false
UNSIGNED_DIRECT_MAIN_RESULT_IS_NOT_FUTURE_PRECEDENT=true
```

The intended public-facing README refinement was applied directly to canonical `main` instead of progressing through the repository's required pull-request path. The content change is accepted, but the transition itself is not treated as governance-complete.

## Exact incident content validation

Local validation was performed on exact canonical SHA `807bda608d65cb10bf65cdf313916d9d0fd62320` with approved evidence baseline `4f5dd94687f8ee5d33a1c08a34ae5bf920b69233`.

- Python 3.12.10
- preflight sync: PASS
- structure validation: PASS
- manifest validation: PASS
- stale-reference scan: PASS
- strict governance: PASS, 0 errors, 0 warnings
- full behavior suite: PASS
- runtime suite: 541 passed
- runtime coverage: 94.31%
- Codex export validation: PASS
- router benchmark: PASS
- router negative fixtures: PASS
- strict runtime guardrail: PASS
- cross-layer synchronicity validator: PASS
- cross-layer synchronicity behavior test: PASS
- plugin JSON parse: PASS
- `git diff --check`: PASS

Prompt-load reporting exceeded the soft threshold for Group B and the grand total, but the canonical checker explicitly classified those results as advisory/report-only and exited successfully.

Negative-path diagnostics printed by governance/router test fixtures were intentional regression cases; the owning test modules passed.

## Canonical commit verification

```text
COMMIT_VERIFIED=false
COMMIT_VERIFICATION_REASON=unsigned
```

The canonical incident commit is not promoted to a verified governance transition unless its verification result is acceptable under repository policy. The observed August 10 result was unsigned.

## Exact-head GitHub check observation

| Required check | Status | Conclusion | Head SHA |
| --- | --- | --- | --- |
| `governance-check` | `completed` | `success` | `807bda608d65cb10bf65cdf313916d9d0fd62320` |
| `validate` | `completed` | `success` | `807bda608d65cb10bf65cdf313916d9d0fd62320` |
| `runtime-tests` | `completed` | `success` | `807bda608d65cb10bf65cdf313916d9d0fd62320` |
| `native-windows-latest` | `completed` | `success` | `807bda608d65cb10bf65cdf313916d9d0fd62320` |
| `native-ubuntu-latest` | `completed` | `success` | `807bda608d65cb10bf65cdf313916d9d0fd62320` |
| `native-macos-latest` | `completed` | `success` | `807bda608d65cb10bf65cdf313916d9d0fd62320` |
| `Analyze (actions)` | `completed` | `success` | `807bda608d65cb10bf65cdf313916d9d0fd62320` |
| `Analyze (python)` | `completed` | `success` | `807bda608d65cb10bf65cdf313916d9d0fd62320` |

Missing or non-successful exact-head checks are not inferred as passing evidence.

## Live `Protect main` observation

```text
RULESET_ID=17927422
RULESET_NAME=Protect main
RULESET_ENFORCEMENT=active
RULE_TYPES=deletion,non_fast_forward,pull_request,required_linear_history,required_signatures,required_status_checks
```

Canonical governance continues to require PR-based progression, signed commits, linear history, required status checks, an up-to-date branch, restricted deletion, blocked force pushes, and Squash-only merge behavior as defined by the active repository ruleset and `docs/governance/AUTONOMOUS_MERGE_READINESS_PROTOCOL.md`.

```text
GITHUB_CAN_MERGE != GOVERNANCE_READY_TO_MERGE
BYPASS_CAPABILITY != GOVERNANCE_AUTHORIZATION
```

## Forward-only remediation

The incident is preserved in canonical history. It must not be erased by amend, reset, rebase, force push, or history rewrite.

The remediation path is:

1. Record the incident on a dedicated branch based on `807bda608d65cb10bf65cdf313916d9d0fd62320`.
2. Validate the exact remediation revision locally.
3. Commit only after maintainer review and authorization.
4. Push and open a normal pull request.
5. Require fresh exact-head required checks and zero unresolved blockers.
6. Merge using the normal Squash path only.
7. Require the resulting canonical Squash commit to be signature-verified.
8. Independently re-read canonical `main`.
9. Reconcile the KB only after Orchestra is `MERGED_VERIFIED`.

## Boundaries

No README reversal, runtime change, test change, workflow change, manifest/version change, release/tag mutation, deployment, marketplace graduation, installed-integration refresh, policy activation, force push, history rewrite, or branch deletion is authorized by this record.
