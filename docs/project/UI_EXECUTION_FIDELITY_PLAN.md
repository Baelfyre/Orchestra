# Orchestra UI Execution Fidelity Plan

Status: APPROVED_DIRECTION_PENDING_CANONICAL_REVIEW

Plan ID: ORCHESTRA_UIEF_V1

Phase family: UIEF

Recorded: 2026-09-04

Canonical planning owner: Orchestra

Entry baseline:
- branch: main
- commit: 592ecbef61fed88b6c8663e658bc6a45350c1bb7
- tree: d496b6da021203b0cfd4e054f76a5804ffecdd11

Related completed foundations:
- UIX design-fidelity program
- CUIR-0 through CUIR-6 reference-intelligence program
- OR-GOV specialist ownership and upstream-contract enforcement

## Purpose

Establish a governed frontend execution-fidelity pipeline so that strong UI/UX design intent survives translation from Cloak and CUIR through architecture, implementation, and rendered validation.

The program addresses a specific implementation risk: Ponytail is optimized for minimal safe implementation, but complex UI/UX may require more code or structure to preserve accepted design intent. Minimal implementation complexity must not become permission to reduce accepted design complexity.

Core rule:

```text
MINIMIZE IMPLEMENTATION COMPLEXITY
WITHOUT MINIMIZING REQUIRED DESIGN COMPLEXITY.
```

## Authority and source-of-truth

This plan is technical planning evidence only. It does not grant implementation, merge, release, deployment, production, dependency-adoption, destructive-action, or policy-activation authority.

Orchestra remains the source of truth for technical planning and implementation state.

Padayon may mirror:
- plan ID;
- canonical path;
- Orchestra revision;
- phase state;
- prompts;
- validation evidence;
- blockers;
- safest next bounded action.

Padayon must not independently redefine UIEF technical contracts or implementation authority.

## Existing ownership preserved

### Conductor
Owns routing, sequencing, context selection, and implementation-profile selection from accepted upstream evidence.

### Cloak
Owns UI/UX requirements, design intent, visual hierarchy, responsive intent, interaction design, accessibility requirements, CUIR pattern selection, and static fidelity review.

### Clockwork
Owns component/state architecture, responsive engineering structure, dependency direction, integration boundaries, and translation of accepted visible-layer intent into maintainable engineering boundaries.

### Ponytail
Owns authorized project-native implementation only. Ponytail may minimize unrelated code and structural complexity but may not simplify away accepted UI/UX requirements.

### Overseer
Owns rendered, interaction, responsive, accessibility, and validation evidence.

### Arbiter
Owns evidence freshness and transition disposition.

### The Tuner
Owns cross-specialist contract coordination and minimal re-entry recommendations when consumed clauses become stale or contradictory.

### The Governor, Cipher, Chronicler
Remain conditional owners for dependency/IP/compliance, security/privacy-control, and persistence/data semantics respectively.

### Weaver
Remains optional. UIEF may evaluate composition/wireframe representation support, but UI design authority remains with Cloak and no Weaver authority expansion is assumed by this plan.

## Existing foundations that UIEF must not rewrite

1. CUIR-0 through CUIR-6 remain closed and are consumed as upstream reference intelligence.
2. Historical UIX proof artifacts and frozen guidance remain historical evidence.
3. Existing UIX design-fidelity schemas remain valid unless a later UIEF phase proves an additive contract or versioned amendment is necessary.
4. Ponytail's historical UIX-9 frozen core surface must not be casually rewritten.
5. Existing generic specialist execution_mode remains reserved for execution-engine semantics such as HOST_NATIVE versus DETERMINISTIC_TEST_ENGINE.
6. UIEF must not create a new specialist unless a later audited gap proves that current ownership cannot represent the required behavior.

## Target pipeline

```text
User intent
  -> Conductor
  -> Cloak design discovery and design intent
  -> CUIR bounded pattern retrieval when applicable
  -> optional composition representation
  -> Clockwork engineering translation when required
  -> conditional Governor/Cipher/Chronicler review
  -> Conductor implementation-profile selection
  -> Ponytail MINIMAL_SAFE or UI_CONTRACT_FIDELITY
  -> Cloak static fidelity review
  -> Overseer rendered/interaction/responsive/accessibility evidence
  -> Arbiter transition disposition
```

