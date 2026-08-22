# Governed UI Design Fidelity System Plan

Status: `DRAFT_DEFERRED_AFTER_EXISTING_PENDING_WORK`

Recorded: 2026-08-22

Audit baseline: `dc119739ef871d77ee91ade4e0d2d9032c804970`

Primary technical authority: `Baelfyre/Orchestra`

## Purpose

Define a governed, model-usable UI/UX system that can preserve high-quality Figma designs, translate them into project-native components, produce consistent new interfaces, and prove rendered fidelity without allowing models to invent arbitrary styling, components, icons, assets, accessibility behavior, or validation baselines.

This plan is documentation and sequencing only. It does not authorize dependency installation, Figma mutation, external API authentication, CI changes, runtime implementation, release, deployment, marketplace publication, protected-state mutation, merge, or policy activation.

## Sequencing Gate

This campaign is the next new UI-system implementation campaign only after the Orchestra work that was already pending when this plan was recorded has been completed, canonically closed, or explicitly reclassified by the maintainer.

The campaign must not preempt:

1. active benchmark, provider, adaptive-learning, Registry, or other already-authorized work;
2. any earlier unchecked item in `docs/project/ROADMAP.md`;
3. any active remediation or validation gate that becomes required before this campaign begins.

At activation time, Conductor and Arbiter must re-read canonical `main`, active PRs, roadmap state, and relevant continuity evidence. This document is a plan, not proof that prerequisites remain unchanged.

## Audit Scope

The audit reviewed the current canonical ownership and UI-related guidance in:

- `skills/cloak/SKILL.md`;
- `skills/cloak/DESIGN_TOKENS_COMPONENT_STATES_GUIDE.md`;
- `skills/clockwork/SKILL.md`;
- `skills/ponytail/SKILL.md`;
- `skills/overseer/SKILL.md`;
- `skills/conductor/SKILL.md`;
- `skills/the-governor/SKILL.md`;
- `SKILL_INDEX.md`;
- `ROUTING_MAP.md`;
- `docs/project/ROADMAP.md`.

## Current Architecture Audit

### Cloak

Current strengths:

- Owns UI/UX requirements, accessibility, responsive behavior, visual hierarchy, interaction design, component usability, form/navigation usability, and design-system consistency.
- Requires evidence review for Figma, GitHub, Storybook, screenshots, and other frontend artifacts rather than allowing unsupported inference.
- Already inspects Figma tokens, components, variants, annotations, descriptions, state coverage, and accessibility notes when evidence exists.
- Already distinguishes primitive, semantic, and component tokens and requires theme/state consistency.
- Already uses a staged workflow covering discovery, strategy, pattern intelligence, implementation handoff, and post-implementation review.
- Already performs a source-level static UI risk audit and explicitly refuses to treat static inspection as rendered proof.

Confirmed gaps:

- No canonical Figma design-preservation workflow exists for structured design context, Code Connect mappings, project component reuse, and exact asset preservation.
- No machine-readable Orchestra UI Design Contract currently binds source design identity, tokens, components, layouts, assets, states, accessibility expectations, and validation evidence.
- No canonical style taxonomy separates foundations, layout systems, full design systems/themes, and surface effects.
- No standard asset contract governs font roles, icon provenance, image semantics, asset identity, and substitution rules.
- No deterministic fidelity result contract distinguishes preserved, intentionally adapted, unresolved, and divergent design details.
- Existing aesthetic templates are useful but remain request-specific profiles rather than a general design-system schema.

### Clockwork

Current strengths:

- Owns component boundaries, state ownership, dependency direction, UI engineering structure, overlay lifecycle, stacking contexts, responsive determinism, and structural correction boundaries.
- Explicitly preserves Cloak accessibility requirements and project component architecture.

Required extension:

- Define a host-neutral design-system adapter boundary so Figma, token tools, Storybook, browser testing, and component libraries remain optional capabilities rather than new Orchestra authority sources or a mandatory frontend stack.
- Define where normalized UI Design Contract data lives and how downstream specialists consume it without coupling Orchestra core to React, Tailwind, shadcn/ui, Radix, Material, or another specific UI framework.

