# Issue #937 R2B Finding Contract Design

**Status:** DRAFT_FOR_SPECIALIST_REVIEW. This is a non-authorizing design note, not an accepted runtime contract.

Remote-state observations below were refreshed on 2026-10-20. No content in this document changes the frozen PR #977 branch.

## Baseline evidence

- Repository baseline: `b215a48b678e8708a8a6e7123f5ee1893d3f4f15`, tree `fac2140e41e81bdf243ddc6c389b38c0453ad28c`.
- R2A is present in `origin/main` through merged PR #976. PR #977 is still an open draft at `ec0c99dd634dc98588b722d07dc2badf63865122`; its source branch is frozen and is not changed here.
- Main's `SpecialistReviewResult` serializes `findings` as strings and requires non-empty evidence references. Its tracked v1 JSON schema is strict (`additionalProperties: false`). `RoutingDisposition.NOT_REQUIRED` and `SpecialistReviewStatus` are separate enums.
- PR #977 changes the Python review result and digest to v2 with `runtime_identity_digest`, but its changed files do not include a v2 result schema. The v1 schema therefore does not describe that draft candidate's serialized result; this is recorded as a frozen-PR review gap and is not repaired here.
- `orchestra_runtime/domain/execution/operation_contracts.py::DEFENSIVE_SECURITY_REVIEW` defines the `NONE` / `REVIEW_ONLY`, non-mutating, non-authorizing, receipt-free operation; `_REGISTERED_ROUTES` binds `security-check/cipher` to it. `orchestra_runtime/services.py::GovernanceValidator.validate` admits the exception only for the exact host `OperationGovernanceContext`, rule, operation, route, and host profile. `machine/governance/policy.v1.json::high-risk-skill-approval` registers that narrow exception.
- The current result has no authorization field. The default MCP runtime remains route-only. No production read-only Cipher engine/provider with qualified host isolation was found.
- The registered defensive review operation is `NONE`, `REVIEW_ONLY`, non-mutating, non-authorizing, and receipt-free. The effectful Cipher route remains protected.

The original issue's client-asserted Boolean root cause is revised by current source: the registered read-only operation is host-classified and its validator exception is tied to trusted operation context. The remaining R2B gap is a production substantive assessment engine and qualified isolation, not permission to make the effectful route runnable.

## Proposed additive result shape

After Cipher and Clockwork accept the finding semantics and the v2 schema gap is resolved in an authorized candidate, a future result version may add `finding_records` while retaining the existing string `findings` field for old consumers. The following is an **abridged illustration**; existing identity fields such as `review_id`, `review_digest`, `request_id`, `request_digest`, `operation_id`, and `specialist` are omitted for readability:

```json
{
  "review_version": "orchestra.specialist-review-result.v3",
  "runtime_identity_digest": "<sha256>",
  "workspace_snapshot_digest": "<sha256>",
  "status": "FINDINGS",
  "conclusion": "A candidate security issue was found.",
  "findings": ["Inactive principal accepted"],
  "finding_records": [
    {
      "finding_id": "finding.<stable-id>",
      "title": "Inactive principal accepted",
      "description": "The authorization branch accepts an inactive principal.",
      "evidence_refs": ["candidate:src/auth.py#L20-L24"]
    }
  ],
  "evidence_refs": ["candidate:src/auth.py#L20-L24"]
}
```

The sample is illustrative. The severity vocabulary and whether each finding must carry a severity are **NOT_FOUND** in the current specialist execution contract and require a Cipher decision. They must not be guessed in this draft.

Contract constraints for a future version:

1. Keep top-level `status`, `conclusion`, `findings`, and result identity fields available to existing consumers. For v3, derive each legacy string from its typed record title so the duplicate views cannot disagree.
2. Include every `finding_records` field in the result digest. Adding records to v2 without changing the version would invalidate digest semantics; use a new version.
3. Require unique non-empty finding IDs, non-empty titles/descriptions, and non-empty per-finding evidence references. Each reference must be present in the enclosing `evidence_refs` set and resolve through the immutable `ReadOnlyWorkspace`; the result digest must cover those references together with request, runtime, and workspace-snapshot identity. The example locator grammar remains unresolved and needs Cipher/Clockwork agreement.
4. A substantive `PASS` may have no finding records but still requires a non-empty conclusion and evidence. `FINDINGS` requires at least one typed record. `INCONCLUSIVE` and `BLOCKED` remain substantive outcomes, not successful review.
5. Keep `NOT_REQUIRED` solely in the routing-disposition contract. It is not a review status, a finding, or evidence that a specialist examined the candidate.
6. Keep result types and schemas free of authorization fields. Neither `PASS` nor a result digest can create `governance_validated`, a receipt, or a protected execution decision.
7. Preserve v2 runtime identity binding from PR #977 if that PR becomes canonical. Any later implementation must rebase its versioning and tests against the merged source, not mutate PR #977.