## Implementation profiles

### MINIMAL_SAFE

Use for ordinary implementation where no accepted high-fidelity UI contract requires preservation beyond normal project-native correctness.

Principle:

```text
SMALLEST CORRECT IMPLEMENTATION
```

### UI_CONTRACT_FIDELITY

Use when accepted upstream evidence requires preservation of complex visible-layer behavior or composition.

Representative triggers:
- frozen UI Design Contract;
- Cloak fidelity handoff;
- selected CUIR pattern references;
- explicit reference/Figma fidelity;
- greenfield or aesthetic-heavy UI;
- non-trivial macro composition;
- deliberate visual hierarchy;
- required responsive reordering or transformations;
- required state/motion/layering behavior.

Principle:

```text
SMALLEST CORRECT IMPLEMENTATION
THAT FULLY PRESERVES THE ACCEPTED DESIGN CONTRACT.
```

Ponytail cannot self-downgrade UI_CONTRACT_FIDELITY to MINIMAL_SAFE.

## Phase sequence

### UIEF-0 - Baseline and drift reconciliation

Goal:
Establish a clean, current implementation baseline before behavior changes.

Required work:
1. Re-read live Orchestra main and active PRs.
2. Reconcile stale Ponytail release-state wording against the published v1.8.0 state.
3. Reconcile active Butler/Caveman UI routing residue with canonical UIX ownership.
4. Inventory historical UIX frozen surfaces and tests that protect them.
5. Inventory every Ponytail frontend, upstream-contract, routing, prompt, and validation surface affected by UIEF.
6. Produce a change-safety map showing amendable, additive, historical-frozen, and out-of-scope files.
7. Make no fidelity behavior change in the same atomic unit unless separately authorized.

Exit:
UIEF_0_BASELINE_RECONCILED

### UIEF-1 - UI implementation profile contract

Goal:
Define the machine-readable switch between ordinary minimal implementation and fidelity-preserving implementation.

Candidate contract:
```text
UIImplementationProfile
- profile
- design_contract_ref
- cloak_handoff_ref
- pattern_refs
- composition_refs
- clockwork_boundary_ref
- required_fidelity
- allowed_deviations
- selection_reason
- selected_by
```

Required rules:
- supported profiles are MINIMAL_SAFE and UI_CONTRACT_FIDELITY;
- Conductor selects the profile from accepted upstream evidence;
- Ponytail cannot change or downgrade the profile;
- UI_CONTRACT_FIDELITY requires traceable design inputs;
- missing required design evidence fails closed;
- the contract grants no new authority.

Exit:
UIEF_1_IMPLEMENTATION_PROFILE_CONTRACT_READY

### UIEF-2 - Conductor fidelity routing and context gate

Goal:
Make high-fidelity UI routing deterministic and prevent visually sensitive work from bypassing required design context.

Required work:
1. Add design-fidelity routing triggers.
2. Add DESIGN_FIDELITY_TRIGGER -> FAST_MODE_PROHIBITED.
3. Preserve simple UI tweaks in FAST only when no fidelity trigger exists.
4. Extend minimal prompt/context assembly with UI fidelity references only when UI_CONTRACT_FIDELITY is selected.
5. Preserve router-first context minimization.

Exit:
UIEF_2_ROUTING_AND_CONTEXT_GATE_READY

### UIEF-3 - Ponytail frontend fidelity execution layer

Goal:
Add progressive-disclosure implementation guidance without casually rewriting the historical frozen Ponytail core skill.

Candidate guide:
```text
skills/ponytail/FRONTEND_FIDELITY_EXECUTION_GUIDE.md
```

Required execution order:
1. Verify frozen design identity.
2. Load required design/pattern references.
3. Inspect project-native components/tokens/assets.
4. Implement semantic structure.
5. Implement macro composition.
6. Preserve hierarchy, spacing relationships, density, and layering.
7. Implement required component and interaction states.
8. Implement responsive transformations.
9. Implement motion only when specified.
10. Compare source implementation to accepted upstream intent.
11. Record every required deviation.
12. Return to Cloak static review.

