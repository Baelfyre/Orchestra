# Spec Kitty-Derived Orchestra Phase 2 Compatibility Matrix

## Status
```text
RUNTIME VALIDATED
MERGED
NOT RELEASED
PR #208
MERGE COMMIT: 1e2992b94abe67a76c1e6ec0b98f8b712ae256e4
REVIEWED HEAD: 1a57c489445a9a333e929cae8f857312bb126a62
VERDICT: PHASE_2_COMPATIBILITY_VALIDATED_AND_MERGED
```

## Overview
This document defines the verified compatibility matrix for the four accepted Spec Kitty-derived contract specifications across Python runtimes, operating systems, hardware architectures, host adapters, schema versions, and legacy records.

## Compatibility Classifications
- `LOCAL_VERIFIED`: Empirically confirmed by baseline test execution on the current local environment (Python 3.11.9 on Windows Win32 x86_64).
- `CI_VERIFIED`: Confirmed by automated GitHub Actions CI workflows.
- `DECLARED_SUPPORT_MATRIX`: Declared as supported in repository packaging metadata (`pyproject.toml` / `setup.py`).
- `DESIGN_TARGET`: Target platform/version evaluated during Phase 1/2A design analysis.
- `FOCUSED_COMPATIBILITY_VERIFIED`: Verified via focused compatibility testing for target behavior without full CI execution.
- `SCAFFOLD_ONLY`: Present as IDE/export scaffold without active runtime execution.
- `UNVERIFIED`: Environment or feature not yet empirically tested.
- `UNSUPPORTED`: Explicitly prohibited or outside architectural scope.

## Supported Runtimes & Environments

| Dimension | Target Variant | Assessment Status | Notes & Evidence |
|---|---|---|---|
| Python Runtime | Python 3.11 (3.11.9) | `LOCAL_VERIFIED` | Primary local development baseline. 390 runtime tests passed with 93.72% coverage. Zero PyPI dependencies. |
| Python Runtime | Python 3.12 | `CI_VERIFIED` | Verified in PR #208 GitHub Actions cross-platform workflow (Ubuntu, macOS, Windows). |
| Python Runtime | Python 3.13 | `REPOSITORY_DECLARED_SUPPORTED` | Supported in repository declaration matrix. |
| Python Runtime | Python 3.14+ | `FOCUSED_COMPATIBILITY_VERIFIED` | Forward compatibility verified without altering project-owned zero-dependency UUIDv7 strategy. |
| Operating System | Windows 11 (Win32 x86_64) | `LOCAL_VERIFIED` / `CI_VERIFIED` | Primary local environment and verified in CI. Behavior suite exit 0. |
| Operating System | Linux (Ubuntu 24.04) | `CI_VERIFIED` | Verified in PR #208 GitHub Actions CI runner (`ubuntu-latest`). |
| Operating System | macOS (Darwin) | `CI_VERIFIED` | Verified in PR #208 GitHub Actions CI runner (`macos-latest`). |
| Architecture | x86_64 (AMD64) | `LOCAL_VERIFIED` / `CI_VERIFIED` | Standard 64-bit architecture in local and CI runners. |
| Architecture | arm64 (AArch64 / Apple Silicon) | `CI_VERIFIED` | 64-bit ARM architecture runner in macOS CI. |

## Adapter & Interface Inventory

| Adapter Name | Directory Path | Current Status | Runtime Integration | Packaging Integration | Phase 2 Impact |
|---|---|---|---|---|---|
| Codex Adapter | `adapters/codex/` | `RUNTIME_SUPPORTED` | Active runtime adapter (`orchestra_runtime/adapters.py`) | Export & IDE validated | RuntimeEnvelope integration supported via `CodexAdapterMixin`. |
| Antigravity Adapter | `adapters/antigravity/` | `RUNTIME_SUPPORTED` | Active runtime adapter (`orchestra_runtime/adapters.py`) | Export & IDE validated | RuntimeEnvelope integration supported via `AntigravityAdapterMixin`. |
| Gemini Adapter | `adapters/gemini/` | `SCAFFOLD_ONLY` | IDE packaging scaffold | Validated by `validate_ide_packaging.py` | Scaffold-only adapter; no runtime envelope impact. |
| Cursor Adapter | `adapters/cursor/` | `SCAFFOLD_ONLY` | IDE packaging scaffold | Validated by `validate_ide_packaging.py` | Scaffold-only adapter; no runtime envelope impact. |
| Windsurf Adapter | `adapters/windsurf/` | `SCAFFOLD_ONLY` | IDE packaging scaffold | Validated by `validate_ide_packaging.py` | Scaffold-only adapter; no runtime envelope impact. |
| Claude Adapter | `adapters/claude/` | `SCAFFOLD_ONLY` | IDE packaging scaffold | Validated by `validate_ide_packaging.py` | Scaffold-only adapter; no runtime envelope impact. |
| VSCode Adapter | `adapters/vscode/` | `SCAFFOLD_ONLY` | IDE packaging scaffold | Validated by `validate_ide_packaging.py` | Scaffold-only adapter; no runtime envelope impact. |

## Record & Schema Compatibility

| Record Type | Version / Format | Compatibility Strategy | Failure / Fallback Behavior |
|---|---|---|---|
| Legacy `ExecutionResult` | Unversioned Python dict/object | Supported without modification | Transcribed into `EXECUTION_RESULT` envelope variant if requested. |
| Legacy `TransitionDecisionRecord` | Unversioned JSON/YAML | Supported without modification | Transcribed into `TRANSITION_DECISION` envelope variant if requested. |
| Legacy `ApprovedUnitPlan` | Standard 4-field structure | Supported without modification | Parsed cleanly; missing extension fields default to `None` / empty lists. |
| Extended `ApprovedUnitPlan` | 15-field extension | Required for new Phase 2E plans | Invalid schemas produce validation errors; legacy parser remains functional. |
| Envelope Payload | `json:orchestra-envelope` (v1.0) | Strict major version matching | Unknown major versions fail closed for machine action; extra fields ignored. |
| Correlation Header | RFC 9562 UUIDv7 string | Optional header string | Missing correlation header defaults to unlinked single-session execution. |
| Phase Retrospective | Markdown/JSON artifact (v1.0) | `MIXED_RETENTION_MODEL` | Missing retrospective does not invalidate completed historical phases. |

## Dependency & Security Assessment
- **External Dependencies**: 0 PyPI runtime dependencies authorized. All implementation must rely strictly on standard library or existing codebase utilities.
- **Data Privacy**: No PII, secrets, API tokens, or credentials permitted in envelope payloads, correlation headers, or retrospectives.
- **Path Security**: All file paths evaluated in unit extensions must be relative to repository root and verified free of path traversal sequences (`..`).

## Phase 2 Test Coverage Requirements
- Runtime coverage gate: `tests/runtime` with coverage >= 90% (Current baseline: 93.84%).
- All adapter output wrappers must pass negative serialization tests.
- Backward compatibility tests must verify that legacy unit plans, execution results, and transition records parse without error.
