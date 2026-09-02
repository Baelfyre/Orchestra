# Scribe `SYSTEM_TO_DOCS` Research Example

## Request

Update a capstone record from an existing application whose repository contains source code and tests but incomplete research documentation.

## Direction

`SYSTEM_TO_DOCS`

## Evidence Classification

- `OBSERVED`: Repository source contains an order-status capability.
- `OBSERVED`: Automated tests exercise the status endpoint.
- `IMPLEMENTED`: Implementation evidence exists for the capability.
- `MISSING_EVIDENCE`: No qualifying test execution record was supplied for this documentation task, so `VALIDATED` is not claimed.
- `UNRESOLVED`: The original research objective is not recoverable from code alone.

## As-Built Reconstruction

| Capability / Behavior | Observed Evidence | Intent Evidence | Validation Evidence | State |
|---|---|---|---|---|
| Order status can be queried | Source and configuration at reviewed revision | Existing issue describes customer visibility need | Test definitions exist; execution evidence absent | `IMPLEMENTED` |

## Research Mapping

The implementation may support a research question about order-status visibility or operational coordination, but Scribe must not manufacture a result or conclusion.

```text
Existing capability
  -> candidate evaluatable question
  -> evaluation design
  -> collected evidence
  -> results
  -> supportable claim
```

Until empirical evidence exists:

- user benefit is not claimed;
- effectiveness is not claimed;
- quantitative improvement is not claimed;
- conclusions remain unwritten or explicitly pending.

## Institutional Mapping

Scribe maps the evidence-backed semantic record into the actual school or panel template supplied for the project. It does not impose a generic Chapter 1 to Chapter 5 structure.

## Specialist Handoff

Clockwork verifies disputed architecture claims, Chronicler verifies persistence claims, Weaver verifies formal models, Overseer owns validation conclusions, and Scribe records only the established facts and research evidence.
