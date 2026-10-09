# TrueSheet Reference for Cloak

Load this file only when reviewing bottom sheets, drawers, modal panels, mobile overlays, native/web presentation differences, keyboard/focus behavior, or related responsive interaction patterns.

Machine identity and ownership live in `../../machine/knowledge/truesheet-specialist-reference.v1.json`. External source: `lodev09/react-native-true-sheet` at `23e119c026e2040d960725bd260e6cd4bf680b95`, MIT. This guide is paraphrased Orchestra-native guidance, not external authority.

## Owned feature references

`TSF-001` `TSF-002` `TSF-003` `TSF-004` `TSF-005` `TSF-006` `TSF-009`

## Review guidance

- Treat sheet/panel presentation as a stateful interaction surface with explicit open, closed, focus, blur, resize/detent, and dismissal behavior.
- Define responsive presentation states instead of assuming one fixed height. Preserve content reachability when the viewport, safe area, keyboard, or content length changes.
- Separate scrollable content from fixed actions or chrome where that improves reachability and prevents critical actions from disappearing off-screen.
- Specify keyboard and focus recovery: initial focus, focus after presentation/dismissal, validation errors, hardware keyboard paths, and screen-reader continuity.
- Define backdrop/dimming and background-interaction semantics explicitly. A visually modal surface should not accidentally leave competing background controls operable.
- Review stacked surfaces for hierarchy, dismissal order, focus restoration, and one authoritative interaction path.
- Treat native and web implementations as potentially different interaction environments. Require equivalent user outcomes and accessibility, not identical implementation mechanics.

## Boundaries

Cloak owns interaction and accessibility requirements, not React Native implementation. Route implementation to Ponytail, architecture/platform boundaries to Clockwork, and readiness/testing to Overseer. Library-specific prop names, support matrices, bugs, and workarounds must remain scoped to the pinned external reference unless independently verified.
