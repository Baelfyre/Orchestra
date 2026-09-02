# Cloak UI Reference Corpus CUIR-5 / CUIR-6 Lifecycle Reconciliation

Status: `LIFECYCLE_RECONCILIATION_CANDIDATE`

Scope: current-state projection only. No CUIR evaluation is re-executed and no Cloak runtime behavior is changed.

## Purpose

Reconcile Orchestra's current machine-facing CUIR lifecycle projection with the already verified canonical CUIR-5 controlled evaluation and CUIR-6 optional-adoption closeout.

The historical phase documents and benchmark records intentionally retain their phase-era candidate wording. Orchestra's `README.json` historical-status policy permits that wording to remain historical while current exact state is projected from verified Git identity and current machine state.

## Canonical evidence

CUIR-5 controlled evaluation:

- canonical PR: `#689`;
- canonical commit: `0736517fc59f3979ec76d642bc2d8ed5c7b858b1`;
- canonical tree: `b0e5d89db6f3c9642465704ecc1ace8c3b905291`;
- GitHub signature: verified / valid;
- disposition: `CONTROLLED_EVALUATION_PASS`;
- recommendation: `ADOPT_OPTIONAL` for CUIR-6 consideration only.

CUIR-6 optional-adoption closeout:

- canonical PR: `#692`;
- canonical commit: `2f11f17742e68560d2a435bcab3f247b52d351ab`;
- canonical tree: `0f114c13d8f5f54ee5ecf1e9deb156ae6fe6e24b`;
- GitHub signature: verified / valid;
- disposition: canonical closeout of the CUIR phase family with bounded progressive retrieval supported optionally.

## Current-state reconciliation

The current machine projection records:

- CUIR-5 as canonical controlled-evaluation evidence with `CONTROLLED_EVALUATION_PASS` and `ADOPT_OPTIONAL` recommendation;
- CUIR-6 as canonical `ADOPT_OPTIONAL` closeout;
- the CUIR phase family as closed;
- the existing CUIR-4 progressive retrieval limits and project-native precedence as unchanged;
- default full-corpus injection as disabled;
- automatic host injection as disabled;
- no new runtime, implementation, provider, release, deployment, policy, destructive, or integration-refresh authority.

## Historical records

The following are deliberately preserved as historical phase artifacts rather than rewritten to appear post-canonical:

- `docs/project/CLOAK_UI_REFERENCE_CORPUS_CUIR5_EVALUATION.md`;
- `machine/evaluation/cloak-ui-reference-cuir5-benchmark.v1.json`;
- `docs/project/CLOAK_UI_REFERENCE_CORPUS_CUIR6_ADOPTION.md`.

Their candidate-era status text records the state in which those artifacts were reviewed. The canonical PR, commit, tree, signature, and current `README.json` projection establish the later lifecycle outcome.

## Residual pull requests

The remaining open CUIR source-candidate pull requests are historical workflow residue and are not additional implementation work:

- `#675` was superseded by canonical CUIR-3 normalization PR `#677`;
- `#678` was superseded by canonical CUIR-3 lifecycle closeout PR `#680`;
- `#681` was superseded by canonical CUIR-4 integration PR `#683`;
- `#684` was superseded by canonical CUIR-4 lifecycle closeout PR `#686`;
- `#687` was superseded by canonical CUIR-5 evaluation PR `#689`.

They may be closed after this reconciliation is canonical. Their branches are retained because branch deletion is a separately protected action.

## Non-goals and authority boundary

This reconciliation does not:

- re-run CUIR-5 evaluation or widen its claims;
- modify CUIR retrieval semantics, limits, provenance, licensing, or source-copying rules;
- make CUIR mandatory for Cloak tasks;
- enable full-corpus or automatic host injection;
- create implementation, architecture, security, provider-routing, merge, release, deployment, production-mutation, policy, destructive, installed-integration-refresh, branch-deletion, force-push, or history-rewrite authority;
- change AR-2 or start AR-3.

Validation and canonical merge evidence remain required before this reconciliation becomes current canonical state.
