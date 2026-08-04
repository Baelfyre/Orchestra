#!/usr/bin/env python3
"""Thin wrapper script for OrchestraStatusProjection CLI.

Delegates execution directly to `orchestra_runtime.status.main()`.
"""

import os
from pathlib import Path
import sys

# Ensure repository root is on sys.path if running uninstalled
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from orchestra_runtime.status import main

if __name__ == "__main__":
    sys.exit(main())