### Ponytail

Current strengths:

- Reuses existing project components, helpers, patterns, and installed dependencies before introducing new abstractions.
- Must follow accepted UI constraints from Cloak and architecture constraints from Clockwork.
- Project conventions override generic implementation examples.

Required extension:

- Add a UI Design Contract implementation gate when such a contract exists.
- Require mapped project components and semantic tokens before generating one-off equivalents.
- Require exact Figma or project assets when supplied, with no invented replacement SVG or placeholder asset.
- Record any necessary fidelity deviation instead of silently approximating the design.

### Overseer

Current strengths:

- Already blocks complete UI readiness when only functional tests pass.
- Requires visual proof, theme parity where applicable, interaction-path proof, responsive evidence, pointer/keyboard/focus checks, and current-commit screenshots or traces.
- Explicitly distinguishes static analysis from rendered validation.

Required extension:

- Add a revision-bound `UI_FIDELITY_EVIDENCE` contract that identifies the Figma/reference source, implementation revision, viewport/theme/state matrix, rendered artifacts, comparison result, accessibility result, and known unsupported cases.
- Establish a baseline-integrity rule: a failed visual comparison cannot be made green merely by replacing the approved reference or expected screenshot. Reference updates require separately justified design-change evidence.
- Add design-system drift checks for unregistered colors, spacing, typography, icons, components, or theme-specific exceptions when a project provides a contract.

### Conductor

Current strengths:

- Preserves Cloak's staged frontend workflow for broad, aesthetic-heavy, or greenfield work.
- Routes frontend changes through Clockwork, Cipher, Chronicler, and other owners when UI decisions cross their boundaries.

Required extension:

- Add explicit routing for design-source ingestion, design-contract creation, implementation, and fidelity validation.
- Keep Figma and external UI tooling as capabilities. They must not become governance or transition authority.

### The Governor

Current strengths:

- Already owns open-source license compatibility, IP, copyright, third-party asset, and dependency governance.

Required extension:

- Review license/IP implications only when Orchestra or a target project proposes copying, vendoring, distributing, or adding a third-party dependency or asset. Reference-only research does not create dependency adoption authority.

### Routing inconsistency requiring reconciliation

`ROUTING_MAP.md` currently names `Butler` as the rendered-validation owner selector and `Caveman` as a stop-condition reporting participant, but neither appears as an active canonical specialist in `SKILL_INDEX.md`.

UIX-0 must determine whether these names refer to host/runtime roles, legacy terminology, or missing canonical ownership. Do not create new specialists merely to preserve those names. The final routing model must have one explicit current owner for rendered-validation selection and one explicit current owner for stop-condition reporting.

## External Repository Audit

Audit date: 2026-08-22.

These repositories are references or optional integration candidates. None is approved as a mandatory Orchestra runtime dependency by this plan.

