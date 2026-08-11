# JavaScript and TypeScript Implementation Reference

## Use When

Load this reference only after repository evidence confirms JavaScript or TypeScript. Preserve the project's module system, compiler target, formatter, lint rules, framework conventions, and runtime version.

## Core Syntax

Prefer `const`; use `let` only when reassignment is required. Avoid `var` unless maintaining legacy code that already depends on it.

```ts
export function normalizeName(value: string | null | undefined): string {
  return value?.trim() ?? "";
}
```

Use `===` and `!==` unless the existing code deliberately relies on coercion.

Prefer nullish coalescing when `0`, `false`, or an empty string are valid values:

```ts
const retries = config.retries ?? 3;
```

Use optional chaining only for genuinely optional paths. Do not use it to hide an invariant violation that should fail.

## Types

- Prefer specific domain types over `any`.
- Use `unknown` for untrusted values until narrowed.
- Narrow unions explicitly.
- Preserve existing exported types and public signatures unless contract change is approved.
- Do not use a type assertion to bypass a runtime trust boundary.

```ts
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
```

Discriminated unions are useful for explicit state machines:

```ts
type Result =
  | { kind: "ok"; value: string }
  | { kind: "error"; message: string };
```

## Async Code

Use `async`/`await` when the project does. Preserve cancellation and timeout behavior already established by the repository.

```ts
export async function loadJson(url: string, signal?: AbortSignal): Promise<unknown> {
  const response = await fetch(url, { signal });
  if (!response.ok) {
    throw new Error(`request failed: ${response.status}`);
  }
  return response.json();
}
```

Rules:
- await promises that own required effects;
- do not create unhandled promises;
- use `Promise.all` only when operations are independent and concurrent execution is safe;
- preserve ordering when side effects depend on sequence;
- do not invent retries or concurrency limits without an accepted contract.

## Collections

Prefer built-ins such as `map`, `filter`, `find`, `some`, `every`, `Set`, and `Map` when they make ownership and intent clearer. Avoid compressed chains when they obscure error handling or state changes.

Use `Set` for uniqueness and `Map` when keys are not naturally object properties.

## Errors

Throw or return errors according to the established project convention. When wrapping, retain the original cause where supported:

```ts
try {
  await persist();
} catch (error) {
  throw new Error("persist failed", { cause: error });
}
```

Do not expose raw errors to users or API clients when they may contain internal details.

## Node.js

- Prefer `node:` built-ins where the repository already uses them.
- Use `path.join`/`path.resolve` rather than string-building filesystem paths.
- Specify text encoding when reading or writing text.
- Avoid sync filesystem APIs on latency-sensitive server request paths unless the existing design accepts them.
- Preserve ESM/CommonJS boundaries. Do not convert module systems incidentally.

```ts
import { readFile } from "node:fs/promises";

const content = await readFile(path, "utf8");
```

## React and Component Code

Cloak owns UI/UX requirements; Clockwork may own state or provider architecture. Ponytail implements accepted behavior.

- Keep render functions pure.
- Derive values instead of duplicating them in state.
- Use effects for synchronization with external systems, not ordinary derivation.
- Clean up listeners, subscriptions, timers, and requests in effects.
- Preserve controlled/uncontrolled component conventions already used by the project.
- Avoid memoization unless identity or measured performance requires it.

```tsx
useEffect(() => {
  const controller = new AbortController();
  void loadData(controller.signal);
  return () => controller.abort();
}, [loadData]);
```

Do not invent dependencies to silence effect linting. Fix stale closures or unstable ownership at the correct layer.

## Validation and Serialization

For external data:
- use the repository's established schema/validation library if one exists;
- otherwise perform narrow runtime checks before trusting values;
- distinguish absent optional fields from invalid fields;
- preserve JSON casing, numeric precision, and date/time conventions already in use.

TypeScript types disappear at runtime and do not validate network, file, environment, or user input.

## Testing

Use the existing framework and nearby test style. Typical patterns may include Jest, Vitest, Node test runner, Playwright, or framework-specific tools, but repository evidence decides.

Prefer a test that fails for the prior bug and passes for the corrected root cause. Do not add a second test framework for one change.

## Common Failure Patterns

Avoid:
- `as any` or broad assertions used to silence real type errors;
- catching and ignoring errors;
- mutation hidden inside getters or render logic;
- duplicate derived state;
- `Promise.all` across operations that must be ordered;
- defaulting with `||` when valid falsy values exist;
- new dependencies for standard-library tasks;
- framework-version-specific APIs without confirming the installed version.
