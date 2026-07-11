# Evidence & Verification Requirements

Every evolution proposal submitted by Artificer must contain verified objective evidence to support its recommendations.

## Evidence Requirements

### 1. File & Line Traceability
- Every cited design pattern must provide an exact file path and line number range from the pinned commit SHA.
- Vague claims (e.g. "somewhere in the router module") are insufficient and must be rejected.

### 2. Evidence Categorization Buckets

Every piece of evidence supporting a proposed pattern must be classified into one of the following seven buckets to denote its validation depth:

- **`SOURCE_CONFIRMED`**: The pattern is present in the static source code of the repository at the pinned commit SHA.
- **`DOCUMENTATION_CLAIM`**: The behavior or pattern exists as a claim or example in the repository's markdown files, READMEs, or documentation, but has not been verified statically.
- **`STATIC_ANALYSIS`**: The pattern's logic, flow, and abstract structure were verified through static AST parsing, control flow graph inspection, or static tools.
- **`EXISTING_TEST_EVIDENCE`**: The repository's pre-existing, checked-in test suite contains unit or integration tests that prove the pattern's behavior.
- **`RUNTIME_CONFIRMED_BY_AUTHORIZED_EXTERNAL_VALIDATION`**: The runtime behavior was verified by running the code, but ONLY within a separately authorized external sandbox (never executed directly by Artificer within the local Orchestra workspace).
- **`INFERENCE`**: The pattern's behavior is logically deduced from surrounding code blocks, API exports, or type annotations.
- **`UNVERIFIED`**: The pattern's functional behavior or execution state remains untested and unvalidated.

> [!WARNING]
> **No-Execution Boundary**: Artificer must never attempt to create `RUNTIME_CONFIRMED` evidence by executing untrusted repository code, scripts, or tests itself. Any dynamic runtime execution must be classified under `RUNTIME_CONFIRMED_BY_AUTHORIZED_EXTERNAL_VALIDATION` and must be performed in an isolated sandbox under a separately authorized maintenance task.

### 3. Structural Analysis
- Document the dependencies required by the pattern.
- Evaluate the size impact (additional lines of code, weight of new dependencies).
- Analyze whether the pattern introduces new API endpoints, database schemas, or filesystem operations.

### 4. Source Confidence Score
Assign a confidence score to guide maintainer decisions:

- **HIGH**: Well-documented, widely adopted pattern with passing tests and verified clean code.
- **MEDIUM**: Functional pattern but lacks clean test cases or documentation; minor refactoring needed.
- **LOW**: Experimental, partially implemented, or poorly written code; requires significant conceptual rework.
