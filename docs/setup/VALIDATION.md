# Validation & Enforceable Governance Guide

Orchestra uses a multi-layered verification system to programmatically enforce project structure, manifest properties, safety guardrails, and concurrent execution safeguards.

---

## 1. Centralized Test Runner (`run-tests.ps1`)

The framework provides a unified test runner, [tests/behavior/run-tests.ps1](file:///c:/conductor/tests/behavior/run-tests.ps1), which executes all structural, consistency, and regression checks.

### How to Run Tests Locally
Open a PowerShell session and execute:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\behavior\run-tests.ps1
```

### What is Validated
The validation suite runs the following checks sequentially:
1. **Structure Validation (`validate-structure.ps1`)**: Verifies that all expected repository directories, specialist skill files, adapter configurations, command entry points, and templates exist and match schema definitions.
2. **Manifest Verification (`validate-manifest.ps1`)**: Cross-checks skill manifests in `plugin.json` against the frontmatter definitions in `skills/**/SKILL.md` to ensure active slugs and properties are aligned.
3. **Stale References Scan (`check-stale-references.ps1`)**: Scans code files for hardcoded obsolete naming references or invalid system identifiers.
4. **Codex Skill Export Alignment (`validate-codex-export.ps1`)**: Verifies that generated/exported Codex skill definitions match the source rules.
5. **Guardrail and Locking Regression Tests**: Runs isolated simulations in temporary workspace folders to assert that security, PII, destructive command blocks, and lock acquisition behaviors function correctly.

---

## 2. Programmatic Runtime Guardrails

Runtime guardrails scan repository files and staged changes for safety and naming violations before git commits or execution.

### Active Safety Scans
- **Secrets Scanning**: Matches patterns for AWS keys, Slack webhooks, private keys, and generic credential variables.
- **Copyleft License Detection**: Warns if GPL, AGPL, or LGPL licenses are added to dependencies.
- **PII Leak Protection**: Detects SSNs or credit card patterns and requires a corresponding `PRIVACY_POLICY.md` file.
- **Destructive Operations Block**: Catches raw volume formatting or unsafe recursive force deletions (`rm -rf`, `Remove-Item -Force`).
- **Unsafe Command Execution**: Prevents dangerous expressions like `Invoke-Expression` or `iex`.
- **Forbidden Target Mutations**: Blocks edits to folders designated in `forbidden_repos` inside `.amalgam/state.json`.

### How to Enable Guardrail Enforcement
By default, guardrail scans are **warning-only and non-blocking** (they output warning logs but exit with code `0` to keep early prototyping fast). 

To turn on strict enforcement (where any violation throws an error and exits with code `1`), set the environment variable:
```powershell
# In PowerShell (Windows)
$env:ORCHESTRA_ENFORCE_GUARDRAILS = "true"

# In Bash (Linux / CI)
export ORCHESTRA_ENFORCE_GUARDRAILS="true"
```
You can also trigger scans manually with parameters:
```powershell
# Run manual scan recursively over the workspace
powershell -File .\scripts\runtime-guardrail.ps1 -Enabled

# Run manual scan with strict enforcement enabled
powershell -File .\scripts\runtime-guardrail.ps1 -Enabled -Enforce
```

---

## 3. Workspace State Locking

State locking prevents concurrent agent executions or developers from accidentally overwriting shared project state files (`PROJECT_STATE.md`, `SESSION_HANDOFF.md`, `DECISION_LOG.md`, `.amalgam/state.json`) during parallel runs.

### How State Locking Works
1. **Lock File**: When an agent begins a workflow task (e.g. implementation or audit), it checks for the existence of `.amalgam/lock.json`.
2. **Process Liveness Verification**: If a lock file exists, `manage-state-lock.ps1` parses the PID and verifies if that process is still running on the system.
   - If the process is dead or the lock is older than 1 hour, the lock is treated as **stale** and automatically ignored.
   - If the process is alive, it blocks the current run and raises a **lock collision** error.
3. **Acquisition & Release**: The active session writes its unique Session ID, PID, and timestamp to the lock. Upon task completion or test suite termination, the lock is released.

### Manual Lock Management
If a lock is abandoned or a crashed process leaves the repository locked, release it manually:
```powershell
powershell -File .\scripts\manage-state-lock.ps1 -Action Release
```
Check if a lock is currently active:
```powershell
powershell -File .\scripts\manage-state-lock.ps1 -Action Check
```
