#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestra_runtime.infrastructure.machine.agentic_workflow import agentic_workflow_errors
from orchestra_runtime.infrastructure.machine.execution_efficiency import execution_budget_errors
from orchestra_runtime.machine_contracts import machine_contract_errors


def main() -> int:
    errors = machine_contract_errors(ROOT) + execution_budget_errors(ROOT) + agentic_workflow_errors(ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"ORCHESTRA_MACHINE_CONTRACTS=FAIL errors={len(errors)}")
        return 1
    print("ORCHESTRA_MACHINE_CONTRACTS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
