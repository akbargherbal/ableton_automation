"""automation.state — set snapshot, diff, and best-effort backup.

Snapshotting is the safety precondition for destructive recipes: capture the
LOM-visible state before acting so a run can report exactly what changed, and
so a diff can drive rollback verification.

Note: the Remote Script currently exposes no `get_project_path` command, so
backing up the .als is best-effort (env ABLETON_SET_PATH, else a LOM query, else
skipped with an explicit warning). See AUTOMATION_PLAN.md §4.C.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .lom import LomClient, LomError

SNAPSHOT_VERSION = 1


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def capture(client: LomClient) -> dict:
    """Return a JSON-serializable snapshot of the LOM-visible set state."""
    session = client.session_info()
    tracks = []
    for i in range(int(session.get("track_count", 0))):
        info = client.track_info(i)
        tracks.append({
            "index": info.get("index", i),
            "name": info.get("name"),
            "mute": info.get("mute"),
            "solo": info.get("solo"),
            "arm": info.get("arm"),
            "volume": info.get("volume"),
            "panning": info.get("panning"),
            "devices": [
                {"index": d.get("index"), "name": d.get("name"),
                 "class_name": d.get("class_name"), "type": d.get("type")}
                for d in info.get("devices", [])
            ],
        })
    return {
        "v": SNAPSHOT_VERSION,
        "captured_at": _utc_stamp(),
        "session": session,
        "tracks": tracks,
    }


def save(snapshot: dict, out_dir: Path | str, label: str = "snapshot") -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{_utc_stamp()}_{label}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, default=str)
    return path


def load(path: Path | str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _track_map(snapshot: dict) -> dict[int, dict]:
    return {int(t["index"]): t for t in snapshot.get("tracks", [])}


def diff(before: dict, after: dict) -> list[dict]:
    """Return a list of {"path", "before", "after"} for every visible change."""
    changes: list[dict] = []

    bs = before.get("session", {})
    as_ = after.get("session", {})
    for key in ("tempo", "signature_numerator", "signature_denominator"):
        if bs.get(key) != as_.get(key):
            changes.append({"path": f"session.{key}", "before": bs.get(key), "after": as_.get(key)})
    if (bs.get("track_count"), bs.get("return_track_count")) != (as_.get("track_count"), as_.get("return_track_count")):
        changes.append({"path": "session.track_count",
                        "before": bs.get("track_count"), "after": as_.get("track_count")})
    if bs.get("master_track", {}).get("volume") != as_.get("master_track", {}).get("volume"):
        changes.append({"path": "master.volume",
                        "before": bs.get("master_track", {}).get("volume"),
                        "after": as_.get("master_track", {}).get("volume")})

    bm, am = _track_map(before), _track_map(after)
    for idx in sorted(set(bm) | set(am)):
        b, a = bm.get(idx), am.get(idx)
        if b is None or a is None:
            changes.append({"path": f"tracks[{idx}]", "before": b, "after": a})
            continue
        for key in ("name", "mute", "solo", "arm", "volume", "panning"):
            if b.get(key) != a.get(key):
                changes.append({"path": f"tracks[{idx}].{key}", "before": b.get(key), "after": a.get(key)})
        bdev = [d.get("name") for d in b.get("devices", [])]
        adev = [d.get("name") for d in a.get("devices", [])]
        if bdev != adev:
            changes.append({"path": f"tracks[{idx}].devices", "before": bdev, "after": adev})
    return changes


def try_project_path(client: LomClient) -> str | None:
    """Best-effort current .als path (env override, then LOM command)."""
    env = os.environ.get("ABLETON_SET_PATH")
    if env:
        return env
    try:
        result = client.send("get_project_path")
    except LomError:
        return None
    if isinstance(result, dict):
        return result.get("file_path") or result.get("path")
    return None


def backup_set(client: LomClient, dest_dir: Path | str) -> Path | None:
    """Copy the current .als to dest_dir. Returns the copy path or None.

    Best-effort: requires ABLETON_SET_PATH or a Remote Script that implements
    `get_project_path`. Never raises for a missing path -- callers should treat
    None as "no file backup available, rely on the JSON snapshot".
    """
    src = try_project_path(client)
    if not src:
        return None
    src_path = Path(src)
    if not src_path.exists():
        return None
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    copy = dest / f"{_utc_stamp()}_{src_path.name}"
    shutil.copy2(src_path, copy)
    return copy
