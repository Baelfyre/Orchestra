# Control Plane Re-foundation P3: Typed Governance and Arbiter Kernel

Status: `STACKED_NONCANONICAL_CANDIDATE`
Parent: `#273`
Child: `#277`
Dependency: PR `#275` exact head `c8872db485b3c7d76db891022a4619e0064c03f8`

## Purpose

Implement the existing canonical governance decision and delegated-execution policies as machine-validated runtime contracts without creating a second governance vocabulary.

The model is split explicitly:

- **Arbiter Analyst** may reason, explain, and propose.
- **Arbiter Kernel** evaluates typed state/evidence and emits the authoritative transition disposition.

Prose cannot override a kernel disposition.

## Preserved canonical policy

This slice implements, rather than redefines:

- `docs/governance/GOVERNANCE_DECISION_PROTOCOL.md`;
- `docs/governance/DELEGATED_EXECUTION_POLICY.md`.

Governance decisions remain:

`APPROVED | ADVISORY_ONLY | REVISION_REQUIRED | BLOCKED | NOT_APPLICABLE`

Transition dispositions remain:

`AUTO_CONTINUE | AUTO_REMEDIATE_AND_REVALIDATE | WAIT_FOR_EVIDENCE | WAIT_FOR_CAPACITY | ESCALATE_HUMAN | STOP`

Precedence remains:

`STOP > ESCALATE_HUMAN > WAIT_FOR_CAPACITY > WAIT_FOR_EVIDENCE > AUTO_REMEDIATE_AND_REVALIDATE > AUTO_CONTINUE`

## Machine contracts

`GovernanceDecisionRecord` is a typed form of the existing compact governance contract, including exact decision enum, reviewer, reason, risks/actions, human-review requirement, and evidence references.

`ArbiterKernelInput` binds the transition evaluation to authority, protected boundaries, policy/scope questions, external authority, contradictions, evidence completeness, required receipts, exact-state validity, freshness, validation, capacity, and remediation budget.

`ArbiterKernelResult` contains only a code-derived disposition, reason codes, and the canonical input digest.

## Fail-closed rules

- invalid authority or protected-boundary failure -> `STOP`;
- governance `BLOCKED` -> `STOP`;
- human review, unresolved policy/scope/authority/contradiction -> `ESCALATE_HUMAN`;
- exhausted remediation budget -> `ESCALATE_HUMAN`;
- unavailable host capacity -> `WAIT_FOR_CAPACITY`;
- missing/stale/mismatched evidence -> `WAIT_FOR_EVIDENCE`;
- deterministic in-scope authorized defect with remaining budget -> `AUTO_REMEDIATE_AND_REVALIDATE`;
- only a fully current, authorized, validated state -> `AUTO_CONTINUE`.

Unsupported governance values are rejected at the typed boundary. Malformed integration-boundary values fail closed to `ESCALATE_HUMAN`. Agent-provided disposition text can be checked against the kernel result but cannot replace it.

## Deferred

This slice does not yet route every Arbiter invocation through the kernel. Compliance record set-equality, host-capability contracts, context/event-store work, and hard execution enforcement remain later phases of #273.

Because PR #275 is exact-head green but blocked by live review policy issue #276, this slice is intentionally stacked and noncanonical until its dependency can be promoted under repository governance.
