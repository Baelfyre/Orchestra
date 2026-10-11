# Documentation Lifecycle Applicability

## Purpose and boundary

This contract makes documentation impact an explicit, risk-proportional part of Orchestra's existing development lifecycle. It helps a task decide which existing documentation must be created, updated, checked, or left alone, and how claims remain tied to their owners and evidence.

It adds no lifecycle stage, candidate-maturity state, governance engine, approval loop, machine-record field, or mandatory CI gate. It does not change implementation, acceptance, qualification, promotion, merge, release, or policy authority. Existing governance and machine contracts remain authoritative. The four applicability outcomes below classify documentation obligations only; they are not candidate states or replacements for the `QualificationGatePlan` status model.

## Applicability outcomes

Assign an outcome to each material documentation obligation, not one blanket status to an entire task. Record the decision in the existing issue, candidate scope, evidence packet, or implementation report where one is already used. Do not create a duplicate record just to carry an outcome.

| Outcome | Meaning and handling |
| --- | --- |
| `REQUIRED` | An approved requirement, user or operator impact, or a material correction to an existing claim requires a durable documentation change. Complete it before the existing validation or decision that relies on that claim. |
| `CONDITIONAL` | A named trigger determines whether work is required. Evaluate the trigger against current scope and evidence; resolve it to `REQUIRED` or `NOT_APPLICABLE` when the relevant lifecycle decision is made. |
| `NOT_APPLICABLE` | The trigger was checked and does not apply. Record a concise reason in the existing task or evidence surface. It never means that applicability was unknown. |
| `UNRESOLVED` | Scope, evidence, or ownership is insufficient to decide. Keep the claim qualified or unpublished and route the question to its owner through Conductor. Only the already-existing governing contract determines whether the unresolved item blocks progression. |

An applicability decision creates no authority. In particular, documentation or a `NOT_APPLICABLE` result cannot satisfy another gate by implication.

## Applicability across Development Lifecycle V2

Use the existing lifecycle stages and records. The timing below identifies when to assess or finish documentation work; it does not add transitions or require a new artifact at every stage.

| Existing lifecycle stage | When and documentation decision | Existing source or evidence to reuse |
| --- | --- | --- |
| Feature Admission | **Before implementation.** If a proposal adds or materially changes a capability, requirement, user promise, or operator obligation, documentation is `CONDITIONAL` and follows the approved admission basis. For a bounded correction, reference the existing issue or accepted requirement. | `FeatureDecisionRecord` or its eligible inline-rationale path; approved requirement and issue records. |
| Baseline + Implementation | **During implementation.** Identify affected claims and docs from the authorized scope. Update only claims whose behavior, setup, supported contract, architecture, security guidance, or operator action changes. Test-only or evidence-only work is normally `NOT_APPLICABLE` to prose when existing documentation remains accurate. | Current tracked source and configuration; owning specialist evidence; existing test and evidence outputs. |
| Candidate Declaration / Feature Freeze | **Before qualification.** Include affected documentation paths in the existing candidate scope and acceptance evidence when they are part of the candidate. Preserve exact head, tree, base, and scope identity. Do not add a freeze field or a second freeze record. | `CandidateMaturityRecord`, its existing freeze scope, and optional existing `gate_applicability_ref`. |
| Qualification Gate Set | **During qualification.** Apply the existing risk-proportional gates to the exact frozen candidate. When documentation is in scope, validate its claims and local references with the same candidate evidence. A documentation correction still receives the engineering evidence required by the qualification contract. | Existing `QualificationGatePlan`, validation output, and `scripts/check_readme_impact.py`; no DOC-L1 CI gate is added. |
| Promotion Adjudication | **Before a promotion decision.** Keep claims about benefit, acceptance, and readiness limited to the recorded decision and its evidence. Scribe can reconcile the representation but cannot recommend or approve promotion from documentation alone. | The existing `FeatureDecisionRecord`, approved decision, and Overseer validation evidence. |
| Merge Preparation | **Before an authorized merge.** Check changed documentation for accurate claims, valid local links and fragments, and the existing changelog/index impacts. Bind validation to the reviewed candidate; any relevant source change makes prior exact-head evidence stale. | Existing documentation map, [changelog guidance](../../skills/scribe/CHANGELOG_ADR_GUIDE.md), impact validator, review evidence, and [merge-readiness protocol](../governance/AUTONOMOUS_MERGE_READINESS_PROTOCOL.md). |
| Merge + Independent Verification | **After an authorized merge.** Independently verify canonical repository state and confirm the documented change is present in the verified tree. Report the state from that readback; do not treat a merge response or documentation text as proof of the merge. | Existing merge-readiness and post-merge verification records. |
| Closeout + Retirement | **At existing closeout.** Correct or supersede affected claims and retain their evidence links. Create or update a retrospective only when the existing retrospective protocol's trigger applies; DOC-L1 creates no retrospective requirement. | Existing closeout/continuity records and the Phase Retrospective Protocol (`replacement_effect: none`). |

