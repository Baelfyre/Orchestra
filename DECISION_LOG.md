# Decision Log

## Date: 2026-06-26

**Decision:**
Add lightweight project memory files (`PROJECT_STATE.md`, `SESSION_HANDOFF.md`, `DECISION_LOG.md`).

**Reason:**
Prevent cross-session drift, preserve latest validated state, and reduce reliance on raw transcript history.

**Rejected Alternatives:**
- Raw transcript logs
- SQL database
- Large JSON-only memory
- Adding new Governor or Stewardess roles at this stage

**Affected Components:**
- Conductor orchestration behavior
- Repo startup workflow
- Future audit and implementation safety

---

## Date: 2026-06-26

**Decision:**
Implement initial Governance Gates (Workspace Boundary, Session Isolation, Audit Mode, Record Accuracy, Caveman Public-Content Exclusion, Ponytail Handoff Restriction, Acme Readiness Gate Expansion).

**Reason:**
Address failure caused by cross-repository context drift where an agent edited the wrong repo (`C:\+AA`) due to stale context.

**Rejected Alternatives:**
- Creating new specialist agents to handle these specific gates.

**Affected Components:**
- `skills/conductor/SKILL.md`
- `skills/chronicler/SKILL.md`
- `skills/scribe/SKILL.md`
- `skills/overseer/SKILL.md`

---

## Date: 2026-06-26

**Decision:**
Use lightweight curated memory files as a token-control and drift-prevention mechanism.

**Reason:**
Repeated prompts, repeated corrections, stale context, and cross-repo drift create unnecessary token usage and implementation risk. A concise repo-local state file can reduce friction by preserving the latest validated state without loading raw conversation history.

**Rejected Alternatives:**
- raw transcript logs
- large history dumps
- SQL memory storage
- long JSON-only memory
- relying only on chat history

**Affected Components:**
- PROJECT_STATE.md
- SESSION_HANDOFF.md
- DECISION_LOG.md
- Orchestra startup workflow
- Workspace Boundary Gate
- Session Isolation Gate

---

## Date: 2026-07-03

**Decision:**
Strengthen Codex adapter export validation so exported routing, governance skills, and relative Markdown links are verified before Codex installation.

**Reason:**
The Codex adapter can pass structural validation while missing governance skills or support documents that exported Conductor and specialist skills reference at runtime.

**Rejected Alternatives:**
- Relying on manual adapter inspection
- Keeping Governor activation-level skills out of the Codex export
- Installing Codex skills before export validation

**Affected Components:**
- adapters/codex/export-codex-skills.ps1
- adapters/codex/validate_codex_export.py
- scripts/refresh-installed-integrations.ps1
- scripts/governance_check.py
- scripts/runtime_guardrail.py

---

## Date: 2026-07-10

**Decision:**
Published v1.1.0 (Specialist Governance & Boundary Standard). Opened v1.1.1 post-release hardening track to fix release-surface drift, stale startup state, and validation gaps found in the post-release audit.

**Reason:**
Post-release audit confirmed core is healthy (42 runtime tests pass, strict governance passes), but Codex metadata and example manifest were stuck at v1.0.0, startup state files referenced a merged branch, and governance only checked path existence in memory files.

**Rejected Alternatives:**
- Regenerating the drifted example manifest (removed instead; canonical plugin.json and MANIFEST_SCHEMA.md suffice)
- Advisory-only governance for structured startup-state claims (strict mode chosen because startup-state accuracy is the stated purpose of these files)

**Affected Components:**
- Codex plugin.json
- Example manifest (deleted)
- scripts/check_for_updates.py
- scripts/validate_structure.py
- scripts/governance_check.py
- PROJECT_STATE.md
- SESSION_HANDOFF.md
- PROJECT_CONTEXT.md

---

## Date: 2026-07-11

**Decision:**
Transition from transient checkout branch validation to stable repository branch policy checking. The validator now parses and verifies `Canonical Branch` and `Base Branch` policy claims in committed files, rather than matching them against `git branch --show-current`.

