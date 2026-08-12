# Responsive CSS Layout and Containment Guide

Use this guide to diagnose layout risk and define implementation-ready responsive requirements without writing production CSS.

## Layout model selection

- Use normal document flow as the default baseline.
- Use Flexbox for primarily one-dimensional distribution and alignment.
- Use Grid when rows and columns need coordinated two-dimensional placement.
- Nested layout models are valid when each level has a clear responsibility. Avoid layout mechanisms chosen only because they happen to make one screenshot align.
- Preserve semantic DOM order even when visual layout changes across breakpoints.

## Intrinsic sizing literacy

Cloak should recognize common causes of unexpected overflow and compression.

- Long unbroken text, intrinsic media sizes, minimum content sizes, and nested flex/grid containers can force a layout wider than its container.
- A flex or grid child may need permission to shrink within its layout context. Diagnose the containing relationship before recommending arbitrary fixed widths.
- Grid tracks should account for content that must shrink or wrap. Avoid layouts whose minimum track size silently preserves desktop width on narrow screens.
- Media should respect its containing region and preserve meaningful aspect ratio unless product requirements explicitly call for cropping.

## Overflow and clipping

Treat overflow as a user-visible behavior decision, not merely a cosmetic property.

- Horizontal scrolling on the entire page is usually a containment defect for ordinary application layouts.
- Local horizontal scrolling can be appropriate for wide data tables, timelines, code, or other content whose two-dimensional relationship must remain intact.
- Clipping must not hide focus indicators, validation messages, menus, tooltips, or actionable content.
- Text truncation needs an evidence-backed reason. Critical labels, values, and error messages should remain perceivable without relying on hover-only disclosure.
- Inspect ancestor overflow, positioning, transforms, and stacking contexts when popovers or focus rings appear cut off.

## Breakpoints and reflow

- Define breakpoints from content pressure and task preservation, not device-name folklore alone.
- Preserve primary task order when columns collapse or navigation changes form.
- Check the narrowest supported viewport, intermediate widths, landscape orientation, text enlargement, browser zoom, and long localized content.
- A responsive design is not complete if a control is merely moved off-screen or hidden without an equivalent accessible path.
- If container queries are already part of the project architecture, review component behavior against its actual container rather than assuming the full viewport controls every layout decision.

## Fixed, sticky, and overlay UI

- Fixed or sticky headers, footers, action bars, and cookie/consent surfaces must not cover focused controls or required content.
- Account for mobile safe areas and on-screen keyboards when they can obscure form actions.
- Verify nested scrolling does not trap keyboard or touch users inside an unexpected region.
- Overlay layering should preserve one clear active interaction surface and predictable dismissal behavior.

## Data-heavy surfaces

For tables, dashboards, grids, and charts:

- Preserve labels, units, legends, and critical comparisons at narrow widths.
- Choose deliberately among column prioritization, wrapping, stacked summaries, local horizontal scroll, or alternate detail views.
- Do not convert tabular relationships into visually convenient cards if that destroys comparisons users need to make.
- Provide an accessible summary or data alternative when a chart alone cannot communicate the decision-relevant information.

## Motion and responsive state

- Layout changes should not create unnecessary motion or spatial disorientation.
- Respect reduced-motion preferences when transitions or animated reflow are part of the experience.
- Loading skeletons, drawers, accordions, and responsive navigation must preserve focus and state when viewport conditions change.

## Review evidence

A static source review may return `STATIC_UI_RISK_LOW`, `STATIC_UI_RISK_DETECTED`, or `STATIC_UI_RESULT_INCONCLUSIVE` according to Cloak's existing contract. Rendered correctness still requires current visual evidence.

## Primary references

- CSS Grid Layout: https://www.w3.org/TR/css-grid-2/
- CSS Flexible Box Layout: https://www.w3.org/TR/css-flexbox-1/
- CSS Overflow: https://www.w3.org/TR/css-overflow-3/
- WCAG 2.2 reflow and focus requirements: https://www.w3.org/TR/WCAG22/