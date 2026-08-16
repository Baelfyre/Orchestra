# Orchestra v1.5.0 Release Readiness Evidence

Status: `EVIDENCE_COMPLETE_SIGNED_CANONICALIZATION_PENDING`

Release theme: **Machine-Verifiable Control Plane and Murmurs**

Current public release: `v1.4.0`

Prepared package version: `1.5.0`

## Evidence identity

The release-confidence campaign was regenerated after the control-plane migration reached `LEGACY_RETIRED`, after the merge-readiness forward stabilization, and after Murmurs became canonical.

The fully validated content candidate is:

```text
source_head=8cf6a1e5c7ed6658642320d8a9b3219729c8f929
source_tree=fbefa531035bad9fa761f3d1431665fb03cf771e
base_main=b7e5ac26dacc00f63315446bff906e9f76b7b8b0
pr=312
```

This source head is intentionally not the final release commit. Adding this readiness record and the machine release index changes the source head. Therefore all evidence below establishes the release content baseline, while the final documentation-complete tree must receive a fresh full matrix, GitHub-signed materialization, protected canonical review, and independent post-merge verification before publication.

## Runtime and coverage evidence

Workflow run: `31935966476`

Artifact: `runtime-test-evidence-31935966476-1`

Artifact id: `9260653852`

Artifact digest:

```text
sha256:cbd621074927f8c17268c7af75b7996145669d12be99e4ab74418281630bdfb4
```

Exact result:

- runtime tests: **1,055 / 1,055 PASS**;
- failures: `0`;
- errors: `0`;
- skipped: `0`;
- statement coverage: **98.47%**;
- branch coverage: **95.36%**;
- global statement minimum: `95%` PASS;
- global branch minimum: `95%` PASS;
- critical control-plane statement floor: `98%` PASS;
- critical control-plane branch floor: `95%` PASS;
- `critical_ready=true`.

The same runtime evidence includes workflow-sanity, Murmurs integration, release-candidate trust-edge, and P9 shadow-conformance regressions. The direct matching P9 route fixture reports zero discrepancies, while negative fixtures verify that specialist, governance, validation, Arbiter, evidence, and stage-progression discrepancies fail closed.

## Coverage miss classification

Machine record:

`machine/release-evidence/v1.5.0-coverage-miss-disposition.json`

The measured inventory contains `109` missed statements and `110` missed branches. Every missed statement is explicitly classified. No coverage pragma, path omission, denominator reduction, or broad exclusion was introduced to manufacture the percentage.

```text
coverage_exclusion_applied=false
broad_coverage_pragmas_added=false
misses_remain_in_metric_denominator=true
unclassified_statement_misses=0
```

The largest retained debt cluster is noncritical legacy/rare coordination recovery and fallback behavior. The only critical uncovered statements are import-time machine/runtime parity traps plus the direct test-evidence CLI dispatch guard. Those lines remain in the denominator and are documented rather than artificially executed by corrupting authoritative load-time state.

Coverage is confidence evidence, not proof of correctness.

## Mutmut LEGACY_RETIRED evidence

Workflow run: `31935966484`

Artifact: `mutation-confidence-31935966484-1`

Artifact id: `9260682301`

Artifact digest:

```text
sha256:e7e3647ac3b83a203e70d04b933044980b73e88bd3af34c54e1683540783c35a
```

The evidence is `orchestra.mutation-evidence.v2`, classification `COMPLETE`, score status `VALID_CLASSIFIED_SCORE`.

- `models.py` retirement target: 4 classified mutants, 1 killed, 3 survived, 0 not checked;
- `services.py` retirement targets: 323 classified mutants, 226 killed, 97 survived, 0 not checked;
- no target-level interrupted, timeout, suspicious, skipped, or unknown result is accepted;
- `mutate_only_covered_lines=true`;
- no numeric mutation acceptance threshold is invented;
- survivors remain visible as confidence evidence.

## Integrated Cosmic Ray evidence

Workflow run: `31935966459`

Artifact: `cosmic-ray-confidence-31935966459-1`

Artifact id: `9260751199`

Artifact digest:

```text
sha256:98fad4a08b22d0eabafdb8327a2336e921a75cfd05f4d040cde65f2be45b9250
```

The artifact is `orchestra.cosmic-ray-evidence.v2` with `VALID_CLASSIFIED_SCORE`.

Raw bounded pilot:

- total: `700`;
- killed: `407`;
- survived: `293`;
- raw score: `58.14%`.

Conservative classification identifies `154` annotation-only/non-runtime mutants as excluded equivalent/non-runtime. Runtime-relevant result:

- total: `546`;
- killed: `407`;
- survived: `139`;
- runtime-relevant score: **74.54%**.

The workflow preserves raw and runtime-relevant denominators separately. Surviving runtime-relevant mutations remain visible; mutation score is not represented as proof of correctness.

## Cross-platform, security, and governance evidence

- Cross-platform Validation run `31935966452`: Windows PASS, Ubuntu PASS, macOS PASS.
- Governance Check run `31935966492`: PASS.
- Validate run `31935966476`: PASS.
- CodeQL on the exact candidate: PASS with no new alerts reported for code changed by PR #312.
- README Impact Gate: PASS after README and README.json were reconciled with the v1.5.0 candidate.
- Strict version parity: PASS across all 11 release surfaces at `1.5.0`.
- `PROJECT_CONTEXT.md` candidate version parity: PASS.

## Murmurs evidence boundary

Murmurs remains presentation-only and defaults to `NORMAL`. The controlled repository comparison exercises the same modeled task/outcome and records:

```text
NORMAL model_progress_calls=4
MURMURS model_progress_calls=0
execution_identity_equal=true
validation_identity_equal=true
governance_identity_equal=true
```

This is structural repository evidence, not billing-token evidence. Comparable live host input/output token counters are unavailable in this campaign, so token deltas remain unavailable and **no percentage token-saving claim is made**.

## SemVer decision

`1.5.0` is selected as a minor release from compatibility evidence:

- no public package surface is removed;
- no public command surface is removed;
- no specialist surface is removed;
- host maturity labels are unchanged;
- retained compatibility names are derived from canonical machine contracts rather than removed;
- Murmurs is additive and opt-in, with `NORMAL` remaining the default.

No evidence supports an intentional breaking public-contract transition requiring `2.0.0`.

## Governance and publication boundary

The following remain required after this evidence record is added:

1. run the complete validation matrix again on the documentation-complete exact head;
2. materialize that exact reviewed tree as a GitHub-verified signed commit on an isolated staging branch;
3. open a fresh protected canonical PR from the signed commit;
4. rerun the complete protected matrix on that exact signed head;
5. require zero unresolved review threads, strict up-to-date state, and fresh raw `mergeable=true, mergeable_state=clean`;
6. ordinary Squash merge with exact expected-head protection and no ruleset bypass;
7. independently verify canonical `main` parent, tree equivalence, commit signature, `LEGACY_RETIRED` state, package `1.5.0`, README/README.json parity, and absence of installed-integration mutation;
8. close #292 and #300 only when their exact exit criteria are satisfied;
9. publish `v1.5.0` only from that exact signed canonical commit and independently verify tag and GitHub Release identity.

MCP remains out of scope until `v1.5.0` is `PUBLISHED_VERIFIED`.

No marketplace publication, deployment, installed-integration refresh, ruleset bypass, branch deletion, force push, history rewrite, destructive cleanup, or MCP implementation is authorized by this evidence record.