**Reason:**
Transient checkout branches are runtime facts, not durable repository-memory facts. Validating them strictly against committed files forces developers to modify committed repository files for every temporary feature branch name, creating self-invalidating state as soon as a pull request merges into the default branch. Using `Canonical Branch: main` avoids making `main` stale immediately post-merge.

**Rejected Alternatives:**
- Advisory-only startup-state validation (rejected; strict startup-state validation remains required for version and baseline alignment).
- Bypassing branch policy checks entirely.

**Affected Components:**
- scripts/governance_check.py
- scripts/test_governance_check.py
- PROJECT_STATE.md
- SESSION_HANDOFF.md

---

## Date: 2026-07-11

**Decision:**
Implemented a deterministic internal validator script (`scripts/validate_artificer_internal.py`) and integrated it into strict governance checking and the behavior runner. The validator enforces schema integrity, markdown boundaries, and ensures non-registration of Artificer on any public runtime surfaces.

**Reason:**
Phase 2 introduces strict enforcement of the Artificer Phase 1 specification boundaries. Artificer must remain internal and non-routable to maintain separation of concerns. Since dynamic execution or external audits are not supported in this phase, no external source execution or audit runtime is introduced. Furthermore, standard library tools were used exclusively, avoiding third-party validation dependencies (such as `jsonschema`).

**Rejected Alternatives:**
- Automatic file repair (rejected; the validator reports failures but does not automatically modify files to prevent accidental configuration rewrites).
- Advisory-only checking for Artificer specification (rejected; strict validation is required to prevent accidental registration in public command/skill surfaces).

**Affected Components:**
- scripts/validate_artificer_internal.py
- tests/behavior/test_artificer_internal.py
- scripts/governance_check.py
- tests/behavior/run_tests.py
- PROJECT_STATE.md
- SESSION_HANDOFF.md

---

## Date: 2026-07-11

**Decision:**
Strengthened the Artificer boundary validator and test suite to resolve false-positive tests identified during a post-merge audit. The validator has been refactored to expose pure, testable functions returning `ValidationFailure` dataclass instances. Documentation-boundary negative safety contracts now require explicit Artificer-bound prohibition statements.

**Reason:**
PR #158 successfully merged the Phase 2 validator, but subsequent audit revealed that some regression tests used placeholder `pass` blocks, did not assert validator responses, or allowed unrelated negative statements to satisfy negative safety contracts. A narrow follow-up PR was chosen instead of reverting. Passing tests now verify the entire repository via `validate_repository()`, and a quality gate prevents any placeholder or unasserted tests in the test suite.

**Rejected Alternatives:**
- Reverting PR #158 (rejected; the validator functionality is sound and integration is correct; fixing the tests directly is less disruptive).
- Allowing implicit or general negative safety contracts (rejected; without explicit Artificer-bound prohibition statements, unrelated negative text can satisfy a contract, risking false-positives).

**Affected Components:**
- scripts/validate_artificer_internal.py
- tests/behavior/test_artificer_internal.py
- internal/artificer/ARTIFICER.md
- CHANGELOG.md
- DECISION_LOG.md
- PROJECT_STATE.md
- SESSION_HANDOFF.md

---

## Date: 2026-07-11

**Decision:**
Completed the specialist-boundary polarity enforcement within the Artificer internal boundary validator (`scripts/validate_artificer_internal.py`). Refactored all keyword-presence validation checks in `check_artificer_boundaries_md()` to require explicit Artificer-bound negative polarity. Introduced sub-clause split-normalizer capabilities and subject-inheritance to reject mixed-polarity bypasses (e.g. positive permissions paired with unrelated negative clauses).

