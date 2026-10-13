# Project-Adaptive JEV Responsibility Adjudication

Status: `OFFLINE_CONTRACT_ONLY; NO_PRODUCTION_CALLER; UNQUALIFIED_HOST_TRUST; NO_PROVIDER_ACCESS`

Last verified against the source and tests in this branch: 2026-10-13.

## Scope and status

This document describes the versioned domain contract `orchestra.jev.responsibility-adjudication.v1`. It is a pure offline contract for optional specialist-responsibility advice. It is not integrated into a Conductor callsite, does not have a trusted host producer, and does not establish mandatory project policy or project applicability. It makes no provider request and uses no credentials.

The contract is separate from `orchestra.jev.adjudication.v1`, which represents the existing post-assessment mitigation-advice flow. Responsibility advice concerns whether a proposed specialist route is supported, should be rechecked, or has an ownership gap or conflict. It does not assess mitigations or replace the existing JEV flow.

## Inputs and binding

`ResponsibilityAdjudicationContext` accepts normalized `TaskProfile` and `AgenticWorkflowProfile` values, specialist-authority records, an authority-registry revision, an optional project-policy-context revision, a project/work-item identity, and a typed source identity. The workflow must identify the same task as the task profile, and referenced specialist roles must be recognized.

The project/work-item identity and source identity are separate. Source identities support a Git repository with commit and tree SHAs, an artifact with an explicit SHA-256 digest, or an artifact with a version. These are shape-checked identity values; their presence does not prove source authenticity or trust. The context has no independent source-scope attestation.

A binding digest is available only when project/work-item identity, source identity, and authority-registry revision are present and every required specialist has an authority record. The digest covers the versioned contract, task and workflow profiles, project/work-item and source identities, normalized specialist-authority content, and supplied registry and policy-context revisions. The policy-context revision is optional and is only an input to the digest, not proof of policy authority.

Changes to any covered task, workflow, source, work-item, specialist-authority, registry, or supplied policy-context value change the binding and make prior advice stale. Missing required binding inputs result in no advice. Digests and revision strings supplied by a caller remain unqualified and do not attest that the underlying records came from an independent or trusted producer.

## Applicability and evaluation

The caller must explicitly set `conductor_requested` to the exact boolean `true` before supplied advice can be considered. This flag is an unqualified request indicator, not authenticated Conductor provenance. A multi-specialist workflow alone does not trigger review. The contract always bypasses a clear single-owner route: one authority domain and one required specialist, single-owner concurrency, matching primary owner, and no re-entry specialist, critic contract, or escalation reason.

The contract does not infer whether a route is ambiguous and does not calculate which responsibility recommendation is correct. It structurally validates a supplied recommendation and checks whether its context digest still matches. A future caller may request this optional check for a contested route, but that behavior is not implemented here.

## Results

Supported advice values are `ROUTE_SUPPORTED`, `CONDUCTOR_RECHECK_RECOMMENDED`, `OWNERSHIP_GAP`, `OWNERSHIP_CONFLICT`, and `ABSTAIN`. Evaluation returns the supplied recommendation when the request is explicit, the route is not a clear single-owner bypass, the binding is complete, and the advice digest matches.

`NO_ADVICE` is returned when the request is absent, the route qualifies for single-owner bypass, binding inputs are insufficient, or advice is unavailable. The result does not encode which of those conditions applied. `STALE` is returned when supplied advice is bound to a different context. Malformed identities, unknown specialist roles, mismatched task/workflow identity, and unsupported recommendation values fail validation.

## Trust and authority limits

All context and recommendations are unqualified offline inputs. The domain contract does not validate independent provenance, consent, project policy, or a trusted host identity. It cannot authorize an operation, dispatch a specialist, activate The Tuner, issue completion credit, or block a read-only assessment. Conductor remains the router; The Tuner remains a coordinator and is not activated by this contract. No workflow transition or execution decision follows from an advice result.

The code contains no project-name-specific branch. The AlteredEgo test is a synthetic portability and assessment-safety example, not project-specific runtime behavior. It shows that an unapproved effectful action does not make this advisory contract block a read-only Cipher assessment; it does not authorize the effectful action.

## Verification and future integration

The synthetic tests cover contract version separation, missing identities, Git and non-Git source identity shapes, unknown roles, untrusted provenance, stale advice after context changes, authority-content changes, clear single-owner bypass, non-automatic multi-specialist behavior, explicit cross-domain advice, malformed recommendations, task/workflow binding, and non-authorizing result fields.

Local tests establish behavior of these typed offline fixtures only. They do not establish production integration, trusted source or authority evidence, mandatory project obligations, privacy or consent guarantees, or live provider compatibility. Any later runtime integration requires a separately approved trusted host contract, independently qualified inputs and applicability rules, and its own implementation and validation authority. This document grants none of those permissions.

## Source references

- [Responsibility-adjudication domain contract](../../orchestra_runtime/domain/adaptive/jev_responsibility_adjudication.py)
- [Existing post-mitigation JEV contract](../../orchestra_runtime/domain/adaptive/jev_adjudication.py)
- [Synthetic responsibility-adjudication tests](../../tests/runtime/test_jev_responsibility_adjudication.py)
