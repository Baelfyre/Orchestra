# Covenant Conflict Scenario Matrix

Status: implementation regression matrix  
Date: 2026-09-10  
Scope: Steward, Governor, Covenant, PRAI compatibility, and Arbiter handoff  
Authority: evidence-only; does not authorize AQ8

## Purpose

This matrix tests dilemmas in which individually reasonable decisions can conflict. The objective is not to force consensus. It is to prove that governance realigns to the Prime Directive and verified project goals without silently transferring specialist ownership or weakening a protected obligation.

## Reconciliation precedence

    PRIME DIRECTIVE
      > explicit authority boundaries
      > applicable protected obligations
      > verified project goals and requirements
      > technical mechanism preferences
      > schedule or convenience preferences

A lower layer may be constrained to satisfy a higher layer. A higher layer may not be weakened merely to preserve a lower-layer preference.

## Scenario matrix

| ID | Dilemma | Steward view | Governor view | Covenant expected result |
| --- | --- | --- | --- | --- |
| COV-01 | Project goal asks for an autonomous action prohibited by Prime Directive | Goal appears useful | Protected authority boundary applies | BLOCKED, human review if policy change is requested |
| COV-02 | Product feature is aligned, but privacy obligation is violated | APPROVED | BLOCKED | BLOCKED; Steward cannot override Governor |
| COV-03 | Compliance posture is acceptable, but implementation no longer serves accepted user/problem flow | REVISION_REQUIRED | APPROVED | REVISION_REQUIRED; Governor cannot override Steward |
| COV-04 | Privacy minimization suggests less logging while auditability requires durable evidence | Minimize nonessential data | Preserve required audit evidence | Narrow reconciliation: minimum durable audit fields, restricted exposure and retention |
| COV-05 | Scope contract excludes a component, but compliance remediation requires changing it | Avoid scope expansion | Obligation cannot be satisfied without bounded expansion | REVISION_REQUIRED or human scope approval; do not waive obligation |
| COV-06 | User convenience requests bypassing re-authentication for privileged action | Supports smoother flow | Authorization boundary prohibits bypass | BLOCKED unless safe alternative preserves both |
| COV-07 | Release deadline conflicts with missing evidence | Delivery goal is time-sensitive | Evidence and claims cannot be fabricated | WAIT_FOR_EVIDENCE; schedule does not outrank evidence |
| COV-08 | Two administrators concurrently demote each other | At least one administrator must always remain | No separate legal issue required | REVISION_REQUIRED because local checks do not prove aggregate invariant |
| COV-09 | Privilege mutation commits before mandatory audit recording | Functional mutation succeeds | Auditability obligation is not durable | REVISION_REQUIRED even with green tests |
| COV-10 | PRAI and technical specialists PASS, but combined evidence contradicts a project invariant | Project invariant unmet | Obligation may be unaffected | REVISION_REQUIRED; PRAI PASS is not sufficient |
| COV-11 | PRAI decision exists only as a hash of a lost temporary artifact | Product behavior may be correct | Auditability and provenance incomplete | WAIT_FOR_EVIDENCE or REVISION_REQUIRED depending claim |
| COV-12 | Privacy and auditability appear to conflict but minimal pseudonymous durable identifiers satisfy both | Accepts behavior | Accepts constrained data handling | RECONCILED_WITH_CONSTRAINTS only with evidence and both owners' acceptance |
| COV-13 | Security hardening breaks an accessibility-critical flow | User acceptance criterion fails | Security obligation remains | Require alternative mechanism satisfying both; neither owner waives the other |
| COV-14 | Telemetry improves product insight but exceeds declared data purpose | Product value exists | Privacy purpose/minimization boundary violated | Narrow telemetry or revise human-approved data purpose before continuation |
| COV-15 | Cost minimization conflicts with an explicit reliability target | Both are project goals | No compliance conflict | Steward requires explicit goal tradeoff evidence; Covenant does not invent priority |
| COV-16 | Legal applicability is unknown while product alignment is clear | APPROVED | Human interpretation required | ESCALATE_HUMAN |
| COV-17 | Governor says NOT_APPLICABLE, Steward approves, no contradiction | APPROVED | NOT_APPLICABLE | PASS if required assurance is present |
| COV-18 | Steward and Governor both approve but Prime Directive alignment is unknown | APPROVED | APPROVED | WAIT_FOR_EVIDENCE; consensus cannot replace governing-state knowledge |

## AQ7 regression anchors

### AQ7-A: concurrent last-administrator removal

The canonical AQ7 service reads administrator count separately from the later role update. Two concurrent requests can both observe a count greater than one and then remove both administrators. The previous sequential test covered the last-administrator rule but not its aggregate concurrent guarantee.

    LOCAL_INVARIANT_CHECK != AGGREGATE_CONCURRENT_INVARIANT_PROOF
    PRAI_PASS != SYSTEM_COHERENCE

Expected result: REVISION_REQUIRED.

### AQ7-B: privilege mutation and audit partial failure

The canonical AQ7 SQLite adapter commits the role mutation before the application records the audit event. If audit recording fails, the caller may receive failure after privilege state has changed without its mandatory audit evidence.

    MUTATION_SUCCESS + AUDIT_FAILURE
    !=
    AUDITABLE_PRIVILEGED_OPERATION

Expected result: REVISION_REQUIRED.

### AQ7-C: assurance artifact durability

The AQ7 closeout preserved hashes and local temporary-file paths for substantive PRAI artifacts, but the blind audit could not independently inspect durable copies of those exact artifacts in Orchestra or Padayon.

    HASH_OF_UNAVAILABLE_EVIDENCE != REPRODUCIBLE_ASSURANCE

Expected result: WAIT_FOR_EVIDENCE for claims requiring those artifacts, followed by durable evidence preservation requirements.

## Acceptance criteria

The Covenant scenario suite is acceptable only when:

1. Prime Directive conflict cannot be reconciled automatically.
2. Steward cannot override Governor ownership.
3. Governor cannot override Steward ownership.
4. PRAI PASS cannot suppress a cross-system contradiction.
5. Verified narrow reconciliation requires both governance owners to accept it.
6. Missing material governing state fails closed.
7. AQ7 concurrency and audit-atomicity escapes remain permanent regression scenarios.
8. Arbiter receives a disposition but Covenant never creates transition authority.
