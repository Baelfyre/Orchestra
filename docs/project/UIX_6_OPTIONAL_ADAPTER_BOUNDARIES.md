# UIX-6 Optional UI Adapter Boundaries

Status: `UIX_6_OPTIONAL_ADAPTER_BOUNDARIES_IMPLEMENTED_NO_ADOPTION_PENDING_CANONICAL_VALIDATION`

Recorded: 2026-08-24

Entry baseline: `7d9c020a5fbd70b7270d86e24f8922928bc5613b`

## Purpose

UIX-6 audits the current host and adapter surfaces before considering optional UI evidence integrations. It prefers project-native evidence and keeps Figma, Code Connect, Storybook, Playwright, axe, and token tooling optional.

## Audit result

The repository currently provides library-neutral UIX contracts and read-only host/adapter certification surfaces. Codex and Antigravity are `SUPPORTED` hosts; Claude Code, Cursor, Windsurf, VS Code/VSCodium, JetBrains, Zed, and Neovim remain `SCAFFOLD_ONLY`. No external UI target, provider call, installed-integration refresh, or UI-tool dependency adoption was used for this audit.

The project-native design-token evidence boundary is available through the UIX-1 through UIX-4 contracts. The five external-tool candidate capabilities are unavailable optional evidence sources. Their absence is reported as an explicit evidence limitation, not silently filled with guessed data.

## Canonical machine surface

- Schema: `machine/schemas/optional-adapter-boundaries.schema.json`
- Capability audit: `machine/ui/optional-adapter-boundaries.v1.json`
- Invalid dependency fixture: `tests/fixtures/ui/uix6-invalid-dependency-adoption.json`
- Invalid authority fixture: `tests/fixtures/ui/uix6-invalid-authority-source.json`
- Deterministic validation: `tests/runtime/test_optional_adapter_boundaries.py`
- Host maturity source: `machine/hosts/update-contract.v1.json`
- Adapter compatibility source: `docs/setup/ADAPTER_SDK_PRAP.md`

Schema version: `orchestra.ui-optional-adapter-boundaries.v1`

## Terminal disposition

`NO_ADOPTION` is the canonical UIX-6 outcome. Implementing optional external-tool adapters would require separate dependency, host, license, security, and supply-chain authority. This phase therefore adds only the capability and adapter boundary contract; it does not install a dependency, create a home-grown Figma client, mutate Figma, refresh an installed integration, add runtime behavior, or make an external service authoritative.

Any later adapter proposal must pass the separate dependency and host authorization gate, preserve project-native fallback behavior, and expose evidence only. Host maturity and PRAP compatibility remain separate facts.
