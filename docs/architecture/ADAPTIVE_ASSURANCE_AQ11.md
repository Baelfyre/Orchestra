# ADAPT-QA AQ11: CritiQual remediation effectiveness pilot

AQ11 implements a deterministic **controlled remediation/effectiveness pilot** over known CritiQual development-assurance escape classes. Its authority model is `EVIDENCE_ONLY_NON_AUTHORIZING`.

## Pilot boundary

The pilot is bound to the observed CritiQual canonical state `166bbac50a4f02e222aa15ff914c60cec658b7c0`, the assurance incident `Baelfyre/Padayon#441`, and mode `CONTROLLED_NON_PRODUCTION_EVIDENCE_PILOT`. CritiQual source mutation is not part of AQ11. Production evidence, deployment, providers, telemetry, release activity, and CUD10 execution remain outside scope.

AQ11 evaluates six controlled escape classes: provenance ownership, aggregate concurrency, calibration evidence integrity, authority boundaries, runtime integration, and gate-coverage truthfulness. Each class must have a before-state defect/risk observation and an after-state outcome backed by explicit evidence.

## Effectiveness semantics

A case counts as effective only when its after-state is `PREVENTED` or `DETECTED_BEFORE_TRANSITION`, the evidence is independently produced, and recurrence is not observed. A remaining escape or recurrence yields `REVISION_REQUIRED`. Inconclusive or non-independent evidence yields `WAIT_FOR_EVIDENCE`.

A complete six-of-six controlled pilot may yield `PASS`, but that result means only that the bounded pilot evidence satisfied its declared evaluator. AQ11 makes no organic effectiveness claim about live CritiQual operation and no production-readiness claim.

## CUD10 and authority boundary

CUD10 remains `READY_NOT_STARTED_HELD_BY_CURRENT_USER`. AQ11 cannot admit, resume, or execute CUD10. A pilot `PASS` is explicitly non-admitting and cannot create transition authority, execution authority, whitelist authority, protected-policy authority, threshold-lowering authority, provider/telemetry authority, production mutation authority, release authority, or deployment authority.

The Arbiter and human governance boundaries remain unchanged. Any future decision to admit CritiQual CUD10 requires its own governed evidence and authority outside AQ11.
