# Governed Autonomy Modes

## Purpose

Governed Autonomy Modes defines how often Orchestra pauses for human approval during an otherwise-authorized development workflow.

```text
AUTONOMOUS_CAPABILITY != AUTONOMOUS_AUTHORITY
BYPASS_CAPABILITY != GOVERNANCE_AUTHORIZATION
CHILD_AUTHORITY <= PARENT_AUTHORITY
```

A profile is a reduction-only preset. It never creates repository, path, action, release, deployment, destructive-operation, or policy authority.

## Orthogonal classifications

Orchestra classifies every run on separate axes:

- Risk Mode: `FAST | STANDARD | GOVERNED | AUDIT | DESTRUCTIVE`.
- Progression Mode: `DIRECT | MANUAL | DELEGATED | LEGACY_FALLBACK`.
- Governance Profile: `HUMAN_GOVERNED | SEMI_AUTONOMOUS | FULL_AUTONOMOUS`.

Risk mode determines context and review depth. Progression mode determines whether a valid envelope exists. Governance profile determines which valid transitions may proceed without another approval.

## Safe default

HUMAN_GOVERNED is the safe default when no valid profile selection is recorded.

Unknown, malformed, missing, stale, contradictory, or unsupported profile state fails closed. A host or adapter must not infer a more permissive profile from task wording, platform capability, mergeability, prior runs, or repository metadata.

## Profiles

### HUMAN_GOVERNED

Orchestra may analyze, implement already-authorized scope, validate, and perform bounded remediation. It pauses before stage, commit, push, pull-request creation, merge, major phase progression, release, deployment, policy activation, destructive action, or another material repository transition.

### SEMI_AUTONOMOUS

Within an explicit grant, Orchestra may analyze, implement, validate, remediate, stage, commit, perform post-commit validation, push, create a pull request, monitor exact-head CI, and perform bounded CI remediation.

Merge and major phase progression remain human-gated. Repository or project policy may require earlier gates.

### FULL_AUTONOMOUS

Within an explicit grant, Orchestra may perform the Semi-Autonomous actions, merge when all governance-readiness gates pass, independently verify canonical post-merge state, synchronize project state, and continue through subsequent authorized phases.

Full Autonomous is continuous bounded progression, not unrestricted execution.

## Canonical action matrix

| Action | Human-Governed | Semi-Autonomous | Full Autonomous |
| --- | --- | --- | --- |
| Analyze authorized scope | automatic | automatic | automatic |
| Implement authorized scope | automatic | automatic | automatic |
| Validate and bounded-remediate | automatic | automatic | automatic |
| Stage and commit | human gate | automatic when granted | automatic when granted |
| Push and create PR | human gate | automatic when granted | automatic when granted |
| Monitor exact-head CI | human gate | automatic when granted | automatic when granted |
| Merge | human gate | human gate | automatic only when granted and governance-ready |
| Major phase progression | human gate | human gate | automatic only when granted and evidence-green |
| Release, deploy, policy activation, destructive action, force push, history rewrite | separate explicit authority | separate explicit authority | separate explicit authority |

The matrix is an upper bound. Effective behavior is always the most restrictive applicable result.

## Effective authority

```text
effective transitions =
  selected profile
  INTERSECT explicit user grant
  INTERSECT repository policy
  INTERSECT project policy
  INTERSECT host capability
  INTERSECT current phase scope
  INTERSECT current evidence
  MINUS hard boundaries
```

If any required input is unavailable or stale, Orchestra returns `WAIT_FOR_EVIDENCE` or `ESCALATE_HUMAN`; it does not infer permission.

## Candidate maturity integration

The [Governed Autonomy Candidate Lifecycle Integration](GOVERNED_AUTONOMY_CANDIDATE_LIFECYCLE_INTEGRATION.md) applies these existing profile ceilings to the Candidate Maturity and Feature Freeze states without creating another autonomy engine.

```text
AUTONOMY_CHANGES_PAUSES_NOT_PREREQUISITES
CANDIDATE_TRANSITION != PERSISTENCE_AUTHORITY
FULL_AUTONOMOUS != FEATURE_ADOPTION_AUTHORITY
```

The integration may remove an unnecessary second human checkpoint only after the transition's prerequisite decision, authority, identity, and evidence already exist.

In particular:

- all profiles may mechanically start already-authorized implementation and record a complete exact Feature Freeze;
- no profile may create its own feature-acceptance/adoption decision;
- Semi-Autonomous and Full Autonomous may record `MERGE_READY` when qualification evidence is current, while Human-Governed retains its major-phase progression gate;
- only Full Autonomous may initiate a merge automatically, and only when an exact candidate/PR merge grant is current and the existing merge evaluator independently permits it;
- post-merge canonical verification may be recorded automatically after independent readback;
- `RETIRED` closes the candidate record and never grants branch-deletion authority.

Any Git write used to persist a maturity record remains separately subject to this document's ordinary action matrix.

## Selection record

Before autonomous state mutation, record:

- run and correlation identity;
- selected and prior profile;
- granting human actor or explicit user instruction;
- repository, branch, base, and phase;
- allowed actions and paths;
- repository/project policy identity;
- hard boundaries;
- selection time and evidence identity;
- parent grant/profile for delegated children.

## Profile changes

- Reducing autonomy takes effect immediately.
- Increasing autonomy requires explicit human authorization.
- An increase invalidates prior transition evidence until the new grant and effective-authority preview are recorded.
- A child may select a stricter profile than its parent but never a more permissive one.
- A resumed or handed-off run must preserve exact profile and grant identity; mismatch returns `WAIT_FOR_EVIDENCE`.

## Repository-policy intersection

Repository capability does not override governance:

- retained bypass capability does not authorize bypass use;
- `mergeable: true` does not prove readiness;
- required checks must exist and belong to the exact current head;
- ruleset or merge-method drift invalidates readiness;
- current Orchestra merges must use Squash and verify the resulting signed canonical commit.

## Hard boundaries

No profile independently authorizes:

- release or publication;
- deployment or production mutation;
- policy activation;
- destructive operations;
- force push or history rewrite;
- secret-handling or infrastructure expansion;
- authority expansion;
- actions prohibited by repository or project policy.

## Contract result

`GOVERNED_AUTONOMY_MODES_DEFINED`
