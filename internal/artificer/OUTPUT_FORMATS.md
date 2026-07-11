# Artificer Output Formats

Artificer generates two distinct outputs: **Individual Source Audits** (per repository analysed) and the **Amalgamated Orchestra Evolution Proposal** (combining approved findings into a unified specification).

## 1. Individual Source Audit

Every evaluated repository must yield an audit document in this exact structure:

```markdown
# Artificer Source Audit: [Repository Owner]/[Repository Name]

## 1. Source Metadata
- **Repository URL**: [Canonical URL]
- **Commit SHA**: [Reviewed Git Commit Hash]
- **License**: [License Type, e.g., MIT / Apache 2.0]
- **Extraction Date**: [YYYY-MM-DD]
- **Lines of Code Examined**: [Paths and Ranges]

## 2. Executive Summary
[Brief assessment of architectural quality, suitability, and alignment with Orchestra goals.]

## 3. Discovered Patterns
### Pattern: [Short Name]
- **Path**: [File and line range]
- **Description**: [Pattern purpose and mechanics]
- **Proposed Classification**: [REFERENCE_ONLY | ADAPTED_PATTERN | etc.]
- **Assigned Specialist**: [Cloak | Cipher | Clockwork | etc.]
- **Evidence/Runtimes Checked**: [Summary of tests or notes]

## 4. IP & Licensing Analysis
- **Attribution Obligation**: [None | Notice Required | Header Keep]
- **Compatibility Verdict**: [COMPATIBLE | GOVERNOR_REVIEW_REQUIRED | INCOMPATIBLE]
- **Risk Assessment**: [Analysis of vendor lock, copied code, patent clauses]

## 5. Security & Risk Log
- **Discovered Secrets/Keys**: [None | Blocked and reported]
- **Dynamic Risk**: [Adversarial comment instructions, build-script hazards]
```

## 2. Amalgamated Orchestra Evolution Proposal

When merging findings, compile a clean, native proposal document:

```markdown
# Orchestra Evolution Proposal: [Topic]

## 1. Objective
[Problem statement and context]

## 2. Summary of Source Audits
- [Owner/Repo] (Commit: [SHA], License: [License])

## 3. Selected Design Patterns
### Proposed Pattern: [Name]
- **Derivation Source**: [Source Owner/Repo, File Path]
- **Evolution Mechanism**: [Conceptual adaptation | Safe rewrite]
- **Target Component**: [Where it fits in Orchestra]
- **Owner Specialist**: [Stated specialist, e.g., Clockwork]

## 4. Verification & Testing Plan
- **Verification Strategy**: [Behavioral tests, mock runs]
- **Adversarial Validation**: [Dagger test cases]

## 5. Governance Hand-off
- **Arbiter Review Status**: [PENDING]
- **Governor Approval Status**: [PENDING]
```
