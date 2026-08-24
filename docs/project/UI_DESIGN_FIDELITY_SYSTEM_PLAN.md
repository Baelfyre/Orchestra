# Governed UI Design Fidelity System Plan

Status: `UIX_5_ACTIVE_SPECIALIST_INTEGRATION`

Recorded: 2026-08-24

Activation baseline: `3a7f18bd49c7aa16cfc4568fd42f9b06c37cb847`

Historical design source: closed-unmerged PR #471 (`docs: plan governed UI design fidelity system`)

Primary technical authority: `Baelfyre/Orchestra`

## Purpose

Define a governed, model-usable UI/UX system that can preserve strong Figma or project-native designs, translate design intent into existing project components and tokens, produce coherent new interfaces, and prove rendered fidelity without allowing models to invent arbitrary styling, components, icons, assets, accessibility behavior, or visual baselines.

The quality target is not a single preferred aesthetic. The target is reproducible design intent, project-native component reuse, accessibility, coherent layout/theme rules, explicit asset provenance, and revision-bound rendered proof.

## Activation decision

The earlier UI design-fidelity draft was intentionally deferred while the comparative Benchmark B work and earlier active work remained ahead of it.

That sequencing gate is now resolved:

- Benchmark B is canonical and terminal.
- B2 topology benefit was not established.
- B3 Murmurs benefit was not established.
- B4 was not eligible and consumed zero calls.
- B5 completed with no promotion.
- PR #471 was closed unmerged rather than rebased or merged from its stale baseline.
- The maintainer selected UI/UX specialist enhancement and visual-fidelity engineering as the next Orchestra workstream.

Unchecked entries in `docs/project/ROADMAP.md` under Deferred and Future Work are backlog candidates, not automatic prerequisites. They do not block UIX unless an item becomes an explicit dependency or the maintainer changes priority.

UIX-0 is complete, UIX-1 is canonical at `c331634dc63fbebb86ca07274c06262d5b52a50d`, UIX-2 is canonical at `8e4f3bb5e878131e8c038ea195311c92ca08cfde`, UIX-3 is canonical at `d27fbd6b89b297646c7e30ffb8bac193bbdc0cf4`, UIX-4 is canonical at `3a7f18bd49c7aa16cfc4568fd42f9b06c37cb847`, and UIX-5 is the active bounded unit on the current source branch. This current-state reconciliation supersedes the earlier UIX-0-only sequencing statement; historical UIX-0 and UIX-1 phase documents retain their phase-era status wording. The plan does not itself authorize dependency installation, Figma mutation, external authentication, release, deployment, marketplace publication, policy activation, or another protected action.

## Existing ownership

### Cloak

Owns UI/UX requirements, accessibility, responsive behavior, visual hierarchy, interaction design, component usability, design-system consistency, design-source evidence, and static fidelity review.

UIX extends Cloak toward a structured design-preservation workflow rather than a generic style-generation role.

### Clockwork

Owns component boundaries, state ownership, dependency direction, responsive determinism, overlay/layering architecture, and host-neutral adapter boundaries.

UIX must not couple Orchestra core to React, Tailwind, shadcn/ui, Radix, Material, Figma, Storybook, Playwright, or another single frontend stack.

### Ponytail

Owns minimal project-native implementation. When a UI Design Contract exists, Ponytail must prefer mapped project components, semantic tokens, and supplied assets before creating one-off equivalents.

### Overseer

Owns rendered validation evidence, revision binding, responsive/state/theme matrices, accessibility evidence, and baseline-integrity checks. Functional tests alone cannot establish visual fidelity.

### Conductor

Owns routing and sequencing. External UI tools provide evidence or implementation capability only and do not become authority sources.

### The Governor

Owns third-party dependency, asset, license, IP, and copyright review when adoption or redistribution is proposed. Reference-only research does not create adoption authority.

### Arbiter

Existing transition authority remains unchanged. UI quality evidence can satisfy evidence requirements but cannot grant authority by itself.

## Target architecture