## Applicability by change type

| Change type | Documentation decision |
| --- | --- |
| Bug fix | `CONDITIONAL`: update user, operator, API, setup, error, or recovery guidance when the observable behavior or instructions change. Otherwise use `NOT_APPLICABLE` if documentation impact is already being tracked; do not create a separate record just to say no docs changed. |
| Feature development | `CONDITIONAL`: document a new or changed user/operator capability, requirement, setup, compatibility promise, or supported workflow when it is part of approved scope. Reuse the admission and acceptance records; internal changes with no documented impact need no new prose artifact. |
| Architecture change | `CONDITIONAL`: update architecture documentation when verified boundaries, ownership, dependency direction, or runtime placement changes. Clockwork owns those technical facts; a proposed design is not as-built documentation. |
| Security change | `CONDITIONAL`: update security guidance when verified controls, configuration, user/operator steps, or exposure claims change. Cipher owns security facts; The Governor owns legal, privacy-governance, compliance, and licensing decisions. Do not publish sensitive details. |
| Release | `CONDITIONAL`: when release work is separately authorized, update release-facing claims from verified release evidence. A changelog entry does not create release authority, and this contract does not authorize release preparation. |
| Test-only or evidence-only change | Normally `NOT_APPLICABLE` to prose if documented commands and claims remain true. Update documentation only when a supported test instruction or claim changes, an existing requirement calls for it, or current changelog policy classifies the change as significant. Preserve evidence in its existing canonical surface rather than copying it into another report. |

Applicability scales with external impact and risk. Internal changes that do not alter documented behavior do not require a new prose artifact merely because code or evidence changed.

## Claim ownership and Scribe activation

The owner of the underlying fact verifies it; Scribe owns its clear, traceable representation. Conductor routes only the specialists needed for the unresolved facts.

| Claim or decision represented | Fact owner |
| --- | --- |
| Problem, business intent, scope, approved requirements, and acceptance | The Steward and the approved project record. |
| Legal, compliance, privacy-governance, licensing, and IP determinations | The Governor and its authoritative decision. |
| Architecture boundaries and runtime placement | Clockwork and the accepted architecture contract. |
| Security controls and threat facts | Cipher and verified security evidence. |
| Persistence and data semantics | Chronicler and verified schema or data evidence. |
| UI behavior and accessibility expectations | Cloak and applicable source or rendered evidence. |
| Implementation status | Current tracked source and the implementation owner; `IMPLEMENTED` is not `VALIDATED`. |
| Tests, validation, and QA conclusions | Overseer and current exact-candidate validation evidence. |
| Lifecycle transition or authority disposition | Arbiter and the applicable governance record. |
| Documentation structure, prose, links, and traceability | Scribe, without authority over the facts above. |

Activate Scribe when durable prose must be authored or reconciled, requirements must be traced into claims, a material documentation drift must be dispositioned, or user/operator/API/setup/release documentation changes. Do not require Scribe for every task: a code-only, test-only, or evidence-only change whose documentation remains accurate needs no Scribe work. A simple documentation-only edit may route directly to Scribe. Scribe may identify an unresolved claim and request re-entry; it cannot approve technical claims, governance decisions, validation, or release.

