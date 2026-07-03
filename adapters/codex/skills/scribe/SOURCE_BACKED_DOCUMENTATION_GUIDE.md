# Source-Backed Documentation Guide

## Purpose
This guide provides a practical general reference for Scribe to produce documentation that is accurate, traceable, submission-ready, and grounded in verified project evidence. It ensures Scribe handles thesis/capstone reports, README accuracy, and final technical summaries without inventing facts or making specialist decisions.

## Source-of-Truth Rule
Scribe must not invent features, test results, build results, screenshots, diagrams, citations, sources, dates, contributors, or readiness status. Do not present AI-generated text as source evidence.

## Scribe Boundary
Scribe owns documentation prose and knowledge transfer. Scribe must not make architecture, database, QA, UI, security, or implementation decisions. Document outputs from the proper specialist after those specialists define the facts.

## Verified Claims vs Draft Claims
- **Verified claim**: Supported by source file, command output, test result, schema, diagram, issue, PR, commit, rubric, or user-approved fact.
- **Draft claim**: Intended or proposed content not yet verified.

## Evidence Mapping
Evidence mapping should connect each important claim to a source artifact or specialist output.

## Claim Verification Rules
- Do not convert planned work into completed work.
- Do not convert a failed, blocked, skipped, or not-run check into a pass.
- Do not present proposals as implemented behavior.
- Do not present assumptions as facts.

## Citation and Reference Discipline
All claims, diagrams, schemas, or test results mentioned in documentation must reference the specific file, commit, output, or specialist that provided them.

## README Accuracy
Ensure that README files accurately reflect the current state of the codebase. Do not list features, setup steps, or commands that do not exist or have not been tested.

## Thesis or Capstone Documentation
When writing academic or formal submission documentation, clearly separate implemented behavior from future work or assumptions. Preserve user-provided wording when the task is refinement, unless the user asks for rewriting.

## Final Submission Packaging
Final submission documentation should check required files, file names, links, build/run commands, screenshots, diagrams, citations, limitations, known issues, and validation evidence.

## Technical Summary Writing
Provide accurate summaries of the repository state based only on verified evidence.

## Handoff Documentation
Ensure all documentation accurately reflects the work completed and clearly notes what is remaining.

## Requirements Traceability
Map requirements directly to test evidence or implementation files to prove completion.

## Architecture Documentation Dependencies
Architecture claims should come from Clockwork or verified architecture files.

## Database Documentation Dependencies
Database claims should come from Chronicler or verified schema/migration files.

## Diagram Documentation Dependencies
Diagram claims should come from Weaver or verified diagram files.

## QA and Testing Documentation Dependencies
QA claims should come from Overseer or verified test evidence.

## Security and Privacy Documentation Dependencies
Security/privacy claims should come from Cipher or verified security/privacy evidence. Stress/resilience claims should come from Dagger only after safety-gated review and should return to Overseer for readiness decisions.

## Known Issues and Limitations
Honestly document known issues, limitations, and unimplemented features.

## Screenshots, Diagrams, and Media Evidence
Only reference diagrams, screenshots, and media that actually exist in the repository or were explicitly provided.

## Placeholder and Assumption Labels
- **Missing evidence**: Required source cannot be found or was not provided.
- **Placeholder**: Intentionally incomplete content that must be revisited. Mark unverified claims clearly.

## Final Readiness Documentation Checklist
- [ ] Are all claims backed by source evidence?
- [ ] Are draft, placeholder, and missing evidence items clearly marked?
- [ ] Have all specialist outputs been accurately transcribed?
- [ ] Are known issues and limitations documented honestly?

## Scribe Output Discipline
- Output must be structured, objective, and evidence-based.
- Public-facing content must not be over-compressed by Caveman style unless the user asks for concise copy.
