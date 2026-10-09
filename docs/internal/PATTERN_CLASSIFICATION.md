# Pattern Classification Taxonomy

Artificer classifies discovered design patterns using a strict taxonomy to ensure clear licensing, compliance, and architectural alignment.

> [!IMPORTANT]
> Pattern classification is enforced by `PATTERN_SCHEMA.json` and is separate from governance outcomes. `REJECTED`, `DEFERRED`, and `DUPLICATE` are governance concepts, not valid pattern classifications; they belong in Phase 4B governance decision and cross-record validation.

## Classifications

### 1. `REFERENCE_ONLY`
- **Definition**: The pattern is used strictly as a conceptual guide or architectural inspiration.
- **Action**: No code is copied or adapted. The concepts are noted, but implementation is completely original.
- **Licensing Impact**: Minimal. No copyright or attribution constraints are triggered.

### 2. `ADAPTED_PATTERN`
- **Definition**: The structural mechanics of the pattern are adapted to fit Orchestra's design, but the code is written from scratch.
- **Action**: Adapt concepts and write fresh, idiomatic Orchestra code.
- **Licensing Impact**: Requires checking if the original license imposes patent or trademark constraints on derivative designs.

### 3. `CODE_REUSE_REVIEW_REQUIRED`
- **Definition**: Candidate for copying portions of code or structural templates directly.
- **Action**: **BLOCKED** from implementation pending Governor audit. Requires license compatibility verification, copyright header checks, and attribution planning.
- **Licensing Impact**: High. Requires MIT compatibility.

### 4. `TEST_CORPUS_CANDIDATE`
- **Definition**: Discovered code or file structures suitable for inclusion in Orchestra's test suites or benchmark corpuses.
- **Action**: Safe to adapt into tests, mocking fixtures, or validation scripts.
- **Licensing Impact**: Must verify that test distribution does not violate source license terms.

### 5. `OUT_OF_SCOPE`
- **Definition**: Discovered code relates to domains that Orchestra does not own (e.g., application business logic).
- **Action**: Stop evaluation.

## Governance Boundary

Phase 4A validates source-intake and pattern schemas only. It does not validate reviews, decisions, proposals, promotions, or cross-record relationships. Phase 4B will validate those governance records and their relationships. Rejection, deferral, and duplicate handling therefore require governance records rather than pattern classification values.