```text
Figma / existing project design evidence
              |
              v
Cloak structured evidence scan
              |
              v
Normalized UI Design Contract
              |
       +------+------+
       |             |
       v             v
 Clockwork       Governor
 architecture    adoption/IP gate
 boundary        when applicable
       |
       v
Ponytail project-native implementation
       |
       v
Cloak renewed static fidelity audit
       |
       v
Overseer rendered + accessibility evidence
       |
       v
Existing Arbiter / governance transition
```

## Normalized UI Design Contract target

UIX-1 should define a versioned machine-readable, library-neutral contract containing at least:

- source provider and artifact/node/revision identity;
- primitive, semantic, and component tokens;
- typography, spacing, radii, borders, shadows, motion, and breakpoints;
- canonical component mappings, variants, states, slots, and accessibility behavior;
- layout regions, responsive ordering, containment, and overflow behavior;
- foundation, layout, theme, and optional-effect profiles;
- font, icon, image, logo, and illustration provenance;
- accessibility semantics, keyboard, focus, contrast, target-size, reduced-motion, and error-state requirements;
- fidelity dispositions: `PRESERVED`, `INTENTIONALLY_ADAPTED`, `UNRESOLVED`, `DIVERGENT`;
- implementation revision, viewport/theme/state matrices, rendered evidence, accessibility evidence, and comparison result.

Missing structured design evidence must remain explicit. Models must not replace missing evidence with fabricated certainty.

## Style taxonomy target

The initial profile taxonomy should distinguish categories rather than treating all visual ideas as peer themes.

Foundation:
- `minimalist`

Layout profile:
- `bento_grid`

Full system/theme profiles:
- `dark_cyberpunk`
- `neo_brutalism`
- `material_3`
- `retro_web_90s`

Optional surface/effect profiles:
- `glassmorphism`
- `neumorphism`
- `claymorphism`
- `aurora`

Accessibility invariants remain active regardless of selected profile. Bento is a layout strategy, not a theme. Complete design systems must not be mixed indiscriminately. Low-contrast effects require restricted use around interaction-critical controls.

## Asset precedence

### Icons

1. exact supplied Figma/project asset;
2. existing project icon component with verified matching glyph;
3. explicitly approved icon library;
4. reviewed custom asset;
5. no icon.

Do not invent SVG paths merely to approximate a known asset.

### Fonts

Use semantic font roles and explicit provenance. A model must not add a font solely for visual novelty.

### Images and logos

Record semantic role, source identity, crop/focal behavior, responsive behavior, alt semantics, and license/provenance where applicable. Known brand assets must not be silently substituted.

## Campaign sequence

### UIX-0: Activation, overlap audit, and contract freeze — ACTIVE

Objectives:

1. Re-read canonical specialist, routing, validation, roadmap, and host/tool boundaries from the B-terminal baseline.
2. Reconcile historical `Butler` and `Caveman` UI-routing references with current canonical ownership without inventing specialists.
3. Audit current Cloak, Clockwork, Ponytail, Overseer, Conductor, Governor, and Arbiter UI responsibilities for overlap and missing ownership.
4. Revalidate the external-reference landscape and classify candidates as reference, optional adapter, optional dependency, or rejected overlap.
5. Determine which existing Orchestra schemas/contracts can be extended and which genuinely require a new UI Design Contract.
6. Define the bounded UIX-1 contract-freeze inputs and explicit non-goals.
7. Perform Governor review before proposing third-party dependency or asset adoption.

Exit state: `UIX_0_CONTRACT_READY`.

UIX-0 is analysis and contract planning. It does not authorize dependency installation, adapter activation, target-project UI mutation, Figma mutation, or production action.

### UIX-1: UI Design Contract schema

Define the normalized schema, deterministic validation rules, valid examples, invalid fixtures, source-evidence classifications, and compatibility requirements.

### UIX-2: Cloak design-source preservation workflow

Add structured Figma/project-design evidence intake, component/token/asset preservation rules, and unresolved-evidence reporting before implementation.

### UIX-3: Theme, layout, and effect profile registry