| Repository | Observed role | License evidence | Decision |
| --- | --- | --- | --- |
| `figma/sds` | Official Figma Simple Design System showing Variables, Styles, Components, Code Connect, Storybook, token extraction, icon generation, and responsive React structure. README labels SDS alpha. | MIT in GitHub repository metadata. | `PRIMARY_REFERENCE`. Study architecture and workflows. Do not vendor or make it Orchestra's UI framework. |
| `figma/code-connect` | Maps production design-system components and properties to Figma. Current README says template files are the only actively maintained Code Connect path. | MIT in GitHub repository metadata. | `OPTIONAL_INTEGRATION`. Prefer template-file workflows when capability and plan prerequisites exist. |
| `shadcn-ui/ui` | Source-owned accessible component distribution model across modern web stacks. | MIT in GitHub repository metadata. | `REFERENCE_OPTIONAL_TARGET_STACK`. Use as a component-ownership reference; never assume a target uses shadcn/ui. |
| `radix-ui/primitives` | Accessible low-level primitives for custom design systems. | MIT in GitHub repository metadata. | `REFERENCE_OPTIONAL_TARGET_DEPENDENCY`. Candidate where already present or separately approved. |
| `adobe/react-spectrum` | Adaptive, accessible, robust UI libraries and WAI-ARIA-oriented behavior. | Apache-2.0 in GitHub repository metadata. | `ACCESSIBILITY_REFERENCE_ALTERNATIVE`. Do not combine competing primitive stacks by default. |
| `style-dictionary/style-dictionary` | Cross-platform design-token build system. | Apache-2.0 in GitHub repository metadata. | `OPTIONAL_TOKEN_ADAPTER_REFERENCE`. Normalized Orchestra contract must remain tool-neutral. |
| `tokens-studio/figma-plugin` | Figma design-token workflow and token synchronization tooling. | MIT in GitHub repository metadata. | `OPTIONAL_DESIGN_TOOL`. Native Figma Variables or an established project token system may be sufficient. |
| `storybookjs/storybook` | Isolated UI component documentation, states, and testing workshop. | MIT in GitHub repository metadata. | `OPTIONAL_EVIDENCE_ADAPTER`. Consume stories/states when target project already uses it or adoption is separately approved. |
| `microsoft/playwright` | Browser automation across Chromium, Firefox, and WebKit. | Apache-2.0 in GitHub repository metadata. | `PREFERRED_RENDERED_VALIDATION_ADAPTER` when present or separately approved. |
| `dequelabs/axe-core` | Automated web accessibility engine. | MPL-2.0 in GitHub repository metadata. | `OPTIONAL_ACCESSIBILITY_VALIDATION_ADAPTER`. Dependency/license review remains required for adoption. |
| `lucide-icons/lucide` | Consistent icon toolkit with Figma/web ecosystem support. | Repository LICENSE identifies ISC for Lucide, with MIT terms for listed Feather-derived icons. | `OPTIONAL_ICON_SOURCE`. Exact project/Figma assets take precedence over substitution. |
| `fontsource/fontsource` | Self-hostable open-source font packages. | Repository metadata reports MIT for Fontsource code. Individual font licenses remain font-specific. | `OPTIONAL_FONT_DELIVERY_REFERENCE`. Every selected font requires its own license/provenance check. |

## Source URLs

- https://github.com/figma/sds
- https://github.com/figma/code-connect
- https://github.com/shadcn-ui/ui
- https://github.com/radix-ui/primitives
- https://github.com/adobe/react-spectrum
- https://github.com/style-dictionary/style-dictionary
- https://github.com/tokens-studio/figma-plugin
- https://github.com/storybookjs/storybook
- https://github.com/microsoft/playwright
- https://github.com/dequelabs/axe-core
- https://github.com/lucide-icons/lucide
- https://github.com/fontsource/fontsource

## Target Architecture

```text
Design source / project design evidence
             |
             v
Cloak design evidence scan
             |
             v
Normalized UI Design Contract
             |
     +-------+--------+
     |                |
     v                v
Clockwork          Governor
architecture       license/IP gate when adoption occurs
boundary
     |
     v
Ponytail project-native implementation
     |
     v
Cloak renewed static design audit
     |
     v
Overseer rendered fidelity + accessibility evidence
     |
     v
Arbiter / existing transition authority
```

External tools supply evidence or implementation capability only. They do not grant authority.

## Normalized UI Design Contract

UIX-1 should define a versioned machine-readable contract with at least these sections:

```text
source
  provider
  artifact_identity
  file_or_document_identity
  node_or_component_identity
  reference_revision_or_timestamp

design_system
  primitive_tokens
  semantic_tokens
  component_tokens
  typography_roles
  spacing_scale
  radii
  borders
  shadows
  motion
  breakpoints

components
  canonical_component
  source_mapping
  variants
  states
  slots
  accessibility_contract
  project_component_mapping

layouts
  pattern
  regions
  responsive_order
  containment
  overflow

theme
  foundation
  layout_profile
  theme_profile
  optional_effects

assets
  fonts
  icons
  images
  logos
  illustrations
  provenance
  license_or_source_status
  semantic_role

accessibility
  semantics
  keyboard
  focus
  names_descriptions
  contrast
  target_size
  reduced_motion
  error_state

fidelity
  preserved
  intentionally_adapted
  unresolved
  divergent

validation
  implementation_revision
  viewport_matrix
  theme_matrix
  state_matrix
  rendered_evidence
  accessibility_evidence
  comparison_result
```

