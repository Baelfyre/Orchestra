# Post-Run Assurance Invariant

PRAI closes a specialist work unit only after the output has been independently
assured. Green tests are evidence, not completion. The completion decision is
deterministic, evidence-only, and never grants execution, merge, release,
provider, or production authority.

## Work-unit contract

Every completed specialist work unit is represented by PraiWorkUnit in
orchestra_runtime/domain/adaptive/prai.py. The required fields are:

- logical_impact and logical_result
- security_impact, security_result, and explicit security_classification when security_impact is NONE
- audit_depth
- required_reviewers
- required_additional_assurance
- evidence_refs
- limitations
- overseer_sufficiency
- arbiter_disposition
- repository, source, candidate, tree, work-item, freshness, and version identity
- independently produced review_receipts

Each receipt binds the same repository, source ref, candidate SHA, tree SHA,
work item, freshness ref, version ref, schema version, evidence layer, evidence
scope, and reviewed paths.
Receipt and work-unit digests use the shared canonicalization helpers.

## Canonical schema and claim coverage

The machine schema and runtime parser use the same canonical field inventory. Every
serialized work-unit and receipt field is required except its derived digest, and
legacy aliases are rejected. The command-line validator reads and validates the
configured `--schema` before constructing or evaluating a work unit.

Risk characteristics are restricted to the allowlist published by the machine
contract. A PASS receipt must exactly cover every changed path, declared risk
characteristic, and declared invariant in the work unit. Partial, unrelated, or
empty claim coverage is insufficient, and unknown risk characteristics fail closed.

The baseline reviewers are Clockwork for logical/system integrity, Cipher for
security and authority integrity, and Overseer for evidence sufficiency. Arbiter
disposition is a transition input. Chronicler, Dagger, Steward, Governor, and
Cloak are added when risk characteristics trigger their owned boundary.
Implementers cannot produce their own assurance.

## Canonical vocabulary and scope relation

Risk labels are canonical uppercase values from the machine contract; serialized
non-canonical casing and unknown labels fail closed. Receipt evidence_layer uses
the AQ1 EVIDENCE_LAYERS vocabulary, while evidence_scope and claim_scope use the
AQ1 evidence-scope vocabulary. The runtime enforces
EVIDENCE_SCOPE_MUST_COVER_CLAIM_SCOPE using the canonical coverage relation, in
addition to exact changed-path, risk, and invariant coverage.

logical_identity is derived from substantive receipt identity, including the
version ref, and any supplied value must match it exactly. Changes to protected PRAI policy, runtime, schema,
or workflow paths derive self-modification and block by default; policy
qualification is not implicit.

## Adaptive audit depth

LIGHT is limited to explicitly classified harmless documentation work.
STANDARD applies to ordinary code or behavior work. DEEP is required for
authentication, authorization, privilege, tenant isolation, external input,
concurrency, state machines, destructive lifecycle, migration, recovery,
retry/idempotency, partial failure, sensitive provenance, resource pressure,
production-critical behavior, or medium-or-higher logical/security impact.

A receipt cannot claim a shallower depth than its work unit. Code-changing work
must include an audited changed path and an explicit assertion that the review
examined changed code.

## Fail-closed assurance

The evaluator blocks for all required negative classes:

1. green tests with a contradictory logical invariant;
2. security-sensitive work without Cipher evidence;
3. harmless documentation without explicit LIGHT logical/security classification;
4. implementer self-certification;
5. stale candidate identity;
6. stale tree identity;
7. LIGHT depth for deep-trigger work;
8. NONE security impact without explicit classification;
9. a broken caller contract;
10. tenant-to-global authority expansion;
11. missing Chronicler evidence when persistence/concurrency is triggered;
12. missing Dagger evidence when adversarial/authority risk is triggered;
13. contradictory logical receipts;
14. duplicate pseudo-independent receipts;
15. stale audit reuse after repair;
16. an audit that never examines changed code;
17. generic green CI substituted for specialist assurance;
18. PRAI policy self-modification used to certify the same work;
19. stale, mismatched, or missing current version context;
20. unknown or noncanonical evidence layers.

Receipt order is normalized before evaluation. Repairs change candidate identity
and require fresh receipts.

A `FAIL_POLICY_SELF_MODIFICATION` result remains `BLOCKED`. PRAI does not authorize an exception and does not amend itself. The orchestration layer must convert that protected stop into `GOVERNANCE_ESCALATION_REQUIRED`: freeze the originating candidate, route independent governance analysis, produce a human-review packet, and terminate the originating run. Any human-approved governance change is executed only in a new execution context under `PROTECTED_GOVERNANCE_ESCALATION_PROTOCOL.md`.

## AQ4/AQ5 integration and transport

The contract uses the AQ4 semantic assurance slots
POST_RUN_LOGICAL_ASSURANCE and POST_RUN_SECURITY_ASSURANCE. AQ5 validation
preserves candidate/tree binding, reviewer independence, security classification,
adaptive depth, receipt freshness, and authority non-expansion.

If native Arbiter MCP transport is rejected by host policy, the deterministic
in-process orchestra_runtime.governance_kernel.evaluate_arbiter fallback may
provide only a transition disposition. It cannot replace Clockwork, Cipher,
Overseer, or any triggered specialist evidence. Missing substantive reviewer
evidence remains fail-closed.

The command-line validator is:

~~~text
python -B scripts/validation/validate_prai.py --work-unit <json> \
  --repository <owner/name> --source-ref <sha> --candidate-sha <sha> \
  --tree-sha <sha> --work-item-ref <ref> --freshness-ref <timestamp> --version-ref <ref>
~~~

PRAI_COMPLETE_CANONICAL_VERIFIED is required before AQ6 admission. AQ6 and
AQ7 are the only authorized autonomous trial phases in the current campaign;
AQ8 and later phases are out of scope.
