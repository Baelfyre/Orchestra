# TrueSheet Reference for Ponytail

Load this file only for React Native sheet/panel implementation, navigation integration, Reanimated coordination, typed native interfaces, native/web implementation divergence, test mocks, or worked-example adaptation.

Machine identity and ownership live in `../../machine/knowledge/truesheet-specialist-reference.v1.json`. External source: `lodev09/react-native-true-sheet` at `23e119c026e2040d960725bd260e6cd4bf680b95`, MIT. This guide is paraphrased Orchestra-native guidance, not copied implementation.

## Owned feature references

`TSF-001` `TSF-002` `TSF-003` `TSF-004` `TSF-006` `TSF-007` `TSF-008` `TSF-009` `TSF-011` `TSF-012` `TSF-013` `TSF-015` `TSF-017` `TSF-018`

## Implementation guidance

- Prefer a small explicit control surface for present, dismiss, and state-change behavior. Keep control ownership obvious and avoid multiple competing command paths.
- Keep responsive presentation, scrolling, keyboard/focus, and lifecycle behavior driven by upstream Cloak requirements rather than hard-coded implementation taste.
- Treat navigation-hosted sheets as navigation participants with explicit mount/unmount, back behavior, focus restoration, and route-state ownership.
- When animation state crosses a React Native/Reanimated boundary, define which side owns source state and how events synchronize it. Avoid duplicate writable state.
- Keep public TypeScript contracts aligned with native method/event payloads. Platform-specific implementations may differ, but incompatible public semantics should be explicit.
- Isolate iOS, Android, and web differences behind deliberate platform boundaries instead of scattering conditionals through unrelated components.
- Use mocks and worked examples as design references for tests and integration shape, not as proof that Orchestra behavior is correct.
- Treat migration notes and troubleshooting recipes as version-scoped evidence. Verify current dependencies and platform versions before applying a workaround.

## Boundaries

Ponytail owns implementation, not UI policy, architecture authority, or validation readiness. Route interaction requirements to Cloak, architecture/native boundaries to Clockwork, and test strategy/readiness to Overseer. Do not vendor TrueSheet, add it as a knowledge-only runtime dependency, or copy its source implementation into Orchestra.
