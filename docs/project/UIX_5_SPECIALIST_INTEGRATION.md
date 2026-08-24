# UIX-5 Specialist Integration Flow

Status: `UIX_5_SPECIALIST_INTEGRATION_IMPLEMENTED_PENDING_CANONICAL_VALIDATION`

Recorded: 2026-08-24

Entry baseline: `3a7f18bd49c7aa16cfc4568fd42f9b06c37cb847`

## Purpose

UIX-5 integrates the UI Design Contract, design-source preservation, profile, and component/asset evidence into the existing specialist workflow. It adds no specialist and changes no specialist authority.

## Canonical machine surface

- Schema: `machine/schemas/specialist-integration-flow.schema.json`
- Flow contract: `machine/ui/specialist-integration-flow.v1.json`
- Invalid authority fixture: `tests/fixtures/ui/uix5-invalid-authority-expansion.json`
- Invalid ownership fixture: `tests/fixtures/ui/uix5-invalid-ownership-overlap.json`
- Deterministic validation: `tests/runtime/test_specialist_integration_flow.py`

Schema version: `orchestra.ui-specialist-integration-flow.v1`

## Governed flow

```text
Conductor routes
  -> Cloak captures design and UX evidence
  -> Clockwork defines component, state, responsive, and integration boundaries
  -> The Governor reviews proposed dependency or asset adoption when applicable
  -> Ponytail implements project-native UI against frozen upstream contracts
  -> Cloak performs renewed static-fidelity review
  -> Overseer produces rendered and accessibility evidence
  -> Arbiter decides the transition disposition
```

The Governor stage is conditional. A dependency or asset proposal receives a governance decision or an explicit not-applicable result before implementation. Cloak intentionally appears before and after implementation; the first pass defines requirements and the second checks the implementation against them.

## Ownership boundaries

- Conductor owns routing and sequencing only.
- Cloak owns design/UX evidence, accessibility requirements, and static fidelity.
- Clockwork owns component/state/responsive architecture and integration boundaries.
- The Governor owns dependency, asset, license, IP, and copyright review.
- Ponytail owns minimal project-native implementation after upstream contracts are frozen.
- Overseer owns rendered, interaction, responsive, and accessibility evidence.
- Arbiter owns evidence freshness, continuity, and transition disposition.

Caveman remains presentation-only. Butler is not a registered or active owner. UI evidence and validation evidence remain evidence, not implementation, approval, release, or execution authority.

## Authority boundary

This is a contract-only integration surface. It does not add runtime integration, frontend dependencies, external-tool authority, Figma mutation, asset or dependency adoption authority, release authority, or policy activation. Missing or contradictory upstream evidence remains unresolved and must stop or reroute through the existing Conductor, Overseer, Governor, or Arbiter boundaries.

UIX-5 exits only after the exact flow, ownership boundaries, negative fixtures, and repository validation are proven, followed by fresh protected-main checks, signed materialization, canonical promotion, and independent readback.
