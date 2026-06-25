# Decision Log

## Date: 2026-06-26

**Decision:**
Add lightweight project memory files (`PROJECT_STATE.md`, `SESSION_HANDOFF.md`, `DECISION_LOG.md`, `.amalgam/state.json`).

**Reason:**
Prevent cross-session drift, preserve latest validated state, and reduce reliance on raw transcript history.

**Rejected Alternatives:**
- Raw transcript logs
- SQL database
- Large JSON-only memory
- Adding new Governor or Stewardess roles at this stage

**Affected Components:**
- Amalgam Conductor orchestration behavior
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
- `skills/amalgam-conductor/SKILL.md`
- `skills/meister-chronicler/SKILL.md`
- `skills/scribe-meister/SKILL.md`
- `skills/acme-overseer/SKILL.md`

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
- .amalgam/state.json, if created
- Amalgam startup workflow
- Workspace Boundary Gate
- Session Isolation Gate
