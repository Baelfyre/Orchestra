# Cloak Frontend-Layout Review

## Scope Reviewed
- Artifact: Responsive account dashboard source and current desktop/mobile screenshots
- User goal: Scan account status, understand alerts, and reach the primary account action
- Evidence: DOM/source order, layout containers, current design tokens, 1440 px and 390 px screenshots

## Confirmed Findings

### High - Task order diverges during narrow reflow
The desktop grid presents account status, the primary action, and recent activity in that task order. At narrow widths the visual order places the complete activity feed before the primary action while the DOM order still places the action earlier. The user has to traverse a large secondary region visually before reaching the primary action.

### Medium - Activity region can force horizontal overflow
A nested grid keeps a minimum content width large enough that long transaction labels push the dashboard wider than the viewport. The screenshot shows clipping at the right edge, and the source contains no local overflow strategy for the activity region.

### Medium - Sticky action bar can obscure focus
The mobile action bar is fixed to the bottom edge. Current evidence does not show additional scroll padding or spacing that would keep the last focusable activity control visible above it.

## Recommendations

1. Preserve the primary task hierarchy when the grid collapses: account status, primary action, then secondary activity.
2. Keep DOM order and keyboard order logical. Do not solve visual order by creating a different keyboard sequence.
3. Let the activity container shrink within the grid and choose a deliberate local overflow/wrapping strategy for content that cannot fit.
4. Reserve enough mobile scroll space that the fixed action bar cannot obscure a focused control or validation message.
5. Reuse current layout primitives and spacing tokens rather than adding page-specific fixed widths.

## Responsive Verification Matrix

| Condition | Expected result |
|---|---|
| Narrow supported viewport | No page-level horizontal scrolling; primary action remains before secondary activity. |
| 200% text zoom | Labels wrap without clipping controls or hiding status. |
| Long localized account name | Header and action remain contained without overlap. |
| Keyboard navigation | Focus order follows the logical task and focused controls remain visible. |
| Reduced motion | Responsive changes do not depend on animated movement for comprehension. |

## Handoff

- Cloak: layout hierarchy, containment, focus-visibility requirements
- Ponytail: implementation changes
- Overseer: current rendered viewport, zoom, keyboard, and regression evidence

## Missing Evidence
- Smallest formally supported viewport
- Landscape mobile state
- Virtual-keyboard interaction with the fixed action bar
- Current browser matrix