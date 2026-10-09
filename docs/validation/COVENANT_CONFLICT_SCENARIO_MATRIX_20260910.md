# Covenant conflict scenario matrix

This matrix is an executable contract. The two runtime tests with the same
scenario identifiers are the authoritative local execution of these cases.
Each result remains evidence-only and is bound to the candidate basis used by
the test.

| ID | Conflict or dilemma | Expected Covenant disposition |
| --- | --- | --- |
| COV-01 | Project goal requests a Prime Directive-prohibited autonomous action | BLOCKED, human review required |
| COV-02 | Steward APPROVED, Governor BLOCKED for privacy/compliance | BLOCKED |
| COV-03 | Governor APPROVED, Steward REVISION_REQUIRED for the user/problem flow | REVISION_REQUIRED |
| COV-04A | Privacy minimization drops mandatory audit evidence | REVISION_REQUIRED |
| COV-04B | Minimum identifiers, restricted exposure, controlled retention, both owners accept | RECONCILED_WITH_CONSTRAINTS |
| COV-05 | Accepted scope excludes compliance-required remediation | REVISION_REQUIRED or ESCALATE_HUMAN |
| COV-06 | Convenience bypasses a privileged-action authentication boundary | BLOCKED |
| COV-07 | Urgent deadline but material validation evidence is unavailable | WAIT_FOR_EVIDENCE |
| COV-08 | Concurrent last-administrator demotions can leave zero administrators | REVISION_REQUIRED, SYSTEM_CONTRADICTION |
| COV-09 | Privilege mutation commits before mandatory audit write fails | REVISION_REQUIRED |
| COV-10 | Steward, Governor, specialists, and PRAI pass but system contradiction exists | REVISION_REQUIRED |
| COV-11 | Decision hash exists but substantive evidence is not retrievable | WAIT_FOR_EVIDENCE |
| COV-12 | Narrow evidence-backed design preserves Prime Directive and goals, both accept | RECONCILED_WITH_CONSTRAINTS |
| COV-13 | Security hardening breaks an accessibility-critical flow | REVISION_REQUIRED |
| COV-14 | Product telemetry exceeds its declared privacy purpose | REVISION_REQUIRED |
| COV-15 | Cost and reliability goals conflict without constitutional priority | WAIT_FOR_EVIDENCE or REVISION_REQUIRED |
| COV-16 | Governor cannot determine legal applicability without human interpretation | ESCALATE_HUMAN |
| COV-17 | Governor protected-obligation domain is genuinely not applicable | PASS |
| COV-18 | Steward and Governor approve while Prime Directive alignment is unknown | WAIT_FOR_EVIDENCE |

## Regression anchors

COV-08 represents the AQ7 aggregate-invariant defect. Two administrators each
observe a count of two, then concurrent demotions can produce zero remaining
administrators. A local precondition check is not an aggregate concurrent
invariant proof.

COV-09 represents the AQ7 partial-failure defect. A database mutation followed
by a failed mandatory audit write is not an auditable privileged operation,
even if the caller receives an error.

## Adversarial permutations

The executable suite also covers missing Steward or Governor judgments, wrong
reviewer identity, invalid disposition, unknown alignment, empty project-goal,
critical-flow, or invariant basis, duplicate evidence references, missing or
malformed identity, stale candidate or tree identity, reconciliation without
evidence, one-owner acceptance, a reconciliation that sacrifices a project
goal or the Prime Directive, an owning governance BLOCK with PRAI PASS, and
human review required with technical PASS.

No case permits majority vote, confidence averaging, the most permissive
reviewer, automatic compromise, PRAI-only certification, or Covenant-created
authority.
