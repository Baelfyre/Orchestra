# Cloak UI Reference Corpus CUIR-5 Controlled Evaluation

Status: `CONTROLLED_EVALUATION_CANDIDATE`

Phase: `CUIR-5`

Canonical input: CUIR-4 lifecycle closeout tree `9a8370d6c4df5f98e6f558df702a0013918af717`.

## Decision question

Does the bounded CUIR-4 progressive retrieval layer add measurable, provenance-safe task-relevant pattern coverage compared with the same Cloak path when no CUIR pattern records are retrieved?

This evaluation does not claim that a deterministic retrieval result proves end-to-end LLM output quality, rendered visual correctness, human usability preference, or production effectiveness.

## Controlled baseline

`NO_CUIR_PATTERN_RETRIEVAL` keeps the frozen Cloak core available but supplies no CUIR normalized pattern records. The comparison therefore measures the incremental contribution of CUIR pattern retrieval only.

## Candidate

`CUIR4_BOUNDED_PROGRESSIVE_RETRIEVAL` uses `scripts/retrieve_cloak_patterns.py` with the canonical limits of at most three problem classes and five patterns per task.

## Benchmark

The machine-readable benchmark is `machine/evaluation/cloak-ui-reference-cuir5-benchmark.v1.json`.

Representative tasks cover:

- multi-step forms and semantic validation state;
- operation progress and outcome state;
- destructive-action separation;
- compact navigation and destination state;
- general UI icons versus brand-icon rights;
- selection and disclosure state.

## Measured criteria

The deterministic evaluator measures:

- expected pattern recall;
- provenance completeness of selected normalized patterns;
- bounded-context compliance;
- implementation-authority boundary compliance;
- source-copying violation signals defined by loss of Orchestra-native normalization or improper implementation authority.

The baseline expected-pattern recall is zero because the baseline intentionally supplies no CUIR pattern records. This value must not be interpreted as a score for the frozen Cloak specialist itself.

## Pass thresholds

The candidate must achieve at least 0.80 expected-pattern recall, complete provenance metadata, complete bounded-context compliance, complete authority-boundary compliance, and zero source-copying violation signals.

## Reproducibility

Run:

```text
python scripts/evaluate_cloak_cuir5.py
pytest -q tests/runtime/test_cloak_ui_reference_corpus_cuir5.py
```

Repository CI remains authoritative for qualification. A local or branch result alone does not establish canonical adoption.

## Disposition rule

If all thresholds pass, the evaluator may recommend `ADOPT_OPTIONAL` for CUIR-6 consideration. If any threshold fails, the disposition is `REVISE_AND_RETEST`.

CUIR-5 does not itself activate policy, grant implementation authority, alter provider routing, authorize deployment, or authorize release/tag publication.
