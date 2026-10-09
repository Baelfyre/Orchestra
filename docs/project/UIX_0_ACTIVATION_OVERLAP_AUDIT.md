# UIX-0 Activation, Ownership, and Overlap Audit

Status: `UIX_0_CONTRACT_READY`

Recorded: 2026-08-24

Canonical activation baseline: `ec515688041125ba0b1191da2ba6e3c7219a09ec`

Activation plan: `docs/project/UI_DESIGN_FIDELITY_SYSTEM_PLAN.md`

## 1. Purpose

UIX-0 determines whether Orchestra can begin a governed UI design-fidelity and UI/UX specialist enhancement program without duplicating existing specialist authority, hard-wiring a frontend stack, or treating external design tools as governance authority.

This audit is read-only/contractual in intent. It does not install dependencies, modify Figma, mutate a target project's UI, activate an external integration, change production behavior, release, deploy, or promote policy.

## 2. Entry-state verification

The UIX campaign was originally drafted in PR #471 and deliberately left inactive while earlier Orchestra work remained ahead of it. PR #471 was closed unmerged rather than rebased or merged from its stale baseline.

The prerequisite comparative Benchmark B program is now terminal and canonically closed:

- B2: `CONFIRMATORY_BENEFIT_NOT_ESTABLISHED`.
- B3: `CONFIRMATORY_BENEFIT_NOT_ESTABLISHED`.
- B4: `NOT_ELIGIBLE_NO_EXECUTION`.
- B5: complete, no promotion.
- Murmurs remains research-only and receives no default/runtime promotion.

The maintainer explicitly selected UI/UX specialist enhancement and visual-fidelity engineering as the next Orchestra workstream.

Unchecked roadmap entries under Deferred and Future Work remain backlog candidates. They are not automatic prerequisites for UIX unless a specific dependency is established or the maintainer changes priority.

## 3. Current specialist ownership audit

### Cloak

Canonical ownership remains:

- visible-layer UI/UX requirements;
- accessibility requirements;
- responsive behavior;
- interaction design;
- visual hierarchy;
- design-system consistency;
- frontend design evidence review;
- source-level static UI risk and fidelity review.

UIX must extend Cloak toward structured design-source preservation. It must not turn Cloak into an implementation or rendered-test owner.

### Clockwork

Canonical ownership remains:

- component and application boundaries;
- state and dependency ownership;
- UI engineering structure;
- layout/overlay architecture when structural engineering is involved;
- host-neutral adapter boundaries.

Clockwork must keep the normalized UI contract independent from any mandatory React, Tailwind, shadcn/ui, Radix, Material, Storybook, Figma, or Playwright stack.

### Ponytail

Canonical ownership remains implementation after upstream requirements are settled.

UIX-1 and later should add a design-contract implementation gate requiring Ponytail to:

1. inspect the target project's established stack;
2. reuse existing mapped components and semantic tokens;
3. preserve exact supplied/project assets where possible;
4. avoid one-off substitutes for known components/assets;
5. report necessary fidelity deviations instead of silently approximating them.

### Overseer

Canonical ownership remains QA strategy, validation boundaries, rendered/browser evidence, acceptance criteria, and readiness evidence.

For UIX, Overseer is the canonical rendered-validation evidence owner. Functional source tests alone cannot establish rendered fidelity.

### Conductor

Conductor remains the exclusive router. It may detect available Figma, Storybook, browser, token, or accessibility capabilities, but availability never creates authority.

### The Governor

Governor review is required only when adoption, copying, redistribution, licensing, asset use, or another IP/compliance consequence is proposed. Reference-only research does not create dependency-adoption authority.

### Arbiter

Arbiter remains the continuity and transition-governance owner. It consumes validation evidence and determines whether work may continue within the current authority envelope.

## 4. Butler and Caveman routing inconsistency resolution

### Finding

The current `ROUTING_MAP.md` UI Engineering and Validation Ownership flow still contains historical references that do not match the canonical skill index:

- `Butler selects rendered-validation owner`;
- `Caveman enforces explicit stop-condition reporting`;
- `Butler or maintainer performs final approval`.

`Butler` is not an active canonical specialist in `SKILL_INDEX.md`.

`Caveman` is a communication/presentation layer and may be used to compress or format a handoff, but it is not transition authority.

### Canonical resolution

Do not create or restore a Butler specialist merely to satisfy the historical wording.

The active ownership model is:

```text
Conductor routes the UI-affecting change
-> Cloak defines/reviews design and static fidelity requirements
-> Clockwork owns engineering correction boundaries when required
-> Ponytail performs authorized implementation
-> Cloak performs renewed static fidelity/risk review
-> Overseer selects and evaluates the required rendered/browser/accessibility evidence
-> Arbiter consumes evidence and owns stop/continue transition disposition
-> Maintainer/human approval remains a separate gate when explicitly required
```

