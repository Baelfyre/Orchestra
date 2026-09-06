# GitHub Copilot Live Capability Probe Guide

## Purpose

This guide defines the exact copy-paste capability probe to evaluate GitHub Copilot's live integration surfaces with Orchestra under the **Universal Adaptive Integration (UAI)** architecture.

Per UAI governance:
```text
CAPABILITY_NEVER_CREATES_AUTHORITY
DO_NOT_FABRICATE_SUPPORT_FROM_DOCUMENTATION
LIVE_EVIDENCE_OVERRIDES_VENDOR_CLAIMS
CONDUCTOR_IS_EXCLUSIVE_ROUTER
ORCHESTRA_COMMAND_INVOCATION != NATIVE_COPILOT_CUSTOM_AGENT_CAPABILITY
```

Capabilities not yet proven on the live Copilot surface remain `AVAILABLE_NOT_YET_VERIFIED` or `UNKNOWN`.

---

## Architectural Distinctions

1. **Orchestra Command Surface**: Orchestra canonically routes development tasks through slash commands such as `/conductor` (orchestration / routing) and `/ponytail` (bounded implementation).
2. **Native Copilot Custom-Agent Capability**: Host-level `@agent` support (e.g. `.github/agents/*.agent.md` or `@conductor`) is evaluated strictly as an optional host transport capability. Native `@agent` support is not a prerequisite for Orchestra routing authority.
3. **Transport Independence**: The UAI resolver maps Orchestra interactions to whatever transport the host supports (slash commands, repository instructions, agent skills, custom agents, MCP, extensions, or CLI). No single transport represents Orchestra's universal architecture.

---

## Probe Matrix Summary

| # | Probe Dimension | Target Surface | Test Mechanism | Deterministic Status | Maintainer Live Action Required |
|---|---|---|---|---|---|
| 1 | Repository & Workspace Instructions | `.github/copilot-instructions.md` | Ask Copilot to state primary Orchestra router | AVAILABLE_NOT_YET_VERIFIED | Prompt in Copilot Chat |
| 2 | Orchestra Command Recognition: Conductor | `/conductor` invocation | Probe A: route without implementing | AVAILABLE_NOT_YET_VERIFIED | Prompt in Copilot Chat |
| 3 | Orchestra Specialist Recognition: Ponytail | `/ponytail` invocation | Probe B: implementation boundaries | AVAILABLE_NOT_YET_VERIFIED | Prompt in Copilot Chat |
| 4 | Orchestra Command Separation | `/conductor` vs `/ponytail` | Probe C: contrast roles and authority | AVAILABLE_NOT_YET_VERIFIED | Prompt in Copilot Chat |
| 5 | Native Custom-Agent Capability | `.github/agents/*.agent.md` / UI picker | Probe D: check `@agent` selector support | AVAILABLE_NOT_YET_VERIFIED | Check agent picker in Chat |
| 6 | Agent Skills Discovery | `.github/skills/*/SKILL.md` or `skills/*/SKILL.md` | Ask Copilot to list available skills | AVAILABLE_NOT_YET_VERIFIED | Prompt in Copilot Chat |
| 7 | MCP Discovery & Tool Visibility | Workspace MCP configuration | Ask Copilot for available external tools | AVAILABLE_NOT_YET_VERIFIED | Check tool icon / call tools |
| 8 | Plugin / Extension Surface | GitHub Copilot Extensions | Inspect marketplace / extension menu | UNSUPPORTED / NOT_INSTALLED | Check extension list |
| 9 | CLI Surface | `gh copilot` or `@github/copilot-cli` | Run `gh copilot --version` | VERIFIED_UNSUPPORTED_LOCALLY | Local CLI verified missing |
| 10 | Workspace & File Permissions | Workspace file read/write | Ask Copilot to inspect `plugin.json` | AVAILABLE_NOT_YET_VERIFIED | Ask Copilot to read a file |
| 11 | Approval & Permission Controls | Edit acceptance / confirmation | Propose an edit to a test file | AVAILABLE_NOT_YET_VERIFIED | Observe diff acceptance flow |
| 12 | Model Selection Controls | Model picker in Copilot UI | Inspect available models (Claude, GPT-4o, o1, etc.) | AVAILABLE_NOT_YET_VERIFIED | Record available model options |
| 13 | Organization / Account Policy | Enterprise / Org policy settings | Observe any disabled features or warnings | AVAILABLE_NOT_YET_VERIFIED | Check for policy notices in Copilot |

---

## Copy-Paste Execution Procedures for Maintainer

### Probe 1: Repository Instructions Observability
**Surface**: GitHub Copilot Chat (VS Code, Web, or Cloud Agent)
**Copy-paste prompt**:
```text
According to the repository instructions for this project, what is the exclusive router and workflow orchestrator, and which specialist owns UI design?
```
**Expected verified evidence**:
- Copilot identifies `Conductor` as the exclusive router.
- Copilot identifies `cloak` as the UI specialist.
- Copilot cites `.github/copilot-instructions.md`.

