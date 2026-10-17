#!/usr/bin/env python3
"""Run the synthetic-only JEV pilot with network dispatch blocked."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import http.client
import io
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "tests" / "fixtures" / "jev_offline_pilot_scenarios.v1.json"
DEFAULT_OUTPUT_DIR = Path.home() / ".orchestra" / "jev-offline-pilot"
CATALOG_SCHEMA = "orchestra.jev-offline-pilot-scenarios.v1"
SESSION_SCHEMA = "orchestra.jev-offline-pilot-session.v1"


class PilotError(RuntimeError):
    pass


class OfflineNetworkAttempt(RuntimeError):
    pass


@contextlib.contextmanager
def offline_network_guard():
    """Block common Python HTTP, DNS, and TCP dispatch paths for the test process."""
    attempts = {"count": 0}

    def blocked_dispatch(*_args: object, **_kwargs: object) -> None:
        attempts["count"] += 1
        raise OfflineNetworkAttempt("network dispatch is blocked by the offline JEV pilot")

    targets = (
        "socket.create_connection",
        "socket.getaddrinfo",
        "socket.socket",
        "urllib.request.urlopen",
        "urllib.request.OpenerDirector.open",
        "http.client.HTTPConnection.connect",
        "http.client.HTTPSConnection.connect",
    )
    with contextlib.ExitStack() as stack:
        for target in targets:
            stack.enter_context(patch(target, side_effect=blocked_dispatch))
        yield attempts


def load_catalog() -> dict[str, object]:
    value = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != CATALOG_SCHEMA:
        raise PilotError("unsupported JEV pilot scenario catalog")
    scenarios = value.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise PilotError("scenario catalog must contain scenarios")
    seen: set[str] = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise PilotError("scenario entry must be an object")
        scenario_id = scenario.get("id")
        test_ids = scenario.get("test_ids")
        if not isinstance(scenario_id, str) or not scenario_id or scenario_id in seen:
            raise PilotError("scenario IDs must be non-empty and unique")
        seen.add(scenario_id)
        if not isinstance(test_ids, list) or not test_ids:
            raise PilotError(f"scenario {scenario_id} has no pytest node IDs")
        for node_id in test_ids:
            if not isinstance(node_id, str) or "::" not in node_id:
                raise PilotError(f"scenario {scenario_id} has an invalid pytest node ID")
            test_path = Path(node_id.split("::", 1)[0])
            if test_path.is_absolute() or ".." in test_path.parts or not (ROOT / test_path).is_file():
                raise PilotError(f"scenario {scenario_id} references an unavailable test file")
        if not isinstance(scenario.get("expected"), dict):
            raise PilotError(f"scenario {scenario_id} has no expected result")
        if scenario.get("response_provenance") not in {
            "NO_PROVIDER_RESPONSE",
            "SYNTHETIC_TYPED_RESPONSE",
            "FAKE_TRANSPORT_SYNTHETIC_RESPONSE",
            "SANITIZED_FIXTURE_REPLAY",
        }:
            raise PilotError(f"scenario {scenario_id} has unrecognized response provenance")
    return value


def _git_snapshot() -> dict[str, str]:
    def output(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(ROOT), *args],
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )
        if result.returncode:
            raise PilotError("could not verify the pilot worktree")
        return result.stdout.strip()

    return {
        "root": output("rev-parse", "--show-toplevel"),
        "branch": output("branch", "--show-current"),
        "head": output("rev-parse", "HEAD"),
        "tree": output("rev-parse", "HEAD^{tree}"),
        "status": output("status", "--porcelain", "--untracked-files=all"),
    }


def _outside_repository(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        return resolved
    raise PilotError("pilot artifacts must be written outside the repository")


def _matches_node_id(collected: str, requested: str) -> bool:
    return collected == requested or collected.startswith(requested + "[")


class _ResultCollector:
    def __init__(self) -> None:
        self.collected: list[str] = []
        self.results: dict[str, dict[str, object]] = {}

    def pytest_collection_finish(self, session) -> None:
        self.collected = [item.nodeid for item in session.items]

    def pytest_runtest_logreport(self, report) -> None:
        item = self.results.setdefault(
            report.nodeid,
            {"status": "PASS", "duration_seconds": 0.0, "failure_class": None},
        )
        item["duration_seconds"] = float(item["duration_seconds"]) + float(report.duration)
        if report.outcome == "failed":
            item["status"] = "FAIL"
            crash = getattr(report.longrepr, "reprcrash", None)
            message = getattr(crash, "message", "")
            candidate = message.split(":", 1)[0].split()[-1] if message else ""
            item["failure_class"] = candidate if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", candidate) else "TEST_FAILURE"
        elif report.outcome == "skipped" and item["status"] == "PASS":
            item["status"] = "SKIP"


def _scenario_status(scenario: dict[str, object], collector: _ResultCollector) -> dict[str, object]:
    node_ids = scenario["test_ids"]
    matched: list[str] = []
    missing: list[str] = []
    for requested in node_ids:
        found = [node for node in collector.collected if _matches_node_id(node, requested)]
        if found:
            matched.extend(found)
        else:
            missing.append(requested)
    cases = [collector.results[node] for node in matched if node in collector.results]
    if missing:
        status = "NOT_COLLECTED"
    elif not cases or len(cases) != len(matched):
        status = "NOT_RUN"
    elif any(case["status"] == "FAIL" for case in cases):
        status = "FAIL"
    elif any(case["status"] == "SKIP" for case in cases):
        status = "SKIP"
    else:
        status = "PASS"

    expected = scenario["expected"]
    return {
        "scenario_id": scenario["id"],
        "name": scenario["name"],
        "status": status,
        "regression_classification": (
            "NO_REGRESSION_OBSERVED" if status == "PASS" else
            "UNRESOLVED_TEST_REGRESSION" if status == "FAIL" else
            "VALIDATION_GAP"
        ),
        "expected": expected,
        "observed": {
            "eligibility": expected.get("eligibility") if status == "PASS" else "UNCONFIRMED",
            "result": expected.get("result") if status == "PASS" else "ASSERTIONS_NOT_CONFIRMED",
            "rejection_reason": expected.get("rejection_reason") if status == "PASS" else None,
            "basis": "all mapped pytest assertions passed" if status == "PASS" else "mapped pytest assertions did not all pass",
        },
        "response_provenance": scenario["response_provenance"],
        "evidence_refs": scenario.get("evidence_refs", []),
        "evidence_gap": scenario.get("evidence_gap"),
        "test_counts": {
            "collected": len(matched),
            "passed": sum(case["status"] == "PASS" for case in cases),
            "failed": sum(case["status"] == "FAIL" for case in cases),
            "skipped": sum(case["status"] == "SKIP" for case in cases),
            "not_collected": len(missing),
        },
        "test_seconds": round(sum(float(case["duration_seconds"]) for case in cases), 6),
        "failure_classes": sorted({str(case["failure_class"]) for case in cases if case.get("failure_class")}),
    }


def _compare(current: list[dict[str, object]], previous_path: Path | None) -> dict[str, object] | None:
    if previous_path is None:
        return None
    previous = json.loads(previous_path.read_text(encoding="utf-8"))
    if not isinstance(previous, dict) or previous.get("schema_version") != SESSION_SCHEMA:
        raise PilotError("comparison artifact is not a JEV pilot session")
    previous_scenarios = previous.get("scenarios")
    if not isinstance(previous_scenarios, list):
        raise PilotError("comparison artifact has no scenario results")
    old = {item.get("scenario_id"): item.get("status") for item in previous_scenarios if isinstance(item, dict)}
    new = {item["scenario_id"]: item["status"] for item in current}
    return {
        "previous_session_id": previous.get("session_id"),
        "status_changes": [
            {"scenario_id": key, "from": old[key], "to": new[key]}
            for key in sorted(old.keys() & new.keys())
            if old[key] != new[key]
        ],
        "new_scenarios": sorted(new.keys() - old.keys()),
        "removed_scenarios": sorted(old.keys() - new.keys()),
    }


def _write_session(path: Path, session: dict[str, object]) -> int:
    session["artifact_bytes"] = 0
    for _ in range(4):
        encoded = (json.dumps(session, indent=2, sort_keys=True) + "\n").encode("utf-8")
        size = len(encoded)
        if session["artifact_bytes"] == size:
            break
        session["artifact_bytes"] = size
    encoded = (json.dumps(session, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(encoded)
    return len(encoded)


def run_pilot(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    selected_ids: set[str] | None = None,
    compare_path: Path | None = None,
) -> dict[str, object]:
    catalog = load_catalog()
    all_scenarios = catalog["scenarios"]
    available = {scenario["id"] for scenario in all_scenarios}
    selected = available if selected_ids is None else selected_ids
    unknown = selected - available
    if unknown:
        raise PilotError("unknown scenario ID")
    scenarios = [scenario for scenario in all_scenarios if scenario["id"] in selected]
    before = _git_snapshot()
    if before["status"] or not before["branch"]:
        raise PilotError("pilot requires a clean branch worktree")
    if compare_path is not None:
        _compare([], compare_path)

    output_dir = _outside_repository(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    session_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_path = output_dir / f"jev-offline-pilot-{session_id}.json"
    suffix = 1
    while output_path.exists():
        output_path = output_dir / f"jev-offline-pilot-{session_id}-{suffix}.json"
        suffix += 1

    collector = _ResultCollector()
    node_ids = list(dict.fromkeys(node_id for scenario in scenarios for node_id in scenario["test_ids"]))
    original_plugin_setting = os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD")
    old_dont_write_bytecode = sys.dont_write_bytecode
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    sys.dont_write_bytecode = True
    started = time.perf_counter()
    cpu_started = time.process_time()
    runner_error = None
    network_guard = {"count": 0}
    with tempfile.TemporaryDirectory(prefix="orchestra-jev-pilot-") as base_temp:
        captured = io.StringIO()
        try:
            with offline_network_guard() as network_guard, contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
                import pytest

                exit_code = int(
                    pytest.main(
                        ["-q", "-p", "no:cacheprovider", "--basetemp", base_temp, *node_ids],
                        plugins=[collector],
                    )
                )
        except Exception as exc:  # noqa: BLE001 - sanitized fail-closed pilot record
            exit_code = 2
            runner_error = type(exc).__name__
        finally:
            if original_plugin_setting is None:
                os.environ.pop("PYTEST_DISABLE_PLUGIN_AUTOLOAD", None)
            else:
                os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = original_plugin_setting
            sys.dont_write_bytecode = old_dont_write_bytecode

    wall_seconds = round(time.perf_counter() - started, 6)
    cpu_seconds = round(time.process_time() - cpu_started, 6)
    after = _git_snapshot()
    scenario_results = [_scenario_status(scenario, collector) for scenario in scenarios]
    test_counts = {
        "collected": len(collector.collected),
        "passed": sum(item["status"] == "PASS" for item in collector.results.values()),
        "failed": sum(item["status"] == "FAIL" for item in collector.results.values()),
        "skipped": sum(item["status"] == "SKIP" for item in collector.results.values()),
    }
    integrity = before == after
    session = {
        "schema_version": SESSION_SCHEMA,
        "session_id": session_id,
        "session_date_utc": dt.datetime.now(dt.timezone.utc).date().isoformat(),
        "pilot_window": catalog.get("pilot_window"),
        "candidate": {key: before[key] for key in ("root", "branch", "head", "tree")},
        "source_integrity": "UNCHANGED" if integrity else "CHANGED",
        "pytest_exit_code": exit_code,
        "runner_error_class": runner_error,
        "scenario_catalog_sha256": hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest(),
        "network_guard": "HTTP_DNS_AND_TCP_BLOCKED_IN_TEST_PROCESS",
        "blocked_network_attempts": network_guard["count"],
        "external_provider_calls": 0,
        "actual_jev_inference": False,
        "synthetic_responses_only": True,
        "test_counts": test_counts,
        "performance": {
            "runner_wall_seconds": wall_seconds,
            "runner_cpu_seconds": cpu_seconds,
            "mapped_test_seconds": round(sum(float(item["test_seconds"]) for item in scenario_results), 6),
            "peak_memory_bytes": None,
            "peak_memory_measurement": "NOT_MEASURED",
        },
        "scenarios": scenario_results,
        "comparison": _compare(scenario_results, compare_path),
    }
    session["status"] = "PASS" if exit_code == 0 and integrity and network_guard["count"] == 0 and all(item["status"] == "PASS" for item in scenario_results) else "FAIL"
    artifact_bytes = _write_session(output_path, session)
    return {
        "status": session["status"],
        "session_id": session_id,
        "artifact_path": str(output_path),
        "artifact_bytes": artifact_bytes,
        "scenario_count": len(scenario_results),
        "test_counts": test_counts,
        "external_provider_calls": 0,
        "actual_jev_inference": False,
        "blocked_network_attempts": network_guard["count"],
        "source_integrity": session["source_integrity"],
        "pytest_exit_code": exit_code,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--scenario", action="append", dest="scenario_ids")
    parser.add_argument("--compare", type=Path)
    parser.add_argument("--list", action="store_true", dest="list_scenarios")
    args = parser.parse_args(argv)
    try:
        catalog = load_catalog()
        if args.list_scenarios:
            print(json.dumps([{"id": item["id"], "name": item["name"], "expected": item["expected"]} for item in catalog["scenarios"]], indent=2))
            return 0
        summary = run_pilot(
            args.output_dir,
            set(args.scenario_ids) if args.scenario_ids else None,
            args.compare,
        )
        print(json.dumps(summary, sort_keys=True))
        return 0 if summary["status"] == "PASS" else 2
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, PilotError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error_class": type(exc).__name__}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