Caveman may compress the resulting communication but may not decide readiness, stop conditions, or authority.

### Required downstream cleanup

The active-source references to Butler/Caveman in UI routing guidance must be reconciled during specialist-integration work. Historical records may retain Butler references when they are clearly historical and non-authorizing.

No new specialist is required.

## 5. Existing Figma/design-to-code capability overlap

The current host environment already exposes structured Figma design-to-code and Code Connect workflows.

The observed design-to-code workflow has important principles that align with the proposed Orchestra contract:

- fetch structured design context before implementing;
- treat generated/reference code as design evidence, not paste-ready final code;
- adapt to the target project's actual stack;
- reuse existing project components and tokens first;
- prioritize Code Connect mappings, component documentation, design annotations, and design tokens over raw visual approximation;
- preserve exact icons/images instead of inventing replacements.

The current Code Connect workflow is template-file oriented and requires published Figma library components plus an eligible Figma plan/seat. It therefore cannot be assumed available for every project.

### Decision

Orchestra must not build a competing Figma client into the core UI contract.

Figma is an optional structured design-evidence capability. The normalized UI Design Contract must support:

- Figma with Code Connect;
- Figma without Code Connect;
- project-native Storybook/component documentation;
- screenshots/reference images with weaker structured evidence;
- existing design systems without Figma;
- explicit `MISSING` or `UNRESOLVED` evidence when none of the above is available.

## 6. External reference revalidation

External repositories remain references or optional adapters. None is adopted as a mandatory Orchestra dependency by UIX-0.

| Candidate | Current UIX-0 classification | Rationale / boundary |
| --- | --- | --- |
| `figma/sds` | `PRIMARY_REFERENCE` | Official Figma example connecting Variables, Styles, Components, Code Connect, and a responsive React implementation. Useful as architecture evidence, not Orchestra's design system. |
| `figma/code-connect` | `OPTIONAL_STRUCTURED_EVIDENCE_ADAPTER` | Maps production components to Figma; template files are now the actively maintained path. Requires supported Figma plan/seat and published components. |
| `shadcn-ui/ui` | `REFERENCE_OPTIONAL_TARGET_STACK` | Strong source-owned accessible component distribution model. Use only when the target project already uses it or adoption is separately approved. |
| `radix-ui/primitives` | `REFERENCE_OPTIONAL_TARGET_DEPENDENCY` | Useful low-level accessibility/component primitive reference. Do not combine competing primitive stacks by default. |
| `adobe/react-spectrum` | `ACCESSIBILITY_REFERENCE_ALTERNATIVE` | Reference for adaptive/accessibility behavior, not a mandatory dependency. |
| `style-dictionary/style-dictionary` | `OPTIONAL_TOKEN_ADAPTER_REFERENCE` | Relevant when a target project already uses or separately adopts a token build pipeline. |
| `tokens-studio/figma-plugin` | `OPTIONAL_DESIGN_TOOL_REFERENCE` | Relevant to Figma token workflows; native variables or an existing project token system may be sufficient. |
| `storybookjs/storybook` | `OPTIONAL_COMPONENT_STATE_EVIDENCE_ADAPTER` | Useful when the target project already maintains stories/component-state documentation. |
| `microsoft/playwright` | `PREFERRED_RENDERED_EVIDENCE_ADAPTER_WHEN_AVAILABLE` | Strong browser evidence across Chromium, Firefox, and WebKit; remains optional and target-project dependent. |
| `dequelabs/axe-core` | `OPTIONAL_ACCESSIBILITY_EVIDENCE_ADAPTER` | Automated accessibility evidence only; never sufficient for full accessibility conformance on its own. |
| `lucide-icons/lucide` | `OPTIONAL_ICON_SOURCE` | Exact project/Figma assets have precedence. Adoption requires project fit and applicable license/provenance review. |
| `fontsource/fontsource` | `OPTIONAL_FONT_DELIVERY_REFERENCE` | Delivery reference only. Every selected font retains its own provenance/license requirement. |

### Adoption rule

External-tool availability never changes Orchestra authority. A later UIX phase may define an adapter contract, but installing or adding a dependency still requires the target repository's own architecture/governance approval.

## 7. UI Design Contract overlap decision

No current Orchestra contract fully captures the required combination of:

