# Governed Autonomy Modes Architecture and Overlap Assessment

## Status

```text
Assessment: COMPLETE
Phase: GA-0
Baseline: 8163c64838d369ea5c4abf45df36f6d6504db9fd
Architecture verdict: NO_DUPLICATE_AUTHORITY_MODEL
Runtime extension verdict: INSTRUCTION_LEVEL_SUFFICIENT_NO_RUNTIME_CHANGE
Target release: v1.2.0
Next phase: GA-1_CANONICAL_AUTONOMY_PROFILE_CONTRACT
```

## Purpose

Governed Autonomy Modes adds a user-selectable progression profile without creating a second authority engine. This assessment maps the proposal to the canonical authority, delegation, lifecycle, evidence, host-continuity, and merge-readiness contracts before implementation.

The governing distinction is:

```text
RISK_MODE != GOVERNANCE_PROFILE
GOVERNANCE_PROFILE != AUTHORITY
AUTONOMOUS_CAPABILITY != AUTONOMOUS_AUTHORITY
BYPASS_CAPABILITY != GOVERNANCE_AUTHORIZATION
```

Risk modes classify the work. Governance profiles limit which otherwise-authorized transitions may proceed automatically. Effective authority remains the intersection of the user grant, repository policy, project policy, host capability, current phase, and selected profile.

## Evidence reviewed

- `orchestra_runtime/authority.py`: immutable authority scope, exact operation/target matching, constraint intersection, trusted provenance, and fail-closed decisions.
- `orchestra_runtime/delegation.py`: child authority/capability reduction, parent identity binding, depth limits, context minimization, and deterministic accepted/rejected evidence.
- `orchestra_runtime/lifecycle.py` and `orchestra_runtime/services.py`: canonical lifecycle enforcement, run composition, execution policy binding, and the existing runtime-only `AuthorityMode.ACTIVE|COMPATIBILITY`.
- `docs/governance/DELEGATED_EXECUTION_POLICY.md`: envelopes, dispositions, external-action authority, remediation, evidence, capacity, and invalidation.
- `docs/governance/AUTONOMOUS_MERGE_READINESS_PROTOCOL.md`: exact-head readiness, current `Protect main` projection, no-bypass rule, Squash verification, and independent canonical read.
- `docs/governance/EVIDENCE_IDENTITY_AND_FRESHNESS_PROTOCOL.md`: revision-bound identity and stale-evidence invalidation.
- `docs/validation/DELEGATED_HOST_RELIABILITY_PROTOCOL.md`: same-host resume, portable handoff, context reset, and live/simulated evidence separation.
- `docs/routing/EXECUTION_MODES_POLICY.md` and `skills/conductor/SKILL.md`: current risk/progression classification and Conductor loop.
- PR #230 incident evidence and the signed, no-bypass PR #231 Squash remediation at `8163c64838d369ea5c4abf45df36f6d6504db9fd`.

## Overlap classification

| Proposed component | Canonical owner | Disposition | GA action |
| --- | --- | --- | --- |
| Root authority and operation scope | `AuthorityScope`, `AuthorityEvaluator`, trusted runtime composition | `SATISFIED_BY_EXISTING_RUNTIME` | Reuse unchanged. A profile may only reduce permitted transitions. |
| Parent/child authority inheritance | `DelegationValidator`, authority/capability intersection | `SATISFIED_BY_EXISTING_RUNTIME` | Reuse `CHILD_AUTHORITY <= PARENT_AUTHORITY`; add profile-level contract coverage only. |
| Transition dispositions | Arbiter and Delegated Execution Policy | `SATISFIED_BY_EXISTING_GOVERNANCE` | Reuse the six canonical dispositions unchanged. |
| Evidence identity and invalidation | Evidence Identity and Freshness Protocol, Overseer | `SATISFIED_BY_EXISTING_GOVERNANCE` | Bind profile decisions to exact current evidence; do not create another evidence store. |
| Merge readiness and canonical verification | Autonomous Merge Readiness Protocol | `SATISFIED_BY_EXISTING_GOVERNANCE` | Reuse exact-head and Squash-aware verification; a profile cannot bypass it. |
| Host resume and portable handoff | Delegated Host Reliability Protocol | `SATISFIED_BY_EXISTING_GOVERNANCE` | Preserve profile and grant identity in continuity records without changing host maturity. |
| Audit provenance | Runtime audit events, correlation identity, delegated records | `SATISFIED_BY_EXISTING_RUNTIME_AND_GOVERNANCE` | Require profile/grant/transition fields in governed evidence; no new persistence layer. |
| Risk classification | `FAST|STANDARD|GOVERNED|AUDIT|DESTRUCTIVE` | `SATISFIED_REQUIRES_TERMINOLOGY_CLARIFICATION` | Keep risk mode orthogonal to governance profile. |
| Runtime `AuthorityMode` | `ACTIVE|COMPATIBILITY` in `orchestra_runtime.services` | `SATISFIED_UNRELATED_NAME_COLLISION` | Do not rename or extend it. The new concept is `GovernanceProfile`, not `AuthorityMode`. |
| User-selectable autonomy profile | No canonical first-class contract | `GENUINELY_NEW_INSTRUCTION_CONTRACT_REQUIRED` | Define Human-Governed, Semi-Autonomous, and Full Autonomous with a safe default and action matrix. |
| Effective-action evaluation | Distributed prose only | `PARTIALLY_SATISFIED_REQUIRES_BOUNDED_EXTENSION` | Add a deterministic instruction-level evaluator/fixture validator for profile, grant, repository policy, evidence, and hard-boundary intersection. |
| Mode selection/change gate | Conductor has generic mode selection but no autonomy-profile gate | `PARTIALLY_SATISFIED_REQUIRES_BOUNDED_EXTENSION` | Extend Conductor source and Codex export with explicit selection, preview, confirmation, reduction, and escalation rules. |

