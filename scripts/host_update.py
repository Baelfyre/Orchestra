#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestra_runtime.host_updates import HostUpdateError, build_host_update_plan


def _print_human(plan: dict[str, object]) -> None:
    print(f"Host: {plan['host_id']} ({plan['maturity']})")
    print(f"Package version: {plan['package_version']}")
    print(f"Update status: {plan['update_status']}")
    if plan.get("latest_version"):
        print(f"Latest version: {plan['latest_version']}")
    print(f"Update mechanism: {plan['update_mechanism']}")
    print("Behavior: READ_ONLY_PLAN")
    print("Execution authorized: false")
    print("Automatic installed-integration refresh: false")
    print("Instructions:")
    for item in plan["update_instructions"]:
        print(f"  - {item}")
    print("Validation:")
    for item in plan["validation_commands"]:
        print(f"  - {item}")
    print("Recovery:")
    for item in plan["recovery_hints"]:
        print(f"  - {item}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="orchestra-host-update",
        description="Resolve a deterministic read-only host update plan. This command never mutates an installed integration.",
    )
    parser.add_argument("--host", required=True, help="Host id or declared alias")
    parser.add_argument("--latest-version", help="Optional observed latest Orchestra version for deterministic status comparison")
    parser.add_argument("--json", action="store_true", help="Emit the machine-readable plan")
    args = parser.parse_args(argv)

    try:
        plan = build_host_update_plan(args.host, latest_version=args.latest_version, root=ROOT).to_dict()
    except HostUpdateError as exc:
        print(f"ORCHESTRA_HOST_UPDATE=FAIL:{exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        _print_human(plan)
    print("ORCHESTRA_HOST_UPDATE=READ_ONLY_PLAN", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
