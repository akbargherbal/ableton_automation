"""automation.als.snapshot — file-level backup/restore for `.als` sets.

Because `.als` edits happen offline, a whole-file copy is the truest rollback
available: it captures the plugin state blob, arrangement, and everything the
shallow LOM snapshot cannot see. Restoring is deliberately blunt -- quit Live,
swap the file, reopen -- which is the rollback model confirmed in Phase 0.4.

`restore()` refuses when the Remote Script socket is reachable (Live is running)
unless `force=True`, mirroring the community writer's guard.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import socket
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..handoff import Handoff

DEFAULT_HOST = os.environ.get("ABLETON_MCP_HOST", "localhost")
DEFAULT_PORT = int(os.environ.get("ABLETON_MCP_PORT", "9877"))


class AlsSnapshotError(RuntimeError):
    """A snapshot/restore operation is unsafe or failed verification."""


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: Path | str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            data = f.read(chunk)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def live_socket_open(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                     timeout: float = 0.25) -> bool:
    """True if the Remote Script socket answers (i.e. Live is running)."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@dataclass
class Snapshot:
    original: str
    snapshot: str
    sha256: str
    size: int
    created_at: str

    def as_dict(self) -> dict:
        return {"original": self.original, "snapshot": self.snapshot,
                "sha256": self.sha256, "size": self.size,
                "created_at": self.created_at}


@dataclass
class RestoreResult:
    snapshot: str
    target: str
    applied: bool
    backup: str | None
    sha256_target: str

    def as_dict(self) -> dict:
        return {"snapshot": self.snapshot, "target": self.target,
                "applied": self.applied, "backup": self.backup,
                "sha256_target": self.sha256_target}


def snapshot(path: Path | str, dest_dir: Path | str | None = None,
             *,
             label: str = "snapshot") -> Snapshot:
    """Copy `path` into an immutable, hashed snapshot file."""
    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(f"set not found: {src}")
    dest = Path(dest_dir) if dest_dir else src.parent / "snapshots"
    dest.mkdir(parents=True, exist_ok=True)
    stamp = _utc_stamp()
    out = dest / f"{stamp}_{label}_{src.name}"
    fd, tmp = tempfile.mkstemp(dir=str(dest), prefix=out.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            with open(src, "rb") as g:
                shutil.copyfileobj(g, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, out)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return Snapshot(original=str(src), snapshot=str(out), sha256=sha256_file(out),
                    size=out.stat().st_size, created_at=stamp)


def restore(snapshot_path: Path | str, target: Path | str, *,
            apply: bool = False, force: bool = False,
            backup: bool = True) -> RestoreResult:
    """Atomically replace `target` with `snapshot_path`.

    Refuses while Live is running unless `force=True`. Backs up the current
    `target` first (unless `backup=False`). Dry-run unless `apply=True`.
    """
    snap, dst = Path(snapshot_path), Path(target)
    if not snap.exists():
        raise FileNotFoundError(f"snapshot not found: {snap}")
    if live_socket_open() and not force:
        raise AlsSnapshotError(
            "Ableton appears to be running (Remote Script socket is open). "
            "Quit Live before restoring, or pass force=True if you are certain "
            "this set is not the open one."
        )
    digest = sha256_file(snap)
    backup_path: Path | None = None
    if apply:
        if dst.exists() and backup:
            backup_path = dst.with_name(f"{dst.name}.{_utc_stamp()}.pre-restore.bak")
            shutil.copy2(dst, backup_path)
        dst.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(dst.parent), prefix=dst.name, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as f:
                with open(snap, "rb") as g:
                    shutil.copyfileobj(g, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, dst)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    return RestoreResult(snapshot=str(snap), target=str(dst), applied=apply,
                         backup=str(backup_path) if backup_path else None,
                         sha256_target=digest)


def verify(path: Path | str, expected_sha256: str) -> bool:
    return sha256_file(path) == expected_sha256


def restore_handoff(target: Path | str, snapshot_path: Path | str) -> Handoff:
    """Guided procedure for the close-swap-reopen restore (Q5 model)."""
    dst, snap = Path(target), Path(snapshot_path)
    digest = sha256_file(snap) if snap.exists() else ""

    def _ok() -> bool:
        return dst.exists() and digest != "" and sha256_file(dst) == digest

    return Handoff(
        id="als_restore",
        title=f"Restore {dst.name} from snapshot",
        anchor="Ableton Live (close the set / quit the app first)",
        steps=[
            "Save nothing further in Live; quit Live (File > Quit) so the set is closed.",
            f"Replace '{dst}' with the snapshot '{snap}'.",
            "Reopen the set in Live and confirm the previous state is present.",
        ],
        expected=f"'{dst}' has SHA-256 {digest[:16]}…",
        verify=_ok,
    )
