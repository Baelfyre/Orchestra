# @codebase_provenance_JEO
# @codebase_rights_JEO
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.validation.build_coverage_inventory import (
    CRITICAL_MODULES,
    build_inventory,
)


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validation" / "build_coverage_inventory.py"


def _coverage(
    paths: list[str], *, below_floor_paths: set[str] | None = None
) -> dict[str, object]:
    below_floor_paths = below_floor_paths or set()
    files: dict[str, dict[str, object]] = {}
    for path in paths:
        low = path in below_floor_paths
        covered_statements = 97 if low else 98
        covered_branches = 18 if low else 19
        files[path] = {
            "summary": {
                "num_statements": 100,
                "covered_lines": covered_statements,
                "missing_lines": 100 - covered_statements,
                "num_branches": 20,
                "covered_branches": covered_branches,
                "missing_branches": 20 - covered_branches,
            },
            "missing_lines": list(range(1, 101 - covered_statements)),
            "excluded_lines": [],
        }
    return {
        "files": files,
        "totals": {
            "num_statements": 100 * len(files),
            "covered_lines": sum(
                record["summary"]["covered_lines"] for record in files.values()
            ),
            "num_branches": 20 * len(files),
            "covered_branches": sum(
                record["summary"]["covered_branches"] for record in files.values()
            ),
        },
    }


def _write_coverage(tmp_path: Path, payload: dict[str, object]) -> Path:
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _critical_rows(inventory: dict[str, object]) -> list[dict[str, object]]:
    return [module for module in inventory["modules"] if module["critical"]]


def test_posix_paths_detect_all_critical_modules_at_policy_floors(tmp_path: Path) -> None:
    inventory = build_inventory(_write_coverage(tmp_path, _coverage(list(CRITICAL_MODULES))))

    rows = _critical_rows(inventory)
    assert inventory["critical_ready"] is True
    assert inventory["critical_failures"] == []
    assert len(rows) == len(CRITICAL_MODULES)
    assert {row["path"] for row in rows} == set(CRITICAL_MODULES)
    assert all(row["statement_percent"] == 98.0 for row in rows)
    assert all(row["branch_percent"] == 95.0 for row in rows)


def test_windows_paths_match_posix_inventory_and_keep_reported_paths(tmp_path: Path) -> None:
    posix = build_inventory(_write_coverage(tmp_path, _coverage(list(CRITICAL_MODULES))))
    windows_paths = [path.replace("/", "\\") for path in CRITICAL_MODULES]
    windows = build_inventory(
        _write_coverage(tmp_path, _coverage(windows_paths))
    )
    project = lambda inventory: {
        row["path"].replace("\\", "/"): (
            row["statement_percent"],
            row["branch_percent"],
        )
        for row in _critical_rows(inventory)
    }

    assert windows["critical_ready"] is True
    assert project(windows) == project(posix)
    assert {row["path"] for row in _critical_rows(windows)} == set(windows_paths)


def test_mixed_separators_detect_all_critical_modules(tmp_path: Path) -> None:
    mixed_paths = [
        path.replace("/", "\\") if index % 2 else path
        for index, path in enumerate(CRITICAL_MODULES)
    ]
    inventory = build_inventory(
        _write_coverage(tmp_path, _coverage(mixed_paths))
    )

    assert inventory["critical_ready"] is True
    assert len(_critical_rows(inventory)) == len(CRITICAL_MODULES)
    assert {row["path"] for row in _critical_rows(inventory)} == set(mixed_paths)


def test_missing_critical_module_has_explicit_failure(tmp_path: Path) -> None:
    missing = CRITICAL_MODULES[4]
    paths = [path for path in CRITICAL_MODULES if path != missing]
    inventory = build_inventory(_write_coverage(tmp_path, _coverage(paths)))

    failure = next(row for row in inventory["critical_failures"] if row["path"] == missing)
    assert inventory["critical_ready"] is False
    assert failure["reasons"] == ["CRITICAL_MODULE_MISSING"]


