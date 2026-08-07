# Delegated Host Reliability Protocol

## Purpose

This protocol defines Phase C reliability evidence for delegated Orchestra execution across context resets, capacity interruptions, and host handoffs. It verifies continuity without granting new execution, Git, merge, release, deployment, or policy authority.

```text
Protocol revision: delegated-host-reliability-v1
Phase: Delegated Phase C
Repository-simulated contract status: IMPLEMENTED
Live installed-host validation status: PENDING_LOCAL_HOST_VALIDATION
Routing owner: Conductor
Continuity coordination: The Tuner
Evidence owner: Overseer
Transition owner: Arbiter
Authority source: existing trusted runtime and delegated execution contracts only
```

## Evidence levels

Phase C distinguishes two evidence levels and MUST NOT treat them as interchangeable.

### `SIMULATED_REPOSITORY_EVIDENCE`

Evidence produced by deterministic repository fixtures, validators, tests, and GitHub Actions. It can prove schema completeness, transition behavior, fail-closed handling, cross-platform parsing, and non-regression. It cannot prove that an installed host actually preserved a live session across a context reset or capacity handoff.

### `LIVE_HOST_EVIDENCE`

Evidence produced by an actual installed host while executing the approved scenario against an exact Orchestra revision and installed bundle. Live evidence must identify the host, revision, bundle identity, checkpoint, handoff, envelope identities, evidence packet identity, result, and source.

A repository-only run MUST NOT set Phase C to `COMPLETE`, `LIVE_VALIDATED`, or an equivalent claim.

## Host maturity boundary

Host reliability claims must preserve the maturity already declared by Orchestra.

- `codex`: active supported integration surface for Phase C evaluation.
- `antigravity`: active supported integration surface for Phase C evaluation.
- `claude-code`: plugin/package compatibility surface. Scaffold-only runtime maturity MUST NOT be promoted to active runtime continuity by this protocol.

A scaffold-only or otherwise unsupported host can prove packaging and portable-contract compatibility, but it cannot satisfy an active-runtime continuity requirement until its declared maturity is separately graduated.

## Portable continuity record

Each continuity attempt must bind these fields:

```yaml
scenario_id: stable scenario identifier
host_from: codex | antigravity | claude-code
host_to: codex | antigravity | claude-code
host_from_maturity: ACTIVE | SCAFFOLD_ONLY
host_to_maturity: ACTIVE | SCAFFOLD_ONLY
evidence_level: SIMULATED_REPOSITORY_EVIDENCE | LIVE_HOST_EVIDENCE
repo_commit_sha: exact 40-character commit SHA
runtime_bundle_sha256: SHA-256 of the installed or simulated portable bundle
correlation_id: canonical Orchestra correlation identifier
run_id: root or delegated run identity
checkpoint_id: checkpoint identity
capacity_handoff_id: handoff identity when capacity transfer occurs
approved_base_sha: exact approved baseline
input_envelope_sha256: canonical input envelope identity
evidence_packet_sha256: canonical evidence packet identity
output_envelope_sha256: canonical output envelope identity when continuation succeeds
resume_attempt: positive integer
expected_disposition: AUTO_CONTINUE | WAIT_FOR_EVIDENCE | WAIT_FOR_CAPACITY | ESCALATE_HUMAN | STOP
authority_preserved: boolean
context_minimized: boolean
side_effect_replayed: boolean
result: deterministic scenario result
```

Live records additionally require an observation timestamp and a source reference that identifies the host-produced evidence artifact. Secrets, credentials, raw private prompts, and unrelated project data MUST NOT be copied into the record.

## Continuity invariants

A successful continuation requires all of the following:

1. `repo_commit_sha` and `approved_base_sha` match the approved execution lineage.
2. The portable runtime or skill bundle identity matches the bundle validated for the continuation.
3. `correlation_id`, `run_id`, checkpoint identity, and delegated authority lineage are preserved.
4. Input and evidence-packet identities match the accepted pre-reset state.
5. No capability, authority, filesystem scope, or external-action grant becomes broader after reset or handoff.
6. Context is minimized to the explicit allowlist; secrets and unrelated values are not inherited.
7. Resume is single-consumption for the same checkpoint/handoff identity unless the underlying contract explicitly defines idempotent replay.
8. A successful resume does not replay an already-completed external side effect.
9. The receiving host supports the capability being resumed under its declared maturity.
10. Overseer evidence is current and Arbiter evaluates the resulting continuation disposition.

## Required scenario classes

Repository simulation and later live validation must cover:

- same-host context reset and resume;
- valid capacity checkpoint followed by `WAIT_FOR_CAPACITY`;
- same-host continuation after capacity becomes available;
- active-host cross-host handoff where the portable contract permits it;
- stale repository revision;
- stale installed bundle identity;
- incomplete checkpoint/evidence packet;
- unsupported or scaffold-only runtime continuation;
- attempted authority expansion during resume;
- duplicate checkpoint consumption or side-effect replay.

## Deterministic dispositions

### `AUTO_CONTINUE`

Allowed only when identity, evidence, authority, context, capability, and replay invariants all pass.

### `WAIT_FOR_EVIDENCE`

Required for stale or missing revision, bundle, checkpoint, envelope, evidence-packet, or validation identity.

### `WAIT_FOR_CAPACITY`

Required when a valid checkpoint exists but the current host cannot continue solely because capacity is unavailable. This disposition does not weaken any evidence or authority requirement.

### `ESCALATE_HUMAN`

Required when continuation depends on a host capability or maturity that Orchestra does not currently claim, or when a material ambiguity cannot be resolved from accepted contracts.

### `STOP`

Required for authority expansion, checkpoint replay conflict, duplicate external side effect, corrupted identity, or any other unsafe continuation that cannot be repaired by obtaining fresh evidence alone.

## Cross-host handoff rule

Cross-host continuation is allowed only between integration surfaces that both declare the required runtime capability. Portable serialization alone is not proof of host execution support. A receiving host that is scaffold-only must produce `ESCALATE_HUMAN` rather than `AUTO_CONTINUE` for active runtime continuation.

## Context-reset rule

A context reset is treated as a continuity boundary, not as a new source of authority. The resumed host receives only the approved envelope, minimal context allowlist, current evidence packet, checkpoint, and handoff record. Conversational memory that is not represented in those accepted artifacts is non-authoritative.

## Live validation matrix

Phase C final live validation must record actual evidence for the host targets required by the current implementation plan while preserving their declared maturity. At minimum:

- Codex active-host reset/resume;
- Antigravity active-host reset/resume;
- an active-host cross-host portable handoff where supported;
- Claude Code packaging/contract compatibility, without claiming active runtime continuity while its runtime maturity remains scaffold-only.

The matrix remains `PENDING_LOCAL_HOST_VALIDATION` until those records exist and validate against the exact installed revision.

## Repository artifacts

- `tests/behavior/delegated-host-reliability-fixtures.json`
- `scripts/validate_delegated_host_reliability_contract.py`
- `tests/runtime/test_delegated_host_reliability_contract.py`
- `docs/validation/checklists/DELEGATED_HOST_RELIABILITY_CHECKLIST.md`

## Preserved boundaries

This protocol does not:

- promote host maturity;
- create persistent collaboration storage, RPC, a daemon, or network orchestration;
- activate automatic policy mutation;
- create deployment or publication authority;
- mutate a consumer repository;
- authorize destructive cleanup;
- replace the delegated execution policy, trusted runtime authority model, Tuner coordination contract, Overseer evidence ownership, or Arbiter transition authority.
