#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestra_runtime.mcp_transport import build_mcp_stdio_transport


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="orchestra-mcp-stdio",
        description="Serve Orchestra's governed MCP 2026-07-28 tool transport over stdio.",
    )
    parser.add_argument(
        "--adapter",
        default="codex",
        help="Existing Orchestra PRAP adapter identity used as the runtime backing adapter (default: codex).",
    )
    args = parser.parse_args(argv)

    try:
        transport = build_mcp_stdio_transport(ROOT, backing_adapter=args.adapter)
    except (OSError, ValueError) as exc:
        print(f"ORCHESTRA_MCP_STARTUP=FAIL:{exc}", file=sys.stderr)
        return 2
    return transport.serve_stdio()


if __name__ == "__main__":
    raise SystemExit(main())
