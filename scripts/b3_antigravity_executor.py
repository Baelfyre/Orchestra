#!/usr/bin/env python3
"""B3 host-parameter adapter over the canonical Antigravity executor."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import antigravity_benchmark_executor as executor


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute one frozen B3 request")
    parser.add_argument("--expected-cli-version", required=True)
    parser.add_argument("--expected-model", required=True)
    parser.add_argument("--agy-executable", type=Path, required=True)
    parser.add_argument("--settings-path", type=Path, required=True)
    parser.add_argument("--workspace-dir", type=Path, required=True)
    parser.add_argument("--caveman-repo-path", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        request = json.loads(sys.stdin.read())
        os.environ["PATH"] = str(args.agy_executable.parent) + os.pathsep + os.environ.get("PATH", "")
        executor.PINNED_MODEL = args.expected_model
        result = executor.execute_request(
            request,
            expected_cli_version=args.expected_cli_version,
            settings_path=args.settings_path,
            workspace_dir=args.workspace_dir,
            caveman_repo_path=args.caveman_repo_path,
            transport="stream-json",
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        result = executor.build_invalid_result({}, "HARNESS_FAILURE", {"error": str(exc)})
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
