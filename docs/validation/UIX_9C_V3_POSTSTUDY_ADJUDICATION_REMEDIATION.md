# UIX-9C V3 Post-study Adjudication Remediation

Status: zero-call, additive, evidence-preserving remediation.

## Preserved live evidence

The V3 live campaign completed six scheduled observations in frozen order `A1, B1, B2, A2, A3, B3` using six model/provider interactions and zero infrastructure replacements. All prior invalid studies remain separate and are not reused.

This remediation does not modify captured live evidence, the V3 stdin transport, the frozen V2 runner, the frozen metric evaluator, the frozen validator, the frozen pair/campaign adjudicator, task fixture, prompts, model, reasoning effort, or scientific resource accounting.

## Defects discovered after capture

1. Pair 2 was counterbalanced as `B2, A2`, but the live runner supplied pair observations to `pair_adjudication()` in execution order. The frozen pair adjudicator requires `(baseline=A, governed=B)`. This created `ARM_IDENTITY_MISMATCH` and `TREATMENT_GUIDANCE_IDENTITY_MISMATCH` only for Pair 2.
2. The frozen `campaign_adjudication()` returns `MIXED_OR_INCONCLUSIVE` for every structurally valid six-observation campaign and therefore never materializes the preregistered `NO_BENEFIT_ESTABLISHED` branch.

A zero-call manual invocation of the unchanged frozen pair adjudicator with `A2` as baseline and `B2` as governed produced a valid Pair 2 with no failure codes and no improved/regressed primary metrics.

## Conservative remediation rule

The additive post-study adjudicator:

- loads the six preserved observations from finalized pair directories;
- validates each observation using the unchanged frozen observation validator;
- reconstructs every pair by scientific arm identity: `A1/B1`, `A2/B2`, `A3/B3`;
- reuses the unchanged frozen pair adjudicator;
- classifies structural/identity failures as `PROTOCOL_INVALID`;
- classifies the exact all-pairs, all-primary-metrics no-delta case as `NO_BENEFIT_ESTABLISHED`, matching the frozen plan statement that valid evidence does not establish a repeatable governed advantage;
- leaves any non-null pattern `MIXED_OR_INCONCLUSIVE` rather than inventing a post-hoc quantitative threshold for the prose-only benefit criterion.

The remediation does not infer harm. `NO_BENEFIT_ESTABLISHED != HARM_ESTABLISHED`.

## Authority boundary

```text
ZERO_CALL_ADJUDICATION_REMEDIATION != LIVE_CALL_AUTHORITY
ZERO_CALL_ADJUDICATION_REMEDIATION != MERGE_AUTHORITY
NO_BENEFIT_ESTABLISHED != ORCHESTRA_HARMS_UI_OUTPUT
CAPTURED_EVIDENCE != MUTABLE_REMEDIATION_INPUT
```
