# GOV-937 Offline Provider-Boundary Qualification

**Result:** `PARTIAL_BLOCKED` while the new stacked draft PR and its exact-head CI are pending. The local offline synthetic provider contract passed its applicable adversarial and repository validation.

**Qualification limit:** this result covers a deterministic in-memory fake over synthetic snapshot bytes only. It does not qualify Cipher, a live model/provider, production data transfer, host isolation, or governance authority.

## Fresh baseline and gap matrix

At preflight on 2026-10-21, `origin/main` was commit `b215a48b678e8708a8a6e7123f5ee1893d3f4f15`, tree `fac2140e41e81bdf243ddc6c389b38c0453ad28c`. Issue #937 remained open and unchanged. PR #983 was an open draft based on `main`, head `4ee018a9e302bd212aa8e9f47af196cf6b2072f0`, tree `225610d117f2dabe4ed6d446716f13668eaefbe7`. Its 10 exact-head checks passed. This addendum records that later CI evidence without modifying PR #983 or its branch.

| Unit | Status | Current evidence |
| --- | --- | --- |
| R2A runtime identity | COMPLETE | Merged PR #976; server-generated MCP identity remains observational. |
| R2B read-only Cipher execution | PARTIAL | PRs #977–#979 remain separate open drafts; no production Cipher activation or host-qualified provider execution was added here. |
| R2C trusted receipt resolution/consumption | PARTIAL | PR #980 transaction tests and PR #982 review-result v2 remain separate open drafts; no production resolver, receipt consumption, or authority activation exists in this candidate. |
| Snapshot/provider boundary | PARTIAL before this candidate | PR #983 established a synthetic snapshot feasibility prototype, not an isolated provider or production integration. |

The default MCP builder remains route-only. Explicit specialist/provider execution builders exist separately and use constructor-owned engine configuration. This candidate does not connect the snapshot prototype to either production path. PR #982’s runtime-bound review-result v2 schema was inspected on its open branch and is absent from this stack base; it is not copied or changed here.

## Architecture decision

Extend the existing `internal/gov_937_snapshot_broker_prototype.py` harness. Reuse its `SnapshotEnvelope`, path allowlist, byte limits, candidate digests, and synthetic runtime-identity digest. The new intent binds one snapshot’s request, candidate, runtime digest, approved paths and file digests, payload size, read-only operation, purpose, `MOCK_ONLY` recipient, 60-second expiry, and single-use ID.

Only the internally constructed `InMemoryRecordingProvider` receives bytes. Its typed request contains the immutable snapshot identity and exact approved files. Its typed response is constrained to deterministic synthetic findings, test-only status, matching request/snapshot/runtime digests, and matching evidence hashes. Missing, malformed, expired, over-budget, cross-candidate, wrong-scope, or replayed intents fail before bytes reach the fake. The intent is a test fixture transfer gate, not human consent, a trusted receipt, or authority.

The prototype remains outside `orchestra_runtime`; no MCP schema, production provider, policy, whitelist, receipt resolver, runtime identity API, or review-result contract changed. The deterministic findings are not `SpecialistReviewResult` and cannot be consumed as approval. `NOT_REQUIRED` is rejected as a provider status.

## Validation evidence

The first focused post-edit attempt had one failing assertion because Windows asyncio emits a benign Proactor debug record. The test was corrected to check the intended security property. The final focused run passed.

| Command | Result |
| --- | --- |
| `python -m pytest tests/runtime/test_gov_937_snapshot_broker_prototype.py -q` | PASS, 55 passed. |
| `python -m pytest tests/runtime --cov=orchestra_runtime --cov-branch --cov-report=term-missing --cov-report=json:artifacts/runtime/coverage.json --junitxml=artifacts/runtime/runtime-junit.xml --cov-fail-under=0` | PASS, 3,628 passed; 97.61% statement and 95.0% branch coverage. |
| `python -m orchestra_runtime.test_evidence --coverage artifacts/runtime/coverage.json --junit artifacts/runtime/runtime-junit.xml --output artifacts/runtime/test-evidence.json --minimum-statement-coverage 97 --minimum-branch-coverage 95` | PASS, 3,628 concrete test cases, 0 failures/errors/skips. |
| `python scripts/validation/build_coverage_inventory.py --coverage artifacts/runtime/coverage.json --output artifacts/runtime/coverage-inventory.json --critical-statement-floor 98 --critical-branch-floor 95` | PASS, no critical coverage failures. |
| `python -m pytest tests/behavior -q -rs` | PASS, 636 passed, 1 skipped, 215 subtests passed. The skipped case requires a case-sensitive filesystem. |
| `python scripts/governance_check.py --strict` | PASS, 0 errors and 0 warnings. |
| `python scripts/validation/validate_architecture_boundaries.py` | PASS. |
| `python scripts/check_stale_references.py` | PASS, no stale/disallowed references. |
| `python tests/behavior/test_readme_impact.py` | PASS, 10 scenarios. |
| `python tests/behavior/test_readme_machine_index.py` | PASS, 18 index entries. |
| `python scripts/check_readme_impact.py` | SKIP, `workflow_dispatch` with no revision-transition event; only internal/test/validation evidence changed. |
| `python tests/behavior/run_tests.py` | NOT_RUN, `ORCHESTRA_APPROVED_BASE_SHA` was unset; no baseline was inferred. |
| `git diff --check` | PASS. |

## Adversarial coverage

The focused tests check byte-for-byte transfer of approved synthetic files; prompt text remains data; no unapproved file, filesystem root, tools, model/provider selection, MCP metadata, or authority field crosses the request contract; transfer denial leaves the recording fake empty; and request, candidate, runtime, path/digest, byte-budget, purpose, recipient, expiry, and replay mismatches fail closed. They also reject partial/untyped and authority-bearing responses, wrong digests/evidence, `NOT_REQUIRED`, timeout, cancellation, and provider exceptions without exposing synthetic secret markers in logs or errors. The default MCP security route remains blocked without a configured trusted execution engine.

## Evidence classes, risks, and next decision

- **Facts:** exact repository/PR identities and check results above were read from Git/GitHub during this task; local commands ran in the isolated stacked checkout.
- **Inference:** the original circular review/authorization topology remains the issue-level design defect. The new fake verifies an offline data-transfer contract only.
- **Assumption:** the fixture factory and test inputs are synthetic. No live-model/provider call, private AlteredEgo source read, or production data access occurred.
- **Risk:** this fake shares the Python process. `asyncio.wait_for` only cancels cooperative coroutines; it cannot terminate hostile CPU-bound code. No operating-system isolation is established.
- **Recommendation:** require a separately approved host, privacy/data-transfer, and isolation qualification before any live provider or Cipher work. Keep protected receipt resolver/consumption and exact-scope authority behind human governance.
- **Blocker:** the new stacked PR and exact-head hosted CI are not yet recorded in this pre-delivery report. Production Cipher execution and trusted receipt activation remain blocked.

Existing PRs #977–#983 remain unchanged. The only proposed changes are the internal prototype, its runtime test file, this addendum and machine record, and `CHANGELOG.md`. No merge, production activation, installed-runtime replacement, protected-governance mutation, live provider invocation, or AlteredEgo access occurred.
