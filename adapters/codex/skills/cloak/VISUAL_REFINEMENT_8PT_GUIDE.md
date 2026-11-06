
# Cloak: Visual Refinement and Soft 8-Point Spacing Guide

**Status:** Optional Orchestra reference. Integrated through progressive disclosure; advisory only, with no implementation or release authority.

**Adaptation notice:** Adapted from the owner-supplied guide for Orchestra. This adaptation updates its integration status and adds canonical links from the existing Cloak foundation and design-token guides. Attributions for cited inspiration are retained below; no author endorsement is implied.

## Activation and precedence

Load this guide only for visual-polish, anti-generic UI review, spacing-rhythm, or design-direction tasks. This is advisory design guidance, not an implementation or release authorization.

Precedence: explicit user requirements and project-native, approved design systems and tokens first; accessibility, functional usability, responsive behavior, data correctness, and brand requirements are not negotiable. External reference examples never override valid project requirements by default.

The Cloak specialist reviews and specifies; Ponytail implements, Clockwork owns cross-component architecture, and Overseer owns validation and readiness. Preserve CUIR-4's optional bounded retrieval limits and source provenance. Never automatically execute an external repository or install its dependencies.

## Soft 8-point spacing system

1. Default to an **8px layout rhythm** for CSS design work. Use the sequence `8, 16, 24, 32, 40, 48, 64, 80, 96` for layout gutters, card padding, group spacing, and section spacing, selecting the smallest step that supports grouping and hierarchy.
2. Use **4px half-steps** for icon-label alignment, text/control internals, dense component details, and typographic rhythm when the project system supports them. Use 2px optical adjustments only when explained by geometry or evidence; do not create routine arbitrary one-off values.
3. Prefer established semantic spacing tokens to hard-coded pixel values. Where appropriate, recommend semantic token mappings (for example, `space-1=4px`, `space-2=8px`, `space-3=16px`, `space-4=24px`, `space-5=32px`, `space-6=48px`, `space-7=64px`). These are proposed reference mappings, **not** a mandate to rename an established token system.
4. Do not force font size, line-height, icon artwork, focus rings, borders, hit targets, intrinsic content sizes, fluid widths, or viewport-responsive dimensions onto exact 8px multiples. Prefer relative units and responsive behavior where appropriate.
5. Do not shrink accessible hit targets or break wrapping, zoom, localization, and text resizing to satisfy the grid. Record any departure from the soft grid when it materially affects layout consistency.
6. Reuse existing approved design scales even if they use a 4px base; a 4px base with a strong 8px layout rhythm is compatible with the 8-point rule.

### Review examples

| UI relationship | Preferred starting values | Review note |
| --- | --- | --- |
| Icon to label | 4px or 8px | Preserve optical and baseline alignment |
| Closely related controls | 8px | Make grouped controls read as one unit |
| Form fields and compact groups | 8px or 16px | Keep errors, hints, and labels associated correctly |
| Card padding | 16px or 24px | Reuse the project's card token and density |
| Grid gap | 16px or 24px | Adapt to screen width and content |
| Major sections | 32px, 48px, or 64px | Convey section separation without wasting space |

These examples are starting values, not hard requirements. A project's validated design system may differ.

## Product-specific direction, before visual modification

Produce a compact, evidence-based direction note:

- **Product and users:** What the screen accomplishes and for whom.
- **Character:** Two or three concrete descriptive traits grounded in product context.
- **Brand and constraints:** Existing palette, font, tokens, layout, accessibility, responsive requirements, and elements that must remain unchanged.
- **Visual focus:** The functional or content-bearing focal point; avoid decorative elements competing with it.
- **Distinctive detail:** One grounded, restrained element that helps identify this product, only when needed.

For an existing approved screen, preserve its visual identity unless a confirmed defect or authorized redesign warrants changing it. When heavy redesign is contemplated without prior authorization, propose changes for approval rather than editing first.

## Visual audit and improvement sequence

First capture observable evidence from a supplied screenshot, design artifact, or authorized local render. Never invent a visual result from source-only inspection. Classify each finding as **confirmed**, **likely source-level risk**, or **unverified**.

Run the smallest necessary passes in this order; skip passes with no supported findings:

