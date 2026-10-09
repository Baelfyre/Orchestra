# Router Dry-Run Test Cases

## Purpose
To validate the Conductor's router-first behavior without executing potentially destructive file changes or invoking long-running execution loops. These cases verify that intent classification, execution mode selection, skill lookup, context hydration, and governance triggers align with the established architectural policies.

## Scope
This document outlines explicit scenario-based inputs for Conductor evaluation. It covers 13 distinct workflow types ranging from simple read-only queries to destructive operations. **Note**: These are strictly dry-run validations; they do not execute file changes or modify the repository.

## Test Method
Each test case should be presented to the Conductor instance as a raw user prompt. The resulting assembled `MINIMAL_PROMPT_FORMAT` output is then inspected against the expected results in this document.

## Pass Criteria
- Conductor selects the correct execution mode.
- Conductor identifies the proper specialist skill without defaulting to `ponytail` for architecture or governance.
- Conductor retrieves only the explicitly required context categories (avoiding bloat).
- Conductor correctly assigns the `Governance Status`.

## Fail Criteria
- Conductor loads full `README.md`, `plugin.json`, or detailed skill files by default.
- Conductor routes security, database, or UI strategy directly to `ponytail`.
- Conductor fails to classify Destructive operations as `BLOCKED_PENDING_AUTHORIZATION`.
- Conductor skips `ROUTING_MAP.md` lookup on ambiguous cross-skill queries.

## Dry-Run Test Matrix

| Case ID | User Request | Expected Intent | Expected Mode | Expected Skill | Required Context | Governance Status | Expected Result |
|---|---|---|---|---|---|---|---|
| TC-01 | "How does the main entry point work?" | Q&A | FAST | `conductor` or `scribe` | Core manifest | NOT_REQUIRED | Assembled fast prompt, minimal context |
| TC-02 | "Fix typos in the installation guide." | Docs | STANDARD | `scribe` | Documentation | NOT_REQUIRED | Routed to scribe, no backend context |
| TC-03 | "Update README.md with the new CLI flags." | Docs | STANDARD | `scribe` | Documentation | NOT_REQUIRED | Routed to scribe, no backend context |
| TC-04 | "Implement a retry wrapper for the API client." | Feature | STANDARD | `ponytail` | Backend/impl | CONDITIONAL | Routed to ponytail, impl context |
| TC-05 | "Refactor the service layer into pure functions." | Refactor | STANDARD | `clockwork` | Backend/impl | CONDITIONAL | Routed to clockwork first |
| TC-06 | "Write unit tests for the auth utility." | Testing | STANDARD | `overseer` | Testing | CONDITIONAL | Routed to overseer, testing context |
| TC-07 | "Add a new user_preferences table and migrate." | Persistence | STANDARD | `chronicler` | Database | CONDITIONAL | Routed to chronicler |
| TC-08 | "Update the GitHub Actions build script." | CI/CD | STANDARD | `overseer` | CI/CD | CONDITIONAL | Routed to overseer, CI/CD context |
| TC-09 | "Implement RBAC middleware for the admin route." | Security | GOVERNED | `cipher` | Security, Gov | REQUIRED | Routed to cipher, gov context loaded |
| TC-10 | "Audit the repo for GDPR compliance." | Audit | AUDIT | `the-governor` | Gov | REQUIRED | Routed to governor, read-only constraints |
| TC-11 | "Check release readiness for v2.0." | Release | RELEASE | `overseer` | Release, Gov | REQUIRED | Routed to overseer, strict gates applied |
| TC-12 | "Run fuzz testing to crash the login page." | Chaos | DESTRUCTIVE | `dagger` | Destructive | BLOCKED_PENDING_AUTHORIZATION | Blocked, waiting for user auth & guardrail |
| TC-13 | "Build a secure dashboard with a new DB schema." | Multi-skill | STANDARD | `conductor` | `ROUTING_MAP.md` | CONDITIONAL | Conductor loads map, plans multi-step route |

## Expected Routing Failures
Conductor must actively fail or pause under the following conditions:
- **Missing explicit target**: "Fix the code." -> Conductor must ask for target clarification instead of guessing.
- **Out of scope specialist request**: "Use ponytail to design the database schema." -> Conductor must re-route to `chronicler` or pause to warn the user of the skill mismatch.

## Governance Validation Cases
Validation must ensure that `docs/governance/GOVERNANCE_LAYER.md` is strictly fetched when tasks (like TC-09, TC-10, and TC-11) trigger security, compliance, or release gates. If a standard code implementation (TC-04) accidentally fetches full governance rules, the test fails due to token bloat.

## Destructive Operation Validation Cases
Validation must ensure that TC-12 results in a hard stop. The prompt package must be flagged as `BLOCKED_PENDING_AUTHORIZATION`. The required context must explicitly mandate `scripts/dagger_guardrail.py` validation before execution can proceed.

## Validation Result
ROUTER_DRY_RUN_CASES_DEFINED
