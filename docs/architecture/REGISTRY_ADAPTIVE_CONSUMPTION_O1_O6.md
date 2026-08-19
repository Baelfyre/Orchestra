# Registry Adaptive Consumption O1-O6

## Status

Candidate implementation after the frozen Antigravity B3 closeout. This program does not reopen B3, merge Registry PR #23, publish a Registry release, promote A5, authorize A6, unblock B4, deploy, or grant Registry evidence any execution authority.

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

`tests/fixtures/compliance-registry/r5-capabilities.json` is an exact copy of the R5 candidate capability manifest used for the cross-repository interface test. Joint tests cover current v0.2 fallback, required/optional capability behavior, multi-jurisdiction selection, scoped freshness, breaking and compatible deltas, specialist resolution, unresolved domains, and authority-expansion rejection.
