# Go and Rust Implementation Reference

## Use When

Load only after repository evidence confirms Go or Rust. Follow the repository's module/workspace structure, compiler/toolchain version, formatting, linting, testing, and error-handling conventions.

## Go

### Core patterns

Prefer small concrete APIs and explicit errors.

```go
func NormalizeName(value string) string {
    return strings.TrimSpace(value)
}
```

Handle errors at the point where a meaningful decision can be made:

```go
value, err := loadValue(ctx, id)
if err != nil {
    return Result{}, fmt.Errorf("load value %q: %w", id, err)
}
```

Use `%w` when wrapping errors that callers may need to inspect.

### Context and concurrency

- Pass `context.Context` through request/cancellation boundaries when the project uses it.
- Do not store contexts in structs unless an established API requires it.
- Close channels from the sending/owning side.
- Avoid goroutines whose lifecycle has no clear owner.
- Prevent goroutine leaks by respecting cancellation and terminal conditions.
- Use mutexes, channels, atomics, or worker pools only when the existing design or Clockwork contract establishes the concurrency model.

```go
select {
case <-ctx.Done():
    return ctx.Err()
case result := <-results:
    return result.Err
}
```

### Resources

Use `defer` for cleanup when ownership is local and the deferred operation is safe.

```go
file, err := os.Open(path)
if err != nil {
    return err
}
defer file.Close()
```

Check close/flush errors when they can affect correctness, especially writes.

### Testing

Use the standard `testing` package and repository helpers unless another established harness exists.

```go
func TestNormalizeName(t *testing.T) {
    if got := NormalizeName("  Ada  "); got != "Ada" {
        t.Fatalf("got %q", got)
    }
}
```

Prefer table-driven tests when multiple cases genuinely share one behavior.

### Common Go mistakes

Avoid:
- ignoring returned errors;
- starting goroutines without lifecycle/cancellation ownership;
- copying structs containing synchronization primitives;
- adding interfaces solely for mocking when a concrete boundary is sufficient;
- using `panic` for recoverable request/data errors;
- introducing global mutable state for convenience.

## Rust

### Ownership and borrowing

Prefer APIs whose ownership reflects the real lifecycle. Borrow data when the caller retains ownership and cloning adds no value.

```rust
fn normalize_name(value: &str) -> String {
    value.trim().to_owned()
}
```

Return borrowed data when the lifetime is naturally tied to the input and an owned value is unnecessary.

### Result and Option

Use `Result` for recoverable failures and `Option` for genuine absence. Propagate errors with `?` when the current layer cannot add a meaningful decision.

```rust
fn load(path: &Path) -> io::Result<String> {
    fs::read_to_string(path)
}
```

Do not use `unwrap()` or `expect()` on untrusted/runtime paths unless failure is provably impossible and the repository accepts that invariant. Tests and one-time initialization may have different conventions.

### Iterators

Use iterators when they remain readable and ownership is clear.

```rust
let names: Vec<_> = users.iter().map(|user| user.name.as_str()).collect();
```

Avoid dense combinator chains when explicit control flow communicates error or state transitions better.

### Concurrency and async

Confirm the runtime before using Tokio, async-std, Rayon, or other concurrency tooling. Do not introduce a runtime or synchronization model incidentally.

- Make task ownership and cancellation explicit.
- Avoid holding mutex guards across `.await` unless the lock type and design explicitly support it.
- Preserve `Send`/`Sync` assumptions established by the architecture.
- Use bounded channels/queues when backpressure is an accepted requirement.

### Testing

Use built-in tests and the repository's integration-test organization.

```rust
#[test]
fn normalizes_whitespace() {
    assert_eq!(normalize_name("  Ada  "), "Ada");
}
```

### Common Rust mistakes

Avoid:
- cloning merely to satisfy the borrow checker without understanding ownership;
- `unwrap()` on recoverable input/I/O paths;
- introducing `unsafe` without explicit necessity, review, and validation;
- selecting an async runtime from generic knowledge rather than repository evidence;
- changing public lifetime/trait bounds casually because downstream effects can be broad.
