# Adaptive assurance AQ-2: risk profiler

AQ-2 selects assurance from material risk characteristics and invariants. Development methodology, changed paths, workflow labels, and diff size are context or observations only. They cannot lower a material assurance requirement.

The pure domain entry point is `orchestra_runtime.domain.adaptive.profile_risk`. It accepts a `RiskProfileInput` containing:

- an AQ-1 development mode;
- changed domains and paths as observations;
- a material behavioral description;
- base quality dimensions and Orchestra overlays;
- normalized risk characteristics and invariants;
- protected gates; and
- an explicit authority boundary.

The returned `AdaptiveRiskProfile` contains a stable fingerprint, required assurance classes, recommended specialist slugs, protected gates, deterministic decision reasons, and a Dagger recommendation. Dagger selection is advisory only. AQ-2 never dispatches specialists, activates a provider, performs a production action, or expands authority.

## Routing rules

The minimum topology always includes `overseer` for independent QA. Material ownership is added from explicit risk properties:

| Observation or risk | Added assurance and specialist |
| --- | --- |
| Documentation change | `DOCUMENTATION_RECONCILIATION`, `scribe` |
| UI accessibility | interaction assurance, `cloak` |
| Migration, transaction, or persistence risk | matching assurance, `chronicler` |
| Authentication or authorization | matching assurance, `cipher` |
| Cross-domain architecture behavior | `ARCHITECTURE_BOUNDARY`, `clockwork` |
| Concurrency, privilege, multi-actor, provenance, deletion, or resource pressure | `ADVERSARIAL_ASSURANCE`, `dagger` recommendation |

Authorization alone does not invoke Dagger. A concurrent or otherwise adversarial material risk does, even when no engine path changed. Small diffs do not downgrade security, privilege, concurrency, deletion, provenance, or aggregate-invariant assurance.

Unknown quality or risk values fail closed. Security-critical behavior with no explicit material risk also fails closed. Duplicate declarations are normalized, and unordered declarations produce the same fingerprint and selections. Protected human gates remain nonwaivable, and path/domain ownership never creates mutation authority.