Define machine-readable profile metadata, composition/conflict rules, and theme-neutral accessibility invariants.

### UIX-4: Component and asset preservation contracts

Define component mapping, variant/state coverage, font/icon/image/logo provenance, substitution rules, and explicit deviation reporting.

### UIX-5: Specialist integration

Integrate bounded responsibilities into Cloak, Clockwork, Ponytail, Overseer, Governor, Scribe, Conductor, and Arbiter without creating competing authority.

### UIX-6: Optional tool adapters

Only after separate architecture/adoption review, consider adapters for structured Figma context/Code Connect, Storybook evidence, Playwright rendered evidence, axe accessibility evidence, and established project token formats.

No optional tool is a mandatory frontend stack or authority source.

### UIX-7: Deterministic validation fixtures

Cover component reuse, token preservation, arbitrary-value drift, state completeness, profile conflicts, asset provenance, responsive containment, accessibility invariants, reference identity, and unauthorized visual-baseline replacement.

### UIX-8: Portable specialist and adapter parity

Update source specialist guidance and only canonically supported portable adapter copies, plus routing, indexes, checklists, and documentation required by actual changed scope.

### UIX-9: Controlled proof campaign

Run a bounded proof against a dedicated fixture or separately approved example project. Compare governed and unguided paths using objective evidence such as component reuse, token violations, accessibility defects, unresolved mappings, and revision-bound screenshot differences. Do not use model self-rating as proof.

## UIX-0 required reads

At minimum:

- `skills/cloak/SKILL.md`
- `skills/cloak/DESIGN_TOKENS_COMPONENT_STATES_GUIDE.md`
- `skills/clockwork/SKILL.md`
- `skills/ponytail/SKILL.md`
- `skills/overseer/SKILL.md`
- `skills/conductor/SKILL.md`
- `skills/the-governor/SKILL.md`
- `SKILL_INDEX.md`
- `ROUTING_MAP.md`
- `docs/project/ROADMAP.md`
- `docs/benchmarking/B_PHASE_CLOSEOUT_DECISION.md`

UIX-0 must also inspect current host/plugin capabilities before making integration claims.

## External reference candidates for UIX-0 revalidation

Historical PR #471 identified these as references/candidates. Their current state, license, maintained integration surface, and overlap must be revalidated before UIX-0 relies on them:

- `figma/sds`
- `figma/code-connect`
- `shadcn-ui/ui`
- `radix-ui/primitives`
- `adobe/react-spectrum`
- `style-dictionary/style-dictionary`
- `tokens-studio/figma-plugin`
- `storybookjs/storybook`
- `microsoft/playwright`
- `dequelabs/axe-core`
- `lucide-icons/lucide`
- `fontsource/fontsource`

Historical classification is evidence, not current adoption authority.

## Validation principles

UIX implementation readiness must eventually prove:

- source and adapter parity for changed specialist surfaces;
- deterministic schema and fixture validation;
- project-stack discovery before framework-specific implementation advice;
- traceability from design evidence to token/component/asset mappings;
- accessibility invariants across supported profiles;
- exact implementation-revision and reference-identity binding for rendered evidence;
- baseline changes cannot silently erase a failing visual comparison;
- responsive and interaction evidence covers the accepted project matrix;
- missing Figma/tool capability becomes an explicit evidence limitation;
- no unauthorized dependency, runtime, or authority expansion.

## Non-goals

The UIX campaign does not:

- turn Orchestra into a component library;
- force a universal visual theme;
- make React, Tailwind, shadcn/ui, Radix, Material 3, Storybook, Playwright, axe, Tokens Studio, Style Dictionary, or Figma mandatory;
- replace target-project design systems;
- allow screenshot matching to override semantics, accessibility, architecture, security, or product requirements;
- permit visual-baseline replacement as a shortcut around fidelity failure;
- authorize Figma writes, dependency installation, release, deployment, marketplace publication, or production mutation.

## Current bounded next action

Complete UIX-5 through fresh exact-head validation and signed canonicalization of the specialist integration flow. Stop before UIX-6 until UIX-5 has an independent canonical readback.