## Evidence locations and acceptance checks

- Current source: `orchestra_runtime/domain/execution/operation_contracts.py` (`RoutingDisposition`, `SpecialistReviewStatus`, `SpecialistReviewResult`, `DEFENSIVE_SECURITY_REVIEW`, `_REGISTERED_ROUTES`); `machine/schemas/specialist-review-result.v1.schema.json` (strict v1); `orchestra_runtime/services.py::GovernanceValidator.validate`; `orchestra_runtime/specialist_execution.py` (snapshot and result checks); `orchestra_runtime/interfaces.py` (read-only engine return type); and `orchestra_runtime/mcp_specialist_execution.py` (opt-in engine factory). The targeted search found no production JSON parser; refresh the consumer inventory before implementation.
- Snapshot boundary: `orchestra_runtime/specialist_execution.py::_repository_file_bytes` rejects symlink traversal. On R2B-2A commit `065fabff5b188117e1bf5270c5025d8f4ea58b0c` (tree `09635c9c8f7b0c738701ac33045ed0cce7d3d859`), `tests/runtime/test_specialist_snapshot_binding.py::test_candidate_snapshot_rejects_symbolic_link_traversal` passed for file and directory links with `python -m pytest tests/runtime/test_specialist_snapshot_binding.py::test_candidate_snapshot_rejects_symbolic_link_traversal -q` (2 passed, 2026-10-20). This is local regression evidence, not a production-engine qualification.
- Frozen PR #977: [PR #977](https://github.com/Baelfyre/Orchestra/pull/977), head `ec0c99dd634dc98588b722d07dc2badf63865122`, tree `c38482c126bc2616cf9fe0fb0879c268153671ab`, based on `b215a48b678e8708a8a6e7123f5ee1893d3f4f15`. As of 2026-10-20 it is an open draft; its v2 code adds runtime identity to the result digest, while its changed-file list does not add a v2 schema. This document reports that gap; it does not repair the frozen branch.
- Current specialist tool observations on 2026-10-20: Cipher returned `BLOCKED_PENDING_VALIDATION`; Conductor, Clockwork, Chronicler, and Overseer returned `NOT_REQUIRED` routing acknowledgements only. No substantive specialist assessment was returned.
- The current v1 schema is `machine/schemas/specialist-review-result.v1.schema.json`; the result type is exported by the domain package and used by the read-only execution interface/runtime and tests. No production JSON parser was found in the targeted search. Refresh this consumer inventory before implementation.
- A future implementation needs versioned-schema tests for v2 and v3 digest coverage, duplicate/missing IDs, missing per-finding evidence, candidate/runtime mismatch, `NOT_REQUIRED` rejection, no authority fields, and both empty-finding `PASS` and non-empty `FINDINGS` outcomes.
- Do not implement this proposal until the v2 schema gap is resolved in a separate authorized candidate, Cipher supplies the severity and evidence contract, and Clockwork confirms the serialization boundary. Satisfying those prerequisites does not itself grant implementation or authority to alter protected controls. Current specialist command responses were `NOT_REQUIRED` routing acknowledgements only; Cipher's command was `BLOCKED_PENDING_VALIDATION`.

## Remaining R2B-2A evidence gap

The host snapshot code rejects symbolic-link traversal. R2B-2A adds file-link and directory-link regression tests in its separate branch. These tests prove a snapshot boundary behavior only. They do not prove provider process isolation, a production Cipher engine, the default MCP route, or live specialist findings. Those remain `BLOCKED_MISSING_EVIDENCE` until a host-owned provider and isolation evidence exist.
