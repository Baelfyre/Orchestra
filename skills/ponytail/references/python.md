# Python Implementation Reference

## Use When

Load this reference only after repository evidence confirms Python. Preserve the supported Python version, formatter, linter, type checker, package manager, framework, and repository conventions.

## Core Syntax

Prefer straightforward functions and data structures. Use type hints where the project uses them.

```python
def normalize_name(value: str | None) -> str:
    return value.strip() if value is not None else ""
```

Use `is None` and `is not None` for `None` checks. Do not use mutable objects as default arguments.

```python
def append_value(value: str, items: list[str] | None = None) -> list[str]:
    result = [] if items is None else list(items)
    result.append(value)
    return result
```

## Data Modeling

Prefer existing project models. For simple internal records, `dataclasses` may be appropriate when the repository already uses standard-library modeling.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class UserRef:
    user_id: str
    display_name: str
```

Do not introduce Pydantic, attrs, a new ORM, or another modeling package when the repository has an established approach.

## Context Management and Cleanup

Use context managers for files, locks, transactions, and resources when supported.

```python
from pathlib import Path

text = Path(path).read_text(encoding="utf-8")
```

```python
with open(path, "r", encoding="utf-8") as handle:
    content = handle.read()
```

Use `try/finally` when cleanup cannot be expressed through an existing context manager.

## Exceptions

Catch only exceptions you can handle meaningfully. Preserve the cause when adding context.

```python
try:
    payload = json.loads(raw)
except json.JSONDecodeError as exc:
    raise ValueError("invalid configuration JSON") from exc
```

Avoid bare `except:` and broad `except Exception:` unless the boundary intentionally converts all failures and still preserves diagnostics appropriately.

## Filesystem and Paths

Use `pathlib.Path` when consistent with the codebase. Avoid machine-specific path strings.

```python
config_path = Path(root) / "config" / "settings.json"
```

Explicitly choose encoding for text I/O. Use temporary files/directories through `tempfile` for test or transient state.

## Iteration and Collections

Use comprehensions when they remain readable. Prefer generators when streaming is materially useful and does not complicate ownership.

Use `set` for uniqueness and dictionaries for keyed lookup. Preserve ordering requirements explicitly rather than relying on accidental traversal behavior.

## Async Code

Use `asyncio` only when the project already has an asynchronous execution model or the accepted architecture requires it.

```python
async def fetch_all(client, urls: list[str]):
    return await asyncio.gather(*(client.fetch(url) for url in urls))
```

Do not add concurrency simply to make code look faster. Confirm independent operations, cancellation semantics, resource bounds, and failure behavior first.

## HTTP and Framework Code

Framework-specific APIs are version-sensitive. Confirm installed versions and copy established local patterns before using Django, Flask, FastAPI, Starlette, SQLAlchemy, or similar frameworks.

At external boundaries:
- validate untrusted input;
- do not rely on type hints as runtime validation;
- avoid leaking raw exception details;
- preserve authentication and authorization middleware/dependencies defined by Cipher-owned requirements.

## Packaging

Determine management from repository evidence such as `pyproject.toml`, `uv.lock`, `poetry.lock`, requirements files, setup metadata, or CI. Do not mix package managers casually.

Prefer invocation through the active environment:

```text
python -m pytest
python -m package_or_module
```

when that convention is supported by the repository.

## Testing

Use existing test conventions. Common repositories may use `pytest` or `unittest`; do not assume which one applies.

```python
def test_normalize_name_trims_value():
    assert normalize_name("  Ada  ") == "Ada"
```

Prefer deterministic fixtures, `tmp_path` or standard temporary directories for filesystem tests, and dependency boundaries already established by the project.

## Common Failure Patterns

Avoid:
- mutable default arguments;
- broad exception swallowing;
- changing working directory as hidden global state;
- relying on platform-specific paths;
- blocking I/O inside an established async request path without evaluating the existing pattern;
- adding package-manager metadata inconsistent with the repository;
- returning `None` for every failure when callers need to distinguish failure modes;
- using type-ignore directives to bypass a real contract error without justification.
