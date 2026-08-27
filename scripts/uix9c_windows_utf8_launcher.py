"""Launch the frozen UIX-9C V2 runner under Python UTF-8 mode.

This is a host-compatibility shim only. It does not modify experiment inputs,
model/provider identity, execution order, evidence logic, or scientific result
classification. Python UTF-8 mode is required because the Windows locale may
otherwise decode Codex JSONL through cp1252 and fail on valid UTF-8 output.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "uix9b_live_proof_runner_v2.py"


def build_command(arguments: Sequence[str]) -> list[str]:
    return [sys.executable, "-X", "utf8", str(RUNNER), *arguments]


def main(arguments: Sequence[str] | None = None) -> int:
    command = build_command(list(sys.argv[1:] if arguments is None else arguments))
    completed = subprocess.run(command, cwd=ROOT, shell=False, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