Explicit prohibition:
Ponytail must not replace a required complex composition with a simpler composition solely because the simpler implementation uses less code.

Exit:
UIEF_3_PONYTAIL_FIDELITY_EXECUTION_READY

### UIEF-4 - Cloak implementation-bound fidelity handoff

Goal:
Convert design intelligence into an implementation-consumable but non-authorizing visible-layer contract.

Candidate additive artifact:
```text
UIFidelityHandoff
```

Candidate fields:
- design_intent;
- information_hierarchy;
- macro_composition;
- selected_pattern_refs;
- pattern_application_reason;
- required_regions;
- component_roles;
- visual_relationships;
- typography_roles;
- spacing_relationships;
- responsive_transformations;
- interaction_states;
- asset_requirements;
- preserve;
- adapt;
- avoid;
- unresolved.

CUIR patterns remain guidance evidence. UIEF binds selected patterns to the accepted design handoff without transferring design authority to Ponytail.

Exit:
UIEF_4_CLOAK_IMPLEMENTATION_BINDING_READY

### UIEF-5 - Clockwork UI engineering translation

Goal:
Translate accepted visual complexity into maintainable engineering structure without redesigning the visible experience.

Required work:
- component boundaries;
- state ownership;
- responsive engineering structure;
- composition/container ownership;
- overlay/layer relationships;
- data-flow boundaries;
- reusable component strategy;
- integration boundaries.

Rule:
```text
DESIGN COMPLEXITY != ARCHITECTURAL COMPLEXITY
```

Clockwork should minimize unnecessary engineering complexity while preserving accepted visible-layer complexity.

Exit:
UIEF_5_ENGINEERING_TRANSLATION_READY

### UIEF-6 - Cross-specialist fidelity chain

Goal:
Integrate routing and handoffs without overlapping specialist authority.

Canonical chain:
```text
Conductor
-> Cloak
-> Clockwork when required
-> Governor/Cipher/Chronicler when triggered
-> Conductor profile selection
-> Ponytail
-> Cloak
-> Overseer
-> Arbiter
```

The Tuner detects semantic invalidation and recommends the smallest re-entry path.

Weaver support may be evaluated for composition representation only. No automatic authority expansion is allowed.

Exit:
UIEF_6_SPECIALIST_INTEGRATION_READY

### UIEF-7 - Fidelity validation system

Goal:
Define layered validation that can distinguish source correctness from rendered design fidelity.

Cloak static review should cover:
- required regions;
- component mappings;
- semantic tokens;
- pattern intent;
- state coverage;
- unapproved substitution;
- source-level responsive intent;
- declared fidelity deviations.

Overseer rendered evidence should cover:
- layout containment;
- responsive behavior;
- hierarchy preservation;
- interaction states;
- keyboard/focus behavior;
- accessibility;
- overflow;
- reduced motion;
- theme/state consistency.

Reuse existing fidelity dispositions where applicable:
- PRESERVED;
- INTENTIONALLY_ADAPTED;
- UNRESOLVED;
- DIVERGENT.

Exit:
UIEF_7_FIDELITY_VALIDATION_READY

### UIEF-8 - Adversarial regression suite

Goal:
Prove that minimalism cannot override accepted UI fidelity.

Minimum adversarial scenarios:
1. required seven-region composition versus easier four-region simplification;
2. deliberate asymmetry versus generic equal-card grid;
3. responsive reorder versus simple vertical stacking;
4. selected CUIR pattern omitted during implementation;
5. Ponytail attempts profile downgrade;
6. required design evidence missing;
7. unapproved deviation;
8. approved intentional adaptation;
9. fidelity-triggered task incorrectly classified FAST;
10. existing project-native component available;
11. simpler code that truly preserves full fidelity.

Tests must assert behavior, not only string presence.

Exit:
UIEF_8_ADVERSARIAL_REGRESSION_PASS

### UIEF-9 - Controlled comparative evaluation

Goal:
Determine whether UIEF improves Codex-generated frontend quality without weakening project-native reuse, accessibility, correctness, or governance.

