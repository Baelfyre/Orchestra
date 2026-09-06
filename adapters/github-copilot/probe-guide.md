# GitHub Copilot Live Capability Probe Guide

## Purpose

This guide defines the exact copy-paste capability probe to evaluate GitHub Copilot's live integration surfaces with Orchestra under the **Universal Adaptive Integration (UAI)** architecture.

Per UAI governance:
```text
CAPABILITY_NEVER_CREATES_AUTHORITY
DO_NOT_FABRICATE_SUPPORT_FROM_DOCUMENTATION
LIVE_EVIDENCE_OVERRIDES_VENDOR_CLAIMS
```

Capabilities not yet proven on the live Copilot surface remain `AVAILABLE_NOT_YET_VERIFIED` or `UNKNOWN`.

---

## Probe Matrix Summary

| # | Probe Dimension | Target Surface | Test Mechanism | Deterministic Status | Maintainer Live Action Required |
|---|---|---|---|---|---|
| 1 | Repository & Workspace Instructions | `.github/copilot-instructions.md` | Ask Copilot to state primary Orchestra router | AVAILABLE_NOT_YET_VERIFIED | Prompt in Copilot Chat |
| 2 | Agent Skills Discovery | `.github/skills/*/SKILL.md` or `skills/*/SKILL.md` | Ask Copilot to list available skills | AVAILABLE_NOT_YET_VERIFIED | Prompt in Copilot Chat |
| 3 | Custom Agent Support | `.github/agents/*.agent.md` | Invoke `@conductor` or custom agent | AVAILABLE_NOT_YET_VERIFIED | Check agent picker in Chat |
| 4 | MCP Discovery & Tool Visibility | Workspace MCP configuration | Ask Copilot for available external tools | AVAILABLE_NOT_YET_VERIFIED | Check tool icon / call tools |
| 5 | Plugin / Extension Surface | GitHub Copilot Extensions | Inspect marketplace / extension menu | UNSUPPORTED / NOT_INSTALLED | Check extension list |
| 6 | CLI Surface | `gh copilot` or `@github/copilot-cli` | Run `gh copilot --version` | VERIFIED_UNSUPPORTED_LOCALLY | Install if desired, else instruction path |
| 7 | Workspace & File Permissions | Workspace file read/write | Ask Copilot to inspect `plugin.json` | AVAILABLE_NOT_YET_VERIFIED | Ask Copilot to read a file |
| 8 | Approval & Permission Controls | Edit acceptance / confirmation | Propose an edit to a test file | AVAILABLE_NOT_YET_VERIFIED | Observe diff acceptance flow |
| 9 | Model Selection Controls | Model picker in Copilot UI | Inspect available models (Claude, GPT-4o, o1, etc.) | AVAILABLE_NOT_YET_VERIFIED | Record available model options |
| 10 | Organization / Account Policy | Enterprise / Org policy settings | Observe any disabled features or warnings | AVAILABLE_NOT_YET_VERIFIED | Check for policy notices in Copilot |

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

### Probe 2: Agent Skills Discovery
**Surface**: GitHub Copilot Chat
**Copy-paste prompt**:
```text
List all Orchestra skills available in this workspace and display the primary purpose of the 'clockwork' and 'cipher' skills.
```
**Expected verified evidence**:
- Copilot recognizes `skills/*/SKILL.md` or reports which skill directories are indexed.

### Probe 3: Custom Agent Dispatch
**Surface**: GitHub Copilot Chat (agent selection menu or `@` mention)
**Action**:
- Type `@` in Copilot Chat to check whether `@conductor` or any custom agent is listed.
- If available, enter:
```text
@conductor Classify this task: Add a new unit test for architecture boundary validation.
```
**Expected verified evidence**:
- Copilot resolves `@conductor` as the custom agent and routes the task to `overseer` or `clockwork`.

### Probe 4: MCP Tool Visibility
**Surface**: GitHub Copilot Chat (with MCP enabled)
**Copy-paste prompt**:
```text
What external MCP tools are currently configured and callable in this session?
```
**Expected verified evidence**:
- Copilot lists MCP tools or reports that MCP tool transport is not active/available.

### Probe 5 & 6: Extension & CLI Inspection
**Local command output already recorded**:
- `gh copilot --version` -> `! Copilot CLI not installed`
- `code --list-extensions` -> `github.copilot` not installed in default local profile.

### Probe 7 & 8: File Access and Approval Controls
**Surface**: GitHub Copilot Chat
**Copy-paste prompt**:
```text
Read line 1-10 of plugin.json and show the exact version string without modifying the file.
```
**Expected verified evidence**:
- Copilot reads `plugin.json` and outputs `"version": "1.9.0"`.

### Probe 9: Model Selection Controls
**Surface**: GitHub Copilot Chat UI
**Action**:
- Check the model dropdown in the Copilot Chat interface.
- Record the exact list of available models (e.g., `Claude 3.5 Sonnet`, `GPT-4o`, `o1-preview`, `o1-mini`).

### Probe 10: Policy Restrictions
**Surface**: GitHub Copilot Chat / GitHub.com settings
**Action**:
- Check whether any features are marked disabled by organization or account policy (e.g., CLI disabled, telemetry policy, model restrictions).
