"""automation.lock — single-run lock.

Only one automation process may drive a given Ableton instance at a time;
concurrent writers corrupt state. Uses an OS advisory lock (fcntl) so a crashed
process is released automatically when its file descriptor closes.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX
    fcntl = None


class LockBusy(RuntimeError):
    """Another automation run already holds the lock."""


class RunLock:
    """Context manager holding an exclusive lock on a file."""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self._fh = None

    def __enter__(self) -> "RunLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.path, "w")
        if fcntl is not None:
            try:
                fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as e:
                self._fh.close()
                self._fh = None
                raise LockBusy(
                    f"Another automation run holds {self.path}. Wait for it to "
                    "finish, or remove the file if you're sure no run is active."
                ) from e
        self._fh.write(str(os.getpid()))
        self._fh.flush()
        return self

    def __exit__(self, *exc) -> None:
        if self._fh is not None:
            try:
                if fcntl is not None:
                    fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
            finally:
                self._fh.close()
                self._fh = None
