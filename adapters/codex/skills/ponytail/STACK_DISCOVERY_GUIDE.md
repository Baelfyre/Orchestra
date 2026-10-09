# Stack Discovery Guide

## Purpose

Identify the actual language, runtime, framework, package manager, build system, and test tooling before Ponytail chooses implementation syntax or commands.

## Discovery Sequence

1. Confirm repository root and current branch.
2. Read the closest project instructions and contribution guidance.
3. Inspect manifests, lockfiles, build files, and CI workflows.
4. Inspect the target file and nearby files for local conventions.
5. Inspect existing tests for framework and fixture patterns.
6. Inspect package scripts or task definitions before selecting commands.
7. Load only the relevant section of `LANGUAGE_IMPLEMENTATION_GUIDE.md`.

Do not infer a stack from the repository name or from a single file when stronger evidence exists.

## Common Stack Evidence

| Evidence | Likely meaning | Do not assume |
| --- | --- | --- |
| `package.json` | Node-based tooling exists | npm is the package manager |
| `package-lock.json` | npm lockfile | every workspace uses npm |
| `pnpm-lock.yaml` | pnpm lockfile | scripts are identical to npm |
| `yarn.lock` | Yarn lockfile | Yarn classic vs modern without config |
| `tsconfig.json` | TypeScript configuration | framework or runtime |
| `pyproject.toml` | Python project/tool configuration | exact package manager |
| `requirements*.txt` | pip-compatible dependency list | project is not also managed by another tool |
| `uv.lock` | uv-managed Python environment is likely | allowed install command without project guidance |
| `poetry.lock` | Poetry-managed dependencies | Poetry version |
| `pom.xml` | Maven Java/JVM build | application framework |
| `build.gradle` / `build.gradle.kts` | Gradle build | wrapper availability |
| `gradlew` / `gradlew.bat` | Gradle wrapper | global Gradle should be used |
| `Cargo.toml` | Rust package | workspace shape |
| `go.mod` | Go module | target Go version without reading the file |
| `composer.json` | PHP Composer project | framework |
| `Gemfile` | Ruby Bundler project | framework |
| `Dockerfile` | container build exists | container is the primary local dev path |
| `Makefile` | project tasks may be wrapped by make | target names |
| `.github/workflows/*` | CI command evidence | local environment exactly matches CI |

## Framework Signals

Confirm framework versions from manifests before using version-sensitive APIs.

Examples of signals:
- React/Next/Vite: dependencies and project scripts in `package.json`.
- Express/Fastify/Nest: dependencies plus server bootstrap code.
- Django/Flask/FastAPI: Python dependencies plus application entry points.
- Spring: Maven/Gradle dependencies and annotated application classes.
- JPA/Hibernate: persistence dependencies and entity/repository patterns.
- pytest/Jest/Vitest/JUnit: existing test imports, config, and scripts.

## Command Discovery

Prefer commands already owned by the repository:

- `package.json` scripts such as `test`, `lint`, `typecheck`, `build`, `validate`.
- `Makefile`, `justfile`, `Taskfile.yml`, npm scripts, Maven goals, or Gradle tasks.
- CI workflow commands when local scripts are absent.
- Project documentation only when it matches current configuration.

Never invent a command merely because it is common for the ecosystem.

## File Ownership Discovery

Before editing:
- search references to the target function/class/module;
- identify callers and consumers;
- identify generated or mirrored copies;
- identify tests for the same behavior;
- identify whether the file is generated from another source.

If a generated file has a canonical generator source, edit the generator source and regenerate only through the established project command.

## Stop Conditions

Return for specialist or user guidance when:
- two conflicting package managers appear and ownership is unclear;
- the runtime version required by the intended syntax cannot be confirmed;
- generated-source ownership cannot be identified;
- multiple implementations exist and architecture ownership is unclear;
- the only apparent validation command performs deployment, destructive mutation, or production access.
