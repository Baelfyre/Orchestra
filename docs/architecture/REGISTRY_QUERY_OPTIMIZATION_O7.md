# O7 — Optimized Registry Consumption

## Status

`O7_0_CONTRACT_FROZEN_RUNTIME_NOT_IMPLEMENTED`

O7 is the approved Orchestra consumer phase for the Registry R7 token-efficient read architecture. O7.0 now freezes Orchestra's consumer-side expectations without implementing R7 capabilities or changing the current O1-O6 runtime path. Registry R7 remains `APPROVED_PLANNED_NOT_IMPLEMENTED`, so O7.1+ must remain blocked until the frozen entry condition `IMPLEMENTED_STABLE_REGISTRY_R7_SURFACE_REQUIRED` is satisfied.

The machine-readable O7.0 contract is [`docs/architecture/contracts/registry-o7-consumer-contract.v1.json`](contracts/registry-o7-consumer-contract.v1.json), validated by [`docs/architecture/contracts/registry-o7-consumer-contract.schema.json`](contracts/registry-o7-consumer-contract.schema.json) and `tests/runtime/test_registry_o7_consumer_contract.py`.

## O7.0 reviewed Registry anchor

The consumer freeze is bound to the signed Registry R7 architecture currently reviewed on `Baelfyre/Orchestra-Compliance-Registry`:

- canonical branch: `main`;
- reviewed commit: `c1910806ed3ea9147af96b1c49a9f72aef75e0f6`;
- reviewed tree: `0c37d7bf47fc20b49b26fea156c8e180db57b4a3`;
- R7 architecture path: `docs/TOKEN_EFFICIENT_QUERY_ARCHITECTURE_R7.md`;
- reviewed R7 document blob: `9f24a10f455a77509ec5246e6981ca2672624ca1`;
- reviewed R7 status: `APPROVED_PLANNED_NOT_IMPLEMENTED`;
- planned Registry feature release boundary: `registry-v0.4.0`.

These identities freeze what Orchestra reviewed. They do not claim that R7 runtime implementation exists, authorize Registry mutation, or make the planned release current.

## Objective

Allow Orchestra to consume the smallest sufficient Registry context through an optional indexed/projection-aware path while preserving all existing O1-O6 compliance semantics, receipts, authority boundaries, and fail-closed behavior.

## Compatibility boundary

O7 is additive. Orchestra continues to require `cap.query.v1` with a consumer minimum contract version of `1.0.0`. R7 optimization capabilities remain optional so their absence cannot break the current O1-O6 direct query path.

O7.0 freezes the following Orchestra-owned minimum acceptance floors at `1.0.0`:

- `cap.query.projection.v1`
- `cap.query.relationships.v1`
- `cap.query.indexed-read.v1`
- `cap.query.budget.v1`
- `cap.transport.mcp.v1`

The `1.0.0` values are Orchestra consumer floors for future negotiation. They are not claims that Registry currently publishes or implements those capabilities.

Optional capability absence disposition: `USE_CURRENT_O1_O6_PATH`.

Required capability incompatibility disposition: `FAIL_CLOSED`.

## Architecture

```text
verified Registry release
        |
        +--> R7 direct local indexed gateway  <-- preferred when available and verified
        |
        +--> existing direct JSON query       <-- deterministic fallback
        |
        `--> optional MCP transport           <-- external host/IDE path
                    |
                    v
          normalized Registry result
                    |
                    v
          ComplianceQueryReceipt
                    |
          Governor -> Steward -> Arbiter
```

MCP is not Orchestra's required internal transport. Direct local deterministic access is preferred for Orchestra; MCP primarily serves external MCP-capable IDEs, hosts, and agents.

## Frozen transport contract

O7.0 freezes this precedence:

1. `DIRECT_LOCAL_INDEXED_GATEWAY` when the future R7 index is available and verified;
2. `DIRECT_LOCAL_JSON_QUERY` as the deterministic local fallback;
3. `OPTIONAL_MCP_TRANSPORT` when explicitly selected or used by an external MCP-capable consumer.

Fallback rules:

- indexed gateway unavailable -> `DIRECT_LOCAL_JSON_QUERY`;
- MCP unavailable -> `DIRECT_LOCAL_QUERY`;
- transport choice cannot expand authority;
- MCP remains optional for Orchestra internal consumption.

## Frozen projection contract

Allowed R7 projection names are frozen as:

- `MINIMAL`
- `SUMMARY`
- `EVIDENCE`
- `FULL`

Workflow defaults are frozen as:

- Conductor discovery -> `MINIMAL`;
- Governor applicability/review -> `SUMMARY` or `EVIDENCE`;
- Steward requirements/traceability -> `EVIDENCE`;
- explicit audit escalation -> `FULL`.

Projection selection changes payload size only. It may not change source identity, obligation identity, freshness meaning, applicability ownership, governance meaning, or authority.

## Frozen receipt normalization

Every future O7 transport and projection must normalize into the existing `ComplianceQueryReceipt` evidence model and preserve:

- Registry repository identity;
- Registry version;
- release sequence;
- release tag;
- release-manifest digest;
- query digest;
- exact source IDs;
- exact obligation IDs;
- freshness evidence;
- capability-negotiation evidence;
- domain-routing evidence.

Governor, Steward, and Arbiter continue using the existing exact-set and freshness contracts. Receipt normalization cannot create authority expansion.

## Frozen integrity semantics

- index identity or digest mismatch -> `REJECT_INDEX_REBUILD_OR_FALLBACK`;
- semantic query mismatch -> `FAIL_CLOSED`;
- required capability incompatibility -> `FAIL_CLOSED`;
- optional capability absence -> `USE_CURRENT_O1_O6_PATH`;
- model-authored integrity repair -> prohibited.

No model-authored repair may override an integrity or semantic mismatch.

## Frozen context-budget integration

Registry projection selection remains subordinate to Orchestra's existing communication/context budget. It does not create an independent budget authority.

Conceptually:

```text
workflow need
   -> evidence/detail requirement
   -> existing Orchestra context budget
   -> bounded future R7 projection
   -> normalized receipt