**Reason:**
A final review of PR #159 identified that several specialist boundary checks in `check_artificer_boundaries_md()` still validated boundaries using simple keyword presence rather than explicit polarity. Simple keyword presence could allow positive permission statements to satisfy a safety contract. Explicit positive permission detection and mixed-polarity test cases have been added to the behavior test suite, verifying that positive/mixed statements successfully trigger validation failures. A narrow follow-up PR was chosen to preserve the integrated validator structure.

**Rejected Alternatives:**
- Verbatim paragraph matching (rejected; matching whole paragraphs verbatim reduces flexibility and is brittle to formatting updates in the specs).
- Deferring the final polarity checks (rejected; keyword-only validation left open potential false-positives for critical safety contracts).

**Affected Components:**
- scripts/validate_artificer_internal.py
- tests/behavior/test_artificer_internal.py
- CHANGELOG.md
- DECISION_LOG.md
- PROJECT_STATE.md
- SESSION_HANDOFF.md

---

## Date: 2026-07-11

**Decision:**
Implemented the Phase 3 Artificer Source-Intake and Pattern-Record Instance Validator, then hardened its schema-configuration defenses, cross-platform path handling, and empty-examined-range tracking. A comprehensive test suite with 54 regression assertions ensures the validator rejects anomalies and missing layouts strictly.

**Reason:**
To assure that governance standards strictly enforce metadata shape, registry formatting, internal slug and boundary constraints, without ever evaluating external source logic dynamically or communicating with external APIs.

**Rejected Alternatives:**
- Using an external JSON schema validator (rejected; requires additional external Python dependencies).
- Live code evaluation of patterns (rejected; explicitly forbidden by governance rules).

**Affected Components:**
- scripts/validate_artificer_records.py
- tests/behavior/test_artificer_records.py
- internal/artificer/records/README.md
- scripts/governance_check.py
- tests/behavior/run_tests.py

---

## Date: 2026-07-12

**Decision:**
Implemented the Phase 4A Artificer Governance Contracts foundation. Created native JSON schemas for Audit Reports, Evolution Proposals, Governance Decisions, and Promotion Records, separating governance outcomes from extraction classification. Created isolated read-only registries for the new records and explicitly documented the Phase 4 no-execution and read-only boundaries.

**Reason:**
Phase 4 separates extraction taxonomy from governance decisions, ensuring a robust, contract-only governance foundation. Phase 4A made narrow, required changes to `internal/artificer/SOURCE_INTAKE_SCHEMA.json`, `internal/artificer/PATTERN_SCHEMA.json`, `scripts/validate_artificer_internal.py`, and focused regression tests to require `default_branch` and separate extraction classifications from governance outcomes.

**Rejected Alternatives:**
- Broad legacy-validator refactoring (rejected; only the narrow contract and boundary changes required by Phase 4A were made).

**Affected Components:**
- internal/artificer/AUDIT_REPORT_SCHEMA.json
- internal/artificer/EVOLUTION_PROPOSAL_SCHEMA.json
- internal/artificer/GOVERNANCE_DECISION_SCHEMA.json
- internal/artificer/PROMOTION_RECORD_SCHEMA.json
- docs/internal/SECURITY_BOUNDARIES.md
- docs/internal/EVIDENCE_REQUIREMENTS.md
- internal/artificer/CHECKLIST.md
- docs/internal/PATTERN_CLASSIFICATION.md

---

## Date: 2026-07-12

**Decision:**
Implemented the separate Phase 4B governance-record validator with deterministic registry-layout, schema, semantic, and cross-record checks for audits, decisions, proposals, and promotions.

**Reason:**
The governance chain must remain traceable and fail closed without cloning, installing, compiling, or executing external sources. Phase 4B does not mutate the Pattern Catalog; strict governance and behavior runners execute the validator.

**Affected Components:**
- scripts/validate_artificer_governance_records.py
- tests/behavior/test_artificer_governance_records.py
- scripts/governance_check.py
- tests/behavior/run_tests.py

---

## Date: 2026-07-12

