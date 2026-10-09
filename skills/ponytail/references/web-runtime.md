# Web Runtime Implementation Reference

## Use When

Load only for accepted HTML, CSS, browser API, or frontend runtime implementation. Cloak owns UI/UX and accessibility requirements; Clockwork owns frontend architecture/state boundaries when those decisions are not already established. Ponytail implements the accepted contract.

## Semantic HTML

Prefer native elements that already provide the required meaning and interaction.

```html
<button type="button">Save</button>
<nav aria-label="Primary">...</nav>
<label for="email">Email</label>
<input id="email" name="email" type="email" autocomplete="email">
```

Do not replace native buttons, links, inputs, headings, lists, tables, or disclosure controls with generic containers unless the accepted design genuinely requires custom behavior.

ARIA supplements semantics; it does not repair an inappropriate base element automatically. Do not add ARIA roles or properties by guesswork.

## Keyboard and Focus

Implement the keyboard contract supplied by Cloak or established component patterns.

- Interactive elements must be keyboard reachable when the interaction is intended for keyboard users.
- Do not add positive `tabindex` values to force custom focus order.
- Move focus only when the interaction requires it, such as accepted modal/dialog workflows or explicit error recovery.
- Restore focus when established component behavior requires it.
- Do not trap focus outside a component that owns a legitimate modal interaction.

## Forms

Use native form behavior where possible.

```html
<form>
  <label for="quantity">Quantity</label>
  <input id="quantity" name="quantity" type="number" min="1" required>
  <button type="submit">Add</button>
</form>
```

Client-side validation improves usability but does not replace server-side trust-boundary validation.

Preserve disabled, pending, error, success, and retry states required by Cloak. Prevent duplicate submissions when the accepted workflow requires single ownership of a mutation.

## CSS Layout

Prefer normal flow, Flexbox, and Grid before JavaScript layout calculations.

```css
.toolbar {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}
```

```css
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
  gap: 1rem;
}
```

Avoid arbitrary fixed dimensions when content or responsive behavior requires flexibility. Preserve project tokens and design-system variables instead of inventing local color, spacing, typography, or z-index systems.

## Browser APIs

Use native APIs when sufficient and supported by the project's browser target.

Examples include:
- `URL` and `URLSearchParams` for URL manipulation;
- `AbortController` for cancellable browser requests;
- `FormData` for form payloads;
- `Intl` for locale-aware formatting when project requirements allow it;
- `matchMedia` for media-query state when CSS alone cannot satisfy the runtime need.

Confirm browser support and existing polyfill policy before using newer APIs.

## Events

- Use the event appropriate to the semantic interaction.
- Avoid duplicate handlers that can dispatch the same mutation twice.
- Clean up manually registered listeners.
- Do not rely on event ordering that is not guaranteed by the project/runtime contract.
- Preserve event propagation intentionally; do not scatter `stopPropagation()` as a symptom fix.

## Network State

For client requests:
- distinguish idle, pending, success, empty, and error states when required;
- abort superseded requests when the project pattern does so;
- do not treat client-side authorization checks as server authorization;
- avoid optimistic mutation unless the accepted contract defines rollback/reconciliation behavior.

## Security Boundaries

Cipher owns security requirements. Ponytail must preserve them while implementing frontend behavior.

Do not:
- insert untrusted HTML with `innerHTML` or framework equivalents without an accepted sanitization boundary;
- store secrets in browser code or public environment variables;
- rely on hidden/disabled UI controls as authorization;
- expose raw infrastructure identifiers or sensitive error payloads unless explicitly accepted.

## Common Failure Patterns

Avoid:
- generic clickable `div` elements where a button/link fits;
- JS layout code that CSS already solves;
- local one-off styling that bypasses the design system;
- positive `tabindex` ordering;
- duplicate submit/completion paths;
- missing cleanup for listeners, timers, observers, or requests;
- new accessibility requirements invented by Ponytail rather than sourced from Cloak or established standards already adopted by the project.
