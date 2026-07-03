# Cloak User-Flow Review

## Scope Reviewed
- Artifact: Checkout user-flow diagram
- User goal: Review an order and complete payment
- Evidence: User-facing steps and error branches

## Confirmed Finding
The payment-failure branch returns to cart and discards the user's delivery selection.

## Recommendation
Return to payment with prior valid selections preserved and a clear recoverable error. Route system sequence or service-message modeling to `weaver`.

## Missing Evidence
- Running error state and persistence behavior
