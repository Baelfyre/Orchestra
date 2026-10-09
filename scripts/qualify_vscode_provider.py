#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from orchestra_runtime.provider_qualification import (
    ProviderQualificationContractError,
    qualify_vscode_provider_observation,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a VS Code multi-harness provider observation and emit a non-authorizing qualification receipt."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        receipt = qualify_vscode_provider_observation(payload)
    except (OSError, json.JSONDecodeError, ProviderQualificationContractError) as exc:
        reason = getattr(exc, "reason_code", "INVALID_VSCODE_PROVIDER_OBSERVATION")
        print(f"ERROR {reason}: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(receipt.to_dict(), indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
