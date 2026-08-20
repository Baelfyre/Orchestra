# O7 — Optimized Registry Consumption

## Status

`APPROVED_PLANNED_NOT_IMPLEMENTED`

O7 is the approved Orchestra consumer phase for the Registry R7 token-efficient read architecture. O7 must not begin runtime implementation until the current Codex baseline program and Orchestra v1.7.0 closeout are complete, and Registry R7 has a stable contract candidate.

## Objective

Allow Orchestra to consume the smallest sufficient Registry context through an optional indexed/projection-aware path while preserving all existing O1-O6 compliance semantics, receipts, authority boundaries, and fail-closed behavior.

## Compatibility boundary

O7 is additive. Orchestra continues to require `cap.query.v1`. R7 optimization capabilities remain optional so `registry-v0.3.0` and the current direct JSON query path continue to work.

Proposed optional capabilities:

- `cap.query.projection.v1`
- `cap.query.relationships.v1`
- `cap.query.indexed-read.v1`
- `cap.query.budget.v1`
- `cap.transport.mcp.v1`

## Architecture

```text
verified Registry release
        |
        +--> R7 direct local indexed gateway  <-- preferred when available
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

## Phase plan

### O7.0 — Consumer contract freeze

Freeze accepted R7 capability IDs, minimum versions, transport preferences, fallback behavior, receipt normalization, integrity failure semantics, and context-budget integration before runtime changes.

### O7.1 — Optional capability negotiation

Extend the existing O1 capability negotiation surface to recognize the R7 capabilities as optional. Their absence must not break the current O1-O6 path.

### O7.2 — Transport abstraction

Preferred order:

1. direct local indexed Registry gateway;
2. direct local JSON query;
3. optional MCP transport when the consumer is external or MCP is explicitly selected.

Transport selection cannot expand authority or alter Registry semantics.

### O7.3 — Projection-aware consumption

Request only the smallest sufficient projection for each workflow stage:

- Conductor discovery -> `MINIMAL`;
- Governor applicability/review -> `SUMMARY` or `EVIDENCE`;
- Steward requirements/traceability -> `EVIDENCE`;
- explicit audit escalation -> `FULL` only when required.

Projection choice changes payload size, not source/obligation identity or governance meaning.

### O7.4 — Existing receipt normalization

Every transport and projection must normalize into the existing compliance evidence model. Preserve exact Registry release identity, query digest, source IDs, obligation IDs, freshness evidence, capability negotiation, and domain-routing evidence.

Governor, Steward, and Arbiter continue using the existing set-equality and evidence-freshness contracts.

### O7.5 — Deterministic failover

- indexed gateway unavailable -> direct JSON fallback;
- MCP unavailable -> direct local query;
- optional capability absent -> current O3 path;
- index identity/digest mismatch -> reject index and rebuild or fall back;
- semantic query mismatch -> fail closed;
- required capability incompatibility -> fail closed.

No model-authored repair may override an integrity or semantic mismatch.

### O7.6 — Context-budget integration

Bind Registry projection selection to Orchestra's existing communication/context budget rather than creating a separate independent budget authority.

Conceptually:

```text
workflow need
   -> evidence/detail requirement
   -> available context budget
   -> R7 bounded projection
   -> normalized receipt
```

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

## Completion gate

O7 is complete only when:

- current O1-O6 tests remain green;
- Registry v0.3 fallback remains compatible;
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
