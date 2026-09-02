# Research and Capstone Documentation Guide

## Purpose

Use this guide when Scribe must document a computing, software, information-systems, data, or related capstone/research project while keeping research claims aligned with actual system and evaluation evidence.

Scribe owns the **documented research narrative, evidence map, and system-to-research traceability**. It does not invent empirical results, choose a methodology without project authority, or reverse-engineer a convenient conclusion from an existing system.

## Institutional Rules Come First

A school, research office, course, adviser, panel, journal, or funding body may prescribe a required structure or rubric. Those requirements are authoritative for the submission.

Do not hardcode one institution's Chapter 1 to Chapter 5 structure into Orchestra.

Instead, maintain a semantic research model and map it into the required template.

## Semantic Research Model

Use only the elements that apply to the project and methodology:

- research or project problem;
- research questions;
- general and specific objectives;
- scope and limitations;
- stakeholders or participants;
- related literature and related systems;
- conceptual or system framework;
- domain narrative;
- requirements;
- methodology;
- system design;
- implementation evidence;
- evaluation method and criteria;
- datasets, questionnaires, instruments, logs, or other evidence sources;
- results;
- discussion;
- conclusions;
- recommendations and future work;
- appendices and artifact evidence;
- citation and provenance records.

A required institutional heading may map to one or more semantic elements. The semantic element is not a replacement for the institution's required format.

## Supported Project Orders

Scribe must adapt to the project's actual lifecycle instead of assuming one universal sequence.

### Plan First

```text
Problem -> Research -> Requirements -> Design -> Build -> Test -> Document Results
```

### Prototype First

```text
Idea -> Prototype -> Observe -> Formalize Problem -> Define Evaluation -> Refine System -> Gather Evidence -> Document Research
```

### Existing System

```text
Existing Application -> Audit -> Reconstruct Supported Requirements -> Reconstruct Domain Narrative -> Define Evaluatable Questions -> Research / Evaluation -> Documentation
```

### Continuous Development

```text
Requirement Change -> Implementation Change -> Test Change -> Evidence Change -> Documentation Change
```

Record which order actually occurred when chronology matters.

## System-Driven Research Documentation

When an implementation exists before the formal research record, use evidence-first reconstruction:

```text
Existing Implementation
  -> Demonstrable Capabilities
  -> Supported Problem / Need
  -> Legitimate Objectives
  -> Evaluatable Questions
  -> Available or Collectable Evidence
  -> Appropriate Evaluation Design
  -> Results
  -> Supportable Claims
```

Critical safeguards:

- Do not infer original developer intent as fact unless evidence establishes it.
- Do not describe an implemented feature as validated merely because code exists.
- Do not create a research question whose answer is already assumed from the implementation.
- Do not write results, discussion, or conclusions before corresponding evidence exists.
- Distinguish historical intent, current implementation, validated behavior, and empirical findings.

## Research-Driven System Development

When research precedes engineering, preserve forward traceability:

```text
Research Problem
  -> Research Questions
  -> Objectives
  -> Domain Investigation
  -> Requirements
  -> Design
  -> Implementation
  -> Evaluation
  -> Evidence
  -> Results
  -> Discussion
  -> Conclusion
```

Scribe structures the narrative and traceability. Technical decisions remain with the appropriate specialists.

## Research-to-System Traceability Matrix

Use when a project needs explicit linkage between research and implementation:

```markdown
| Research Question / Goal | Objective | Requirement / Capability | Implementation Evidence | Evaluation Method | Evidence / Result | Supported Claim | Status |
|---|---|---|---|---|---|---|---|
```

Do not populate a result or supported claim until evidence exists.

## Capstone Evidence Map

```markdown
| Deliverable / Rubric Item | Required Evidence | Current Artifact | State | Gap / Next Action |
|---|---|---|---|---|
```

Possible states include `PROPOSED`, `APPROVED`, `PLANNED`, `IMPLEMENTED`, `VALIDATED`, `MISSING_EVIDENCE`, `UNRESOLVED`, and project-specific equivalents.

## Claim Discipline

A research or capstone statement should be classified by what the evidence can support.

Examples:

- `IMPLEMENTATION_CLAIM`: repository evidence shows a capability exists.
- `VALIDATION_CLAIM`: qualifying verification evidence shows expected behavior under stated conditions.
- `EMPIRICAL_CLAIM`: collected and analyzed research evidence supports a finding.
- `INTERPRETIVE_CLAIM`: discussion or interpretation derived from evidence, clearly distinguished from raw results.
- `PLANNED_CLAIM`: intended future work, not yet implemented or evaluated.
- `UNSUPPORTED_CLAIM`: current evidence is insufficient.

Never transform `IMPLEMENTED` into `VALIDATED`, or `VALIDATED` into empirical effectiveness, without corresponding evidence.

## Artifact Evidence

Research claims may be supported by project-appropriate artifacts such as:

- source code and exact revisions;
- configuration and dependency manifests;
- datasets and data dictionaries;
- notebooks and analysis scripts;
- test runs and benchmark outputs;
- evaluation protocols;
- survey or interview instruments;
- anonymized study records where ethically and legally appropriate;
- verified diagrams;
- deployment or environment records;
- screenshots or recordings when they genuinely evidence the claim;
- specialist-reviewed technical facts.

Evidence suitability depends on the claim. A source file is not a substitute for a user study, and a user survey is not a substitute for a security verification.

## Literature and Citation Handling

- Prefer primary and authoritative sources for technical definitions, standards, protocols, and claims.
- Keep literature claims separate from project implementation claims.
- Record source revision, publication date, effective date, or retrieval date when freshness matters.
- Do not fabricate citations, DOIs, page numbers, authors, datasets, or empirical findings.
- Institution-specific citation rules override generic defaults.

## Specialist Boundaries

- Clockwork establishes architectural facts.
- Chronicler establishes data and persistence facts.
- Weaver owns formal models and diagrams.
- Overseer establishes validation and QA evidence.
- Cipher establishes security/privacy technical facts.
- Cloak establishes UX/UI facts.
- The Governor handles legal, regulatory, IP, licensing, or privacy-governance interpretation where applicable.
- Implementation specialists establish source-code implementation facts.

Scribe turns those verified facts into coherent research documentation without re-owning the decisions.

## Reference Foundation

This guide is original Orchestra guidance. It uses public descriptions of standards and research-reporting resources as conceptual foundations without reproducing protected templates or standards text.

- APA Journal Article Reporting Standards provide reporting guidance for quantitative, qualitative, and mixed-method research. Institutional rules remain authoritative for a capstone submission.
- ACM artifact-evaluation practices reinforce documenting code, data, environment, dependencies, and reproducibility evidence where relevant to computing research.
- ISO/IEC/IEEE 15289 is used as a lifecycle-documentation reference family, supporting the principle that information artifacts are maintained throughout the system lifecycle rather than produced only at the end.
