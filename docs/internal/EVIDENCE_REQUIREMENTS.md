# Evidence & Verification Requirements

Every evolution proposal submitted by Artificer must contain verified objective evidence to support its recommendations.

## Evidence Requirements

### 1. File & Line Traceability
- Every cited design pattern must provide an exact file path and line number range from the pinned commit SHA.
- Vague claims (e.g. "somewhere in the router module") are insufficient and must be rejected.

### 2. Runtime Verification Record
- Document if the pattern's behavior was tested under live execution.
- If tested, record:
  - Host environment (e.g., Node version, Python version, OS platform).
  - Executed commands or scripts used to trigger the behavior.
  - Actual console output, log traces, or profile files.
- If not tested, explicitly state: `Runtime behavior: NOT_TESTED`.

### 3. Structural Analysis
- Document the dependencies required by the pattern.
- Evaluate the size impact (additional lines of code, weight of new dependencies).
- Analyze whether the pattern introduces new API endpoints, database schemas, or filesystem operations.

### 4. Source Confidence Score
Assign a confidence score to guide maintainer decisions:

- **HIGH**: Well-documented, widely adopted pattern with passing tests and verified clean code.
- **MEDIUM**: Functional pattern but lacks clean test cases or documentation; minor refactoring needed.
- **LOW**: Experimental, partially implemented, or poorly written code; requires significant conceptual rework.