The schema must remain library-neutral. A React project, JavaFX project, or another frontend stack may use different implementation mechanisms while consuming the same design intent where applicable.

## Canonical Style Taxonomy

The first profile registry should distinguish categories rather than treating every visual idea as a peer theme.

### Foundation

- `minimalist`

### Layout profile

- `bento_grid`

### Full system or theme profile

- `dark_cyberpunk`
- `neo_brutalism`
- `material_3`
- `retro_web_90s`

### Optional surface/effect profile

- `glassmorphism`
- `neumorphism`
- `claymorphism`
- `aurora`

Rules:

- Accessibility invariants remain active regardless of theme.
- A theme cannot redefine semantic meaning solely through color or decorative effect.
- Effect profiles must declare allowed surfaces and prohibited contexts.
- Neumorphism and similarly low-contrast treatments require restricted use for interaction-critical controls.
- Bento is a layout strategy, not a color/theme system.
- Material 3 is treated as a complete design-system profile when explicitly selected, not mixed indiscriminately with incompatible full-system profiles.
- Models must not compose conflicting full-system profiles without an explicit project contract.

## Asset Contracts

### Fonts

Use semantic roles such as `body`, `display`, and `mono`, with approved families, weights, fallback stacks, loading behavior, and license/provenance. Do not allow a model to introduce a new font merely for visual novelty.

### Icons

Precedence:

1. exact supplied Figma/project icon asset;
2. existing project icon component with a verified matching glyph;
3. explicitly approved icon library;
4. reviewed custom asset;
5. no icon.

Do not invent SVG paths as a substitute for a known design asset.

### Images

Classify images by semantic role, including content, decorative, avatar, logo, background, screenshot, illustration, and product media. Record alt semantics, aspect ratio, focal/crop behavior, source identity, and responsive behavior where applicable.

## Implementation Campaign

### UIX-0: Activation, overlap audit, and contract freeze

- Verify all pre-existing pending Orchestra work is complete or explicitly closed/reclassified.
- Re-read live main, roadmap, PRs, specialist contracts, adapter maturity, and current external-tool constraints.
- Reconcile `Butler` and `Caveman` references with canonical ownership.
- Confirm no duplicate design-system authority is introduced.
- Classify each external repository as reference, optional adapter, optional dependency, or rejected overlap.
- Run Governor review before any third-party code, dependency, or asset adoption.

Exit: `UIX_0_CONTRACT_READY` with no implementation authority implied.

### UIX-1: UI Design Contract schema

- Define the normalized schema and validation rules.
- Add deterministic examples and invalid fixtures.
- Preserve project-native stack and token tools as higher-priority implementation evidence.
- Define source evidence classes: `CONFIRMED`, `MISSING`, `INFERRED_WITH_EXPLICIT_APPROVAL`, `UNRESOLVED`.

### UIX-2: Cloak design-source preservation workflow

- Add a Figma-aware structured-evidence path.
- When structured Figma context exists, inspect it before relying on screenshots alone.
- Prefer Code Connect mappings, component documentation, design annotations, tokens, and exact assets before raw visual approximation.
- Generate a UI Design Contract and unresolved-evidence list instead of implementation code.
- Add a project-existing-design-system audit path for non-Figma work.

### UIX-3: Theme, layout, and effect profile registry

- Add machine-readable profile metadata for the initial ten requested styles.
- Define composition compatibility and conflict rules.
- Define theme-neutral accessibility invariants.
- Define token categories for typography, spacing, color, border, radius, shadow/elevation, motion, and responsive behavior.

### UIX-4: Component and asset preservation contracts

- Define canonical component mapping and variant/state coverage.
- Define font, icon, image, logo, and illustration provenance rules.
- Define substitution policy and explicit deviation reporting.
- Define project component reuse metrics without turning metrics into release authority.

