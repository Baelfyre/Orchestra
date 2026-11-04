<!-- @codebase_provenance_JEO -->
<!-- @codebase_rights_JEO -->

# GOV-937 continuation addendum: 2026-10-20

**Disposition:** `REQUEST_MORE_EVIDENCE`
**Authority effect:** None. This addendum is not a human decision, authorization receipt, exception, or permission to execute protected operations.
**Original packet:** `GOV-937-escalation-packet-2026-10-20.json` remains unchanged.

## Fresh state

- Orchestra `origin/main`: `b215a48b678e8708a8a6e7123f5ee1893d3f4f15`, tree `fac2140e41e81bdf243ddc6c389b38c0453ad28c`.
- Issue #937 remains open. The issue's earlier reproduction baseline predates current main; current main and implementation evidence take precedence.
- PR #976 is merged at `b215a48b678e8708a8a6e7123f5ee1893d3f4f15` and completes R2A runtime identity.
- Frozen draft PR #977 remains open at `ec0c99dd634dc98588b722d07dc2badf63865122`; its branch and files were not modified.
- PRs #978–#982 remain open drafts at the heads below. No review submissions were present on #977–#981. PR #982 has only a Copilot quota notice, not an approval or substantive review.

| PR | Exact head | validate | Governance Check | Required Analysis | Cross-platform |
| --- | --- | --- | --- | --- | --- |
| #977 | `ec0c99dd634dc98588b722d07dc2badf63865122` | 39377627106 PASS | 39377627250 PASS | 39377627137 PASS | 39377627307 PASS |
| #978 | `ba17689192309bca5819fd72a90ed04feec1dbf8` | 39416703035 PASS | 39416703062 PASS | 39416703037 PASS | 39416702973 PASS |
| #979 | `8094d36607bdeee8c7badc8aee3bdb27da8f7a35` | 39416716145 PASS | 39416716070 PASS | 39416716104 PASS | 39416716068 PASS |
| #980 | `6573353cf84efaa1b11107418843f8cb9776be18` | 39416721076 PASS | 39416721109 PASS | 39416721154 PASS | 39416721146 PASS |
| #981 | `19501f4c0b84a21ce845002d2e177fbb45dc53b9` | 39416726659 PASS | 39416726753 PASS | 39416726815 PASS | 39416726741 PASS |
| #982 | `36aae532ba68cfe9614165527d3e1a32a868075e` | 39442048656 PASS | 39442048902 PASS | 39442049040 PASS | 39442048666 PASS |

The original Stage 1 failures on #978–#981 were missing focused `CHANGELOG.md` entries for their significant test or packet paths. Those entries were added on the respective branches; no governance threshold, rule, or validator was relaxed. PR #982's initial README impact failure was a missing `README.json` index entry for the new v2 schema; the entry is present on its current head. All listed checks are now green on the listed exact heads. Each hosted Cross-platform Validation run passed on Ubuntu, macOS, and Windows. This table is separate-PR CI evidence, not CI for the local integration candidate below.

## R2A/R2B/R2C evidence update

| Unit | Status | Current evidence and limit |
| --- | --- | --- |
| R2A runtime identity | COMPLETE | Merged PR #976 exposes server-generated, observational runtime identity. It does not grant authority. |
| R2B read-only Cipher | PARTIAL; host qualification blocked | PR #977 binds an opt-in defensive review result to runtime identity and host-computed candidate snapshot. PR #978 adds symlink traversal regression coverage; PR #979 prevents `NOT_REQUIRED` routing from counting as substantive review. PR #982 supplies the strict v2 result schema. No concrete production `IReadOnlySpecialistExecutionEngine` or qualified host isolation implementation was found in the current runtime tree. The live MCP `security-check` call returned `BLOCKED_PENDING_VALIDATION`; it produced no Cipher findings. |
| R2C trusted receipt path | PARTIAL; production wiring NOT_FOUND | PR #980 is synthetic SQLite lifecycle evidence only. Current runtime has receipt domain contracts, ports, and a verifier use case, but no production store, context-provider implementation, independent human-authority source, or MCP receipt-reference consumer was found. |

### Combined #977 + #982 validation

A temporary, unpushed integration branch `JEO/issue-937-977-982-integration-20261020` combined the exact PR heads without changing either source branch. The integration commit is `be77469748dd97c4a66e34f3e8ded8c742829223`, tree `c5027b1a7fa6889aa3b0504e0cf4eeac873bdd01`. The only merge conflict was the changelog header; the resolution retained both PR entries.