---

### Probe A: Conductor Command Recognition
**Surface**: GitHub Copilot Chat (VS Code, Web, or Cloud Agent)
**Copy-paste prompt**:
```text
/conductor

Classify and route this task without implementing it:

Add a new unit test that validates an existing architecture boundary.

State:
1. task classification;
2. selected specialist or route;
3. why that route is appropriate;
4. authority boundaries;
5. whether implementation is authorized.
```
**Expected verified evidence**:
- `/conductor` recognized or correctly interpreted.
- Conductor acts as router/orchestrator.
- No direct implementation occurs merely from classification.
- Routing remains bounded by Orchestra specialist ownership.
- Capability does not create authority.
*(Do not hard-code an expected destination specialist if the current Orchestra routing contract legitimately chooses another valid specialist.)*

---

### Probe B: Ponytail Specialist Recognition
**Surface**: GitHub Copilot Chat (VS Code, Web, or Cloud Agent)
**Copy-paste prompt**:
```text
/ponytail

Without modifying any files, explain how you would approach a small implementation change that simplifies existing code while preserving observable behavior.

Also state:
1. your specialist role;
2. what work you own;
3. what work you must not override;
4. when the task must return to Conductor or another specialist.
```
**Expected verified evidence**:
- `/ponytail` recognized or correctly interpreted.
- Ponytail identifies as bounded implementation specialist.
- Ponytail does not claim Conductor routing authority.
- Ponytail does not override architecture, UI fidelity, security, persistence, or governance ownership.
- Complexity reduction must preserve accepted behavior/design requirements.
- Cross-specialist needs return through Conductor.

---

### Probe C: Command Separation
**Surface**: GitHub Copilot Chat (VS Code, Web, or Cloud Agent)
**Copy-paste prompt**:
```text
According to this repository's Orchestra instructions, explain the difference between:

/conductor
/ponytail

Do not modify any files.
```
**Expected verified evidence**:
- `/conductor` = orchestration / routing entry.
- `/ponytail` = bounded implementation specialist.
- `CONDUCTOR != PONYTAIL`.
- `ROUTING_AUTHORITY != IMPLEMENTATION_AUTHORITY`.

---

### Probe D: Native Copilot Custom-Agent Observation
**Surface**: GitHub Copilot Chat (agent selection menu or `@` mention)
**Action**:
- Check whether the Copilot UI exposes custom agents or an `@` agent selector (e.g. typing `@` in Chat).
- Record the observed state:
  - `SUPPORTED_VERIFIED`: Custom agent menu lists workspace or user agents.
  - `SUPPORTED_WITH_LIMITS`: Custom agent recognized only in specific surfaces or with limitations.
  - `UNSUPPORTED`: No `@` agent mechanism exposed.
  - `BLOCKED_BY_POLICY`: Disabled by organization or account policy.
  - `UNKNOWN`: Not determinable from current interface.
**Boundary Note**:
- Native `@agent` support is recorded strictly as host capability; it is not a prerequisite for Orchestra.

---

### Probe 2: Agent Skills Discovery
**Surface**: GitHub Copilot Chat
**Copy-paste prompt**:
```text
List all Orchestra skills available in this workspace and display the primary purpose of the 'clockwork' and 'cipher' skills.
```
**Expected verified evidence**:
- Copilot recognizes `skills/*/SKILL.md` or reports which skill directories are indexed.

---

### Probe 4: MCP Tool Visibility
**Surface**: GitHub Copilot Chat (with MCP enabled)
**Copy-paste prompt**:
```text
What external MCP tools are currently configured and callable in this session?
```
**Expected verified evidence**:
- Copilot lists MCP tools or reports that MCP tool transport is not active/available.

---

### Probe 5 & 6: Extension & CLI Inspection
**Local command output already recorded**:
- `gh copilot --version` -> `! Copilot CLI not installed`
- `code --list-extensions` -> `github.copilot` not installed in default local profile.

---

### Probe 7 & 8: File Access and Approval Controls
**Surface**: GitHub Copilot Chat
**Copy-paste prompt**:
```text
Read lines 1-10 of plugin.json and show the exact version string without modifying the file.
```
**Expected verified evidence**:
- Copilot reads `plugin.json` and outputs `"version": "1.9.0"`.

---

### Probe 9: Model Selection Controls
**Surface**: GitHub Copilot Chat UI
**Action**:
- Check the model dropdown in the Copilot Chat interface.
- Record the exact list of available models (e.g., `Claude 3.5 Sonnet`, `GPT-4o`, `o1-preview`, `o1-mini`).

---

### Probe 10: Policy Restrictions
**Surface**: GitHub Copilot Chat / GitHub.com settings
**Action**:
- Check whether any features are marked disabled by organization or account policy (e.g., CLI disabled, telemetry policy, model restrictions).
