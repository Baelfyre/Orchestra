"""Run the OR-GOV-7 behavior matrix under the runtime coverage gate.

The repository's runtime coverage job collects only ``tests/runtime``. Reusing
the focused matrix here keeps the evaluator's branch coverage aligned without
creating a second assertion set.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "overseer_architecture_validation_behavior",
    ROOT / "tests" / "behavior" / "test_overseer_architecture_validation_contract.py",
)
assert SPEC and SPEC.loader
BEHAVIOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BEHAVIOR)


def test_or_gov_7_behavior_matrix_runs_under_runtime_coverage() -> None:
    BEHAVIOR._run()