**Decision:**
Implemented Phase 4C-A as a standard-library-only, read-only renderer that
validates the complete Phase 4B governance repository before converting one
canonical audit JSON record into deterministic Markdown on standard output.

**Reason:**
Human-readable audit views must preserve validated JSON as the sole governance
authority, remain independent of repository location and filesystem order, and
create no Catalog, governance, source, or runtime writes.

**Rejected Alternatives:**
- Writing rendered Markdown files (rejected; Phase 4C-A is stdout-only).
- Combining Catalog synchronization with rendering (rejected; Phase 4C-B owns
  the separate Pattern Catalog gate).
- Adding a Markdown or schema dependency (rejected; existing validation and the
  Python standard library cover the required behavior).

**Affected Components:**
- scripts/render_artificer_audit_report.py
- tests/behavior/test_artificer_audit_report_renderer.py
- scripts/governance_check.py
- scripts/test_governance_check.py
- tests/behavior/run_tests.py
- docs/internal/ARTIFICER_PHASE4_GOVERNANCE_CONTRACT.md
- docs/internal/ARTIFICER_WORKFLOW.md
- internal/artificer/reviews/README.md

---

## Date: 2026-07-12

**Decision:**
Implement Phase 4C-B as a deterministic, read-only gate that treats validated
promotion JSON as canonical and `docs/internal/PATTERN_CATALOG.md` as a manual,
human-readable projection that must match those records exactly.

**Reason:**
The Catalog must remain manually synchronized, fully traceable, and unable to
invent implementation or approval authority in Markdown. Exact whole-file
comparison keeps stale rows, stale entries, reordered content, and formatting
drift visible at the first deterministic line mismatch.

**Rejected Alternatives:**
- Automatic Catalog rewrites (rejected; Phase 4C-B is read-only).
- Catalog-derived authority (rejected; validated JSON promotion records remain canonical).
- Advisory-only mismatch reporting (rejected; the Catalog gate is a strict validator).

**Affected Components:**
- scripts/validate_artificer_pattern_catalog.py
- tests/behavior/test_artificer_pattern_catalog.py
- scripts/governance_check.py
- scripts/test_governance_check.py
- tests/behavior/run_tests.py
- docs/internal/PATTERN_CATALOG.md
- docs/internal/ARTIFICER_PHASE4_GOVERNANCE_CONTRACT.md
- docs/internal/ARTIFICER_WORKFLOW.md
- internal/artificer/promotions/README.md
- internal/artificer/CHECKLIST.md

---

## Date: 2026-07-12

**Decision:**
Audit OpenHero and Strix in separate PRs. OpenHero is the first Phase 4.5
pilot, pinned to commit `16ffaa7e6dc39eb390011d81c420353b5d1dbaff`, and the
pilot remains static and read-only.

**Reason:**
Pilot evidence must stay pinned, scoped, and reviewable without mixing two
external repositories or implying governance advancement. Phase 4.5-A creates
source-intake, pattern, and audit records only. Media libraries and third-party
assets stay outside the code-license conclusion. The substring-domain allowlist
is recorded as `OUT_OF_SCOPE` source classification, not as a governance
rejection. Governance decisions, proposals, promotions, and Catalog updates
remain later manual actions.

**Rejected Alternatives:**
- Auditing OpenHero and Strix together (rejected; mixes evidence and raises review risk).
- Treating the substring allowlist as a governance rejection record (rejected; Phase 4.5-A records source findings only).
- Advancing directly into proposal or promotion artifacts (rejected; pilot is evidence-only).

