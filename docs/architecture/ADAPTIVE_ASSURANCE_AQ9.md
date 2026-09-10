# ADAPT-QA AQ9: Deep Assurance Expansion

## Status and purpose

AQ9 deepens the existing deterministic assurance system after the AQ9 scope policy became canonical. It does not add a parallel QA engine, a new runtime authority, or any production behavior. The phase is evidence-only and uses the authority model `EVIDENCE_ONLY_NON_AUTHORIZING`.

AQ9 adds four explicit assurance families:

```text
MUTATION
PROPERTY
METAMORPHIC
BOUNDED_FUZZ
```

The goal is to challenge existing deterministic assurance logic from different directions while preserving the repository's current coverage, governance, provenance, signed-materialization, and fail-closed controls.

## Canonical input boundary

AQ9 begins from canonical Orchestra commit `1e1a0f18ebb144bed76bc2ec617d3a3913b1c041`, where the human-approved AQ9 assurance-scope policy is already canonical and post-merge verified.

The exact implementation inventory is fixed to nine paths:

1. `CHANGELOG.md`
2. `README.json`
3. `cosmic-ray.toml`
4. `docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md`
5. `machine/adaptive/aq9-deep-assurance.v1.json`
6. `machine/schemas/aq9-deep-assurance.v1.schema.json`
7. `scripts/validation/validate_aq9.py`
8. `tests/behavior/run_tests.py`
9. `tests/runtime/test_adaptive_assurance_aq9.py`

No production runtime module is added by AQ9.

## Mutation assurance

AQ9 preserves every existing Cosmic Ray target and adds `scripts/validation/classify_adaptive_assurance_scope.py` as an actual mutation target. The mutation test command retains the evidence, governance-kernel, and preexecution suites and adds the protected scope-policy regression plus the AQ9 deep-assurance runtime suite.

The existing scoreable-compatibility requirement is preserved. AQ9 does not lower or invent a mutation threshold merely to obtain PASS.

## Property assurance

The PROPERTY layer executes 64 deterministic cases over the canonical AQ9 scope classifier. It proves that exact AQ9 classification is invariant to path order, only the complete exact inventory receives the historical phase-separation result, removing any required AQ9 path revokes that result, unknown supersets remain fail-closed, and duplicate normalized paths are rejected.

## Metamorphic assurance

The METAMORPHIC layer executes 32 deterministic transformations. It checks that equivalent path permutations and slash normalization preserve the exact classification, while path removal or unknown-path addition revokes the exemption. Restoring the exact inventory restores only the approved phase-separation result.

## Bounded fuzz assurance

The BOUNDED_FUZZ layer uses fixed seed `20260911` and 256 bounded cases. It generates AQ9 anchor-bearing non-exact subsets and controlled unknown-path supersets with at most 12 generated paths. The oracle is narrow: any AQ9-identifiable scope that is not exactly the complete nine-path inventory must remain fail-closed `APPLICABLE` for historical PRAI, AQ5, and AQ7 classifiers.

The fixed seed makes failures reproducible. Unsafe or duplicate normalized path inputs remain rejection cases rather than being silently repaired.

## Machine contract and semantic parity

`machine/adaptive/aq9-deep-assurance.v1.json` is the canonical machine description of AQ9. Its JSON Schema validates structural shape, while `scripts/validation/validate_aq9.py` additionally enforces semantic parity across the exact inventory, assurance families and bounds, Cosmic Ray mutation targets and test surfaces, behavior-suite registration, README references, and non-authorizing authority boundary.

Schema validity alone is not sufficient. Semantic drift is fail-closed.

## Assurance truthfulness

AQ9 does not reinterpret one evidence family as another. Cosmic Ray proves mutation behavior only for configured targets. Property tests prove stated invariants only over their deterministic case space. Metamorphic tests prove declared relations only over bounded transformations. Bounded fuzzing provides reproducible adversarial sampling, not exhaustive proof. Cross-platform CI remains portability evidence and CodeQL remains static-analysis evidence.

No individual green check is treated as universal assurance.

## Authority boundary

AQ9 creates no execution, transition, whitelist, provider, telemetry, production, credential, deployment, or release authority. It cannot amend a protected policy that blocks its own progression and cannot lower assurance thresholds. If progression requires a protected governance change, the autonomous run terminates at that boundary for human review.

## Completion gate

AQ9 may be considered complete only after the exact source candidate is fully qualified, independently reviewed for scope and evidence truthfulness, protection-compliantly signed/materialized when required, promoted through a signed identical-tree carrier, and post-merge verified on canonical `main`.

Required identity invariant:

```text
QUALIFIED_SOURCE_TREE == SIGNED_MATERIALIZED_TREE == CANONICAL_TREE
```

Until those steps complete, AQ9 remains an implementation candidate rather than a canonical completion claim.
