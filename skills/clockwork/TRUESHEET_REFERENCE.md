# TrueSheet Reference for Clockwork

Load this file only for React Native native-component architecture, navigation/platform boundaries, Fabric/Codegen/TurboModule design, typed native contracts, iOS/Android host architecture, or shared native state.

Machine identity and ownership live in `../../machine/knowledge/truesheet-specialist-reference.v1.json`. External source: `lodev09/react-native-true-sheet` at `23e119c026e2040d960725bd260e6cd4bf680b95`, MIT. This guide adapts architecture patterns only.

## Owned feature references

`TSF-007` `TSF-008` `TSF-009` `TSF-010` `TSF-011` `TSF-012` `TSF-013` `TSF-014`

## Architecture guidance

- Separate public React/TypeScript contracts from platform host implementations and from generated/native interface specifications.
- Make navigation ownership explicit when a native presentation surface is also part of route state. Avoid two independent lifecycles controlling the same surface.
- Treat animation integration as a state-boundary problem: identify the authoritative state, event direction, and synchronization contract.
- Use Fabric/Codegen/TurboModule concepts as reference patterns for typed interface generation and native boundary reduction, not as mandatory architecture for unrelated projects.
- Keep TypeScript method and event shapes traceable to native interfaces; surface intentional platform capability differences instead of hiding them.
- Encapsulate iOS and Android presentation mechanics behind stable boundaries. Shared behavior belongs above platform-specific host code when semantics truly match.
- Shared C++ or shadow-node state is justified only when it reduces duplicated cross-platform state ownership. Do not introduce native complexity solely to mirror an external library.
- Native/web parity means equivalent governed outcomes, not identical components or lifecycle mechanics.

## Boundaries

Clockwork owns architecture review, not implementation or UX. Route implementation to Ponytail, interaction/accessibility requirements to Cloak, and validation evidence to Overseer. Do not generalize TrueSheet-specific native structures into Orchestra requirements without project evidence.
