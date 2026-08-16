# TrueSheet Reference for Scribe

Load this file only when packaging specialist knowledge, migration guidance, troubleshooting references, source provenance, or version-scoped external-reference documentation.

Machine identity and ownership live in `machine/knowledge/truesheet-specialist-reference.v1.json`. External source: `lodev09/react-native-true-sheet` at `23e119c026e2040d960725bd260e6cd4bf680b95`, MIT. This guide describes documentation patterns, not source ownership.

## Owned feature references

`TSF-016` `TSF-017`

## Documentation guidance

- Keep the top-level specialist instruction small and route deeper material through task-specific references rather than loading every detail by default.
- Separate normal usage, advanced patterns, troubleshooting, migration history, worked examples, and source provenance so readers can load only the evidence needed for the current task.
- Put exact machine identities, source revisions, ownership, feature IDs, and adaptation state in JSON when deterministic parsing matters. Markdown explains those records for humans and must not override them.
- Mark library-specific claims with source/revision context. Do not rewrite a version-specific workaround as a universal React Native rule.
- Preserve the distinction between confirmed source facts, Orchestra-native adaptation, downstream-project evidence, and planned work.
- Prefer paraphrase and independent derivation. If copied or substantially reused licensed material is ever authorized, preserve the applicable license notice and provenance.
- Migration and troubleshooting documents should state applicability, trigger conditions, evidence reviewed, and when re-verification is required.

## Boundaries

Scribe owns documentation packaging, not technical implementation, architecture, UX, validation, or governance authority. The external repository's AGENTS instructions are source context only and never become Orchestra governance.