- exact design-source identity;
- source evidence confidence;
- project component mapping;
- semantic token mapping;
- component variants/states/slots;
- layout/responsive intent;
- theme/profile semantics;
- font/icon/image/logo provenance;
- accessibility requirements;
- explicit fidelity deviations;
- exact implementation revision;
- rendered evidence matrix and reference identity.

A new normalized UI Design Contract is therefore justified, provided it remains library-neutral and consumes existing specialist authority rather than replacing it.

## 8. UIX-1 frozen input set

UIX-1 may design the contract against the following frozen top-level concepts:

```text
source
project_stack
confidence

design_system
components
layouts
profiles
assets
accessibility
fidelity
validation
```

### `source`

Must support provider, artifact/file identity, node/component identity where applicable, reference revision/timestamp, and provenance.

### `project_stack`

Must record the project's discovered implementation framework, existing component system, token mechanism, asset mechanism, and available evidence adapters without treating any one stack as mandatory.

### `confidence`

Use explicit evidence states:

- `CONFIRMED`
- `MISSING`
- `INFERRED_WITH_EXPLICIT_APPROVAL`
- `UNRESOLVED`

No silent inference state is allowed.

### `design_system`

Must distinguish primitive, semantic, and component tokens plus typography, spacing, radii, borders, elevation/shadow, motion, and breakpoints where applicable.

### `components`

Must support canonical design component identity, variants, states, slots, accessibility contract, and project-native component mapping.

### `layouts`

Must support regions, responsive order, containment, overflow, and layout-pattern intent without encoding raw framework syntax as the canonical meaning.

### `profiles`

Must distinguish foundation, layout, full system/theme, and optional effect profiles so incompatible visual systems are not mixed accidentally.

### `assets`

Must cover font, icon, image, logo, and illustration identity/provenance plus substitution disposition.

### `accessibility`

Must cover semantics, keyboard, focus, accessible names/descriptions, contrast, target size, reduced motion, errors, and relevant state requirements.

### `fidelity`

Use explicit dispositions:

- `PRESERVED`
- `INTENTIONALLY_ADAPTED`
- `UNRESOLVED`
- `DIVERGENT`

### `validation`

Must bind evidence to exact implementation revision, exact reference identity, viewport/theme/state matrix, rendered artifacts, accessibility evidence, and comparison disposition.

## 9. UIX-1 deterministic rules to preserve

The contract must enforce these principles:

1. Discover the target project's real stack before framework-specific guidance.
2. Existing project components/tokens outrank generic generated equivalents.
3. Exact supplied/project assets outrank invented replacements.
4. Missing design evidence remains explicit.
5. A screenshot diff is evidence, not product authority.
6. Functional tests do not prove visual fidelity.
7. Accessibility requirements remain active across every theme/profile.
8. Baseline/reference replacement cannot be used to erase a failing visual result without separately justified design-change evidence.
9. Figma, Storybook, Playwright, axe, token tools, and component libraries remain optional capabilities.
10. External-tool or plugin availability does not grant implementation, merge, release, or production authority.

## 10. Non-goals for UIX-1

UIX-1 must not:

- implement target-project UI;
- modify Figma;
- install Figma/Storybook/Playwright/axe/token/component dependencies;
- force React, Tailwind, shadcn/ui, Radix, Material, or another stack;
- create a Butler specialist;
- move QA authority away from Overseer;
- move transition authority away from Arbiter;
- make Caveman a validation/transition authority;
- define a single universal visual theme;
- claim automated accessibility checks establish complete WCAG conformance;
- authorize release, deployment, installed-integration refresh, policy activation, or production mutation.

## 11. UIX-0 exit disposition

```text
UIX_0 = CONTRACT_READY
NEW_SPECIALIST_REQUIRED = false
NEW_NORMALIZED_UI_DESIGN_CONTRACT = justified
FIGMA_CORE_DEPENDENCY = false
CODE_CONNECT_REQUIRED = false
STORYBOOK_REQUIRED = false
PLAYWRIGHT_REQUIRED = false
AXE_REQUIRED = false
TARGET_PROJECT_COMPONENT_REUSE = required_when_evidence_exists
MISSING_DESIGN_EVIDENCE = explicit_fail_to_uncertainty_not_fabrication
RENDERED_EVIDENCE_OWNER = overseer
TRANSITION_DISPOSITION_OWNER = arbiter
CAVEMAN_AUTHORITY = none
BUTLER_ACTIVE_OWNERSHIP = none
NEXT_UNIT = UIX_1_UI_DESIGN_CONTRACT_SCHEMA
UIX_1_IMPLEMENTATION_AUTHORIZED_BY_THIS_AUDIT = false
```

UIX-0 is complete when this audit is canonical and exact-head validation is green. UIX-1 remains a separate bounded implementation unit.