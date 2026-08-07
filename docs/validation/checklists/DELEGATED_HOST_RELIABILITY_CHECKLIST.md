# Delegated Host Reliability Checklist

Use this checklist with `docs/validation/DELEGATED_HOST_RELIABILITY_PROTOCOL.md` and the existing delegated execution, evidence, Tuner coordination, trusted runtime, and Arbiter transition contracts.

## Baseline and identity

- [ ] Exact repository commit and approved baseline are recorded.
- [ ] Installed or simulated runtime/skill bundle SHA-256 is recorded.
- [ ] Correlation ID and run identity match the pre-boundary execution lineage.
- [ ] Checkpoint, capacity handoff, input envelope, evidence packet, and output envelope identities are explicit.
- [ ] Evidence level is exactly `SIMULATED_REPOSITORY_EVIDENCE` or `LIVE_HOST_EVIDENCE`.
- [ ] Repository simulation is not represented as live installed-host evidence.

## Host maturity

- [ ] Source and destination host maturity match Orchestra's current declared support level.
- [ ] Codex and Antigravity active-host scenarios remain within their declared capabilities.
- [ ] Claude Code scaffold/package compatibility is not represented as active runtime continuity.
- [ ] Unsupported or scaffold-only active runtime continuation produces `ESCALATE_HUMAN`.
- [ ] No host maturity is promoted by a test fixture, validator, or documentation-only record.

## Context reset and handoff

- [ ] Resume receives only accepted envelope, minimal context, evidence packet, checkpoint, and handoff records.
- [ ] Unrepresented conversational memory is treated as non-authoritative.
- [ ] Context allowlist is explicit and excludes secrets and unrelated values.
- [ ] A valid capacity interruption produces `WAIT_FOR_CAPACITY` without changing authority or evidence requirements.
- [ ] Cross-host handoff occurs only when both active hosts support the required portable capability.

## Authority and replay

- [ ] Effective authority after resume is equal to or narrower than pre-reset authority.
- [ ] Capability grants and filesystem scope are equal to or narrower than the accepted envelope.
- [ ] External-action grants are not widened by reset or handoff.
- [ ] Duplicate checkpoint consumption is rejected.
- [ ] Already-completed external side effects are not replayed.
- [ ] Authority expansion, corrupted identity, or side-effect replay produces `STOP`.

## Evidence and dispositions

- [ ] `AUTO_CONTINUE` requires complete identity, evidence, capability, authority, context, and replay checks.
- [ ] Stale or missing revision, bundle, checkpoint, envelope, or evidence identity produces `WAIT_FOR_EVIDENCE`.
- [ ] Capacity-only interruption with a valid checkpoint produces `WAIT_FOR_CAPACITY`.
- [ ] Unsupported host capability or maturity produces `ESCALATE_HUMAN`.
- [ ] Unsafe authority/replay conflicts produce `STOP`.
- [ ] Overseer owns evidence sufficiency and Arbiter owns the final continuation disposition.

## Live validation

- [ ] Codex active-host reset/resume has actual installed-host evidence.
- [ ] Antigravity active-host reset/resume has actual installed-host evidence.
- [ ] At least one supported active-host cross-host handoff has actual evidence when the current implementation permits it.
- [ ] Claude Code packaging/contract compatibility is checked without overstating runtime maturity.
- [ ] Live evidence identifies observation timestamp and host-produced artifact source.
- [ ] Phase C remains `PENDING_LOCAL_HOST_VALIDATION` until required live evidence exists.

## Closeout

- [ ] Repository fixture validator passes.
- [ ] Runtime pytest coverage for the host reliability contract passes.
- [ ] Full behavior, runtime, governance, packaging, and cross-platform CI remain green.
- [ ] No persistence, RPC, daemon, deployment, publication, destructive cleanup, or policy authority was introduced.
