# UIX-4 Component and Asset Preservation Contracts

Status: `UIX_4_COMPONENT_ASSET_PRESERVATION_IMPLEMENTED_PENDING_CANONICAL_VALIDATION`

Recorded: 2026-08-24

Entry baseline: `d27fbd6b89b297646c7e30ffb8bac193bbdc0cf4`

## Purpose

UIX-4 defines the evidence-bound contract used to preserve project-native component mappings, interaction-state and variant coverage, semantic tokens, and font/icon/image/illustration/logo provenance before implementation. It makes substitution and intentional deviation visible instead of allowing a visually plausible approximation to become an undocumented source of truth.

## Canonical machine surface

- Schema: `machine/schemas/component-asset-preservation.schema.json`
- Contract: `machine/ui/component-asset-preservation-contract.v1.json`
- Invalid substitution fixture: `tests/fixtures/ui/uix4-invalid-unapproved-substitution.json`
- Invalid coverage fixture: `tests/fixtures/ui/uix4-invalid-incomplete-state-coverage.json`
- Deterministic validation: `tests/runtime/test_component_asset_preservation.py`

Schema version: `orchestra.component-asset-preservation.v1`

## Preservation precedence

1. Exact supplied project asset or component.
2. Verified existing project-native equivalent.
3. Approved semantic mapping.
4. Explicitly approved adaptation.
5. Reviewed new implementation.
6. `UNRESOLVED` rather than a fabricated replacement.

Components must record variants, interaction states, semantic tokens, mapping target, and coverage disposition. Incomplete coverage blocks implementation readiness. An intentional adaptation requires both a reason and an approval reference.

## Asset provenance and substitution

Every font, icon, image, illustration, and logo record requires source identity, provenance status, license or source status, an evidence reference, and a substitution policy. Known assets cannot be approximated without explicit approval and provenance. Invented SVG or logo paths, novelty fonts, and silent known-asset substitutions remain prohibited.

## Authority boundary

This contract is evidence. It does not grant implementation, CSS, validation, dependency-adoption, external-tool, or Figma-mutation authority. Governor review remains applicable when asset, license, IP, or dependency adoption is proposed.

## Ownership and exit

Cloak owns preservation semantics and static fidelity requirements. Clockwork owns later component boundaries. Ponytail owns only authorized project-native implementation. Overseer owns rendered and accessibility evidence. Conductor and Arbiter retain routing and transition ownership.

UIX-4 exits only after exact-tree validation, fresh protected-main checks, signed materialization, canonical promotion, and independent tree/signature readback.