```

`maximum_context_bytes` is treated as a bounded input when the future R7 surface supports it. TOON selection and token/workflow savings claims require measured evidence rather than design intent.

## Phase plan

### O7.0 — Consumer contract freeze

`COMPLETE_AS_CONTRACT_FREEZE_RUNTIME_NOT_IMPLEMENTED`

Frozen by the machine-readable contract and deterministic tests described above. O7.0 creates no R7 runtime capability, no new Registry transport implementation, and no execution authority.

### O7.1 — Optional capability negotiation

`BLOCKED_PENDING_IMPLEMENTED_STABLE_REGISTRY_R7_SURFACE`

Extend the existing O1 capability negotiation surface to recognize the R7 capabilities as optional. Their absence must not break the current O1-O6 path.

### O7.2 — Transport abstraction

Preferred order:

1. direct local indexed Registry gateway;
2. direct local JSON query;
3. optional MCP transport when the consumer is external or MCP is explicitly selected.

Transport selection cannot expand authority or alter Registry semantics.

### O7.3 — Projection-aware consumption

Request only the smallest sufficient projection for each workflow stage using the frozen projection contract.

Projection choice changes payload size, not source/obligation identity or governance meaning.

### O7.4 — Existing receipt normalization

Every transport and projection must normalize into the existing compliance evidence model using the frozen receipt identity set.

Governor, Steward, and Arbiter continue using the existing set-equality and evidence-freshness contracts.

### O7.5 — Deterministic failover

Apply the frozen failover and integrity dispositions. No model-authored repair may override an integrity or semantic mismatch.

### O7.6 — Context-budget integration

Bind Registry projection selection to Orchestra's existing communication/context budget rather than creating a separate independent budget authority.

### O7.7 — Joint R7/O7 conformance

Establish semantic parity among direct JSON, indexed Registry query, MCP query, and Orchestra-normalized query for source IDs, obligation IDs, freshness, Registry identity, domain routing, and query/receipt semantics.

Payload representations may differ in size; compliance meaning and exact canonical identities may not.

## Frozen O1-O6 invariants

O7 does not replace or weaken:

- O1 capability negotiation;
- O2 compatibility/fail-closed behavior;
- O3 deterministic query selection semantics;
- O4 query-scoped freshness;
- O5 release-delta impact analysis;
- O6 governed domain-to-specialist routing;
- Conductor's exclusive routing role;
- Governor applicability ownership;
- Steward requirements/traceability ownership;
- Arbiter exact-state and set-equality enforcement.

## O7.1+ entry gate

O7.1+ runtime implementation is not authorized by O7.0. It must remain blocked until an implemented stable Registry R7 surface exists and can be verified against the frozen consumer contract.

The frozen gate token is:

`IMPLEMENTED_STABLE_REGISTRY_R7_SURFACE_REQUIRED`

A future trusted immutable Registry release is additionally required before release integration. Contract validation, Registry capability presence, transport availability, mergeability, or a green CI result does not independently grant runtime, merge, release, deployment, or policy authority.

## Completion gate

O7 is complete only when:

- current O1-O6 tests remain green;
- existing direct-query fallback remains compatible;
- R7 capability negotiation is deterministic;
- direct/indexed/MCP semantic parity passes;
- existing compliance receipts remain authoritative for downstream workflow state;
- integrity mismatch fails closed;
- context-budget behavior is bounded and deterministic;
- token/workflow savings are measured rather than assumed.

## Planned release boundary

O7 is intended for an Orchestra release after Registry R7 is completed and published as an immutable trusted release. The current planning target is Orchestra `v1.8.0`; release selection remains subject to the normal governed release closeout.

## Dependency

Registry R7 owns the entity/read model, derived index, projections, query gateway, and MCP adapter. Orchestra must not duplicate those query semantics. See `docs/TOKEN_EFFICIENT_QUERY_ARCHITECTURE_R7.md` in `Baelfyre/Orchestra-Compliance-Registry`.
