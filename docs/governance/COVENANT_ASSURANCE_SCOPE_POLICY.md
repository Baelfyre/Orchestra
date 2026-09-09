# Covenant Assurance Scope Policy

**Contract:** `ORCHESTRA_COVENANT_ASSURANCE_SCOPE_POLICY_V1`  
**Authority:** explicit human `APPROVE_POLICY_AMENDMENT` decision  
**Authority record:** Padayon commit `74bf85651e0f7a935b039fb82adbfadd68917b20`  
**Originating frozen candidate:** Orchestra PR #868 at `745609d541e97e61f28b1d3c6f9295ba0245d914`  
**Policy-amendment run:** Run N+1

## Purpose

The historical AQ5, AQ6, and PRAI exact-scope inventories predate The Covenant. They remain authoritative for their original assurance implementations and must not be broadened merely to make a later governance layer fit those historical inventories.

This policy recognizes The Covenant as a separate governance-assurance implementation scope while preserving historical exact inventories unchanged.

## Classification invariant

```text
COMPLETE_DECLARED_COVENANT_SCOPE
= NOT_APPLICABLE_TO_HISTORICAL_AQ5_AQ6_PRAI_EXACT_INVENTORIES

PARTIAL_ANCHORED_COVENANT_SCOPE
= APPLICABLE

MIXED_COVENANT_SCOPE
= APPLICABLE

UNKNOWN_OR_UNANCHORED_COVENANT_SCOPE
= APPLICABLE
```

The exact complete scope is defined mechanically by
`COVENANT_IMPLEMENTATION_PATHS` in
`scripts/validation/classify_adaptive_assurance_scope.py`.

Unique Covenant anchors are separately declared by
`COVENANT_SCOPE_ANCHOR_PATHS`. If any such anchor appears without the complete declared Covenant slice, historical gates remain fail-closed applicable.

## Historical inventory protection

This amendment does not add, remove, or reinterpret any path in:

- `PRAI_IMPLEMENTATION_PATHS`
- `AQ5_IMPLEMENTATION_PATHS`
- `AQ6_IMPLEMENTATION_PATHS`
- `AQ7_IMPLEMENTATION_PATHS`

It does not change coverage thresholds, required checks, PRAI dispositions, protected governance, Prime Directive interpretation, or transition authority.

## Amendment independence

The policy-amendment candidate itself is a governance-only change set:

- `CHANGELOG.md`
- `docs/governance/COVENANT_ASSURANCE_SCOPE_POLICY.md`
- `scripts/test_governance_check.py`
- `scripts/validation/classify_adaptive_assurance_scope.py`

That change set is already classified as governance-only by the pre-amendment canonical classifier. Therefore the new Covenant exact-scope rule is not required to exempt or certify its own policy-amendment candidate.

The amended classifier must not be represented as independently certifying its own amendment. Canonical promotion additionally requires the human policy authority, ordinary repository checks, independent review, signed materialization when required, and post-merge canonical readback.

## Fresh Covenant reconsideration

After this policy amendment becomes canonical:

1. PR #868 remains historical frozen evidence and is not resumed.
2. A new Covenant implementation candidate is created from the new canonical main.
3. The new candidate excludes the policy-amendment-only classifier repair.
4. Scenario and conflict testing runs on that fresh candidate.
5. PRAI PASS remains evidence only and is not sufficient for Covenant PASS.
6. AQ8 remains unauthorized until a later explicit admission decision.

## Authority boundary

This policy creates no execution, merge, release, deployment, or transition authority. It only defines assurance applicability classification for the separately governed Covenant implementation scope.
