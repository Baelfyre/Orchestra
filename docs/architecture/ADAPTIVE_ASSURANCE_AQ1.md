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

## Evidence qualification (AQ1-R1)

`AssuranceEvidence` is qualified only when it carries an originating source, authoritative source reference, producer, validator, source/candidate/work-item bindings, freshness and version references, an `AUTHORITATIVE` provenance qualification, an evidence layer, an evidence scope, and a claim scope. These fields record and bind external authority; caller-controlled metadata does not create authority by itself.

Evidence layers are explicit: `STATIC`, `UNIT`, `DOMAIN`, `CONTRACT`, `INTEGRATION`, `HTTP`, `RUNTIME`, `PERSISTENCE`, `CONCURRENCY`, `SECURITY`, `PROVENANCE`, `MUTATION`, `ADVERSARIAL`, `DOCUMENTATION`, and `COMPLETION_STATE`. A layer qualifies only the completion states that explicitly accept it. For example, `UNIT` evidence cannot qualify `SECURITY_VERIFIED`, and `STATIC` evidence cannot qualify `RUNTIME_VERIFIED`.

Evidence scope records what the evidence proves, while claim scope records what the caller is asking to assert. The validator applies the explicit coverage relation `EVIDENCE_SCOPE <= CLAIM_SCOPE`: a narrower scope cannot qualify a broader claim. Binding and freshness references are checked against the requested source, candidate, work item, version, and freshness values when supplied. Missing, stale, mismatched, self-asserted, unverified, or semantically insufficient evidence fails closed.

Schema validity, CI success, record binding, evidence presence, lower assurance layers, and canonical verification are not substitutes for semantic evidence sufficiency. `CANONICAL_VERIFIED` remains limited to source/evidence qualification and never proves empirical effectiveness.

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
