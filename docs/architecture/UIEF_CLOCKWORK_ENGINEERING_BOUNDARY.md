# UIEF Clockwork Engineering Boundary

Status: UIEF-5 CANDIDATE

Program: ORCHESTRA_UIEF_V1

## Purpose

This boundary defines how Clockwork translates an accepted Cloak `UIFidelityHandoff` into maintainable engineering structure while preserving the accepted visible-layer contract.

Core invariant:

```text
DESIGN_COMPLEXITY != ARCHITECTURAL_COMPLEXITY
```

Engineering structure may be simplified only when visible fidelity is unchanged.

## Accepted input

Clockwork consumes an accepted `UIFidelityHandoff` owned by Cloak.

The handoff remains authoritative for:
- design intent;
- information hierarchy;
- macro composition;
- required regions;
- visual, typography, and spacing relationships;
- responsive transformations;
- interaction states;
- asset requirements;
- preserve/adapt/avoid/unresolved dispositions.

Clockwork may not rewrite those decisions.

## Clockwork output

The UIEF-5 output is `UIEngineeringTranslation`:

`machine/ui/ui-engineering-translation.v1.json`

It defines:
- component boundaries;
- state ownership;
- responsive engineering structure;
- composition/container ownership;
- overlay and stacking-context ownership;
- data-flow boundaries;
- reusable component strategy;
- integration boundaries;
- dependency direction;
- unresolved engineering questions.

## Ownership boundary

Clockwork owns engineering translation.

Cloak retains visible design authority.

Ponytail owns implementation after an accepted engineering boundary exists.

Overseer owns validation strategy and rendered evidence.

Conductor owns cross-specialist sequencing. UIEF-5 does not activate the UIEF-6 chain.

Cipher and Chronicler remain conditional owners for security/privacy and persistence mechanics respectively.

## Preservation rules

Every accepted macro-composition identity must have an explicit engineering owner.

Accepted responsive transformations must be translated into engineering mechanisms rather than replaced by generic stacking or simpler breakpoints.

Project-native components, tokens, and assets remain preferred when they satisfy the accepted handoff.

Clockwork may reduce:
- unnecessary wrappers;
- duplicate state owners;
- redundant abstractions;
- needless third-party dependencies;
- accidental coupling.

Clockwork may not reduce:
- required regions;
- deliberate hierarchy;
- responsive transformation behavior;
- interaction state coverage;
- accepted layering;
- visible relationships.

## Authority

The UI engineering translation contract does not authorize:
- visible-layer redesign;
- application-code implementation;
- third-party dependency adoption;
- release or deployment;
- UIEF-6 execution.

Those actions retain their existing authority and specialist gates.

## Portable surfaces

- `skills/clockwork/UI_ENGINEERING_TRANSLATION_GUIDE.md`
- `adapters/codex/skills/clockwork/UI_ENGINEERING_TRANSLATION_GUIDE.md`
- `machine/ui/ui-engineering-translation.v1.json`
- `machine/schemas/ui-engineering-translation.v1.schema.json`
- `orchestra_runtime/domain/orchestration/ui_fidelity.py`

## Exit

UIEF-5 is ready only when the contract, runtime validation, Codex parity, and boundary regressions pass at the exact candidate head.

Exit marker:

`UIEF_5_ENGINEERING_TRANSLATION_READY`
