# ADAPT-QA AQ-1: Normative Assurance Doctrine

Status: contract defined for AQ-1. AQ-2 and later phases are not implemented by this document or its runtime surface.

## Purpose

ADAPT-QA is Orchestra-derived assurance doctrine for selecting an appropriate development and evidence posture. It is not an external normative standard. AQ-1 defines the minimum vocabulary and gates so that a work item cannot silently turn a prototype, inferred behavior, or domain-only implementation into a product-complete claim.

The canonical planning authority is the Padayon record at `projects/orchestra/10-approved/plans/Orchestra_ADAPT_QA_Repository_Assurance_Enhancement_Plan_20260907.md#AQ-1`, read from Padayon canonical main at the AQ-1 admission boundary.

The machine contract is [`aq1-normative-doctrine.v1.json`](../../machine/adaptive/aq1-normative-doctrine.v1.json), validated by [`adaptive-assurance-doctrine.v1.schema.json`](../../machine/schemas/adaptive-assurance-doctrine.v1.schema.json). The pure domain rules are in [`assurance.py`](../../orchestra_runtime/domain/adaptive/assurance.py).

## Development modes

Every bounded work item selects one of these methodology-neutral modes:

- `SPEC_FIRST`: requirement, invariant, implementation, and test are traced before completion is claimed.
- `DISCOVERY_FIRST`: a prototype may precede documentation, but product completion requires reconciliation.
- `AS_BUILT`: observed behavior is reconstructed without inventing historical intent.
- `RECONCILIATION`: conflicting source records are made explicit and resolved under authority.
- `DEFECT_DRIVEN`: the assurance slice is organized around a reproduced defect and its regression evidence.
- `MAINTENANCE`: an existing behavior is changed or preserved with evidence proportional to the change.

Transitions among all six declared modes are supported. The plan's illustrative sequence `DISCOVERY_FIRST -> PROTOTYPE -> SYSTEM_TO_DOCS -> RECONCILIATION -> HARDENING -> CANONICAL` describes intermediate work posture, not additional declared mode values.

## Source truth

Every behavioral statement is labeled exactly once as:

- `OBSERVED`: directly established by source, execution, or recorded evidence.
- `INFERRED`: a reasoned interpretation that has not been made authoritative.
- `DECIDED`: an authorized resolution or requirement.
- `UNVERIFIED`: present but not qualified for completion claims.

`INFERRED` evidence cannot become `DECIDED` without an authority reference. `UNVERIFIED` evidence cannot qualify completion.

## Completion states

The explicit completion vocabulary is:

`IDEATED`, `PROTOTYPED`, `DOMAIN_IMPLEMENTED`, `APPLICATION_INTEGRATED`, `API_INTEGRATED`, `UI_INTEGRATED`, `UNIT_VERIFIED`, `CONTRACT_VERIFIED`, `INTEGRATION_VERIFIED`, `RUNTIME_VERIFIED`, `SECURITY_VERIFIED`, `ADVERSARIALLY_VERIFIED`, `CANONICAL_VERIFIED`, and `PRODUCT_COMPLETE`.

These are explicit claims, not an implied ladder. A lower state does not prove any higher state. `CANONICAL_VERIFIED` qualifies source identity and evidence binding only; it does not prove empirical effectiveness. `DOMAIN_IMPLEMENTED` does not prove application integration.

`PRODUCT_COMPLETE` requires explicit evidence. A `DISCOVERY_FIRST` item also requires an explicit reconciliation qualification, and an item containing `DOMAIN_IMPLEMENTED` must contain explicit `APPLICATION_INTEGRATED` evidence before product completion.

## Validation fixtures

The contract defines seven fixtures for the AQ-1 boundary:

1. `SPEC_FIRST` traces requirement -> invariant -> implementation -> test.
2. `DISCOVERY_FIRST` permits a prototype before documentation.
3. `DISCOVERY_FIRST` blocks `PRODUCT_COMPLETE` until reconciliation.
4. `AS_BUILT` reconstruction does not invent historical intent.
5. Conflicting documentation and code select `RECONCILIATION`.
6. `INFERRED` cannot become `DECIDED` without authority.
7. Completion-state escalation without evidence fails closed.

The focused executable coverage is [`test_adaptive_assurance_aq1.py`](../../tests/runtime/test_adaptive_assurance_aq1.py).

## Authority and boundaries

Conductor remains the router, Ponytail owns implementation, Overseer owns validation strategy and evidence review, and Arbiter owns transition disposition. AQ-1 changes no routing authority, provider eligibility, external integration, or governance gate. AQ-2 through AQ-14 remain outside this implementation, and CUD10 remains held and unauthorized by this phase.