### UIX-5: Specialist integration

- Cloak: design evidence, contract creation, style/profile review, static fidelity audit.
- Clockwork: adapter/component boundaries and target-stack architecture.
- Ponytail: contract-bound project-native implementation and deviation reporting.
- Overseer: rendered fidelity, accessibility, theme, responsive, and interaction evidence.
- Governor: dependency/license/IP review only when adoption is proposed.
- Scribe: durable human documentation.
- Conductor: minimum required route and cross-domain sequencing.
- Arbiter: existing transition and continuity authority remains unchanged.

### UIX-6: Optional tool adapters

Implement only those justified by activation-time architecture review:

- Figma structured design context and Code Connect capability adapter;
- Storybook component/state evidence reader;
- Playwright rendered screenshot and interaction evidence adapter;
- axe-core accessibility evidence adapter;
- token-tool adapters for established target-project formats, with Style Dictionary or Tokens Studio support considered only when justified.

No adapter may convert external-tool availability into authority.

### UIX-7: Deterministic validation fixtures

Add fixtures and tests for:

- component mapping and reuse;
- semantic token preservation;
- arbitrary-value drift detection;
- state matrix completeness;
- theme profile composition conflicts;
- font/icon/image provenance;
- responsive ordering and containment contracts;
- accessibility invariants;
- reference identity and fidelity evidence;
- stale or unauthorized visual baseline replacement.

### UIX-8: Portable specialist and adapter parity

- Update source specialist guidance and only the portable adapter copies that Orchestra canonically supports.
- Preserve source/Codex or other adapter parity rules already owned by the repository.
- Update routing, checklists, machine indexes, documentation, and examples as required by actual changed scope.

### UIX-9: Controlled proof campaign

- Run a bounded reference implementation against a dedicated fixture or approved example project.
- Compare an unguided model path with the governed UI contract using objective evidence such as token violations, component reuse, accessibility defects, unresolved mappings, and screenshot differences when an approved visual reference exists.
- Do not use model self-rating as proof of UI quality.
- Do not promote the campaign to release scope until exact-head validation and human visual approval are complete.

## Validation Requirements

At minimum, implementation readiness must prove:

- source and adapter parity for changed specialist surfaces;
- schema validation and deterministic fixture coverage;
- no unauthorized runtime or dependency expansion;
- project-stack discovery precedes framework-specific implementation advice;
- design tokens and component mappings remain traceable to source evidence;
- accessibility requirements remain invariant across supported themes;
- visual evidence is tied to the exact implementation revision and exact approved reference identity;
- reference/baseline changes are separately justified and cannot silently erase a failing diff;
- responsive and interaction evidence covers the accepted project matrix;
- missing Figma/tool capability degrades to an explicit evidence limitation rather than fabricated certainty.

Existing Orchestra governance, exact-head checks, required signatures, PR rules, and human gates remain authoritative.

## Explicit Non-Goals

This campaign does not:

- turn Orchestra into a component library;
- make React, Tailwind, shadcn/ui, Radix, Material 3, Storybook, Playwright, axe-core, Tokens Studio, or Style Dictionary mandatory across projects;
- force one visual theme across all projects;
- replace target-project design systems;
- allow models to redraw known assets merely because a similar icon or font exists;
- permit screenshot matching to override semantics, accessibility, architecture, security, or product requirements;
- allow visual-baseline replacement to be used as a shortcut around a fidelity failure;
- authorize Figma writes, dependency adoption, release, deployment, or marketplace publication.

## Final Planned State

The intended final behavior is:

```text
Figma or existing design evidence
-> structured scan
-> normalized UI Design Contract
-> project component/token resolution
-> governed implementation
-> static UI audit
-> rendered/browser validation
-> accessibility validation
-> exact-reference fidelity evidence
-> existing Orchestra transition governance
```

The quality target is not a single preferred aesthetic. The target is reproducible design intent, component reuse, accessibility, coherent theme/layout rules, explicit asset provenance, and revision-bound rendered proof.