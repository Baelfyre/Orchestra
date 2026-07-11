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
