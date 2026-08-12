# Cloak User-Flow Review

## Scope Reviewed
- Artifact: Checkout user-flow diagram plus supplied payment error screens
- User goal: Review an order, complete payment, and recover without re-entering valid information
- Evidence: User-facing steps, validation branches, payment failure state, and success destination

## Confirmed Findings

### Critical - Payment failure discards completed delivery work
The payment-failure branch returns the user to Cart and clears the previously valid delivery selection. The user must repeat an unrelated completed step even though the failure occurred during payment.

### High - Failure state does not identify ownership of retry
The error screen shows both Retry payment and Return to cart with equal visual weight. It does not explain whether the existing payment attempt is still pending or safe to retry.

### Medium - Focus destination after failure is unspecified
The diagram shows the failed state but does not define where keyboard focus moves when the payment screen changes to the error state.

## Recommendations

1. Return the user to the payment step with prior valid delivery and order-review selections preserved unless the backend explicitly invalidated them.
2. Provide one authoritative retry path and expose pending/completed state clearly enough to prevent duplicate payment actions.
3. Put the actionable error and safe retry guidance near the payment task. Avoid generic failure text that forces users to infer what happened.
4. Move focus to an error heading/summary when the failure replaces the current payment content and users would otherwise lose context.
5. Keep Return to cart available as a secondary user-controlled exit without making it the only recovery route.
6. Route payment-state idempotency, backend mutation ownership, and persistence semantics to Clockwork/Cipher/Chronicler as appropriate. Cloak owns only the user-visible recovery contract.

## State Continuity Matrix

| State | Preserve | Primary user action |
|---|---|---|
| Payment pending | Delivery choice, cart, order summary | Wait or cancel only when supported. |
| Recoverable failure | Valid prior selections and entered non-sensitive data | Retry payment once. |
| Payment declined | Order context | Choose another allowed payment method or exit safely. |
| Session/permission failure | Only data policy permits retaining | Re-authenticate or follow the provided safe recovery path. |
| Success | Final order summary | Continue to receipt/order status. |

## Handoff

- Cloak: user-visible state continuity, hierarchy, focus, and recovery path
- Clockwork: payment-state and client/server ownership
- Cipher: payment/authentication security policy
- Chronicler: persistence semantics if state retention depends on stored records
- Ponytail: implementation
- Overseer: retry, duplicate-action, keyboard, and current rendered evidence

## Missing Evidence
- Current idempotency/retry contract
- Running focus behavior
- Exact retention policy for sensitive payment fields
- Persistence behavior across session expiry