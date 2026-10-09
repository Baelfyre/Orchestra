# Output Formats

## Caveman

```markdown
# Overseer Quick QA Review

## Quality Objective
-

## Evidence Reviewed
-

## Confirmed Issues
1.
2.
3.

## Highest-Risk Gap
-

## Recommended Next Action
-
```

## Full QA Review

```markdown
# Overseer Quality Review

## Scope Reviewed
- Project:
- Quality Objective:
- Review Mode:
- Evidence Reviewed:

## Review Confidence
Confidence Level: High / Medium / Low
Reason:

## Executive Summary

## Confirmed Quality Strengths

## Requirements Testability Issues

## Test Coverage Issues

## Test Case Quality Issues

## Defect and Risk Issues

## Regression Readiness

## Verification and Validation Notes

## Release Readiness

## Missing Evidence

## Priority Fixes

## Recommended Test or QA Actions

## Final Recommendation
```

## Delegated Unit Evidence

### ExecutionEvidencePacket

Use this format when producing or verifying focused validation evidence for a delegated internal unit or a manual multi-domain handoff governed by the same Phase 2 evidence semantics.

```markdown
- schema_version:
- evidence_id:
- envelope_id:
- phase_id:
- unit_id:
- repository_identity:
- branch:
- approved_base_sha:
- current_commit_sha:
- working_tree_fingerprint:
- changed_paths:
- implementation_summary:
- validation_commands:
- validation_results:
- skipped_checks:
- known_limitations:
- scope_audit_result: PASS | FAIL
- protected_repository_result: PASS | FAIL
- security_and_secret_result: PASS | FAIL
- design_contradiction_state: NONE | PENDING
- identity_canonicalization_version: orchestra-evidence-v1
- collaboration_session_id:
- cross_layer_contract_hash:
- cross_layer_contract_revision:
- tracked_patch_hash:
- staged_patch_hash:
- untracked_file_manifest:
- added_blob_hashes:
- artifact_lifecycle_records:
- specialist_reentry_completed:
- open_invalidation_events:
- evidence_producer:
- evidence_timestamp:
- freshness_reference:
```

Evidence packets contain paths, statuses, commands, and cryptographic identities. They must not embed secrets or private file contents.

### Architecture Validation Contract

Use this existing evidence/QA surface when accepted upstream contracts create
architecture validation obligations. Keep the machine payload conformant to
the repository schema at machine/schemas/architecture-validation-contract.v1.schema.json.

```markdown
contract_refs:
exact_revision:
environment_identity:

functional_validation: PROVEN | NOT_PROVEN | NOT_REQUIRED | FAILED
capacity_validation: PROVEN | NOT_PROVEN | NOT_REQUIRED | FAILED
performance_validation: PROVEN | NOT_PROVEN | NOT_REQUIRED | FAILED
tenant_isolation_validation: PROVEN | NOT_PROVEN | NOT_REQUIRED | FAILED
migration_validation: PROVEN | NOT_PROVEN | NOT_REQUIRED | FAILED
failure_behavior_validation: PROVEN | NOT_PROVEN | NOT_REQUIRED | FAILED
compatibility_validation: PROVEN | NOT_PROVEN | NOT_REQUIRED | FAILED

limitations:
evidence_refs:
```

`PROVEN` requires current evidence for every accepted criterion at the exact
revision and environment. Missing, skipped, stale, flaky, crashed, or
mismatched evidence is `NOT_PROVEN`, not `FAILED`. `NOT_REQUIRED` is allowed
only when accepted contracts establish that the dimension is inapplicable.
