"""automation.probe — device parameter capture.

Two modes:

* snapshot_loaded_devices — read-only. Dumps every device already on the set,
  so a chain can be documented without touching anything.
* probe_plugin — briefly loads a plugin onto a throwaway scratch track, dumps
  its parameters, then removes the track. Requires an explicit live=True so a
  dry run is the default. This is how unknown plugins get classified as
  LOM-drivable vs GUI-only.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from . import plugin_profiles
from . import plugins as plugins_mod
from .lom import LomClient


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def snapshot_loaded_devices(client: LomClient, out_dir: Path | str) -> dict:
    """Read-only: dump parameters for every device on every session track."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    index: dict = {"captured_at": _stamp(), "tracks": []}
    for track in client.all_tracks():
        entry = {"track_index": track.get("index"), "track_name": track.get("name"),
                 "devices": []}
        for dev in track.get("devices", []):
            di = dev.get("index")
            try:
                params = client.device_parameters(track["index"], di)
            except Exception as e:  # a broken device shouldn't abort the sweep
                entry["devices"].append({"index": di, "name": dev.get("name"),
                                         "error": f"{type(e).__name__}: {e}"})
                continue
            mode = plugin_profiles.classify(params.get("device_name", ""),
                                            params.get("parameter_count"))
            path = out / f"track{track['index']}_device{di}_{_safe(dev.get('name','dev'))}.json"
            payload = {"track_index": track["index"], "device_index": di,
                       "control_mode": mode, **params}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
            entry["devices"].append({
                "index": di, "name": params.get("device_name", dev.get("name")),
                "class_name": params.get("device_class"),
                "parameter_count": params.get("parameter_count"),
                "control_mode": mode, "path": str(path),
            })
        index["tracks"].append(entry)
    index_path = out / f"index_{_stamp()}.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, default=str)
    index["index_path"] = str(index_path)
    return index


def _safe(name: str) -> str:
    return "".join(c if (c.isalnum() or c in "-_") else "-" for c in name).strip("-") or "dev"


def probe_plugin(client: LomClient, plugin_query: str, out_dir: Path | str,
                 *, live: bool = False, settle: float = 3.0) -> dict:
    """Load a plugin on a scratch track, capture its params, remove the track.

    live=False resolves and reports the match without loading anything.
    """
    plugin = plugins_mod.resolve_plugin(client, plugin_query)
    plan = {"plugin": plugin["name"], "path": plugin["path"], "uri": plugin["uri"]}
    if not live:
        return {"dry_run": True, **plan}

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    original_count = int(client.session_info()["track_count"])
    scratch = client.create_midi_track(-1)["index"]
    try:
        client.load_browser_item(scratch, plugin["uri"])
        time.sleep(settle)
        devices = client.track_info(scratch).get("devices", [])
        if not devices:
            raise RuntimeError(f"{plugin['name']!r} loaded but no device appeared")
        di = devices[-1]["index"]
        params = client.device_parameters(scratch, di)
        mode = plugin_profiles.classify(params.get("device_name", ""),
                                        params.get("parameter_count"))
        payload = {"probed_at": _stamp(), "control_mode": mode,
                   "plugin_query": plugin_query, **params}
        fname = out / f"{_safe(plugin['name'])}__{mode}.json"
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        return {"dry_run": False, "control_mode": mode,
                "parameter_count": params.get("parameter_count"),
                "path": str(fname), **plan}
    finally:
        # always return the session to its original track count
        for _ in range(5):
            try:
                if int(client.session_info()["track_count"]) <= original_count:
                    break
                client.delete_track(int(client.session_info()["track_count"]) - 1)
            except Exception:
                time.sleep(0.5)
