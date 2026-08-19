# Registry Adaptive Consumption O1-O6

## Status

O1-O6 are canonical on Orchestra `main` from implementation merge `955a4b4918e28638a50e9564d1e3ea0127ae5f73` / tree `4cba8642eb63b38b283db67010e01f204c92780b`. Registry R1-R6 are also canonical and current-facing state is reconciled at `20eb859db153f17e24c052a13765e982d51cedbf` / tree `763be9062a0c23031c794403dc4592f5db4389b0`.

The cross-repository R5 capability interface was verified by exact Git blob identity: Registry `registry/capabilities.json` and Orchestra `tests/fixtures/compliance-registry/r5-capabilities.json` both use blob `978c1a6eecffe802df79e6d110a16b780ec6bd3f`. The immutable trusted Registry release remains `registry-v0.2.0`; it predates R1-R6 and is not changed or republished by this alignment.

This program does not reopen B3, promote A5, authorize A6, unblock B4, deploy, publish a Registry release, or grant Registry evidence any execution authority.

## Architecture

```text
verified Registry bundle
        |
        +-> explicit capability surface / v0.2 legacy profile
        |       -> O1 capability negotiation
        |       -> O2 fail-closed compatibility
        |
        +-> sources + obligations
        |       -> O3 multi-jurisdiction query selection
        |       -> exact consumed source/obligation sets
        |
        +-> source-status + review-due
        |       -> O4 query-scoped freshness
        |
R6 release delta
        -> O5 scoped impact classification
        -> O6 governed domain-to-specialist resolution
        -> Conductor remains exclusive router
```

## O1 Capability Negotiation

`orchestra_runtime/registry_adaptive.py` defines Orchestra's required and optional Registry capabilities. Required capability absence or incompatible major contract version fails closed. Optional absence is recorded without making the current trusted release unusable.

The Registry capability manifest is descriptive evidence. Orchestra rejects capability surfaces that attempt to grant legal, applicability, execution, merge, or release authority.

## O2 Registry v0.2 Compatibility

The immutable trusted `registry-v0.2.0` release predates R5. Orchestra therefore uses an explicit local compatibility profile only when the verified Registry version is exactly `0.2.0` and `registry/capabilities.json` is absent.

The profile exposes only the already-supported query surface. It is labeled `LEGACY_V0_2_COMPATIBILITY_PROFILE`; it does not pretend the Registry published R5 metadata. Missing R5 capabilities remain visible as optional capability gaps.

A future unknown Registry release with no capability manifest fails closed rather than inheriting the v0.2 exception.

## O3 Multi-Jurisdiction Query

`scripts/compliance_registry_adaptive.py query` accepts repeated `--jurisdiction`, `--provider`, and `--domain` arguments. Selection is deterministic and preserves obligation-to-source references. The returned source set is the set actually referenced by the selected obligations, plus an explicitly requested source when supplied.

The query also emits Orchestra's existing `ComplianceQueryReceipt`, binding the adaptive path back into the established Governor/Steward/Arbiter source and obligation set-equality protocol.

## O4 Query-Scoped Freshness

Freshness is calculated only over the sources consumed by the current query. A stale unrelated source cannot poison an unrelated query. A stale, overdue, or untracked required source produces `STALE` or `INCOMPLETE` and cannot be silently ignored.

Global Registry status remains available through the original client. Query-scoped freshness is additional bounded evidence, not a replacement for Registry integrity verification.

## O5 Release-Delta Impact Analysis

Orchestra consumes the closed R6 release-delta contract and independently verifies its stable digest and non-authorizing authority label. Dispositions map to:

| Registry delta disposition | Orchestra action |
| --- | --- |
| `UNCHANGED` | `NO_REVALIDATION` |
| `COMPATIBLE_SCOPED_CHANGE` | `SCOPED_REVALIDATION` |
| `REVALIDATION_REQUIRED` | `SCOPED_REVALIDATION` |
| `UNSUPPORTED_CAPABILITY_CHANGE` | `FULL_REVALIDATION_FAIL_CLOSED` |
| `HUMAN_REVIEW_REQUIRED` | `HUMAN_REVIEW_REQUIRED` |

Malformed, tampered, or authorizing deltas fail closed.

## O6 Dynamic Domain-to-Specialist Resolution

Registry domains map deterministically onto existing Orchestra specialists. This is route evidence only. It never creates agents, invokes specialists directly, or changes authority. Conductor remains the exclusive router under `ROUTING_MAP.md`.

Known compliance, security, persistence, architecture, lifecycle, AI, accessibility, and provider-policy domains have explicit mappings. Unknown domains return `HUMAN_ROUTING_REQUIRED` with no specialist selected automatically.

## Evidence Receipts

Every adaptive query emits a stable receipt binding:

- canonical Registry repository;
- verified Registry version, release sequence, tag, and manifest digest;
- exact query filters;
- sorted consumed source IDs;
- sorted consumed obligation IDs;
- capability-negotiation digest;
- query-scoped freshness digest;
- domain-routing digest;
- optional release-impact digest;
- `authority_expansion = false`.

This supplements, rather than replaces, the existing compliance query and consumption receipts.

## Joint Contract Fixture

`tests/fixtures/compliance-registry/r5-capabilities.json` is the exact R5 capability manifest used for the cross-repository interface test. Its Git blob is identical to canonical Registry `registry/capabilities.json` at the reconciled R1-R6 state. Joint tests cover current v0.2 fallback, required/optional capability behavior, multi-jurisdiction selection, scoped freshness, breaking and compatible deltas, specialist resolution, unresolved domains, and authority-expansion rejection.
