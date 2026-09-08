"""Regression tests for legacy workflow-dispatch evidence-baseline contracts."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "tests" / "behavior" / "run_tests.py"
WORKFLOW_PATHS = (
    ".github/workflows/validate.yml",
    ".github/workflows/cross-platform-validation.yml",
    ".github/workflows/governance-check.yml",
    ".github/workflows/required-analysis-compat.yml",
)
VALID_BINDING = (
    "github.event_name == 'workflow_dispatch' "
    "&& inputs.approved_base_sha || ''"
)
EVENT_GUARD = re.compile(
    r"github\.event_name\s*==\s*['\"]workflow_dispatch['\"]",
    re.IGNORECASE,
)
FORBIDDEN_BASELINE_REFERENCES = (
    "github.sha",
    "origin/main",
    "merge-base",
    "head^",
    "head~",
)
CONTROLLED_ENV = (
    "ORCHESTRA_APPROVED_BASE_SHA",
    "GITHUB_EVENT_PATH",
    "GITHUB_EVENT_NAME",
    "GITHUB_ACTIONS",
    "GITHUB_SHA",
)

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only on minimal Python installs
    yaml = None


spec = importlib.util.spec_from_file_location(
    "orchestra_behavior_runner", RUNNER_PATH
)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load tests/behavior/run_tests.py")
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def _strip_inline_comment(value: str) -> str:
    quote = None
    for index, character in enumerate(value):
        if character in "'\"" and (quote is None or quote == character):
            quote = None if quote == character else character
        elif character == "#" and quote is None and (
            index == 0 or value[index - 1].isspace()
        ):
            return value[:index].rstrip()
    return value.strip()


def _mapping_entries(text: str) -> dict[tuple[str, ...], str]:
    """Extract nested mapping keys for the contract fallback parser."""

    entries: dict[tuple[str, ...], str] = {}
    stack: list[tuple[int, tuple[str, ...]]] = []
    block_scalar_indent: int | None = None
    sequence_indent: int | None = None

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip():
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if "\t" in raw_line[:indent]:
            raise AssertionError(f"YAML tab indentation at line {line_number}")

        if sequence_indent is not None:
            if indent > sequence_indent:
                continue
            sequence_indent = None

        if block_scalar_indent is not None:
            if indent > block_scalar_indent:
                continue
            block_scalar_indent = None

        stripped = raw_line[indent:]
        if stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            sequence_indent = indent
            continue

        match = re.match(r"([^:#][^:]*):(?:\s*(.*))?$", stripped)
        if match is None:
            raise AssertionError(f"Unsupported YAML mapping at line {line_number}")

        while stack and indent <= stack[-1][0]:
            stack.pop()

        key = _unquote(match.group(1))
        value = _strip_inline_comment(match.group(2) or "")
        path = (stack[-1][1] if stack else ()) + (key,)
        if path in entries:
            raise AssertionError(f"Duplicate YAML key at line {line_number}: {path}")
        entries[path] = _unquote(value)

        if value in {"|", "|-", "|+", ">", ">-", ">+"}:
            block_scalar_indent = indent
        if not value:
            stack.append((indent, path))

    return entries


def _workflow_contract(text: str) -> dict[str, object]:
    if yaml is not None:
        payload = yaml.safe_load(text)
        if not isinstance(payload, dict):
            raise AssertionError("Workflow YAML did not load as a mapping")
        trigger = payload.get("on")
        if trigger is None:
            trigger = payload.get(True)
        if not isinstance(trigger, dict):
            raise AssertionError("Workflow YAML has no event mapping")

        dispatch = trigger.get("workflow_dispatch")
        dispatch_inputs = (
            dispatch.get("inputs", {})
            if isinstance(dispatch, dict)
            else {}
        )
        approved_input = (
            dispatch_inputs.get("approved_base_sha", {})
            if isinstance(dispatch_inputs, dict)
            else {}
        )
        env = payload.get("env")
        env = env if isinstance(env, dict) else {}
        return {
            "dispatch": "workflow_dispatch" in trigger,
            "approved_input": isinstance(dispatch_inputs, dict)
            and "approved_base_sha" in dispatch_inputs,
            "required": (
                approved_input.get("required")
                if isinstance(approved_input, dict)
                else None
            ),
            "type": (
                approved_input.get("type")
                if isinstance(approved_input, dict)
                else None
            ),
            "binding": env.get("ORCHESTRA_APPROVED_BASE_SHA"),
            "pull_request": "pull_request" in trigger,
            "push": "push" in trigger,
        }

    entries = _mapping_entries(text)
    return {
        "dispatch": ("on", "workflow_dispatch") in entries,
        "approved_input": (
            "on",
            "workflow_dispatch",
            "inputs",
            "approved_base_sha",
        )
        in entries,
        "required": entries.get(
            ("on", "workflow_dispatch", "inputs", "approved_base_sha", "required")
        ),
        "type": entries.get(
            ("on", "workflow_dispatch", "inputs", "approved_base_sha", "type")
        ),
        "binding": entries.get(("env", "ORCHESTRA_APPROVED_BASE_SHA")),
        "pull_request": ("on", "pull_request") in entries,
        "push": ("on", "push") in entries,
    }


def _load_workflow(path: str) -> dict[str, object]:
    return _workflow_contract((ROOT / path).read_text(encoding="utf-8"))


def _contract_errors(contract: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if not contract["dispatch"]:
        errors.append("workflow_dispatch is missing")
    if not contract["approved_input"]:
        errors.append("approved_base_sha input is missing")
    if contract["required"] is not True and str(contract["required"]).lower() != "true":
        errors.append("approved_base_sha must be required")
    if str(contract["type"]).lower() != "string":
        errors.append("approved_base_sha must be a string input")

    binding = str(contract["binding"] or "")
    normalized = re.sub(r"\s+", " ", binding).strip().lower()
    if not binding:
        errors.append("ORCHESTRA_APPROVED_BASE_SHA binding is missing")
    if "inputs.approved_base_sha" not in normalized:
        errors.append("binding does not use inputs.approved_base_sha")
    if not EVENT_GUARD.search(binding):
        errors.append("manual input is not guarded by workflow_dispatch")
    if "&&" not in binding or "||" not in binding:
        errors.append("PR and push paths are not preserved by an empty fallback")

    for forbidden in FORBIDDEN_BASELINE_REFERENCES:
        if forbidden in normalized:
            errors.append(f"forbidden baseline reference: {forbidden}")
    if re.search(r"(?<![a-z0-9_./-])main(?![a-z0-9_./-])", normalized):
        errors.append("forbidden baseline reference: main")

    if not contract["pull_request"]:
        errors.append("pull_request event is missing")
    if not contract["push"]:
        errors.append("push event is missing")
    if not EVENT_GUARD.search(binding):
        errors.append("pull_request baseline is forced to the manual input")
        errors.append("push baseline is forced to the manual input")
    return errors


def _all_contract_errors(workflows: dict[str, str]) -> list[str]:
    errors: list[str] = []
    expected = set(WORKFLOW_PATHS)
    actual = set(workflows)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        errors.append(
            f"expected exactly four workflows; missing={missing}, extra={extra}"
        )
    for path in WORKFLOW_PATHS:
        text = workflows.get(path)
        if text is None:
            continue
        for error in _contract_errors(_workflow_contract(text)):
            errors.append(f"{path}: {error}")
    return errors


def _fixture(
    *,
    input_present: bool = True,
    required: bool = True,
    binding: str | None = VALID_BINDING,
) -> str:
    lines = [
        "name: fixture",
        "on:",
        "  workflow_dispatch:",
    ]
    if input_present:
        lines.extend(
            [
                "    inputs:",
                "      approved_base_sha:",
                "        description: Explicit approved evidence baseline commit SHA",
                f"        required: {str(required).lower()}",
                "        type: string",
            ]
        )
    lines.extend(
        [
            "  pull_request:",
            "    branches:",
            "      - main",
            "  push:",
            "    branches:",
            "      - main",
            "env:",
        ]
    )
    if binding is None:
        lines.append("  OTHER: value")
    else:
        lines.append(f"  ORCHESTRA_APPROVED_BASE_SHA: {binding}")
    return "\n".join(lines) + "\n"


def _assert_rejected(text: str, marker: str) -> None:
    errors = _contract_errors(_workflow_contract(text))
    assert any(marker in error for error in errors), (marker, errors)


def _binding_for_event(
    binding: str, event_name: str, approved_base_sha: str
) -> str:
    if EVENT_GUARD.search(binding) and event_name == "workflow_dispatch":
        return approved_base_sha
    return ""


@contextmanager
def _environment(**values: str | None):
    original = {key: os.environ.get(key) for key in CONTROLLED_ENV}
    try:
        for key in CONTROLLED_ENV:
            os.environ.pop(key, None)
        for key, value in values.items():
            if value is not None:
                os.environ[key] = value
        yield
    finally:
        for key in CONTROLLED_ENV:
            os.environ.pop(key, None)
        for key, value in original.items():
            if value is not None:
                os.environ[key] = value


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _repository_head() -> str:
    return _git(ROOT, "rev-parse", "HEAD")


@contextmanager
def _event(payload: dict[str, object]):
    handle, name = tempfile.mkstemp(
        prefix="orchestra-workflow-event-", suffix=".json"
    )
    os.close(handle)
    path = Path(name)
    path.write_text(json.dumps(payload), encoding="utf-8")
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


def test_wdb_1_dispatch_without_input_is_rejected():
    _assert_rejected(_fixture(input_present=False), "approved_base_sha input is missing")


def test_wdb_2_dispatch_input_must_be_required():
    _assert_rejected(_fixture(required=False), "approved_base_sha must be required")


def test_wdb_3_dispatch_input_must_be_bound():
    _assert_rejected(_fixture(binding=None), "binding is missing")


def test_wdb_4_github_sha_is_not_a_manual_baseline():
    _assert_rejected(_fixture(binding="github.sha"), "github.sha")


def test_wdb_5_implicit_baseline_fallbacks_are_rejected():
    for fallback in ("main", "origin/main", "merge-base", "HEAD^"):
        binding = (
            "github.event_name == 'workflow_dispatch' "
            f"&& {fallback} || ''"
        )
        _assert_rejected(_fixture(binding=binding), "forbidden baseline reference")


def test_wdb_6_all_four_workflows_are_required():
    workflows = {path: _fixture() for path in WORKFLOW_PATHS}
    workflows.pop(WORKFLOW_PATHS[-1])
    errors = _all_contract_errors(workflows)
    assert any("exactly four workflows" in error for error in errors), errors


def test_wdb_7_pull_request_is_not_forced_to_manual_input():
    _assert_rejected(
        _fixture(binding="inputs.approved_base_sha"),
        "pull_request baseline is forced",
    )


def test_wdb_8_push_is_not_forced_to_manual_input():
    _assert_rejected(
        _fixture(binding="inputs.approved_base_sha"),
        "push baseline is forced",
    )


def test_wdb_9_valid_dispatch_binding_is_exact():
    workflows = {path: _load_workflow(path) for path in WORKFLOW_PATHS}
    for path, contract in workflows.items():
        errors = _contract_errors(contract)
        assert not errors, (path, errors)
        binding = str(contract["binding"])
        assert (
            _binding_for_event(binding, "workflow_dispatch", "BASELINE")
            == "BASELINE"
        )
        assert _binding_for_event(binding, "pull_request", "BASELINE") == ""
        assert _binding_for_event(binding, "push", "BASELINE") == ""


def test_wdb_10_invalid_dispatch_baseline_fails_closed():
    with _environment(
        ORCHESTRA_APPROVED_BASE_SHA="f" * 40,
        GITHUB_ACTIONS="true",
        GITHUB_EVENT_NAME="workflow_dispatch",
    ):
        try:
            runner.resolve_evidence_baseline(str(ROOT))
        except RuntimeError as exc:
            assert "not available locally" in str(exc)
        else:
            raise AssertionError("unavailable explicit baseline was accepted")


def test_wdb_11_verified_pull_request_base_remains_supported():
    baseline = _repository_head()
    with _event({"pull_request": {"base": {"sha": baseline}}}) as event_path:
        with _environment(
            GITHUB_ACTIONS="true",
            GITHUB_EVENT_NAME="pull_request",
            GITHUB_EVENT_PATH=str(event_path),
        ):
            assert runner.resolve_evidence_baseline(str(ROOT)) == baseline


def test_wdb_12_verified_push_before_remains_supported():
    baseline = _repository_head()
    with _event({"before": baseline}) as event_path:
        with _environment(
            GITHUB_ACTIONS="true",
            GITHUB_EVENT_NAME="push",
            GITHUB_EVENT_PATH=str(event_path),
        ):
            assert runner.resolve_evidence_baseline(str(ROOT)) == baseline


def main() -> int:
    tests = (
        ("WDB-1", test_wdb_1_dispatch_without_input_is_rejected),
        ("WDB-2", test_wdb_2_dispatch_input_must_be_required),
        ("WDB-3", test_wdb_3_dispatch_input_must_be_bound),
        ("WDB-4", test_wdb_4_github_sha_is_not_a_manual_baseline),
        ("WDB-5", test_wdb_5_implicit_baseline_fallbacks_are_rejected),
        ("WDB-6", test_wdb_6_all_four_workflows_are_required),
        ("WDB-7", test_wdb_7_pull_request_is_not_forced_to_manual_input),
        ("WDB-8", test_wdb_8_push_is_not_forced_to_manual_input),
        ("WDB-9", test_wdb_9_valid_dispatch_binding_is_exact),
        ("WDB-10", test_wdb_10_invalid_dispatch_baseline_fails_closed),
        ("WDB-11", test_wdb_11_verified_pull_request_base_remains_supported),
        ("WDB-12", test_wdb_12_verified_push_before_remains_supported),
    )
    for identifier, test in tests:
        test()
        print(f"{identifier}=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
