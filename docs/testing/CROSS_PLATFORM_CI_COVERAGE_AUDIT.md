# Audit Report: Cross-Platform CI Coverage

## 1. Result
The current CI pipeline has significant cross-platform coverage gaps. While Linux (`ubuntu-latest`) receives comprehensive validation, macOS receives only partial validation, and Windows is entirely excluded from the automated CI matrix. Furthermore, the core runtime test suite (`pytest tests/runtime`) is completely missing from the cross-platform matrix.

## 2. Critical findings
- **Severity**: Critical
- **File path**: `.github/workflows/cross-platform-validation.yml`
- **Function/Component**: `native-validation` job `matrix`
- **Evidence**: The matrix `os` only includes `ubuntu-latest` and `macos-latest`. `windows-latest` is omitted entirely.
- **Reason**: Orchestra claims cross-platform support and has extensive path-handling logic for Windows. Excluding Windows from CI represents a severe blind spot where platform-specific path bugs or executable differences can easily slip through.
- **Minimal remediation plan**: Add `windows-latest` to the `cross-platform-validation.yml` matrix. Add conditional logic (`if: runner.os != 'Windows'`) to the POSIX-only script verification steps to prevent Windows runner failures.

- **Severity**: Critical
- **File path**: `.github/workflows/cross-platform-validation.yml`
- **Function/Component**: `Run Native Validation` step
- **Evidence**: `pytest tests/runtime` is absent from the validation commands.
- **Reason**: The `orchestra_runtime` test suite ensures the core Python logic functions correctly. Currently, it only runs on Ubuntu (via `validate.yml`). This means there is zero automated testing of the core runtime logic on macOS or Windows.
- **Minimal remediation plan**: Add `pytest` and `pytest-cov` to the dependency installation step. Add `run_report runtime_tests python -m pytest tests/runtime -q` to the `Run Native Validation` step.

## 3. Major findings
- **Severity**: Major
- **File path**: `.github/workflows/validate.yml`
- **Function/Component**: Entire workflow
- **Evidence**: Only runs on `ubuntu-latest`.
- **Reason**: Having two separate workflows (`validate.yml` and `cross-platform-validation.yml`) that partially overlap creates an inconsistent testing landscape. `validate.yml` runs `tests/behavior/run_tests.py` (which is also run by cross-platform CI) and `pytest tests/runtime` (which is not).
- **Minimal remediation plan**: Migrate the `pytest tests/runtime` step directly into the `cross-platform-validation.yml` script to guarantee consistent runtime testing across all supported operating systems.

## 4. Minor findings
- **Severity**: Minor
- **File path**: `.github/workflows/cross-platform-validation.yml`
- **Function/Component**: `Verify POSIX Scripts`
- **Evidence**: Step runs `file` and `test -x` on `.sh` scripts unconditionally.
- **Reason**: Windows runners lack native `file` and `test -x` for shell scripts without bash/WSL, which will cause the workflow to fail on Windows.
- **Minimal remediation plan**: Add `if: runner.os != 'Windows'` to the POSIX verification step.

## 5. Cleanup findings
- **Severity**: Cleanup
- **File path**: `.github/workflows/governance-check.yml`
- **Function/Component**: Entire workflow
- **Evidence**: Only runs on `ubuntu-latest`.
- **Reason**: Governance metadata validation is highly platform-agnostic, making Ubuntu-only execution perfectly acceptable and efficient.
- **Minimal remediation plan**: No changes required.

## 6. Validation run
Tests were not run. (Initial audit mode only).

## 7. Recommended next action
Implement the cross-platform coverage remediations in a follow-up wave. Update the `cross-platform-validation.yml` file to include `windows-latest` in the matrix, skip POSIX checks on Windows, and enforce full `pytest tests/runtime` execution across all platforms.

## 8. Implementation Status
*Note added during Wave 5A implementation:*
The cross-platform coverage remediations recommended above were implemented in `fix/wave5a-cross-platform-ci-coverage`. Windows was added to the matrix, POSIX-only checks were skipped on Windows, and runtime tests were added to the native validation suite across all platforms.
