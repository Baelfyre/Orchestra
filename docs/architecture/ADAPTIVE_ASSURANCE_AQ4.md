# Adaptive assurance AQ-4: manifests and evidence receipts

AQ-4 is the deterministic evidence layer between the AQ-3 specialist routing
receipt and later phase-specific validation. It records what assurance is
required for one candidate and whether attributable evidence satisfies each
declared slot. It is descriptive and non-authorizing.

## Contract surface

The machine contract is
`machine/adaptive/aq4-assurance-manifests-receipts.v1.json`. Its two strict
JSON Schemas are `machine/schemas/assurance-manifest.v1.schema.json` and
`machine/schemas/evidence-receipt.v1.schema.json`. The pure runtime is
`orchestra_runtime/domain/adaptive/assurance_manifest.py`.

`build_assurance_manifest` consumes a qualified AQ-2 risk profile and an AQ-3
routing receipt. The resulting manifest binds:

- repository, source reference, candidate SHA, tree SHA, work item, and
  deterministic manifest digest;
- AQ-1 development mode, completion target, protected gates, and authority
  boundary;
- AQ-2 quality dimensions, risk characteristics, invariants, and risk
  fingerprint;
- AQ-3 selected canonical specialists and required assurance; and
- explicit evidence slots with required layer, scope, validator, source truth,
  provenance, risks, invariants, identity binding, freshness, and independence.

`build_evidence_receipt` and `validate_evidence_receipt` bind one observed
result to a manifest and, when supplied, its slot. Receipts accept only
`PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`. A passing command or test must
carry an exit code. A passing CI or workflow receipt must carry a workflow run
or job/check identity. A passing nonzero exit is rejected.

## Sufficiency and normalization

`reconcile_manifest_evidence` validates receipts, normalizes their order, and
counts only evidence that is fresh, source-bound, attributable, authoritative,
layer-sufficient, scope-sufficient, and within the slot declaration.

The reconciler is fail-closed for missing slots, weaker predecessor assurance,
wrong candidate or tree, stale evidence, broad coverage, lower evidence
layers, caller-authored authoritative provenance, and contradictory execution
records. Exact duplicate receipt IDs may normalize, but do not increase the
assurance count. Conflicting results for one logical execution, one gate/run,
or reuse of one logical execution as independent evidence are rejected.

The manifest and every receipt use canonical JSON digests. Input mappings are
strict: undeclared fields, invalid enum values, malformed identities, invalid
timestamps, and non-boolean binding flags fail closed. Schema validity alone is
not semantic validity; `validate_assurance_contract` checks the declarative
contract against the runtime constants.

## Authority and phase limits

AQ-4 follows the invariant:

`WORKFLOW_TOPOLOGY_CHANGE != AUTHORITY_EXPANSION`

Manifests and receipts do not dispatch specialists, execute tests, authorize a
transition, activate a provider, perform production work, persist or promote
state, sign material, merge, reconcile Padayon, or implement AQ-5/AQ-6 gate
enforcement. Evidence can establish a descriptive sufficiency result only.

AQ-1, AQ-2, and AQ-3 source and test paths remain read-only during AQ-4. A
candidate is not a phase completion claim until the separately governed phase
gate and exact-head review requirements pass.

## Validation

The AQ-4 runtime tests cover all required negative cases AQ4-N1 through
AQ4-N18, determinism, order invariance, assurance monotonicity, authority
non-expansion, identity monotonicity, contradiction monotonicity, and duplicate
normalization. The focused command is:

```text
python -B -m pytest -p no:cacheprovider tests/runtime/test_adaptive_assurance_aq4.py --cov=orchestra_runtime.domain.adaptive.assurance_manifest --cov-branch
```

The phase gate also requires the AQ1-AQ4 regression suite, schema validation,
contract/runtime parity, architecture-boundary validation, compile checks,
governance checks, and exact-head CI. Coverage targets are at least 97 percent
statement and 95 percent branch coverage for the AQ-4 runtime.
