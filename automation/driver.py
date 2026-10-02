"""automation.driver — the unified actuator.

Combines the LOM client (primary), the UIA subprocess bridge (fallback/reach),
state snapshot/diff, verification, a single-run lock, and structured logging
behind one context-managed object. Recipes and the CLI use this; nothing else
should talk to lom/uia directly.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from . import plugins as plugins_mod
from . import state as state_mod
from . import uia
from . import verify
from .lock import RunLock
from .log import RunLog
from .lom import LomClient

RUNS_DIR_NAME = "RUNS"


class ChannelUnavailable(NotImplementedError):
    """No channel on the LOM -> ALS -> UIA ladder can perform an action.

    Carries the per-channel availability so callers (CLI, agent) can present the
    deterministic offline route (`.als` configure + reopen) or the live GUI
    route (UIA) instead of a bare failure.
    """

    def __init__(self, message: str, channels: dict | None = None):
        super().__init__(message)
        self.channels = channels or {}


class Driver:
    """One automation run against one Ableton instance."""

    def __init__(self, run_dir: Path | str | None = None, *, name: str = "run",
                 dry_run: bool = False, use_lock: bool = True,
                 snapshot_on_enter: bool = True, interactive: bool = False,
                 unattended: bool = False, offline: bool = False) -> None:
        self.repo = uia.repo_root()
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.run_dir = Path(run_dir) if run_dir else self.repo / RUNS_DIR_NAME / f"{stamp}_{name}"
        self.name = name
        self.dry_run = dry_run
        self.use_lock = use_lock
        self.snapshot_on_enter = snapshot_on_enter
        self.interactive = interactive
        self.unattended = unattended
        self.offline = offline
        self.log = RunLog(self.run_dir, run_id=f"{stamp}_{name}")
        self.client = LomClient()
        self._lock = RunLock(self.repo / RUNS_DIR_NAME / ".automation.lock")
        self.before: dict | None = None
        self.after: dict | None = None

    def __enter__(self) -> "Driver":
        if self.use_lock:
            self._lock.__enter__()
        if not self.offline:
            self.client.connect()
        self.log.event("run_start", name=self.name, dry_run=self.dry_run,
                       offline=self.offline, run_dir=str(self.run_dir))
        if self.snapshot_on_enter and not self.offline:
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
        device_name = params.get("device_name", "")
        mode = plugin_profiles.classify(device_name, params.get("parameter_count"))
        if mode == "gui":
            available = ", ".join(plugin_profiles.parameter_names(params)[:8])
            channels = plugin_profiles.describe_channels(
                device_name, params.get("parameter_count"))
            raise ChannelUnavailable(
                f"Device {device_name!r} on track {track_index} is GUI-only "
                f"(exposes {params.get('parameter_count')} LOM param(s): "
                f"{available}). LOM set_device_parameter cannot drive it. "
                "Next channel: '.als' expose offline then reopen (driver."
                "als_configure) or plugin-GUI via UIA (driver.uia_control). "
                "See docs/CAPABILITY_MATRIX.md.",
                channels=channels,
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

    # -- ALS channel (offline; LOM -> ALS -> UIA ladder) ---------------------

    def als_info(self, path: str) -> dict:
        from .als import read as als_read
        info = als_read.file_info(path)
        self.log.event("als_info", path=path, **{k: info[k] for k in
                       ("major_version", "minor_version", "creator")})
        return info

    def als_devices(self, path: str) -> list[dict]:
        from .als import read as als_read
        devs = [d.as_dict() for d in als_read.devices(path)]
        self.log.event("als_devices", path=path, device_count=len(devs))
        return devs

    def als_configure(self, source: str, output: str, requested: list[str], *,
                      device: int = 0, apply: bool = False, backup: bool = True,
                      overwrite: bool = False,
                      declared_names: list[str] | None = None):
        """Expose GUI-only plugin parameters by editing a copy of `source`.

        Resolves the friendly `requested` names against the plugin's declared
        parameter list (`plugin_profiles`, saved from `get_parameter_names`),
        then rewrites exactly three fields per slot. Offline: the set must be
        closed, and the effect appears on reopen. Dry-run unless `apply=True`.
        """
        from . import plugin_profiles as pp
        from .als import configure as als_configure, read as als_read
        desc = (f"als configure {source} -> {output} "
                f"[device {device}] {requested}")
        self.log.event("action_start", label=desc, layer="als")
        src_dev = als_read.device(source, device)
        if src_dev is None:
            from .als.configure import AlsConfigError
            raise AlsConfigError(f"device {device} not found in {source}")
        if declared_names is None:
            declared_names = pp.declared_parameter_names(src_dev.name)
        if not declared_names:
            from .als.configure import AlsConfigError
            raise AlsConfigError(
                f"no declared-parameter profile for {src_dev.name!r}. Run "
                f"get_parameter_names on the running plugin and save it to "
                f"{pp.declared_profile_path(src_dev.name)}"
            )
        exposures = als_configure.resolve_exposures(src_dev, declared_names,
                                                    requested)
        result = als_configure.write(source, output, exposures, device=device,
                                     apply=apply, backup=backup,
                                     overwrite=overwrite)
        self.log.event("action_result", label=desc, layer="als",
                       result="success", applied=result.applied,
                       exposed_before=result.exposed_before,
                       exposed_after=result.exposed_after,
                       sha256_source=result.sha256_source,
                       sha256_output=result.sha256_output)
        return result

    def als_snapshot(self, path: str, dest_dir: str | None = None,
                     label: str = "snapshot"):
        from .als import snapshot as als_snapshot
        snap = als_snapshot.snapshot(path, dest_dir, label=label)
        self.log.event("als_snapshot", original=snap.original,
                       snapshot=snap.snapshot, sha256=snap.sha256,
                       size=snap.size)
        return snap

    def als_restore(self, snapshot_path: str, target: str, *,
                    apply: bool = False, force: bool = False, backup: bool = True):
        from .als import snapshot as als_snapshot
        result = als_snapshot.restore(snapshot_path, target, apply=apply,
                                      force=force, backup=backup)
        self.log.event("als_restore", snapshot=result.snapshot,
                       target=result.target, applied=result.applied,
                       backup=result.backup, sha256_target=result.sha256_target)
        return result

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

    # -- guided human steps --------------------------------------------------

    def handoff(self, handoff, *, interactive: bool | None = None) -> str:
        """Emit a guided human step and (optionally) block until done.

        - always logs `handoff_required` and returns the formatted instructions
          (agent-mediated mode: the agent relays them, then resumes),
        - `interactive=True` blocks on Enter and runs the handoff's verify(),
        - `unattended=True` on the Driver raises HandoffRequired instead of
          silently proceeding, so batch items are marked as needing a human.
        """
        from .handoff import HandoffRequired, format_handoff
        text = format_handoff(handoff)
        self.log.event("handoff_required", id=handoff.id, title=handoff.title,
                       menu_path=handoff.menu_path, steps=handoff.steps,
                       expected=handoff.expected)
        self.log.info(text)
        if self.unattended:
            raise HandoffRequired(handoff)
        block = self.interactive if interactive is None else interactive
        if block:
            try:
                input("  [enter when done, or Ctrl-C to abort] ")
            except EOFError:
                raise HandoffRequired(handoff)
            if handoff.verify is not None and not handoff.verify():
                self.log.event("handoff_result", id=handoff.id, result="failed")
                raise verify.VerificationFailed(
                    f"handoff {handoff.id!r} did not verify after the human step")
            self.log.event("handoff_result", id=handoff.id, result="success")
        return text

    # -- analysis ------------------------------------------------------------

    def analyze(self, audio_path: Path | str, target_lufs: float | None = None) -> dict:
        from .analysis import measure
        result = measure.analyze(audio_path, target_lufs=target_lufs)
        self.log.event("analysis", **result)
        return result