**Affected Components:**
- internal/artificer/records/cristianolivera1__openhero__16ffaa7e6dc3/source-intake.json
- internal/artificer/records/cristianolivera1__openhero__16ffaa7e6dc3/patterns/responsive-progressive-gallery.json
- internal/artificer/records/cristianolivera1__openhero__16ffaa7e6dc3/patterns/optimistic-engagement-state-reconciliation.json
- internal/artificer/records/cristianolivera1__openhero__16ffaa7e6dc3/patterns/fallback-backed-code-loading.json
- internal/artificer/records/cristianolivera1__openhero__16ffaa7e6dc3/patterns/layered-archive-submission-validation.json
- internal/artificer/records/cristianolivera1__openhero__16ffaa7e6dc3/patterns/substring-domain-allowlist.json
- internal/artificer/reviews/cristianolivera1__openhero__16ffaa7e6dc3/audit-report.json
- docs/internal/ARTIFICER_PHASE4_GOVERNANCE_CONTRACT.md
- docs/internal/ARTIFICER_WORKFLOW.md
- internal/artificer/CHECKLIST.md
---

## Date: 2026-07-12

**Decision:**
Conduct the Strix pilot independently from the completed OpenHero pilot. Phase
4.5-B is pinned to commit
`09872744f5a9d3ffad750478f823e656ac1a7c88` and is limited to static,
read-only inspection of selected orchestration and safety-boundary files.

No Strix code, dependency, Docker image, model, agent, scan, target, exploit,
payload, API, browser, shell, proxy, or external tool may be executed. Offensive
skill and payload directories remain excluded from the audit.

The reviewed repository and package metadata declare Apache-2.0. Any future
reuse, adaptation, or distribution requires Governor and maintainer review of
license-copy, attribution, NOTICE, modified-file, patent, and trademark
obligations.

The fail-open system-prompt rendering mechanism is recorded as an
`OUT_OF_SCOPE` source-pattern classification. It is not a governance rejection.

OpenHero records remain unchanged. Strix findings are audit evidence only and
do not constitute a vulnerability disclosure, governance approval, proposal,
promotion, Pattern Catalog entry, pentesting authorization, or implementation
authorization.

**Reason:**
Strix is a high-risk offensive-security source whose documented capabilities
include dynamic testing, shell access, Docker-backed execution, exploitation,
and proof-of-concept generation. Restricting the pilot to pinned static evidence
keeps the Artificer audit non-executing, independently reviewable, and within
the approved governance boundary.

**Rejected Alternatives:**
- Auditing Strix together with OpenHero (rejected; the pilots require separate evidence and review chains).
- Installing or executing Strix to validate runtime behavior (rejected; external execution is prohibited).
- Reviewing exploit skills, payloads, targets, or proof-of-concept artifacts (rejected; outside the authorized pilot scope).
- Treating the prompt-rendering finding as a governance rejection (rejected; this phase creates source and audit evidence only).
- Advancing directly into decisions, proposals, promotions, Catalog synchronization, or implementation (rejected; those remain later manual actions).

**Affected Components:**
- CHANGELOG.md
- DECISION_LOG.md
- PROJECT_STATE.md
- SESSION_HANDOFF.md
- docs/internal/ARTIFICER_PHASE4_GOVERNANCE_CONTRACT.md
- docs/internal/ARTIFICER_WORKFLOW.md
- internal/artificer/CHECKLIST.md
- internal/artificer/records/usestrix__strix__09872744f5a9/source-intake.json
- internal/artificer/records/usestrix__strix__09872744f5a9/patterns/declared-scope-context.json
- internal/artificer/records/usestrix__strix__09872744f5a9/patterns/validated-specialist-delegation.json
- internal/artificer/records/usestrix__strix__09872744f5a9/patterns/lifecycle-gated-agent-completion.json
- internal/artificer/records/usestrix__strix__09872744f5a9/patterns/run-wide-tool-extension-registry.json
- internal/artificer/records/usestrix__strix__09872744f5a9/patterns/fail-open-system-prompt-rendering.json
- internal/artificer/reviews/usestrix__strix__09872744f5a9/audit-report.json

---

## Date: 2026-07-12

**Decision:**
Recorded Phase 5B-A OpenHero governance decisions for three approved concept-only reference patterns, one deferred concept-only UI pattern, and one rejected security anti-pattern. No Strix governance decisions, proposals, promotions, Pattern Catalog changes, or implementation authority were created in this Phase 5B-A record set.

