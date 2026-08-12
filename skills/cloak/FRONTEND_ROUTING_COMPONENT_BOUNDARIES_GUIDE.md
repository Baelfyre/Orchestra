# Frontend Routing and Component Boundary Guide

Use this guide when UI structure involves client-side navigation, nested layouts, route-specific states, deep links, or reusable component boundaries. Cloak owns user-visible behavior, not application architecture.

## Route experience contract

For each user-visible route or screen, review:

- entry path and primary user goal
- page title and visible heading
- active navigation indication
- loading, empty, error, success, retry, permission, and not-found states when applicable
- focus destination after navigation
- back/forward behavior
- deep-link behavior
- responsive navigation behavior
- unsaved-change recovery where relevant

## Navigation semantics

- Use one stable label for the same destination unless the contexts genuinely require different language.
- Distinguish global, local, contextual, and utility navigation.
- Current-location indication should be visually and programmatically perceivable.
- A hidden navigation item is not authorization. Cipher owns access-control policy and enforcement review.
- If a user can legitimately deep-link to a route, the direct route should provide the same understandable state and permissions as navigation through the menu.

## Focus and route transitions

- Route changes that replace the main view should provide a predictable context cue for keyboard and screen-reader users.
- Preserve focus only when the same control remains the logical task continuation.
- Do not leave focus on detached DOM content after route replacement.
- Loading transitions should not repeatedly move focus while data resolves.
- Error and permission states should provide a clear next action and a reachable navigation path.

## History and recovery

- Browser Back and Forward should not unexpectedly discard completed safe state or repeat destructive actions.
- If unsaved user input would be lost, provide an evidence-backed warning and recovery path.
- Redirects should not create loops or strand users on transient screens.
- Scroll restoration should support the task rather than always forcing the same position.

## Component boundary literacy

Cloak may recommend a reusable visual/interaction boundary when repeated UI has the same user-visible contract.

A useful component boundary usually has:

- one clear user-facing responsibility
- stable inputs and visible states
- a consistent accessibility contract
- predictable responsive behavior
- reusable design-system constraints

Cloak must not decide React provider architecture, query-cache ownership, service boundaries, persistence ownership, or business-rule placement. Route those decisions to Clockwork or the appropriate specialist.

## Shared state warning signs

Route architecture alignment to Clockwork when the UI review exposes:

- duplicate sources of truth across route and component state
- state synchronization loops
- route guards that embed business authorization logic
- components whose data ownership is unclear across nested routes
- optimistic or cached state whose failure behavior changes the business contract
- server/client rendering boundaries that affect authoritative state

## Permission-aware UX

- Navigation may hide unavailable actions to reduce confusion, but backend enforcement remains mandatory.
- Permission-denied screens should explain the user-visible limitation without leaking sensitive policy details.
- Avoid redirect behavior that makes an authorization failure look like missing data or a broken route.
- Route policy and threat questions to Cipher.

## Handoff

Cloak hands off the user-visible route contract, semantic navigation structure, responsive shell behavior, focus expectations, and component-state matrix. Ponytail implements it. Clockwork owns architecture and state placement. Cipher owns authorization. Overseer owns route and state validation evidence.