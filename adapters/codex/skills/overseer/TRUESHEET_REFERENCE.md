# TrueSheet Reference for Overseer

Load this file only when designing validation for sheets/panels, keyboard/focus behavior, lifecycle events, navigation integration, platform divergence, mocks, mobile E2E flows, or migration/troubleshooting regressions.

Machine identity and ownership live in `../../machine/knowledge/truesheet-specialist-reference.v1.json`. External source: `lodev09/react-native-true-sheet` at `23e119c026e2040d960725bd260e6cd4bf680b95`, MIT. External test results are reference inputs only and never Orchestra validation evidence.

## Owned feature references

`TSF-004` `TSF-006` `TSF-007` `TSF-009` `TSF-015` `TSF-017` `TSF-018`

## Validation guidance

- Build a state matrix for presentation, dismissal, focus/blur, keyboard visibility, size/detent changes, navigation transitions, and stacked surfaces.
- Test focus restoration and keyboard paths separately from visual presentation. Include hardware keyboard and accessibility paths where the product supports them.
- Validate navigation-hosted panels across back actions, route replacement, unmount/remount, deep linking, and interrupted transitions where relevant.
- Keep native iOS, native Android, and web evidence separate when implementations differ. A pass on one platform does not prove another.
- Use consumer mocks to isolate application logic, but keep at least one integration path that exercises the real boundary owned by the downstream project.
- Use mobile E2E flows to validate user-observable behavior, not internal implementation details.
- Turn migration notes and historical troubleshooting themes into targeted regression hypotheses only after confirming the downstream stack/version is applicable.
- Preserve evidence identity: upstream passing tests or examples cannot satisfy Orchestra or downstream-project readiness gates.

## Boundaries

Overseer owns validation strategy and evidence quality, not feature implementation, architecture, or UI policy. Route implementation to Ponytail, architecture to Clockwork, and interaction/accessibility decisions to Cloak.
