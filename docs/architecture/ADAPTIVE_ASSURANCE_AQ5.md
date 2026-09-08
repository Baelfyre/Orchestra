# AQ-5 Repository QA Compliance

AQ-5 is the independent repository-level control for the adaptive assurance
chain. It answers one bounded question:

```text
DID_THIS_CHANGE_RECEIVE_ALL_ASSURANCE_REQUIRED_BY_ITS_RISK_PROFILE?
```

The control consumes an AQ-4 assurance manifest and its source-bound evidence
receipts. It evaluates claims; it does not rerun tests, grant authority,
activate providers, promote a phase, or perform repository mutation.

## Inputs and decision

`orchestra_runtime.domain.adaptive.qa_compliance` is a pure deterministic
domain module. `evaluate_qa_compliance` validates:

- AQ-4 manifest and receipt semantics;
- current repository, source, candidate, and tree identity;
- exact changed-path and declared-path equality, with the maximum nine-path
  scope preserved;
- declared semantic risks and their required assurance classes;
- required assurance and protected-gate evidence;
- completion-state evidence, including HTTP plus runtime evidence for
  `RUNTIME_VERIFIED`;
- caller and integration evidence before `PRODUCT_COMPLETE`;
- executed-test claims and changed-code coverage;
- nonzero execution results, stale receipts, and policy self-modification.

The returned `QaComplianceDecision` is canonicalized and SHA-256 bound. Its
authority model is `EVIDENCE_ONLY_NON_AUTHORIZING`; every authority field is
false. A `PASS` result is evidence for an independent review gate, not a
transition authorization.

## Required negative fixtures

The runtime suite keeps these fail-closed cases executable:

| Fixture | Required rejection |
| --- | --- |
| F1 | security-sensitive change without security evidence |
| F2 | concurrent change without concurrency evidence |
| F3 | runtime claim supported only by API/OpenAPI evidence |
| F4 | product-complete claim without caller and integration evidence |
| F5 | `PASS` receipt with nonzero exit |
| F6 | receipt or claim bound to an old candidate SHA |
| F7 | required test claimed without execution evidence |
| F8 | executed test does not cover changed code |
| F9 | changed path omitted from the declaration |
| F10 | executor modifies a protected assurance policy |
| F11 | current repository/source/candidate/tree identity is missing, including stale packet self-validation |

## Execution boundary

The CLI in `scripts/validation/validate_qa_compliance.py` is the only I/O
adapter. It reads JSON manifest and receipt inputs, requires explicit current
repository, source, candidate, and tree identities, invokes the pure evaluator,
and optionally writes the descriptive decision JSON. The evaluator fails closed
with `AQ5_CURRENT_IDENTITY_REQUIRED` if any current identity is omitted, so a
stale manifest cannot self-validate against matching stale receipts. The AQ-5
domain module does not access the network, providers, filesystem, test runner,
Git state, or promotion machinery.

The reusable workflow
`.github/workflows/qa-compliance.yml` runs the focused AQ-5 runtime and
behavior suites, validates machine-contract and JSON-Schema parity, and checks
the exact AQ-5 path scope. AQ-1 through AQ-4 implementation paths remain
outside the AQ-5 change set.