1. **Spacing and alignment:** Identify arbitrary gaps, inconsistent card padding, broken visual groups, uneven columns, and crowding. Apply the soft 8-point rule and 4px micro-adjustments.
2. **Color and hierarchy:** Reduce competing decorative emphasis without removing valid brand colors, semantic status signals, or contrast.
3. **Icon system:** Ensure consistent sizes, alignment, semantics, and accessible labels; preserve justified brand iconography.
4. **Interface copy:** Prefer specific labels and verifiable claims; preserve intended meaning, audience vocabulary, and localization.
5. **Typography:** Reduce accidental scale proliferation while respecting project fonts, legibility, text resizing, and line lengths.
6. **Layout:** Review structure, viewport containment, density, responsive transformations, and task-completion flow. Preserve agreed sections and information architecture.
7. **Component details:** Audit radii, borders, shadows, charts, states, and design-system parity only where inconsistent.
8. **Visuals:** Prefer purposeful, sourced, or product-specific imagery to generic filler. No generation or external asset use without appropriate task authorization and rights handling.
9. **Motion:** Keep it purposeful and compatible with reduced-motion preferences.

Do **not** categorically prohibit gradients, playful colors, emoji, heavy typography, equal-width cards, motion, or centered layouts. They are problems only when unsupported by the product's branding, content, accessibility, or interaction needs. Avoid replacing one formulaic aesthetic with another.

## Lightweight anti-generic checklist

- Is every visual recommendation linked to a documented problem or accepted design direction?
- Does the screen reflect its product rather than a generic AI template?
- Does hierarchy make the primary action and key information obvious?
- Is spacing consistent in comparable contexts, using approved tokens or the soft 8-point system?
- Are icons and controls meaningfully labeled, accessible, and keyboard usable?
- Does the design preserve verified data, functionality, empty/error/loading/success states, and responsive behavior?
- Are color and motion conveying meaning rather than merely decorating the UI?
- Are any requested new assets and claims sourced and licensed?

## Validation and evidence

Compare a before and after render when browser access is available and authorized. Use the same viewport, theme, content, and task, and include at least desktop and narrow-screen checks if relevant. Do not claim a rendered pass without rendered evidence. Cloak may record review findings; Overseer owns final validation gates.

For new anti-generic heuristics, test at least one case with a real existing brand and one case exhibiting generic repetitive AI defaults. Record justified changes, false positives, accessibility regressions, visual-diff evidence, preserved layout requirements, and remaining uncertainties. Reuse Orchestra's existing CUIR-5 and UIEF evidence conventions where applicable, without claiming the historical CUIR-5 pass validates these new heuristics.

Mshumer-style repeated-output analysis is optional, not required for ordinary Cloak reviews. Do not run bulk model generation, provider calls, browser snapshots of third-party websites, or dependency installs by default. If separately authorized, bound cost, time, data exposure, licensing, and comparison methodology before an experiment.

## Attribution and source provenance

- Product-specific visual-polish review, anti-generic signs, and ordered passes were informed by **Damir Sokolovsky**, [`heydamir/unslop` at commit `a6f121e`](https://github.com/heydamir/unslop/blob/a6f121eee5f29c2f74976b75456feae8b66afb3a/skills/unslop/SKILL.md), licensed **[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)**. The source guide describes its content as an independently structured summary rather than a verbatim reproduction. This Orchestra adaptation updates integration status and adds links from the existing Cloak foundation and design-token guides. No endorsement is implied.
- Repeated model-output analysis and before/after experimental methodology were informed by **Matt Shumer**, [`mshumer/unslop`](https://github.com/mshumer/unslop), licensed **[MIT](https://github.com/mshumer/unslop/blob/edcb62386d129c65e4395f0cfcc9168eb1ba2148/LICENSE)**. This guide uses those ideas conceptually and does not copy code or substantial text. If covered material is copied later, retain the original copyright and permission notice.
- Android's dp-based spacing is an analogous density-independent design principle, not a numeric conversion to CSS px. Queensland Government guidance directly documents a pixel-based spacing grid: [Queensland spacing guidance](https://www.designsystem.qld.gov.au/styles/spacing). Android reference: [Android layout guidance](https://developer.android.com/design/ui/mobile/guides/layout-and-content/grids-and-units).
- Conceptual inspiration does not grant rights to third-party assets, trademarks, or implementation code; check each asset's own license and rights before use.
