# Ponytail Implementation Patterns

Use these as implementation reasoning examples, not as architecture or product requirements. Existing repository conventions and specialist-owned contracts remain authoritative.

## Pattern 1: Fix the Shared Root Cause

**Situation**: Three callers fail when a shared parser receives an empty string.

Weak approach:
- add the same empty-string guard in all three callers.

Preferred Ponytail approach:
- confirm the parser is the correct ownership point;
- add one narrow parser-level correction;
- add one regression test proving the shared behavior;
- verify callers do not rely on the prior failure behavior.

Why: the smaller correct diff removes the defect once instead of multiplying maintenance.

## Pattern 2: Implement a Cipher Contract Without Rewriting Security Policy

**Accepted Cipher requirement**:
- the server must reject access when the authenticated principal does not own the requested object.

Ponytail implementation behavior:
1. locate the established authentication principal and repository/service boundary;
2. reuse the current authorization helper if one exists;
3. enforce the check on the server-side object path;
4. return the project's accepted denial response;
5. add/update a focused unauthorized-object regression test;
6. do not invent a new role model or client-side-only check.

If the correct ownership rule is ambiguous, reroute to Cipher.

## Pattern 3: Implement a Chronicler Contract Without Inventing Persistence Semantics

**Accepted Chronicler requirement**:
- a record update must reject stale versions using the existing version column.

Ponytail implementation behavior:
1. inspect the current repository/ORM pattern;
2. implement the accepted version predicate or framework-supported optimistic-lock mechanism;
3. preserve the transaction boundary established by Clockwork/Chronicler;
4. map stale-write failure to the existing application error contract;
5. add a focused persistence/integration regression test.

Do not add a new version column, isolation level, retry loop, or transaction boundary without Chronicler/Clockwork ownership.

## Pattern 4: Implement a Cloak Interaction Contract

**Accepted Cloak requirement**:
- while a save-owned completion mutation is pending, the completion affordance must not dispatch another completion request.

Ponytail implementation behavior:
1. find the state that owns the active mutation;
2. bind actionable state to that existing source of truth;
3. preserve keyboard and disabled-state behavior specified by Cloak;
4. remove duplicate dispatch paths rather than adding timers or ad hoc flags when one owner already exists;
5. add a focused interaction test proving one completion dispatch.

Do not redesign the workflow or change server completion authority.

## Pattern 5: Implement an Overseer Test Request

**Overseer asks**:
- add regression coverage for malformed configuration without expanding the suite.

Ponytail implementation behavior:
1. inspect nearby tests and fixture style;
2. add the smallest case that reproduces the failure;
3. invoke the same public or internal boundary used by the defect;
4. assert the observable contract, not incidental implementation details;
5. run the narrow test, then required repository validation.

Do not add a new test framework or broad fixture hierarchy for one case.

## Pattern 6: Dependency Request

**Request**: add a library for a small formatting operation.

Ponytail ladder:
1. search for an existing project helper;
2. check standard library/native APIs;
3. check installed dependencies already used for the same purpose;
4. only add a new dependency when the accepted requirement still cannot be met cleanly.

If a dependency is added, preserve the repository package manager and lockfile, then run dependency/security/license checks required by the project.

## Pattern 7: Generated Source

**Situation**: an exported client contains the wrong output.

Ponytail behavior:
1. determine whether the client is generated;
2. find the OpenAPI/schema/template/generator input;
3. fix the canonical input or generator;
4. run the repository-owned generation command;
5. inspect generated diff for deterministic scope;
6. run compile/type/test checks for both source and generated consumer surfaces.

Manual patching of generated output is only acceptable when the repository explicitly treats that file as editable source.

## Pattern 8: Complete Handoff Delta

For material cross-domain work, the implementation handoff should be compact but complete:

```text
baseline: <approved SHA>
head/worktree: <current identity>
changed paths: <exact list>
implemented contracts: <contract IDs/revisions>
behavioral delta: <what changed>
potential invalidations: <owners to re-enter>
generated artifacts: <none or exact identities>
validation executed: <exact commands/results>
known limitations: <bounded residuals>
```

Do not claim another specialist's decision as Ponytail's own. Do not claim readiness beyond the validation actually executed.
