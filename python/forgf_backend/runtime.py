"""Runtime helpers for local imports inside the shared python workspace."""

from __future__ import annotations

import sys
from pathlib import Path


PYTHON_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]


def ensure_python_root_on_path() -> None:
    python_root_str = str(PYTHON_ROOT)
    if python_root_str not in sys.path:
        sys.path.insert(0, python_root_str)
