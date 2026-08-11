# Build and Test Tooling Guide

## Purpose

Select implementation and validation commands from repository evidence instead of ecosystem habit. This guide does not authorize installation, deployment, release, external mutation, or production access.

## Command Selection Order

Use the strongest repository-owned source available:

1. explicit project validation documentation;
2. package/task scripts;
3. wrapper scripts checked into the repository;
4. CI workflow commands;
5. framework/build configuration;
6. only then, a conventional direct tool invocation when the repository clearly supports it.

If two sources conflict, inspect which one is current and used by CI. Do not guess.

## JavaScript and TypeScript

Read `package.json` scripts before choosing a command.

Common script shapes are:

```text
npm test
npm run lint
npm run typecheck
npm run build
npm run validate
```

These are examples, not defaults. Use `pnpm`, Yarn, Bun, or another package manager only when lockfiles/configuration prove that choice.

Rules:
- do not run install with a different package manager because it is locally convenient;
- do not rewrite a lockfile unless the accepted dependency change requires it;
- prefer `npm ci` in CI-like clean installs only when the repository uses npm and has a compatible lockfile;
- do not invoke a framework CLI globally when the repository provides a local script or package binary.

## Python

Determine environment management from `pyproject.toml`, lockfiles, requirements files, project docs, and CI.

Common repository-owned commands may wrap:

```text
python -m pytest
python -m ruff check .
python -m mypy ...
python -m package.module
```

Do not assume pytest, Ruff, mypy, uv, Poetry, pip-tools, or another tool is present. Preserve the supported Python version.

## Java and JVM

Prefer checked-in wrappers:

```text
./mvnw test
./gradlew test
gradlew.bat test
```

Use exact repository goals/tasks. Do not switch between Maven and Gradle, bypass wrappers, or add plugin goals by convention.

When integration tests use containers, databases, or external services, confirm whether the repository supplies an isolated test harness before running them.

## Go

Use `go.mod`/workspace evidence and existing scripts. Common commands include:

```text
go test ./...
go vet ./...
go build ./...
```

Do not assume all packages, tags, race tests, or integration tests are safe without repository guidance.

## Rust

Read `Cargo.toml`, workspace metadata, toolchain configuration, and CI. Common commands include:

```text
cargo test
cargo check
cargo clippy
cargo fmt --check
```

Do not modify the lockfile or toolchain configuration unless required by the accepted change.

## Shell and PowerShell

Prefer repository wrappers rather than reconstructing long command sequences manually. Check native process exit codes and fail when required validation fails.

When a repository has both `.ps1` and `.sh` wrappers, use the one appropriate to the current host unless a cross-platform comparison is itself part of the required gate.

## Validation Layers

Classify checks before running them:

- **format**: deterministic style or whitespace checks;
- **lint/static**: rule and code-quality checks;
- **typecheck/compile**: type and compilation contracts;
- **unit**: isolated behavior;
- **integration**: component/service/persistence interaction;
- **contract**: API/schema/interface compatibility;
- **browser/E2E**: rendered workflow behavior;
- **security**: repository-approved security scans and control checks;
- **packaging/export**: generated artifacts and portable distribution parity;
- **release**: complete release-readiness gate owned by Overseer and repository governance.

Ponytail may execute checks but does not redefine which layers are required for release.

## Narrow Check vs Transition Gate

During implementation, run the narrowest useful check after each bounded edit when practical. Before PR publication/update, merge, or another governed transition, run the repository-required complete gate on the exact current head.

```text
narrow implementation check != release readiness
passing one test != full validation
validation on old head != validation on current head
```

Any source change after validation invalidates the affected exact-head evidence.

## Generated Artifacts

Before editing a generated file:
1. identify its canonical input/generator;
2. confirm the generation command;
3. edit the canonical source;
4. regenerate through the repository-owned command;
5. confirm the generated delta is deterministic and scoped.

Do not manually patch generated output unless the repository explicitly treats it as canonical source.

## Dependency Changes

If a dependency must change:
- verify the package manager;
- identify the minimum compatible change;
- update manifest and lockfile through the native package manager when possible;
- run the repository's dependency/security policy checks;
- review transitive changes and unexpected lockfile churn;
- route license/compliance uncertainty to The Governor and security implications to Cipher.

## Failure Handling

If validation fails:
- capture the exact command and failure;
- determine whether the failure is introduced by the change, pre-existing, environmental, or capacity-related;
- fix only within the authorized scope;
- rerun the failed narrow check, then rerun every required gate invalidated by the correction;
- never mark the phase complete because a different check passed.

If the required tool or environment is unavailable, report the gate as unavailable or blocked. Do not substitute an informal review and call it equivalent.
