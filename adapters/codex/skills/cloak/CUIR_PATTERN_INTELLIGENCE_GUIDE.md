# Cloak CUIR-4 Pattern Intelligence Guide

Use this guide only when the active task needs design-pattern selection or comparison. Do not load the full CUIR corpus by default.

## Retrieval flow

1. Preserve project-native requirements, components, tokens, and assets as the primary design authority.
2. Classify the UI problem into at most three problem classes using `machine/knowledge/cloak-ui-pattern-intelligence-cuir4.v1.json`.
3. Retrieve only the matching normalized CUIR-3 categories from `machine/knowledge/cloak-ui-reference-cuir3.v1.json`.
4. Keep the selected pattern set at five patterns or fewer. Prefer matched category priority, then stronger evidence count, then stable pattern ID order.
5. Preserve each selected pattern's provenance and reuse classification. `REFERENCE_ONLY` means concept guidance only; do not copy source expression or assets.
6. For unknown or mixed tasks, use only the semantic accessibility baseline instead of loading broad corpus context.
7. Treat the result as advisory design intelligence. It grants no code implementation, architecture, security, merge, release, deployment, or policy authority.

## Rights and accessibility

- Project-native design requirements override external inspiration unless the project requirement itself is invalid or unsafe.
- General UI icons may use the catalog's notice-bearing treatment only when the applicable license obligations are preserved.
- Brand icons remain subject to separate brand/trademark rights review even when copyright reuse is permissive.
- Never promote generic click targets, placeholder-only labels, motion-only status, or unlabeled icon controls from reference implementations.

## Handoff

- Frontend implementation: Ponytail.
- Shared component or architecture decisions: Clockwork.
- Security-sensitive controls: Cipher.
- Readiness and evaluation gates: Overseer.

The deterministic helper `scripts/retrieve_cloak_patterns.py` mirrors this retrieval policy for validation and reproducible inspection. It does not make implementation decisions.
