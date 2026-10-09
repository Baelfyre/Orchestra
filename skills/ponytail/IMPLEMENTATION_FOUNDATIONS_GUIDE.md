# Implementation Foundations Guide

## Purpose

Give Ponytail enough implementation knowledge to make safe, minimal code changes without relying only on generic model intuition. This guide defines universal implementation reasoning. Load stack-specific syntax only after the repository proves which stack is in use.

## Implementation Order

Before writing code:

1. Read the requested behavior and the files that own it.
2. Trace the real call or data path far enough to locate the correct edit point.
3. Check whether the codebase already has a helper, abstraction, component, convention, or dependency that solves the problem.
4. Prefer standard-library or native-platform capabilities when they satisfy the accepted contract.
5. Use the smallest change that fixes the shared root cause.
6. Preserve public contracts unless the approved change explicitly modifies them.
7. Add or update the smallest useful regression check for non-trivial changed behavior.
8. Run repository-owned validation for the affected surface.

This retains Ponytail's minimalism heritage while keeping Orchestra specialist decisions authoritative.

## Source of Truth

- Inspect before editing.
- Edit the Git-tracked source of truth, not generated output, installed copies, caches, or runtime mirrors unless explicitly required.
- Never invent files, functions, types, tables, routes, configuration keys, environment variables, scripts, framework behavior, or runtime versions.
- Treat lockfiles, manifests, build files, CI workflows, existing tests, and nearby code as evidence of project conventions.
- Preserve user-approved and specialist-owned architecture, security, persistence, UI, and QA decisions.

## Root-Cause Implementation

A small diff is only useful when it is placed at the correct ownership point.

Prefer:
- one fix in a shared parser over duplicate guards in every caller;
- one boundary validation at the real trust boundary over repeated downstream checks;
- one reusable existing helper over a second implementation;
- one transaction-safe operation over compensating cleanup after partial mutation.

Do not widen the refactor merely because a broader redesign would be cleaner.

## Control Flow and State

- Keep control flow explicit enough to understand locally.
- Prefer early returns when they reduce nesting and preserve readability.
- Do not silently swallow exceptions.
- Make state transitions explicit when behavior depends on lifecycle or status.
- Preserve idempotency when an operation may be retried.
- Avoid hidden mutation across module boundaries.
- Clean up listeners, file handles, connections, locks, timers, tasks, and temporary resources according to the language/runtime pattern already used by the project.

## Input and Output Boundaries

At every external or trust boundary:
- validate shape and required values using the project's existing validation mechanism;
- normalize only when normalization is explicitly part of the accepted behavior;
- distinguish invalid input from missing optional input;
- avoid exposing secrets, internal stack traces, private identifiers, or raw infrastructure details;
- preserve encoding, locale, timezone, numeric precision, and serialization rules already established by the codebase.

Cipher owns security requirements. Chronicler owns persistence semantics. Ponytail implements their accepted contracts.

## Error Handling

- Handle errors at the layer that can make a meaningful decision.
- Preserve the original cause when wrapping errors.
- Do not turn every error into success or a generic null value.
- Use cleanup/finally/defer/context-manager patterns where the language supports them.
- User-visible error wording belongs to Cloak when it changes UX requirements.
- Retry policy, backoff policy, and failure-domain design belong to Clockwork/Cipher/Dagger when not already decided.

## Async and Concurrency

Before changing concurrent code:
- identify the shared mutable state;
- identify ordering assumptions;
- identify cancellation and timeout behavior;
- preserve existing locking, queueing, transactional, or actor ownership patterns;
- avoid fire-and-forget work unless the project deliberately uses it;
- make retries idempotent or protected against duplicate effects.

New concurrency architecture belongs to Clockwork. Resilience pressure scenarios belong to Dagger.

## Configuration and Secrets

- Reuse the project's existing configuration system.
- Do not add a new config source for one value when an established source exists.
- Never hardcode secrets, tokens, credentials, private keys, or machine-specific paths.
- Preserve precedence rules among environment variables, config files, defaults, and runtime arguments.
- Do not rewrite a configuration object in a way that discards unrelated existing keys.

## Dependency Discipline

Before adding a dependency:
1. search the repository for an existing solution;
2. check the standard library or platform;
3. check already-installed dependencies;
4. add a new dependency only when the accepted task justifies ownership of it.

Respect the project's lockfile and package-manager conventions. Do not regenerate unrelated dependency state.

## Tests and Checks

Non-trivial changed behavior should leave a focused regression check when the repository has an applicable test path.

Prefer:
- extending a nearby test file;
- one test proving the reported failure and expected result;
- existing fixtures and helpers;
- deterministic inputs;
- no new testing framework unless explicitly approved.

Overseer owns test strategy and release readiness. Ponytail implements tests and runs narrow checks.

## Diff Discipline

- Keep the changed-file set narrow.
- Avoid unrelated formatting churn.
- Avoid changing generated files unless the project's generation contract requires it.
- Review the final diff for accidental edits, debug output, placeholders, TODOs, temporary files, and secrets.
- Run `git diff --check` or the project-equivalent whitespace validation when available.

## Specialist Handoffs

Route unresolved decisions instead of guessing:
- architecture or ownership -> Clockwork
- security requirements -> Cipher
- persistence semantics -> Chronicler
- visible UI/UX requirements -> Cloak
- test strategy or readiness -> Overseer
- multi-domain sequencing -> Conductor
- continuity or transition readiness -> Arbiter

Ponytail is the implementation owner after those contracts are clear.