## Minimum traceability and drift handling

For each material changed claim, keep the shortest available forward and reverse path:

```text
approved objective / requirement
  -> implementation or an explained NOT_APPLICABLE relationship
  -> relevant test or validation evidence, when required
  -> documented claim with its source owner

documented claim
  -> evidence -> validation -> implementation -> approved requirement / objective
```

Use existing issue, requirement, specialist, test, evidence-packet, and candidate identifiers. Cite exact repository paths and exact commit/tree identity when the claim is revision-sensitive. A missing node is `NOT_APPLICABLE` only when assessed; use `MISSING_EVIDENCE` or `UNRESOLVED` when its basis is absent or contradictory. AI-generated prose is not evidence.

When claims diverge from current evidence, use the existing documentation vocabulary:

- `DOC_DRIFT`: documentation conflicts with verified current behavior; correct the claim when authorized and revalidate its links and evidence.
- `IMPLEMENTATION_DRIFT`: implementation conflicts with an approved requirement; route to the technical owner and applicable governance record instead of rewriting the requirement in prose.
- `MISSING_EVIDENCE`: required support for a claim is absent; qualify or withhold the claim until its owner supplies evidence.
- `UNRESOLVED`: evidence or authority conflicts; preserve both sides and route the decision through Conductor.
- `STALE_INVALIDATED`: a source, tree, base, scope, acceptance, or policy change invalidated previously bound evidence; replace the evidence before making a current claim.

Do not silently promote proposed, planned, implemented, failed, skipped, not-run, assumed, or historical material into approved, validated, passed, verified, or current claims.

## Existing contracts and efficiency safeguards

| Existing authority or tool | Reuse |
| --- | --- |
| [Prime Directive / Development Lifecycle V2](../governance/PRIME_DIRECTIVE_LIFECYCLE_V2_REALIGNMENT.md) | Lifecycle sequence and the separation between validation, adoption, merge, and release authority. |
| [Feature Admission Policy](../governance/FEATURE_ADMISSION_POLICY.md) and `machine/schemas/feature-decision-record.v1.schema.json` | Admission, promotion, and existing rationale evidence. |
| [Candidate Maturity and Feature Freeze](../governance/CANDIDATE_MATURITY_FEATURE_FREEZE.md) and `machine/schemas/candidate-maturity-record.v1.schema.json` | Candidate identity, scope, freeze, and evidence freshness. |
| [Qualification Gates, Evaluation, and Independent Audit](../governance/QUALIFICATION_GATES_EVALUATION_AUDIT.md) and `machine/schemas/qualification-gate-plan.v1.schema.json` | Risk-proportional qualification, gate applicability, and exact-candidate evidence. DOC-L1 outcomes do not replace its gate statuses. |
| [Phase Retrospective Protocol](../governance/PHASE_RETROSPECTIVE_PROTOCOL.md) | Existing retrospective triggers and record ownership; no duplicate closeout artifact. |
| [Scribe documentation standards](../../skills/scribe/DOCUMENTATION_STANDARDS.md), [traceability](../../skills/scribe/REQUIREMENTS_TRACEABILITY_GUIDE.md), [documentation reconciliation](../../skills/scribe/DOCUMENTATION_SYSTEM_RECONCILIATION_GUIDE.md), [governance integration](../../skills/scribe/GOVERNANCE_DOCUMENTATION_INTEGRATION_GUIDE.md), and [link and claim validation](../../skills/scribe/LINK_CLAIM_VALIDATION_GUIDE.md) | Evidence-backed prose, claim tracing, drift labels, specialist ownership, and non-authorizing documentation. |
| [Documentation impact validator](../../scripts/check_readme_impact.py) | Existing changed-path decisions for root README, machine index, and detailed documentation. Use its existing invocation; do not add a new mandatory CI gate. |

To avoid repeated work, assess the final changed-path set once, update the existing authoritative document instead of copying it, and run each applicable validation once against the final candidate. Add no new report when an existing issue, candidate record, validation output, or retrospective already carries the evidence. A source or candidate identity change invalidates only the dependent evidence, which must then be rerun under its existing contract.