**Reason:**
The Phase 5A independent governance review established the corrected OpenHero dispositions, and the Maintainer adopted those outcomes. Recording OpenHero decisions separately preserves licensing and security review clarity, keeps the MIT-licensed OpenHero governance chain independent from the Apache-2.0 Strix review, and prevents premature proposal, promotion, Pattern Catalog, or implementation advancement.

Approved `REFERENCE_ONLY` patterns remain restricted to `CONCEPT_ONLY`. The deferred UI pattern requires an approved roadmap need before advancement. The `OUT_OF_SCOPE` substring-domain mechanism is rejected and implementation-blocked. No OpenHero source reuse, media reuse, or third-party asset reuse is authorized.

**Rejected Alternatives:**
- Recording OpenHero and Strix decisions together.
- Automatically approving all audited patterns.
- Approving Responsive Progressive Gallery without a roadmap need.
- Approving the substring allowlist as an implementation pattern.
- Creating a proposal or promotion in the same phase.
- Copying external source implementation.

**Affected Components:**
- CHANGELOG.md
- DECISION_LOG.md
- PROJECT_STATE.md
- SESSION_HANDOFF.md
- docs/internal/ARTIFICER_PHASE4_GOVERNANCE_CONTRACT.md
- docs/internal/ARTIFICER_WORKFLOW.md
- internal/artificer/decisions/cristianolivera1__openhero__16ffaa7e6dc3/fallback-backed-code-loading.json
- internal/artificer/decisions/cristianolivera1__openhero__16ffaa7e6dc3/layered-archive-submission-validation.json
- internal/artificer/decisions/cristianolivera1__openhero__16ffaa7e6dc3/optimistic-engagement-state-reconciliation.json
- internal/artificer/decisions/cristianolivera1__openhero__16ffaa7e6dc3/responsive-progressive-gallery.json
- internal/artificer/decisions/cristianolivera1__openhero__16ffaa7e6dc3/substring-domain-allowlist.json

---

## Date: 2026-07-12

**Decision:**
Recorded Phase 5B-B Strix governance decisions for four approved concept-only patterns and one rejected implementation-blocked prompt-safety anti-pattern. Governor review was mandatory for all Strix records. No proposal, promotion, Pattern Catalog update, source reuse, prompt reuse, or implementation authority was created in this phase, and existing OpenHero decisions remain unchanged.

**Reason:**
The Strix review is security-sensitive and Apache-2.0 licensed, so governance decisions must be recorded separately from OpenHero and require mandatory Governor review. The Phase 5A independent review provided corrected dispositions, and this record preserves evidence, licensing, security, and specialist traceability without advancing any proposals or Catalog lifecycle changes.

Approved `REFERENCE_ONLY` patterns remain restricted to `CONCEPT_ONLY`, while the `OUT_OF_SCOPE` fail-open prompt-rendering pattern cannot receive `APPROVED` status and is therefore rejected with `IMPLEMENTATION_BLOCKED`. Governor approval accepts the governance disposition and restriction only; it does not authorize Strix source, prompt, payload, example, or implementation reuse.

**Rejected Alternatives:**
- Combining OpenHero and Strix decisions in one PR.
- Treating Governor review as optional.
- Automatically promoting approved decisions.
- Approving the fail-open prompt mechanism.
- Copying Strix source, prompts, payloads, examples, or implementation.
- Creating the authority/capability proposal in this same phase.
- Modifying the Pattern Catalog before promotion.

