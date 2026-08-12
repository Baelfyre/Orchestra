# Cloak Navigation-Structure Review

## Scope Reviewed
- Artifact: Analytics dashboard navigation map and route inventory
- User goal: Move between Overview, Reports, and Saved views while retaining orientation
- Evidence: Desktop navigation, mobile drawer, route labels, direct-link behavior, and permission-state screenshots

## Confirmed Findings

### High - Saved views has two competing navigation homes
Saved views appears under Reports and Settings with different labels. Both entries navigate to the same destination, so users cannot build a stable mental model of where saved analysis belongs.

### High - Direct route loses orientation
Opening a saved-view deep link renders the content but does not mark a current navigation item or provide a route heading that names Saved views. The screen is usable but lacks location context.

### Medium - Mobile navigation omits the current-state cue
The desktop sidebar highlights the active section, while the mobile drawer only closes after navigation. The current destination is not identified when the drawer is reopened.

## Recommendations

1. Choose one task-based primary home for Saved views and use one stable label.
2. If Reports needs a shortcut, present it as a contextual shortcut rather than a second primary navigation location.
3. Ensure direct links render the same page title/heading, current-location cue, permission state, and recovery options as menu navigation.
4. Preserve current-location indication in both desktop and mobile navigation.
5. After a client-side route change, provide a predictable focus/context target such as the new page heading when focus would otherwise remain on a removed navigation control.
6. Keep permission-based hiding as a usability rule only. Route authorization enforcement to Cipher.

## Route Experience Matrix

| Route condition | Expected result |
|---|---|
| Normal navigation | One active location and one visible page heading. |
| Direct deep link | Same orientation and permission behavior as menu entry. |
| Back / Forward | History returns to the prior logical view without duplicate navigation state. |
| Permission denied | Clear limitation and safe next action without exposing sensitive policy detail. |
| Not found | Distinct not-found state, not an ambiguous permission or empty-data screen. |
| Mobile drawer | Current destination remains perceivable when navigation reopens. |

## Handoff

- Cloak: information architecture, route labels, current-location and focus requirements
- Clockwork: client-side route/state architecture when ownership is unclear
- Cipher: authorization policy
- Ponytail: implementation
- Overseer: direct-link, history, mobile, focus, and permission-state validation

## Missing Evidence
- Search behavior across saved views
- Unsaved-change handling
- Browser history behavior after report filters