# Offline Capability Coverage Foundation

## Purpose

The capability coverage foundation evaluates whether explicit task facets have matching capability declarations or evidence references. It is a pure domain operation: it performs no discovery, plugin invocation, provider access, persistence, memory writes, or routing and does not select a specialist or tool.

The evaluator is additive to `TaskProfile` v1, D2 v1, and existing routing contracts. Callers must provide the facet-to-capability mapping explicitly; this module does not infer capabilities from task prose or change those contracts.

## Inputs and result

`TaskCapabilityFacet` names a facet and its required capability identifiers. `CapabilityDeclaration` records an internal or external source's claim and references. Source kind is descriptive only and confers no priority. `TrustedCapabilityEvidence` represents evidence expected from a future trusted producer, separately from declarations.

For each required facet/capability pair, `evaluate_capability_coverage` returns one of:

- `DECLARED`: a source declares support without trusted verification evidence.
- `VERIFIED`: current supporting evidence was supplied through the trusted-producer input.
- `UNKNOWN`: evidence is explicitly unknown or trusted evidence freshness cannot be established.
- `MISSING`: no matching evidence exists, or evidence declares that the capability is unsupported.
- `STALE`: all matching evidence is expired.
- `CONFLICT`: non-stale evidence from the same `(source_kind, source_id)` contains both support and non-support claims. The disagreement remains unresolved. Different sources may make different claims without creating a conflict.

Claims are first evaluated per `(source_kind, source_id)`, then aggregated without selecting or prioritizing a source. Any within-source conflict keeps the aggregate `CONFLICT`, even if another source supports the capability. Otherwise, aggregate precedence is `VERIFIED`, `DECLARED`, `UNKNOWN`, `MISSING`, then `STALE`. Thus, a current negative claim remains `MISSING` when another source has only stale support; `STALE` applies when all matching evidence is expired. All evidence remains attached to the result. Evidence references and result items are sorted to make output independent of input ordering. Malformed identifiers, duplicate facets or records, unsupported claims, and invalid timestamps are rejected. Expired evidence remains visible in the result and cannot establish current verified coverage.

## Trust and integration boundary

The evaluator does not authenticate a `TrustedCapabilityEvidence` producer. Its type and `producer_id` are provenance fields, not cryptographic or host-verified proof. Only a future trusted composition boundary may supply that input after independently validating its producer and evidence. A caller-provided label or declaration cannot be promoted to verified evidence by this evaluator.

This foundation does not inspect host inventory, discover internal specialists or external plugins, invoke tools, resolve conflicting recommendations, admit specialists, or modify Conductor/AWF routing. Any later integration requires its own approved design and trusted producer contract.

## Validation

Focused synthetic tests cover declared and missing coverage, future trusted-producer input, unknown and stale evidence, cross-source disagreement, within-source conflicts, complementary coverage, malformed and duplicate records, and input-order invariance. Architecture boundaries and repository governance remain required for changes to this domain surface.
