# Orchestra AR-2 Domain Context Extraction

## Status

`AR-2 DOMAIN/CONTEXT EXTRACTION CANDIDATE`

This record defines the first bounded `domain/context` extraction under the canonical runtime architecture refoundation plan. It is an implementation record for the current candidate only. Validation success does not create release, deployment, policy, provider-routing, destructive, or later-phase authority.

## Source baseline

- Repository: `Baelfyre/Orchestra`
- Canonical branch at extraction start: `main`
- Canonical baseline: `ffa9b6c7e06130e5c3dd03c8fc333c2c6cce1102`
- Canonical baseline tree: `3cb9523376c0411e3ef40b41cd87fe8ed6569847`
- Current phase: `AR-2 DOMAIN EXTRACTION`
- AR-3 started: `false`

## Bounded ownership moved inward

The candidate establishes `orchestra_runtime.domain.context` as the canonical owner of pure context-domain state and deterministic context compilation:

- `CurrentProjectState`
- `ContinuityEvent`
- `CONTEXT_STATE_SCHEMA_VERSION`
- `compile_context`

Canonical runtime paths:

- `orchestra_runtime/domain/context/state.py`
- `orchestra_runtime/domain/context/compiler.py`
- `orchestra_runtime/domain/context/__init__.py`

These modules depend only on Python standard-library value semantics plus the already-canonical inward-only `orchestra_runtime.shared.canonicalization` primitives.

## Compatibility boundary

Existing callers may continue importing the moved symbols from `orchestra_runtime.context_state`. The legacy module imports and re-exports the canonical domain symbols so object identity and existing call behavior remain stable during the strangler migration.

The following behavior deliberately remains on the legacy module in this increment:

- `JsonlContinuityStore`
- filesystem `Path` ownership
- JSONL file read/write behavior
- `render_state_markdown`
- `assert_markdown_parity`

This is intentional. Filesystem persistence belongs to the later infrastructure/persistence extraction, and Markdown projection should not be pulled into the domain layer merely to make the legacy module a syntactically pure facade.

## Dependency invariants

`orchestra_runtime.domain.context` must not import:

- `orchestra_runtime.application`
- `orchestra_runtime.infrastructure`
- `orchestra_runtime.entrypoints`
- flat legacy runtime modules
- repository `internal/`
- filesystem/network/process I/O modules prohibited by the runtime architecture policy

The existing machine architecture validator enforces these rules for all migrated domain files.

## Behavior preservation

The candidate preserves the established context-state contracts:

1. exact 40-character canonical Git SHA normalization;
2. deterministic sorting and duplicate rejection for stable state references;
3. canonical JSON validation for continuity event payloads;
4. stable state and event receipt digests;
5. strict continuity-event sequence and previous-digest semantics;
6. bounded L0-L3 progressive context compilation;
7. explicit L3 history requirement with no inferred history;
8. same-project history enforcement.

Legacy JSONL persistence and deterministic Markdown parity remain covered by the existing `tests/runtime/test_context_state.py` suite.

## New qualification coverage

`tests/runtime/test_domain_context.py` proves:

- legacy exports are the same canonical domain symbols;
- state normalization/digest behavior is preserved;
- L0-L3 context compilation remains behaviorally equivalent;
- L3 history remains explicit and fail closed;
- the legacy JSONL and Markdown surfaces continue to operate with the new domain entities.

## Explicit non-goals

This increment does not:

- move JSONL persistence into infrastructure;
- move Markdown rendering into an entrypoint/presentation package;
- extract `communication_budget.py`;
- extract `correlation.py`;
- move application use cases or repository ports;
- change provider or MCP behavior;
- change runtime authority semantics;
- start AR-3;
- publish or move a release/tag;
- deploy or mutate production;
- activate policy/rulesets;
- refresh installed integrations;
- delete branches;
- force push or rewrite history.

`communication_budget.py` remains outside this first slice because its current measurement type depends on the legacy presentation model. `correlation.py` remains outside this first slice because UUID generation currently owns clock and entropy acquisition. Those ownership seams require separate bounded treatment rather than being moved inward by path alone.

## Exit condition

This candidate may be canonicalized only after exact-head governance, architecture, runtime, required-analysis, and cross-platform qualification passes with no unresolved review blocker. Canonicalization of this slice does not itself start AR-3 or authorize v1.8 publication.