def test_zero_critical_matches_fail_cli_with_all_missing_paths(tmp_path: Path) -> None:
    coverage_path = _write_coverage(
        tmp_path, _coverage(["orchestra_runtime/unrelated.py"])
    )
    output_path = tmp_path / "inventory.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--coverage",
            str(coverage_path),
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    stdout = json.loads(result.stdout)
    report = json.loads(output_path.read_text(encoding="utf-8"))

    missing_in_report = {
        failure["path"]
        for failure in report["critical_failures"]
        if "CRITICAL_MODULE_MISSING" in failure["reasons"]
    }
    missing_in_stdout = {
        failure["path"]
        for failure in stdout["critical_failures"]
        if "CRITICAL_MODULE_MISSING" in failure["reasons"]
    }
    assert result.returncode == 1
    assert stdout["critical_ready"] is False
    assert report["critical_ready"] is False
    assert missing_in_report == set(CRITICAL_MODULES)
    assert missing_in_stdout == set(CRITICAL_MODULES)


def test_duplicate_normalized_critical_identity_fails_explicitly(tmp_path: Path) -> None:
    identity = CRITICAL_MODULES[0]
    alias = identity.replace("/", "\\")
    paths = [*CRITICAL_MODULES, alias]
    inventory = build_inventory(_write_coverage(tmp_path, _coverage(paths)))

    duplicate_failures = [
        failure
        for failure in inventory["critical_failures"]
        if "DUPLICATE_CRITICAL_MODULE_IDENTITY" in failure["reasons"]
    ]
    identity_rows = [
        row for row in _critical_rows(inventory) if row["path"].replace("\\", "/") == identity
    ]
    assert inventory["critical_ready"] is False
    assert duplicate_failures == [
        {"path": identity, "reasons": ["DUPLICATE_CRITICAL_MODULE_IDENTITY"]}
    ]
    assert {row["path"] for row in identity_rows} == {identity, alias}


def test_duplicate_literal_json_key_is_rejected(tmp_path: Path) -> None:
    module = CRITICAL_MODULES[0]
    record = json.dumps(_coverage([module])["files"][module])
    coverage_path = tmp_path / "duplicate.json"
    coverage_path.write_text(
        f'{{"files":{{"{module}":{record},"{module}":{record}}},"totals":{{}}}}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate object key"):
        build_inventory(coverage_path)


@pytest.mark.parametrize("separator", ["/", "\\"])
def test_below_floor_critical_module_fails_with_each_separator(
    tmp_path: Path, separator: str
) -> None:
    paths = [path.replace("/", separator) for path in CRITICAL_MODULES]
    below_floor = CRITICAL_MODULES[0].replace("/", separator)
    inventory = build_inventory(
        _write_coverage(
            tmp_path,
            _coverage(paths, below_floor_paths={below_floor}),
        )
    )

    failure = next(
        row for row in inventory["critical_failures"] if row["path"] == below_floor
    )
    assert inventory["critical_ready"] is False
    assert failure["reasons"] == [
        "CRITICAL_STATEMENT_COVERAGE_BELOW_FLOOR",
        "CRITICAL_BRANCH_COVERAGE_BELOW_FLOOR",
    ]


def test_noncritical_lookalikes_do_not_affect_critical_inventory(tmp_path: Path) -> None:
    lookalikes = [
        "prefix/orchestra_runtime/evidence.py",
        "orchestra_runtime/evidence.py.bak",
        r"C:\repo\orchestra_runtime\evidence.py",
        "../orchestra_runtime/evidence.py",
    ]
    paths = [*CRITICAL_MODULES, *lookalikes]
    inventory = build_inventory(
        _write_coverage(
            tmp_path,
            _coverage(paths, below_floor_paths=set(lookalikes)),
        )
    )
    rows = {row["path"]: row for row in inventory["modules"]}

    assert inventory["critical_ready"] is True
    assert len(_critical_rows(inventory)) == len(CRITICAL_MODULES)
    assert all(rows[path]["critical"] is False for path in lookalikes)
    assert all(rows[path]["statement_percent"] == 97.0 for path in lookalikes)


def test_malformed_and_inconsistent_coverage_keep_error_behavior(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        build_inventory(malformed)

    payload = _coverage(list(CRITICAL_MODULES))
    payload["files"][CRITICAL_MODULES[0]]["summary"]["missing_lines"] = 99
    inconsistent = _write_coverage(tmp_path, payload)
    with pytest.raises(ValueError, match="coverage statement totals are inconsistent"):
        build_inventory(inconsistent)
