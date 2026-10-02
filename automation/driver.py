"""automation.driver — the unified actuator.

Combines the LOM client (primary), the UIA subprocess bridge (fallback/reach),
state snapshot/diff, verification, a single-run lock, and structured logging
behind one context-managed object. Recipes and the CLI use this; nothing else
should talk to lom/uia directly.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from . import plugins as plugins_mod
from . import state as state_mod
from . import uia
from . import verify
from .lock import RunLock
from .log import RunLog
from .lom import LomClient

RUNS_DIR_NAME = "RUNS"


class Driver:
    """One automation run against one Ableton instance."""

    def __init__(self, run_dir: Path | str | None = None, *, name: str = "run",
                 dry_run: bool = False, use_lock: bool = True,
                 snapshot_on_enter: bool = True) -> None:
        self.repo = uia.repo_root()
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.run_dir = Path(run_dir) if run_dir else self.repo / RUNS_DIR_NAME / f"{stamp}_{name}"
        self.name = name
        self.dry_run = dry_run
        self.use_lock = use_lock
        self.snapshot_on_enter = snapshot_on_enter
        self.log = RunLog(self.run_dir, run_id=f"{stamp}_{name}")
        self.client = LomClient()
        self._lock = RunLock(self.repo / RUNS_DIR_NAME / ".automation.lock")
        self.before: dict | None = None
        self.after: dict | None = None

    def __enter__(self) -> "Driver":
        if self.use_lock:
            self._lock.__enter__()
        self.client.connect()
        self.log.event("run_start", name=self.name, dry_run=self.dry_run,
                       run_dir=str(self.run_dir))
        if self.snapshot_on_enter:
            self.before = self.snapshot("before")
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        try:
            if self.client.connected:
                if self.snapshot_on_enter:
                    try:
                        self.after = self.snapshot("after")
                        assert self.before is not None
                        changes = state_mod.diff(self.before, self.after)
                        self.log.event("run_diff", changes=changes,
                                       change_count=len(changes))
                    except Exception as e:  # never mask the real error on exit
                        self.log.event("run_diff_failed", error=f"{type(e).__name__}: {e}")
                self.log.event(
                    "run_end",
                    result="failed" if exc_type else "success",
                    error=None if exc is None else f"{exc_type.__name__}: {exc}",
                )
        finally:
            self.client.close()
            if self.use_lock:
                self._lock.__exit__(None, None, None)
        return False

    # -- state ---------------------------------------------------------------

    def snapshot(self, label: str = "snapshot") -> dict:
        snap = state_mod.capture(self.client)
        path = state_mod.save(snap, self.run_dir, label)
        self.log.event("snapshot", label=label, path=str(path),
                       tracks=len(snap.get("tracks", [])))
        return snap

    def backup(self) -> Path | None:
        path = state_mod.backup_set(self.client, self.run_dir / "backup")
        self.log.event("backup", available=bool(path),
                       path=str(path) if path else None)
        return path

    # -- helpers -------------------------------------------------------------

    def _may_proceed(self, description: str, layer: str) -> bool:
        self.log.event("action_start", label=description, layer=layer)
        if self.dry_run:
            self.log.info(f"  [dry-run] {description}")
            self.log.event("action_result", label=description, layer=layer,
                           result="dry_run")
            return False
        return True

    # -- LOM actions ---------------------------------------------------------

    def device_control_mode(self, track_index: int, device_index: int) -> str:
        """Return "lom" or "gui" for a device (see plugin_profiles)."""
        from . import plugin_profiles
        params = self.client.device_parameters(track_index, device_index)
        return plugin_profiles.classify(params.get("device_name", ""),
                                        params.get("parameter_count"))

    def set_param(self, track_index: int, device_index: int, name: str,
                  value: float, *, parameter_index: int | None = None,
                  chain_index: int | None = None, check_value: bool = True,
                  tol: float = 0.02) -> dict | None:
        desc = f"set track[{track_index}].device[{device_index}].{name} = {value}"
        from . import plugin_profiles
        params = self.client.device_parameters(track_index, device_index,
                                               chain_index=chain_index)
        mode = plugin_profiles.classify(params.get("device_name", ""),
                                        params.get("parameter_count"))
        if mode == "gui":
            available = ", ".join(plugin_profiles.parameter_names(params)[:8])
            raise NotImplementedError(
                f"Device {params.get('device_name')!r} on track {track_index} is "
                f"GUI-only (exposes {params.get('parameter_count')} LOM param(s): "
                f"{available}). It cannot be driven by set_device_parameter. Use "
                "the plugin GUI (UIA) or preset loading instead -- see "
                "docs/CAPABILITY_MATRIX.md."
            )
        if not self._may_proceed(desc, "lom"):
            return None
        result = self.client.set_device_parameter(
            track_index, device_index, value, parameter_name=name,
            parameter_index=parameter_index, chain_index=chain_index,
        )
        actual = None
        if check_value:
            actual = verify.param_value(self.client, track_index, device_index,
                                        name, chain_index=chain_index)
            if actual is None or abs(actual - value) > tol:
                self.log.event("action_result", label=desc, layer="lom",
                               result="failed", actual=actual)
                raise verify.VerificationFailed(
                    f"{name!r} on track {track_index}/device {device_index}: "
                    f"requested {value}, read back {actual}"
                )
        self.log.event("action_result", label=desc, layer="lom", result="success",
                       actual=actual, display=result.get("display_value"))
        return result

    def set_track_volume(self, track_index: int, value: float,
                         tol: float = 0.01) -> dict | None:
        desc = f"set track[{track_index}] volume = {value}"
        if not self._may_proceed(desc, "lom"):
            return None
        result = self.client.set_track_volume(track_index, value)
        actual = float(self.client.track_volume(track_index)["volume"])
        if abs(actual - value) > tol:
            self.log.event("action_result", label=desc, layer="lom",
                           result="failed", actual=actual)
            raise verify.VerificationFailed(
                f"track {track_index} volume: requested {value}, read back {actual}"
            )
        self.log.event("action_result", label=desc, layer="lom", result="success",
                       actual=actual)
        return result

    def set_tempo(self, bpm: float, tol: float = 0.01) -> dict | None:
        desc = f"set tempo = {bpm}"
        if not self._may_proceed(desc, "lom"):
            return None
        self.client.set_tempo(bpm)
        actual = float(self.client.session_info()["tempo"])
        if abs(actual - bpm) > tol:
            self.log.event("action_result", label=desc, layer="lom",
                           result="failed", actual=actual)
            raise verify.VerificationFailed(f"tempo: requested {bpm}, read back {actual}")
        self.log.event("action_result", label=desc, layer="lom", result="success",
                       actual=actual)
        return {"tempo": actual}

    def load_plugin(self, track_index: int, plugin_name: str, *,
                    exact: bool = False) -> dict | None:
        plugin = plugins_mod.resolve_plugin(self.client, plugin_name, exact=exact)
        desc = f"load plugin {plugin['name']!r} on track[{track_index}]"
        if not self._may_proceed(desc, "lom"):
            return plugin
        result = self.client.load_browser_item(track_index, plugin["uri"])
        loaded = bool(isinstance(result, dict) and result.get("loaded", True))
        self.log.event("action_result", label=desc, layer="lom",
                       result="success" if loaded else "failed", uri=plugin["uri"])
        if not loaded:
            raise verify.VerificationFailed(f"loading {plugin['name']!r} returned not-loaded")
        return plugin

    def load_instrument(self, track_index: int, uri: str) -> dict | None:
        desc = f"load instrument/effect uri={uri!r} on track[{track_index}]"
        if not self._may_proceed(desc, "lom"):
            return None
        result = self.client.load_instrument_or_effect(track_index, uri)
        self.log.event("action_result", label=desc, layer="lom", result="success")
        return result

    def import_audio(self, track_index: int, file: str,
                     position_beats: float = 0.0) -> dict | None:
        from .paths import to_windows_path
        win_path = to_windows_path(file)
        desc = f"import {win_path} -> track[{track_index}] @ {position_beats} beats"
        if not self._may_proceed(desc, "lom"):
            return None
        result = self.client.create_arrangement_audio_clip(
            track_index, win_path, position_beats)
        self.log.event("action_result", label=desc, layer="lom", result="success")
        return result

    def list_devices(self, track_index: int) -> list[dict]:
        return self.client.track_info(track_index).get("devices", [])

    # -- UIA fallback/reach --------------------------------------------------

    def uia_control(self, automation_id: str, action: str, value: Any = None,
                    *, live: bool = False, timeout: float = 90.0) -> "uia.UiaResult":
        desc = f"uia {action} {automation_id}" + ("" if value is None else f" = {value}")
        self.log.event("action_start", label=desc, layer="uia")
        result = uia.run_control(automation_id, action, value, live=live, timeout=timeout)
        self.log.event("action_result", label=desc, layer="uia", result="success"
                       if result.ok else "failed", returncode=result.returncode)
        return result

    def uia_task(self, task: str, **kwargs: Any) -> "uia.UiaResult":
        desc = f"uia task {task} {kwargs or ''}".strip()
        self.log.event("action_start", label=desc, layer="uia")
        result = uia.run_task(task, **kwargs)
        self.log.event("action_result", label=desc, layer="uia",
                       result="success" if result.ok else "failed",
                       returncode=result.returncode)
        return result

    # -- analysis ------------------------------------------------------------

    def analyze(self, audio_path: Path | str, target_lufs: float | None = None) -> dict:
        from .analysis import measure
        result = measure.analyze(audio_path, target_lufs=target_lufs)
        self.log.event("analysis", file=str(audio_path), **result)
        return result