## Architecture decision

No new runtime authority, delegation, lifecycle, capability, repository, persistence, adapter capability, or host process is justified.

The existing runtime already answers whether an operation is within authority. Governed Autonomy Modes answers a narrower workflow question: whether an authorized transition may proceed without another human checkpoint. That decision remains instruction-level because Orchestra has no canonical runtime component that performs GitHub transitions independently of the governed host workflow.

The bounded extension is:

1. one canonical profile contract;
2. one execution protocol that intersects profile with existing authority and evidence;
3. one machine-readable behavior fixture;
4. one focused validator with adversarial regression tests;
5. Conductor selection/progression instructions and portable Codex parity;
6. current-state, release-candidate, roadmap, and user documentation.

## Canonical profile semantics

- `HUMAN_GOVERNED`: safe default. Material repository transitions and major phase progression require human confirmation.
- `SEMI_AUTONOMOUS`: may progress through bounded implementation, validation, remediation, stage, commit, push, PR creation, and exact-head CI. Merge and major phase progression remain human-gated unless a stricter layer requires an earlier gate.
- `FULL_AUTONOMOUS`: may continue through all explicitly granted development transitions while authority and exact-state evidence remain valid. It cannot cross a hard boundary or a repository/project restriction.

Increasing autonomy requires explicit human authority and a recorded grant. Reducing autonomy takes effect immediately. Unknown, absent, stale, or contradictory profile/grant state fails closed; absence defaults to `HUMAN_GOVERNED`.

## GA-1 through GA-7 exact path boundary

Implementation may change only:

- `AGENTS.md`
- `CHANGELOG.md`
- `PROJECT_CONTEXT.md`
- `PROJECT_STATE.md`
- `README.md`
- `SESSION_HANDOFF.md`
- `adapters/codex/skills/conductor/REFERENCE_CONTEXT.md`
- `adapters/codex/skills/conductor/SKILL.md`
- `docs/governance/DELEGATED_EXECUTION_POLICY.md`
- `docs/governance/GOVERNANCE_LAYER.md`
- `docs/governance/GOVERNANCE_REVIEW_FLOW.md`
- `docs/governance/GOVERNED_AUTONOMY_MODES.md`
- `docs/governance/GOVERNED_AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/project/GOVERNED_AUTONOMY_MODES_ARCHITECTURE_OVERLAP_ASSESSMENT.md`
- `docs/project/ROADMAP.md`
- `docs/releases/v1.2.0-governed-orchestration-release-candidate.md`
- `docs/routing/EXECUTION_MODES_POLICY.md`
- `scripts/governance_check.py`
- `scripts/validate_governance_protocol_consistency.py`
- `scripts/validate_governed_autonomy_modes_contract.py`
- `skills/conductor/SKILL.md`
- `tests/behavior/governed-autonomy-modes-fixtures.json`
- `tests/behavior/run_tests.py`
- `tests/runtime/test_governed_autonomy_modes_contract.py`

Any required path outside this list is scope expansion and requires `ESCALATE_HUMAN_SCOPE_EXPANSION`.

## Protected boundaries

The implementation must not change:

- `orchestra_runtime/**`;
- authority, delegation, lifecycle, capability, or persistence models;
- plugin manifests, package versions, or marketplace maturity;
- the R7 simulated host-reliability fixture or validator;
- accepted R7 source evidence identities;
- CI workflows or repository rulesets;
- release tags, GitHub Releases, deployments, installed integrations, or policy activation.

Claude Code remains `SCAFFOLD_ONLY`. The current public release remains `v1.1.2`. The target remains `v1.2.0` in `PREPARED_NOT_RELEASED` state. R8 remains separately human-authorized.

## Phase mapping

- GA-1: canonical profile names, safe default, action matrix, precedence, switching, inheritance, and hard boundaries.
- GA-2: profile/grant/repository-policy intersection in the instruction-level evaluator.
- GA-3: Conductor selection gate, effective-authority preview, and explicit confirmation for increases.
- GA-4: progression mapping for implementation through Squash-aware post-merge verification.
- GA-5: audit fields, resume/handoff preservation, stale-state invalidation, and recovery behavior.
- GA-6: adversarial fixture and focused regression tests.
- GA-7: final current-state, roadmap, release-candidate, README, and adapter-parity reconciliation.

## Clockwork decision

```text
Status: Ready
Boundary map:
  GovernanceProfile -> reduces existing authority and transition automation
  AuthorityScope/DelegationValidator -> remain canonical and unchanged
  Arbiter dispositions -> remain canonical and unchanged
  Merge/host/evidence protocols -> remain canonical and reused
Blocked:
  GovernanceProfile -> creating authority
  GovernanceProfile -> bypassing repository policy or evidence
  GovernanceProfile -> extending runtime AuthorityMode
  GovernanceProfile -> crossing R8 or another hard boundary
Smallest safe fix: instruction contracts, deterministic fixture validator, Conductor selection, documentation parity
Stop/Go: Safe to implement inside the exact path boundary
```

## Verdict

`NO_DUPLICATE_AUTHORITY_MODEL`

GA-1 through GA-7 may proceed as one sequential bounded implementation because they share the same repository, baseline, authority boundary, validation matrix, rollback boundary, and protected surfaces. Any new commit invalidates prior exact-head evidence and requires full revalidation.