Arms:
- baseline: current Codex/Ponytail path;
- candidate: Cloak/CUIR + UI fidelity handoff + Clockwork translation + Ponytail UI_CONTRACT_FIDELITY.

Representative task classes:
- dashboard;
- admin/SaaS;
- onboarding;
- analytics/data-dense;
- marketplace/community;
- form workflow;
- mobile-responsive dashboard;
- visually distinctive landing experience.

Evaluation dimensions:
- requirement coverage;
- information hierarchy;
- composition quality;
- visual coherence;
- typography/spacing;
- project-native reuse;
- responsive behavior;
- accessibility;
- interaction completeness;
- arbitrary styling drift;
- unnecessary code complexity;
- fidelity deviations;
- blinded human preference where feasible.

Do not use model self-rating as primary proof.

Possible dispositions:
- PROMOTE;
- PROMOTE_WITH_LIMITS;
- NO_BENEFIT_ESTABLISHED;
- REGRESSION.

Exit:
UIEF_9_CONTROLLED_EVALUATION_COMPLETE

### UIEF-10 - Portable integration and closeout

Goal:
Integrate only validated UIEF behavior into portable specialist surfaces and close the program without rewriting historical evidence.

Required work:
- canonical/Codex parity;
- prompt-load validation;
- routing validation;
- CUIR compatibility;
- UIX compatibility;
- Ponytail behavior regressions;
- full Orchestra validation;
- machine discovery updates where justified;
- documentation reconciliation;
- exact-head validation;
- canonical readback;
- human gate for protected transitions.

Exit:
UIEF_COMPLETE_CANONICAL_VERIFIED

## Phase dependency

```text
UIEF-0
-> UIEF-1
-> UIEF-2
-> UIEF-3
-> UIEF-4
-> UIEF-5
-> UIEF-6
-> UIEF-7
-> UIEF-8
-> UIEF-9
-> UIEF-10
```

The sequence is intentionally serial at program start because each phase defines or consumes contracts needed by the next phase.

## Validation principles

UIEF must prove:
1. accepted design complexity cannot be silently reduced by Ponytail minimalism;
2. project-native components/tokens/assets retain precedence;
3. missing design evidence remains explicit;
4. fidelity mode does not grant design authority to Ponytail;
5. fidelity mode does not create dependency, release, deployment, or production authority;
6. CUIR remains advisory reference intelligence;
7. UIX historical proof artifacts remain historically valid;
8. FAST cannot bypass a material fidelity trigger;
9. rendered evidence remains Overseer-owned;
10. transition authority remains Arbiter-owned;
11. any model-quality improvement claim is evidence-bound.

## Non-goals

UIEF does not:
- create a new frontend framework;
- force React, Tailwind, shadcn/ui, Material, Radix, Figma, Storybook, Playwright, or another stack;
- reopen CUIR;
- rewrite historical UIX results;
- make Weaver a UI design authority;
- make Ponytail a UI/UX decision owner;
- authorize third-party asset/dependency reuse;
- guarantee that Codex will outperform Claude;
- claim access to proprietary provider internals;
- authorize implementation merely because this plan exists.

## External research boundary

Publicly available provider guidance and open-source UI references may be studied through existing provenance and governance rules. Any Anthropic/Claude comparison must distinguish observable/public behavior from proprietary internal behavior.

```text
PUBLIC GUIDANCE OR OBSERVED OUTPUT
!=
PROPRIETARY INTERNAL ALGORITHM
```

## Padayon continuity projection

Recommended Padayon mirror fields:
- program_id: ORCHESTRA_UIEF_V1;
- canonical_plan_path: docs/project/UI_EXECUTION_FIDELITY_PLAN.md;
- canonical_source_revision;
- phase;
- status;
- validation evidence;
- blockers;
- authority state;
- next bounded action.

The Padayon projection is continuity-only and must be reconciled against live Orchestra source before execution.

## Current bounded next action

After this plan is reviewed and canonically established, begin UIEF-0 as a separate bounded audit/reconciliation unit.

Do not begin UIEF-1 implementation until UIEF-0 is complete, validated, canonically read back, and the next phase is separately authorized.
