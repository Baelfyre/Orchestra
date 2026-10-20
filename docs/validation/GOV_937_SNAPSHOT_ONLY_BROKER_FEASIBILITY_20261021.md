# GOV-937 Snapshot-Only Broker Feasibility

**Status:** synthetic prototype and local validation complete; strict staged governance, draft PR, and hosted exact-head checks are pending.

**Disposition:** `BROKER_SYNTHETIC_FEASIBILITY_PASS` applies only to the offline synthetic prototype after all S6 gates pass. It does not qualify Cipher, an inference provider, an installed host, or production data transfer.

## Scope and isolation

- Repository: `Baelfyre/Orchestra`.
- Fresh base: commit `b215a48b678e8708a8a6e7123f5ee1893d3f4f15`, tree `fac2140e41e81bdf243ddc6c389b38c0453ad28c`.
- Execution branch: `JEO/issue-937-snapshot-broker-feasibility`, created from that clean base in a fresh C: clone under `CodexWorktrees/orchestra-937-snapshot-broker`. The first isolated D: worktree exhausted its available disk space; that checkout and its unstaged files remain preserved. The dirty source checkout was preserved.
- Preview source identity was verified read-only at `d23fc66accc3f3a52a2ab494e8ce655b42ae57b5`, tree `5aa714e88c0f3e4739e564c4008b2974125cbe34`. This verifies source identity only, not installed-host parity.
- Issue #937 remains open. Draft PRs #977–#982 remain open and were not modified. Their observed heads are recorded in the companion machine record.
- No AlteredEgo source or private workspace data was read. No model, provider, network, MCP runtime engine, or external service was invoked by the prototype.

## S0: current source and root-cause review

The issue's design-level deadlock remains. Fresh `main` contains the bounded `defensive-security-review` contract and host-created read-only workspace snapshot code, but the policy exception is limited to the exact trusted review-only host profile. MCP's ordinary builder remains route-only; substantive execution requires a separate explicit engine builder. A test-only in-memory broker does not create that trusted host profile or satisfy protected execution.

Fresh `main` contains `specialist-review-result.v1`. The v2 schema is `NOT_FOUND` on `origin/main`; related evidence is PR #982, open draft at head `36aae532ba68cfe9614165527d3e1a32a868075e`. That proposal adds runtime-identity binding. This candidate leaves both review-result contracts unchanged and does not turn mock output into either contract.

PR #980 remains a separate draft covering atomic receipt lifecycle tests. It does not configure a production receipt resolver or activate consumption. PR #981 remains the separate governance decision packet and host qualification evidence. Its WSL/Bubblewrap outcome is `HOST_ARCHITECTURE_NOT_FIT`. PR #977 remains frozen. PRs #978 and #979 retain their separate symlink and typed-findings scope.

## S1: contract and bounds

The prototype is isolated in `internal/gov_937_snapshot_broker_prototype.py`, outside `orchestra_runtime` and unreferenced by runtime composition. Its host-created producer is pinned at construction to a marker-bearing synthetic fixture root. Its `build` call accepts only logical paths; it has no client root, filesystem handle, tool selector, or provider selector.

The host configuration binds a synthetic repository/base/head/tree identity, approved file digests, and a runtime-identity digest. The envelope records ordered paths, per-file SHA-256 values, a manifest digest, a content digest, request identity, snapshot digest, and `TEST_ONLY_NON_AUTHORIZING` mode. The candidate and runtime values in tests are synthetic fixtures, not production identities or R2A evidence.

Limits are four files, 4 KiB per file, 12 KiB total content, 50 ms for the asynchronous mock, and 2 KiB serialized output. Paths must be canonical NFC relative paths; case/Unicode normalization collisions, traversal, symlinks/reparse points, hardlinks, non-regular files, changed files, stale expected digests, binary/NUL content, unsupported UTF-8, and the explicit synthetic secret marker fail closed. File identity and metadata are checked before, during, and after descriptor reads. A deterministic in-memory digest check binds copied bytes to the fixture identity.

The mock receives only an immutable in-memory envelope containing bytes and digests. It has no filesystem root or filesystem API, shell, tool, MCP, provider, network, or live-model interface. The envelope carries logical review paths only. Its typed result is distinct from `SpecialistReviewResult`, labeled `TEST_ONLY`, bound to the request and snapshot, and contains no governance or receipt fields. Broker request replay, malformed output, invalid evidence, timeouts, cancellation, and engine errors return no assessment.

