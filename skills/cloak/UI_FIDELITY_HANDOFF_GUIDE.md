# Cloak UI Fidelity Handoff Guide (UIEF-4)

This guide governs the Cloak implementation-bound visible-layer fidelity handoff contract (UIFidelityHandoff) under the UI Execution Fidelity (UIEF) architecture.

## 1. Specialist Authority and Separation of Concerns

- **Cloak (Design Authority)**: Owns the visible-layer design intent, information hierarchy, macro-composition specification, pattern selection, and the UIFidelityHandoff contract. Cloak never authors code implementations or modifies persistence/infrastructure.
- **Conductor (Routing Authority)**: Retains upstream authority over UIImplementationProfile selection (MINIMAL_SAFE vs UI_CONTRACT_FIDELITY). Cloak binds to the selected profile and does not self-assign or re-route profiles.
- **Ponytail (Implementation Consumer)**: Downstream implementation specialist that strictly consumes the UIFidelityHandoff without authoring, inventing, or altering design decisions.
- **Clockwork Boundary**: UIEF-5 Clockwork engineering translation remains strictly outside UIEF-4. Cloak does not generate architectural refactoring or engineering translations.

## 2. Provenance and Reference Discipline

- **CUIR References**: Selected CUIR-3/CUIR-4 normalized patterns must carry explicit provenance IDs (source_kind: CUIR_NORMALIZED). They provide structural pattern guidance without copying external assets.
- **Project-Native Primacy**: Native components, design tokens, and existing layouts (source_kind: PROJECT_NATIVE) outrank external references unless explicitly deprecated.
- **Provider References**: Public provider guidance (PUBLIC_PROVIDER_GUIDANCE) and observed provider outputs (OBSERVED_PROVIDER_OUTPUT) are marked advisory_only: true and serve solely as comparative evidence. Never claim proprietary provider internal algorithms or copy third-party source code.
- **Reference Integrity**: Every repository-local `reference_ref` in the canonical UIEF reference profile or handoff must resolve to a real repository path. CUIR pattern identifiers must exist in the canonical CUIR catalog. Do not create placeholder project-native, provider, component, asset, token, or specification paths merely to satisfy a contract field. Omit optional evidence when no traceable source exists, and keep missing consuming-project evidence explicit in `unresolved`.

## 3. Required Semantic Structure

The UIFidelityHandoff machine contract must bind:
1. **Design Intent**: Concise, actionable specification of accepted user-facing intent.
2. **Information Hierarchy**: Ordered levels from topmost landmarks to granular elements with target component mapping.
3. **Macro Composition**: Uncompromised structural compositions (layouts, split panes, action bars) that Ponytail is prohibited from simplifying solely to reduce code size.
4. **Selected Pattern References**: Curated patterns with source kind, reference link, and provenance identifier.
5. **Pattern Application Reason**: Transparent rationale for each chosen pattern.
6. **Required Regions**: Explicit landmarks (BANNER, NAVIGATION, MAIN, COMPLEMENTARY) and placement rules.
7. **Component, Typography, Spacing, and Visual Roles**: Explicit definitions preventing implementation-level guesswork.
8. **Responsive Transformations**: Concrete breakpoint transitions preserving core utility across desktop, tablet, and mobile viewports.
9. **Interaction States**: Comprehensive state coverage (DEFAULT, HOVER, FOCUS_VISIBLE, ACTIVE, DISABLED, LOADING, EMPTY, ERROR).
10. **Preserve / Adapt / Avoid Constraints**: Unambiguous guardrails defining non-negotiable elements (preserve), flexible margins (adapt), and forbidden anti-patterns (avoid).
11. **Explicit Unresolved Items**: Unresolved requirements or missing design tokens must be explicitly enumerated in unresolved. Never invent missing facts or silently drop unresolved requirements.

## 4. Handoff Consumption by Ponytail

Ponytail consumes the handoff via `to_ponytail_context()`:
- Ponytail executes the defined composition using project-native code and components.
- Any deviation required by technical constraints must be recorded as an authorized UIDeviationRecord in Ponytail execution payload.
- Omission of required compositions without an authorized deviation fails closed.
