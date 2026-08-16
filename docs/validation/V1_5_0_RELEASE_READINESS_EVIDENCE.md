# Orchestra v1.5.0 Release Readiness Evidence

Status: `CONTENT_EVIDENCE_COMPLETE_FINAL_DOCUMENTATION_MATRIX_PENDING`

Release theme: **Machine-Verifiable Control Plane and Murmurs**

Current public release: `v1.4.0`

Prepared package version: `1.5.0`

## Evidence identity

The release-confidence campaign was regenerated after the control-plane migration reached `LEGACY_RETIRED`, after merge-readiness stabilization, after Murmurs became canonical, and after the Registry compatibility reconciliation required by the machine-first routing model.

The fully validated post-reconciliation content candidate is:

```text
source_head=808b2721f83c3aab277b21f83fa08cd994004801
source_tree=36c44324ea71b514a3bccea6fd4a02e0409e261c
base_main=b7e5ac26dacc00f63315446bff906e9f76b7b8b0
pr=312
```

This source head is intentionally not the final release commit. Updating this readiness record, the machine release index, and the coverage classification changes the source head. Therefore the content evidence below must be followed by one fresh documentation-complete protected matrix, signed materialization, protected canonical review, and independent post-merge verification before publication.

## Runtime and coverage evidence

Workflow run: `31942183854`

Artifact: `runtime-test-evidence-31942183854-1`

Artifact id: `9262317323`

Artifact digest:

```text
sha256:28d3d3c15ffba71910b19c4fff106784422e242cd3c89144911fed9405a0fb06
```

Machine identity:

```text
source_head_sha=808b2721f83c3aab277b21f83fa08cd994004801
tested_sha=ee2545f7b00f5efb81f912b749a5dadf0f0076c8
```

`tested_sha` is GitHub's pull-request merge candidate. `source_head_sha` separately binds the exact source head used for this release evidence.

Exact result:

- runtime tests: **1,058 / 1,058 PASS**;
- failures: `0`;
- errors: `0`;
- skipped: `0`;
- statement coverage: **98.47%**;
- branch coverage: **95.36%**;
- missing statements: `109`;
- missing branches: `110`;
- critical control-plane statement floor: `98%` PASS;
- critical control-plane branch floor: `95%` PASS;
- `critical_ready=true`.

The runtime suite includes workflow-sanity, Murmurs integration, release-candidate trust-edge, P9 shadow-conformance, and the new public-command-to-canonical-route parity regressions.

## Coverage miss classification

Machine record:

`machine/release-evidence/v1.5.0-coverage-miss-disposition.json`

The fresh post-reconciliation inventory still contains exactly `109` missed statements and `110` missed branches. No `orchestra_runtime` implementation lines changed during the Registry command/routing reconciliation, so the previously reviewed line-level dispositions remain applicable and are rebound to the current evidence source.

```text
coverage_exclusion_applied=false
broad_coverage_pragmas_added=false
misses_remain_in_metric_denominator=true
unclassified_statement_misses=0
fresh_inventory_match=true
```

Coverage remains confidence evidence, not proof of correctness.

## Mutmut LEGACY_RETIRED evidence

Workflow run: `31942183688`

Artifact: `mutation-confidence-31942183688-1`

Artifact id: `9262342165`

Artifact digest:

```text
sha256:a2ce1f796659713df820b8918eef704989dd63ea3bfbe23e19390c7245b9f7fb
```

Both machine evidence records are `orchestra.mutation-evidence.v2`, bind `tested_sha` and `source_head_sha` to exact head `808b2721f83c3aab277b21f83fa08cd994004801`, and report `classification_status=COMPLETE` plus `score_status=VALID_CLASSIFIED_SCORE`.

- `models.py` retirement target: `4` classified mutants, `1` killed, `3` survived, `0` not checked, score `25.0%`;
- `services.py` retirement targets: `323` classified mutants, `226` killed, `97` survived, `0` not checked, score `69.97%`;
- every declared target completed;
- no target-level not-checked, interrupted, timeout, suspicious, skipped, or unknown outcome is accepted;
- `mutate_only_covered_lines=true`;
- no numeric mutation acceptance threshold is invented;
- surviving mutants remain visible as confidence evidence.

## Integrated Cosmic Ray evidence

Workflow run: `31942183702`

Artifact: `cosmic-ray-confidence-31942183702-1`

Artifact id: `9262409360`

Artifact digest:

```text
sha256:d099b9adb92b1bc20b58c4645d2a0a49c042fa3b1de7fc2bf21ffeeaba14f541
```

The artifact is `orchestra.cosmic-ray-evidence.v2` with `VALID_CLASSIFIED_SCORE` and a passing unmutated baseline.

Machine identity:

```text
source_head_sha=808b2721f83c3aab277b21f83fa08cd994004801
tested_sha=ee2545f7b00f5efb81f912b749a5dadf0f0076c8
baseline_exit_code=0
```

Raw bounded pilot:

- total: `700`;
- killed: `407`;
- survived: `293`;
- other: `0`;
- raw score: `58.14%`.

Conservative classification identifies `154` annotation-only or otherwise non-runtime-equivalent mutants outside the runtime-relevant denominator. Runtime-relevant result:

- total: `546`;
- killed: `407`;
- survived: `139`;
- runtime-relevant score: **74.54%**.