**Affected Components:**
- CHANGELOG.md
- DECISION_LOG.md
- PROJECT_STATE.md
- SESSION_HANDOFF.md
- docs/internal/ARTIFICER_PHASE4_GOVERNANCE_CONTRACT.md
- docs/internal/ARTIFICER_WORKFLOW.md
- internal/artificer/decisions/usestrix__strix__09872744f5a9/declared-scope-context.json
- internal/artificer/decisions/usestrix__strix__09872744f5a9/fail-open-system-prompt-rendering.json
- internal/artificer/decisions/usestrix__strix__09872744f5a9/lifecycle-gated-agent-completion.json
- internal/artificer/decisions/usestrix__strix__09872744f5a9/run-wide-tool-extension-registry.json
- internal/artificer/decisions/usestrix__strix__09872744f5a9/validated-specialist-delegation.json

---

## Date: 2026-07-12

**Decision:**
Implemented Issue #171 governance, prompt-load, and routing recalibration before Artificer Phase 5C. Established one canonical shared governance decision protocol, restored Conductor to lightweight routing, added deterministic routing and governance anti-drift validation, and defined the post-cleanup prompt-load bootstrap baseline. No Artificer proposal, promotion, Pattern Catalog update, source-reuse authority, prompt-reuse authority, or implementation authority was created in this issue.

**Reason:**
Governance decision values, gate rules, ownership statements, and compact output structure had drifted across the governance layer and specialist skill files. Conductor had also grown beyond its historical review baseline and was repeating routing and governance material that already belonged in lighter canonical sources. Issue #171 needed deterministic protection before Phase 5C so future changes cannot silently reintroduce duplicated policy, route architecture or governance work straight to Ponytail, or self-raise prompt-load baselines to hide drift.

The canonical shared protocol now lives in `docs/governance/GOVERNANCE_DECISION_PROTOCOL.md`. Shared decision values remain `APPROVED`, `ADVISORY_ONLY`, `REVISION_REQUIRED`, `BLOCKED`, and `NOT_APPLICABLE`. Shared gates remain blocking for governance `BLOCKED`, pausing for `REVISION_REQUIRED`, pausing for `human_review_required: true`, and blocking for Arbiter `HOLD` or `BLOCKED`. Steward and Governor retain role-specific output fields and review nuance only. The prompt-load bootstrap baseline is explicit configuration enforced by strict governance rather than advisory reporting alone.

**Rejected Alternatives:**
- Keeping duplicated decision tables and gate rules in multiple governance files.
- Letting Conductor continue to carry repeated routing and governance policy instead of routing from lighter canonical sources.
- Treating routing benchmarks as sufficient without deterministic fixture validation.
- Raising baselines implicitly inside the same feature change that caused growth.
- Beginning Artificer Phase 5C before governance and routing drift protections were in place.

**Affected Components:**
- CHANGELOG.md
- DECISION_LOG.md
- PROJECT_STATE.md
- SESSION_HANDOFF.md
- SKILL_INDEX.md
- ROUTING_MAP.md
- docs/governance/GOVERNANCE_LAYER.md
- docs/governance/GOVERNANCE_DECISION_PROTOCOL.md
- docs/performance/PROMPT_LOAD_BASELINE.json
- docs/performance/PROMPT_LOAD_RECALIBRATION_AUDIT.md
- docs/performance/PROMPT_LOAD_THRESHOLD_POLICY.md
- skills/conductor/SKILL.md
- skills/the-steward/SKILL.md
- skills/the-governor/SKILL.md
- adapters/codex/skills/conductor/SKILL.md
- adapters/codex/skills/conductor/ROUTING_MAP.md
- adapters/codex/skills/the-steward/SKILL.md
- adapters/codex/skills/the-governor/SKILL.md
- adapters/codex/validate_codex_export.py
- scripts/measure_prompt_load.py
- scripts/check_prompt_load_thresholds.py
- scripts/validate_prompt_load_budget.py
- scripts/validate_governance_protocol_consistency.py
- scripts/validate_routing_contract.py
- scripts/governance_check.py
- scripts/test_governance_check.py
- tests/behavior/router-contract-fixtures.json
- tests/behavior/test_prompt_load_budget.py
- tests/behavior/test_governance_protocol_consistency.py
- tests/behavior/test_router_contracts.py
- tests/behavior/run_tests.py
