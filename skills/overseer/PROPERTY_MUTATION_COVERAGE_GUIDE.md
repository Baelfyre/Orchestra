# Property, Mutation, and Coverage Guide

## Property-Based Testing

Start with a stable invariant and a generator domain. Bound size, depth, numeric range, Unicode classes, sequence length, and invalid-input ratio so the run remains useful and reproducible.

Evidence includes:

- property and requirement/risk link;
- generator and shrinker configuration;
- seed, tool/runtime version, example count, discard rate, and timeout;
- original and minimized counterexample;
- replay command or procedure;
- classification/distribution when input mix matters.

Example-based tests remain useful for named regressions and requirements. A property that merely repeats implementation logic adds little evidence.

## Mutation Testing

Select risk-bearing modules and a stable passing test baseline. Distinguish:

- killed mutant: a test detected the behavioral change;
- survived mutant: the suite did not detect it and needs interpretation;
- uncovered mutant: mutated code was not executed;
- invalid/equivalent mutant: no meaningful behavior change can be demonstrated;
- timeout/error: tool or test reliability needs investigation.

Mutation score is not comparable across tools, operators, scopes, or exclusions without normalization. Do not chase a percentage by adding brittle assertions against implementation details.

## Coverage Interpretation

State whether evidence is line, statement, branch, condition, path, function, or changed-line coverage. Review critical uncovered behavior, excluded/generated code, exception paths, platform branches, and test oracle strength.

High coverage can coexist with weak assertions. Low coverage may be acceptable outside the changed risk surface if residual risk is explicit. Coverage gates support, but do not replace, requirements traceability, mutation evidence, contract tests, E2E evidence, or manual validation.