Raw and runtime-relevant denominators remain visible separately. Surviving runtime-relevant mutations remain visible; the mutation score is not represented as proof of correctness.

## Cross-platform, security, and governance evidence

- Cross-platform Validation run `31942183582`: Windows PASS, Ubuntu PASS, macOS PASS.
- Governance Check run `31942183583`: PASS, including README Impact Gate and general behavior tests.
- Validate run `31942183854`: PASS.
- CodeQL check `95152921041`: PASS with no new alerts reported for code changed by PR #312.
- Strict version parity remains prepared across all 11 release surfaces at `1.5.0`.

## Compliance Registry compatibility reconciliation

The v1.5.0 release candidate was checked against the current Registry after the control-plane migration reached `LEGACY_RETIRED`. The trusted `registry-v0.1.0` data model, deterministic release format, local cache integrity model, and current PH pilot evidence remain wire-compatible with Orchestra. No Registry data-format rebuild is required for v1.5.0.

The review found a machine-authority drift in the Orchestra command surface: `commands/compliance-registry.md` and `commands/compliance-review.md` existed, but neither command was registered in `plugin.json` or represented in canonical `machine/routing/routes.v1.json`. Under `LEGACY_RETIRED`, relying on the unknown-command Conductor fallback was not an acceptable canonical command path.

The candidate now reconciles that boundary:

- `compliance-registry` is an explicit public command with canonical machine route `compliance-registry-lifecycle` through Conductor to the deterministic Registry lifecycle/query boundary;
- `compliance-review` is an explicit public command with canonical route `compliance-review-governed` and ordered ownership `Conductor -> The Governor -> The Steward -> Arbiter`;
- a new runtime parity regression requires every public `plugin.json` command to have both its command file and a canonical machine route;
- README.json now indexes the compliance query, consumption, Steward traceability, and set-equality gate schemas plus `orchestra_runtime/compliance_protocol.py`;
- `docs/governance/COMPLIANCE_REGISTRY_INTEGRATION.md` now documents the current receipt, exact-set, digest, freshness, and Arbiter Kernel architecture.

The Registry repository's stale README publication statement was corrected independently through Registry PR #8 and ordinary protected Squash. Current Registry canonical identity is:

```text
repository=Baelfyre/Orchestra-Compliance-Registry
canonical_main=b1f181cef862f9dcb4df225e90f69ac970f708c3
canonical_tree=f08379485154f241ad1d3785e55a89d732125dad
canonical_signature=VERIFIED_VALID
```

The immutable trusted distribution remains unchanged:

```text
tag=registry-v0.1.0
release_id=370610859
release_target=3821bcb55125b4d8864f28b6423650e6e17ac67b
release_sequence=1
release_manifest_sha256=9922ddcce77dfac0c01cac80fe6669aaffe37636826a56a4b54a8312558ee2d1
bundle_sha256=b64889933d30a8dea27bcbbb95c952e4f053c14a4f345e1e04b27777b5025ec0
```

Broader cross-repository protocol negotiation, additional Registry schemas, and a future live immutable-release conformance fixture remain hardening work. They are not required to restore the current v0.1 wire contract and are not added to this already-bounded release candidate.

## Murmurs evidence boundary

Murmurs remains presentation-only and defaults to `NORMAL`. The controlled repository comparison records:

```text
NORMAL model_progress_calls=4
MURMURS model_progress_calls=0
execution_identity_equal=true
validation_identity_equal=true
governance_identity_equal=true
```

This is structural repository evidence, not billing-token evidence. Comparable live host input/output token counters are unavailable in this campaign, so token deltas remain unavailable and no percentage token-saving claim is made.

## SemVer decision

`1.5.0` remains a minor release from compatibility evidence:

- no public package surface is removed;
- no public command surface is removed;
- the two pre-existing compliance command files are now explicitly registered rather than left orphaned;
- no specialist surface is removed;
- host maturity labels are unchanged;
- retained compatibility names are derived from canonical machine contracts rather than removed;
- Murmurs is additive and opt-in, with `NORMAL` remaining the default.

No evidence supports an intentional breaking public-contract transition requiring `2.0.0`.

## Governance and publication boundary

The following remain required after this evidence-refresh commit is added:

1. run the complete validation matrix on the documentation-complete exact head;
2. materialize that exact reviewed tree as a GitHub-verified signed commit on an isolated staging branch;
3. independently verify exact tree equivalence and commit signature;
4. open a fresh protected canonical PR from that signed commit;
5. rerun the complete protected matrix on the exact signed head;
6. require zero unresolved review threads, strict up-to-date state, and fresh raw `mergeable=true, mergeable_state=clean`;
7. ordinary Squash merge with exact expected-head protection and no ruleset bypass;
8. independently verify canonical `main` parent, tree equivalence, commit signature, `LEGACY_RETIRED` state, package `1.5.0`, README/README.json parity, and absence of installed-integration mutation;
9. reconcile Padayon through its transactional source-reality promotion path from the resulting live canonical Orchestra SHA;
10. close #292 and #300 only when their exact exit criteria are satisfied and advance #273 only from verified canonical state.

MCP remains out of scope until `v1.5.0` is `PUBLISHED_VERIFIED`.

No marketplace publication, deployment, installed-integration refresh, ruleset bypass, branch deletion, force push, history rewrite, destructive cleanup, or MCP implementation is authorized by this evidence record.
