# AQ8 Assurance Scope Policy

**Contract:** `ORCHESTRA_AQ8_ASSURANCE_SCOPE_POLICY_V1`  
**Authority:** explicit human `APPROVE_POLICY_AMENDMENT` decision  
**Authority record:** Padayon commit `707693aebac73d84cf46f92d725f2d0d99b4b712`  
**Escalation:** `ORCHESTRA_AQ8_ASSURANCE_SCOPE_POLICY_ESCALATION_20260910`  
**Originating frozen candidate:** Orchestra PR #875 at `06e4d12fdcb6fc7f5d604a9a36936a3fd1c98a8c` / tree `74b6e315dd7b6493bf7938c96648176b1ead21b1`  
**Policy-amendment run:** Run N+1

## Purpose

The historical PRAI, AQ5, AQ6, and AQ7 exact-scope inventories were defined before AQ8. AQ8 is a separately admitted later assurance phase whose complete implementation slice cannot truthfully equal those historical implementation inventories.

This policy recognizes AQ8 as a separate assurance scope while preserving every historical inventory, threshold, disposition, and authority boundary unchanged.

## Classification invariant

```text
COMPLETE_DECLARED_AQ8_SCOPE
= NOT_APPLICABLE_TO_HISTORICAL_PRAI_AQ5_AQ7_EXACT_INVENTORIES

PARTIAL_AQ8_SCOPE
= APPLICABLE

MIXED_AQ8_SCOPE
= APPLICABLE

UNKNOWN_OR_UNANCHORED_AQ8_SCOPE
= APPLICABLE
```

The exact complete AQ8 implementation slice is defined mechanically by `AQ8_IMPLEMENTATION_PATHS` in `scripts/validation/classify_adaptive_assurance_scope.py`.

Unique AQ8 anchors are separately declared by `AQ8_SCOPE_ANCHOR_PATHS`. If any AQ8 anchor appears without the complete declared AQ8 slice, the historical gates remain fail-closed `APPLICABLE`.

`CHANGELOG.md` and `README.json` remain neutral documentation triggers for exact-scope classification and do not change the semantic identity of the AQ8 implementation slice.

## Complete declared AQ8 slice

The policy-bound complete AQ8 slice is:

- `docs/architecture/ADAPTIVE_ASSURANCE_AQ8.md`
- `machine/adaptive/aq8-high-risk-assurance-packs.v1.json`
- `machine/schemas/aq8-high-risk-assurance-packs.v1.schema.json`
- `orchestra_runtime/domain/adaptive/__init__.py`
- `orchestra_runtime/domain/adaptive/high_risk_assurance.py`
- `scripts/validation/validate_aq8.py`
- `tests/behavior/run_tests.py`
- `tests/runtime/test_adaptive_assurance_aq8.py`

This declaration describes the AQ8 implementation topology only. It does not certify any candidate and does not make a partial, mixed, or unknown change safe.

## Historical inventory protection

This amendment does not add, remove, or reinterpret any path in:

- `PRAI_IMPLEMENTATION_PATHS`
- `AQ5_IMPLEMENTATION_PATHS`
- `AQ6_IMPLEMENTATION_PATHS`
- `AQ7_IMPLEMENTATION_PATHS`

It does not change:

- statement or branch coverage thresholds;
- required GitHub checks;
- PRAI dispositions or evidence requirements;
- Covenant dispositions or evidence requirements;
- Prime Directive interpretation;
- Arbiter transition ownership;
- protected-governance escalation behavior;
- release, deployment, provider, credential, telemetry, or production authority.

## Amendment independence

The Run N+1 policy-amendment candidate is governance-only under the pre-amendment canonical classifier. Its permitted surfaces are bounded to governance documentation, the classifier implementation, machine-index/changelog parity, and dedicated protected-governance regression testing.

The new AQ8 complete-scope rule must not be represented as independently certifying the amendment that creates it. Qualification instead depends on:

1. the human policy decision recorded in Padayon;
2. pre-amendment governance classification of the amendment candidate;
3. ordinary repository validation and protected checks;
4. independent semantic review;
5. signed materialization when required by the current promotion lane;
6. protected-main exact-head validation;
7. independent canonical readback after merge.

## Originating candidate remains frozen

PR #875 remains historical evidence and must not be resumed or repaired.

Its ordinary unresolved defects remain preserved as evidence, including documentation parity, validator dependency assumptions, protected branch coverage, and exact-head matrix failures.

The policy amendment does not retroactively make PR #875 merge-ready.

## Fresh AQ8 reconsideration

After this amendment becomes canonical:

1. PR #875 remains frozen and unmerged.
2. A fresh Run N+2 AQ8 candidate is created from the new canonical `main`.
3. The fresh candidate reimplements the AQ8 slice from canonical source and historical #875 evidence rather than rebasing or cherry-picking the frozen candidate wholesale.
4. Ordinary AQ8 defects identified during #875 review must be repaired in the fresh candidate, including documentation parity, validator dependency handling, branch coverage, and whitespace cleanliness.
5. The fresh complete AQ8 slice must classify `NOT_APPLICABLE` to historical PRAI/AQ5/AQ7 exact inventories; partial, mixed, unknown, or scope-drifted AQ8 candidates must classify `APPLICABLE`.
6. PRAI and Covenant remain mandatory evidence layers for the fresh AQ8 run.
7. All current protected exact-head checks must pass before any promotion consideration.
8. AQ9 remains unauthorized until AQ8 completes its own governed closeout and receives a separate admission decision.

## Authority boundary

This policy changes assurance applicability classification only. It creates no implementation, merge, signed-materialization, release, deployment, provider, credential, telemetry, production, AQ9, or other protected-action authority.