An actual local MCP response produced through the opt-in read-only route validated against `specialist-review-result.v2.schema.json`. Its review digest matched the serialized findings, its runtime digest matched server-generated MCP runtime identity, and its workspace digest matched the host-computed candidate snapshot. A tampered snapshot changed the digest. The engine and workspace provider in this check were synthetic test fixtures. This proves serialization/schema compatibility and digest binding in the combined candidate, not production execution or host isolation.

The exact full runtime command on that integration commit completed with **3,581 passed, 0 failed, 0 skipped** in 530.83 seconds:

```text
python -m pytest tests/runtime --cov=orchestra_runtime --cov-branch --cov-report=term-missing --cov-report=json:artifacts/runtime/coverage.json --junitxml=artifacts/runtime/runtime-junit.xml --cov-fail-under=0
python -m orchestra_runtime.test_evidence --coverage artifacts/runtime/coverage.json --junit artifacts/runtime/runtime-junit.xml --output artifacts/runtime/test-evidence.json --minimum-statement-coverage 97 --minimum-branch-coverage 95
python scripts/validation/validate_architecture_boundaries.py
python scripts/governance_check.py --strict
python tests/behavior/test_readme_machine_index.py
python tests/behavior/test_readme_impact.py
git diff --check origin/main...HEAD
```

Machine evidence passed at 97.62% statement and 95.00% branch coverage. Architecture boundaries, strict governance, README machine index, 10 documentation-impact scenarios, and `git diff --check` passed. `python tests/behavior/run_tests.py` stopped before executing tests because no explicit approved `ORCHESTRA_APPROVED_BASE_SHA` or verified PR/push event baseline was available; no baseline was invented. The integration branch was not pushed and no hosted CI is claimed for it.

### Receipt transaction and human-authority boundary

PR #980's synthetic SQLite tests cover audit-write rollback, one concurrent single-use winner, replay denial, and persistence across fixture restart. They establish those properties for a test fixture only; they do not prove production database isolation, durability, or authorization.

In current runtime source, `VerifyGovernanceReceipt.execute` calls `consume_once` and then `record_audit` as separate store operations. The existing `test_audit_failure_denies_even_after_atomic_consumption` confirms fail-closed denial after an audit failure, but the valid single-use receipt may already be consumed and stranded. The production store transaction boundary that commits consumption and its required audit atomically is `NOT_FOUND`.

An independently controlled human-authority source, its issuer/identity verification, and its durable decision audit are also `NOT_FOUND` in the current Orchestra runtime. The closest evidence is the existing escalation packet's requirement for human review; that requirement is not itself a human decision or authority source.

## Threat model and human decisions

The implementation must continue to reject prompt, MCP argument, and arbitrary metadata claims of `governance_validated=true`; inline receipt JSON; unknown, forged, expired, consumed, cross-repository, cross-candidate, wrong-rule, wrong-operation, over-scoped, or wrong-context receipts; and routing acknowledgements presented as substantive findings. A production review engine would also need measured controls against file mutation, symlink/parent traversal, TOCTOU drift, network and child-process escape, privilege escalation, resource exhaustion, and unintended secret exposure. Current evidence does not qualify those host controls.

Before any production receipt wiring or host-engine activation, a human must decide:

1. **Authority source:** name the independently controlled human decision source, accountable authority, issuer/authentication method, provenance verification, and durable audit owner. Presently `NOT_FOUND`.
2. **Receipt transaction:** approve a store design whose single-use consume and required audit event commit atomically, with defined restart, concurrency, and failure behavior.
3. **Exact scope:** confirm required repository, candidate base/head/tree, protected rule, operation, target/scope, constraints, evidence digest, expiry, consumption, and fresh-context/non-transitive semantics.
4. **Host qualification:** identify one supported host engine/provider and return repeatable platform-specific isolation evidence before considering production read-only Cipher dispatch. Windows MCP currently blocks; Linux/macOS parity is unverified.
5. **Governance path:** decide whether future work can proceed under existing policy after ordinary authorized validation, or requires a separate protected-governance packet and fresh human decision. Any policy/validator change remains separately gated.

**Recommended present action:** keep protected execution and production receipt consumption blocked; request the missing source, store, and host-isolation evidence; then submit a new exact-candidate decision in a fresh context. Do not issue or consume an approval in this run. No reviewer `PASS`, human decision, or AlteredEgo Phase 2 authorization is claimed.

## AlteredEgo #7 read-only disposition

Issue #7 remains `BLOCKED_PENDING_VALIDATION` and says its evidence handoff is not an approval. Its named candidate remains head `e4b052625fb222facd63d8227b3c1d8eb1f590b5`, tree `32ad5ea6d1d7f3d2032ad14512d9e23d418eea00`. Only linked Issue #7 and a read-only main-ref identity were consulted; no local AlteredEgo checkout or files were opened or modified. No Phase 2 authorization is inferred.