## S2: implementation boundary

The prototype is opt-in only in its test harness. There is no runtime import, MCP registration, route selection, prompt flag, client metadata field, receipt API, persistence, or provider adapter. A missing mock engine fails closed. The deterministic mock emits one synthetic finding only when the approved fixture contains the test marker; the finding text explicitly says it is not Cipher review.

## S3: synthetic adversarial qualification

Focused result: `34 passed` on the final run of `python -m pytest tests/runtime/test_gov_937_snapshot_broker_prototype.py -q`. The suite exercises allowlist inclusion/exclusion, traversal, symlink and hardlink denial, rename/edit/race rejection, path collisions, encoding/size/secret-marker rejection, candidate/runtime/request/manifest/content binding, replay, instruction-injection containment, no tool/provider route, malformed output/evidence/authority fields, timeout/cancellation/exception handling, and no fixture writes. The route-only MCP builder rejects `security-check` when no trusted execution engine is configured.

The first focused attempt had 10 failing cases. Inspection showed Windows `fstat().st_ctime_ns` differs from path `lstat().st_ctime_ns`; the descriptor comparison now uses stable identity, mode, size, modification-time, link-count, and reparse metadata, while expected content digests still bind bytes. The first test version also incorrectly treated an empty typed finding list as a partial response. These issues were repaired, and the focused suite then passed with no skips.

## S4: compatibility and trust limits

The default route-only MCP behavior and protected governance policy are unchanged. Existing v1/v2 contracts, receipt code, and PR branches are unchanged. This is not an operating-system sandbox: Python code in the same process could use ambient capabilities even when this mock interface exposes none. The tests demonstrate the behavior of this fixed deterministic mock and the snapshot contract against synthetic temporary files; they do not prove isolation from a compromised producer, hostile engine implementation, host process, or provider.

Windows path metadata and symlink/hardlink checks passed in the current test environment. Filesystem guarantees vary by host and filesystem. The timeout cancels the cooperative mock coroutine; it cannot terminate arbitrary hostile in-process code. The runtime identity digest is a synthetic fixture value and is not connected to the current R2A startup identity. No protected receipt is created, resolved, validated, or consumed.

## S5: evidence and decisions

The companion JSON records the exact baseline, source/test digests, S0–S6 outcomes, adversarial probes, and validation state. The changelog records the non-production candidate. `README.json` and public README were not changed because the new module is test-only research under `internal/`; it is not a runtime, machine contract, install surface, or product capability.

Before any live provider or Cipher work, a separate human decision must authorize the exact host/runtime and data-transfer boundary, privacy/data-handling review, actual provider adapter and transport validation, substantive Cipher review criteria, and trusted receipt resolver/context/consumption lifecycle. Current tests, this feasibility result, the preview source, and passing CI create none of that authority.

## S6: validation and delivery

Local validation in the clean C: clone:

- `python -m pytest tests/runtime/test_gov_937_snapshot_broker_prototype.py -q`: **34 passed**.
- `python -m pytest tests/runtime -q`: **3607 passed, 36 subtests passed**.
- `python -m pytest tests/behavior -q -rs`: **636 passed, 1 skipped, 215 subtests passed**. The skipped case requires a case-sensitive filesystem.
- `python scripts/validation/validate_architecture_boundaries.py`: **PASS**.
- `python scripts/check_stale_references.py`: **PASS**, no stale or disallowed references found.
- `python tests/behavior/run_tests.py`: **NOT RUN** because `ORCHESTRA_APPROVED_BASE_SHA` is unset; no baseline was inferred.
- The README impact helper returned **SKIP** because this local invocation had no revision-transition event; no README file changed.

`git diff --cached --check`, `python scripts/governance_check.py --strict` (Stage 1 strict deterministic gates: 0 errors, 0 warnings), and `python scripts/check_stale_references.py` passed. `python scripts/check_readme_impact.py` returned `SKIP event=workflow_dispatch reason=no_revision_transition` because the local run had no PR revision transition; no README changed.

Implementation commit `b4d98a33bc0a7cdd9d77f2c3f7374bddd949293a` was created. Post-commit focused tests passed (**34 passed**), strict governance passed (**0 errors, 0 warnings**), architecture boundaries passed, and `git show --check --oneline HEAD` passed with a clean worktree.

An evidence-only follow-up commit will record these post-commit results. Push, draft PR, and exact-head hosted CI remain pending. No merge, production activation, installed-runtime refresh, or governance mutation is authorized.
