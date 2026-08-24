# B-Phase Terminal Closeout Decision

Status: `CANONICAL_EVIDENCE_COMPLETE_NO_PROMOTION`

Recorded: 2026-08-24

Evidence baseline: `8cfb48d501ade0ce31722495c913078f269031f2`

## Decision

The comparative Benchmark B program is complete. The canonical evidence does not establish a confirmatory benefit for either tested A5 sequential topology ordering or Murmurs communication presentation.

The B-phase result therefore closes the current hypotheses without promotion:

- B2: `CONFIRMATORY_BENEFIT_NOT_ESTABLISHED`.
- B3: `CONFIRMATORY_BENEFIT_NOT_ESTABLISHED`.
- B4: `NOT_ELIGIBLE_NO_EXECUTION`.
- B5: complete with no promotion.

Murmurs remains preserved as an experimental/research communication format. It is not promoted to Orchestra's default communication mode, is not required by specialists, and gains no runtime or production authority from the completed experiment.

A5 topology execution likewise receives no execution-effective promotion from B2.

## Confirmatory evidence summary

### B2

The valid B2.5 replacement completed 40/40 accepted runs with 120 model calls. The preregistered confirmatory criteria were not all satisfied, so topology benefit was not established.

### B3 Murmurs

The B3 confirmatory experiment completed 450/450 accepted runs with 450 model calls and 8,885,182 accepted tokens.

Primary result:

- median output-token reduction: `-1.03%`;
- bootstrap 95% CI: `[-4.68%, 2.07%]`;
- exact sign-test p: `0.8699229710286416`;
- conclusion: `CONFIRMATORY_BENEFIT_NOT_ESTABLISHED`.

The interval crosses zero and the directional test does not establish a repeatable advantage under the frozen confirmatory design.

## Resource accounting

Total B-phase model calls, including preserved stopped/invalid evidence: `911`.

This resource history remains part of the empirical audit trail. Stopped or invalid evidence is not silently rewritten into accepted confirmatory evidence.

## Research disposition

The current Murmurs and A5 topology benefit hypotheses are closed as negative/non-confirmatory results. Do not spend additional model calls attempting to rescue either result through post-outcome threshold changes, repeated reruns, or equivalent remeasurement.

A future experiment is permitted only when it states a materially different mechanism or hypothesis, freezes a new outcome-blind design, receives the required authority, and keeps the prior negative result intact.

## Canonical evidence

Human-readable evidence:

- `docs/benchmarking/B3_CONFIRMATORY_RECONCILIATION.md`
- `docs/benchmarking/B_PHASE_FINAL_EVIDENCE_SYNTHESIS.md`

Machine-readable evidence:

- `machine/benchmarking/b3-confirmatory-reconciliation.v1.json`
- `machine/benchmarking/b4-controlled-interaction-disposition.v1.json`
- `machine/benchmarking/b5-final-evidence-synthesis.v1.json`

## Authority boundary

This closeout does not authorize:

- Murmurs default/runtime promotion;
- A5 execution-effective topology promotion;
- runtime attachment;
- release/publication;
- deployment or production mutation;
- policy activation;
- installed-integration refresh;
- destructive cleanup;
- branch deletion;
- force push or history rewrite.

The next selected Orchestra workstream is the governed UI design-fidelity and UI/UX specialist enhancement campaign. Its first bounded unit is UIX-0.