"""automation.paths — WSL <-> Windows path translation.

Ableton runs on Windows, so any file path handed to the Remote Script (audio
imports, exports) must be a Windows path, not a WSL one.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def to_windows_path(path: Path | str) -> str:
    """Convert a WSL path to its Windows equivalent via wslpath.

    Falls back to the original string if wslpath is unavailable (e.g. already a
    Windows path passed through from the caller).
    """
    raw = str(path)
    try:
        proc = subprocess.run(["wslpath", "-w", raw], capture_output=True,
                              text=True, timeout=10)
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return raw
