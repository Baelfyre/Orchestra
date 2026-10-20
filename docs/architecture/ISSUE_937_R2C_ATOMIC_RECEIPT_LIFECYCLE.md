# Issue #937 R2C-2A Synthetic Receipt Lifecycle

**Status:** SYNTHETIC_TEST_ONLY. No production receipt source, resolver, persistence, or MCP wiring is added.

Source observations are bound to `b215a48b678e8708a8a6e7123f5ee1893d3f4f15` / `fac2140e41e81bdf243ddc6c389b38c0453ad28c` and were rechecked on 2026-10-20.

## Confirmed source behavior

`orchestra_runtime/application/use_cases/verify_governance_receipt.py::VerifyGovernanceReceipt.execute` resolves and validates a trusted receipt, calls `GovernanceReceiptStore.consume_once`, and then separately calls `record_audit`. `orchestra_runtime/application/ports/governance_receipts.py::GovernanceReceiptStore` exposes those as separate operations. The existing test `tests/runtime/test_governance_receipt_foundations.py::test_audit_failure_denies_even_after_atomic_consumption` passed on 2026-10-20 and confirms that an audit write failure returns a denial after the one-time receipt has already been consumed. This fails closed for authorization but can strand a valid receipt without its required audit event.

The production port currently has separate `consume_once` and `record_audit` operations. A targeted search over `orchestra_runtime` for `GovernanceReceiptStore`, `GovernanceReceiptContextProvider`, `AuthorizeGovernedOperation`, and `governanceReceiptRef` found only the protocol/use-case declarations and no production implementation or MCP reference consumer. This branch does not change that port, the verifier, or the MCP contract.

## Test-only transaction model

`tests/runtime/test_governance_receipt_atomic_lifecycle.py` at commit `15112d46afd6a3e2eea55177660cf56798ae669f` (tree `3175844c07082c916d801378c3e97652730e2d6e`) uses Python's local SQLite runtime 3.49.1 (`python -m sqlite3 --version`) and a temporary database to exercise a candidate lifecycle invariant:

- begin an immediate write transaction;
- atomically update a synthetic unconsumed receipt and append its audit event;
- roll back both writes if the audit append fails;
- allow exactly one successful concurrent consume;
- audit a denied concurrent replay;
- preserve the consumed state and audit history across a new fixture instance.

The fixture exposes no `AuthorizationDecision`, verifier, context provider, production port, trusted source, or MCP integration. Its boolean return is only whether the synthetic database row changed; it is not authorization.

## Limits and required future contract

The exact validation run was `python -m pytest tests/runtime/test_governance_receipt_atomic_lifecycle.py -q` (3 passed) on 2026-10-20 against that commit's content. This demonstrates behavior for the test fixture on the recorded SQLite version only. It does not prove production database isolation, production durability, receipt authenticity, trusted human-authority provenance, candidate/rule/scope validation, fresh execution-context binding, or production consumption. Those production integrations are **NOT_FOUND** in the targeted runtime search.

Before production wiring, Chronicler and Clockwork must define a store/transaction boundary that commits one-time consumption and its required audit atomically. Cipher and The Governor must separately review authority provenance and policy consequences. A future production design must continue to deny when trusted context, receipt provenance, candidate identity, candidate base/head/tree, protected rule, operation, target/scope, constraints, evidence binding, freshness/expiry, consumption state, or fresh execution-context binding is missing or mismatched.

Specialist command tools returned `NOT_REQUIRED` routing acknowledgements for Chronicler, Clockwork, and Overseer; none supplied a substantive contract or validation decision. No reviewer endorsement is claimed here.
