"""automation.uia — subprocess bridge to the Windows UI-automation scripts.

The proven click primitives live in scripts/automate_ableton_task.py and must
run under Windows ``python.exe`` (pywinauto cannot see Ableton from WSL). This
module shells out to it, from the repo root, using a **relative** script path:
when a Windows executable is launched from WSL the working directory is
translated to a UNC path, so relative paths resolve correctly (verified).

This is the fallback/reach layer. Prefer automation.lom for anything the Live
Object Model exposes.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

SCRIPT_REL = os.path.join("scripts", "automate_ableton_task.py")

# The click primitives only ever write these three types; anything else is
# refused by the script itself (UnsupportedControlType).
EVENT_PREFIX = "EVENT: "


class UiaError(RuntimeError):
    """The UI-automation script failed (non-zero exit or could not launch)."""


def repo_root() -> Path:
    env = os.environ.get("ABLETON_REPO_ROOT")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[1]


def windows_python() -> str:
    return os.environ.get("ABLETON_WIN_PYTHON", "python.exe")


def is_available() -> bool:
    """True if the Windows interpreter can be invoked at all."""
    try:
        proc = subprocess.run(
            [windows_python(), "--version"],
            capture_output=True, text=True, timeout=15,
        )
        return proc.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


@dataclass
class UiaResult:
    returncode: int
    events: list[dict] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def events_of(self, event_type: str) -> list[dict]:
        return [e for e in self.events if e.get("type") == event_type]

    @property
    def last_result(self) -> dict | None:
        results = self.events_of("action_result")
        return results[-1] if results else None


def _parse_events(combined: str) -> list[dict]:
    events: list[dict] = []
    for line in combined.splitlines():
        if not line.startswith(EVENT_PREFIX):
            continue
        body = line[len(EVENT_PREFIX):]
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def run_automation(args: Sequence[str], *, timeout: float = 180.0,
                   cwd: Path | None = None) -> UiaResult:
    """Invoke automate_ableton_task.py with `args`; parse its EVENT stream."""
    root = cwd or repo_root()
    cmd = [windows_python(), SCRIPT_REL, *[str(a) for a in args]]
    try:
        proc = subprocess.run(
            cmd, cwd=str(root), capture_output=True, text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        combined = (e.stdout or "") + (e.stderr or "")
        raise UiaError(
            f"UI-automation timed out after {timeout}s: {' '.join(cmd)}"
        ) from e
    except OSError as e:
        raise UiaError(
            f"Could not launch {windows_python()!r} ({e}). Is Windows Python "
            "on PATH from WSL?"
        ) from e

    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    return UiaResult(
        returncode=proc.returncode,
        events=_parse_events(combined),
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
    )


def list_tasks(timeout: float = 30.0) -> dict:
    result = run_automation(["--list-tasks"], timeout=timeout)
    if not result.ok:
        raise UiaError(f"--list-tasks failed (exit {result.returncode}): {result.stderr.strip()}")
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    raise UiaError("--list-tasks produced no JSON schema line")


def run_control(automation_id: str, action: str, value: Any = None,
                *, live: bool = False, timeout: float = 90.0) -> UiaResult:
    """Act on one automation_id (L3 fallback path).

    action: "click" (CheckBox flip) or "set" (needs value).
    """
    args: list[Any] = ["--control", automation_id, "--action", action]
    if value is not None:
        if isinstance(value, bool):
            args += ["--value", "true" if value else "false"]
        else:
            args += ["--value", value]
    if live:
        args.append("--live")
    result = run_automation(args, timeout=timeout)
    if not result.ok:
        raise UiaError(
            f"UIA control failed for {automation_id!r} "
            f"(exit {result.returncode}): {result.stderr.strip() or result.stdout.strip()[-400:]}"
        )
    return result


def send_keys(keys: str, *, live: bool = False, timeout: float = 40.0) -> UiaResult:
    """Send a raw pywinauto keystroke sequence to the Ableton window.

    Examples: "^+r" (Ctrl+Shift+R, Export Audio/Video), "^s" (Save),
    "^+s" (Save As), "^z" (Undo), "^b" (Bounce).
    """
    args = ["--keys", keys]
    if live:
        args.append("--live")
    return run_automation(args, timeout=timeout)


def open_set(file_path: str, *, live: bool = False,
             discard_unsaved: bool = False,
             timeout: float = 150.0) -> UiaResult:
    """Open a Live set by absolute Windows path via the Open dialog.

    Used by the `.als` channel to reopen a configured copy for LOM
    verification; requires the Windows UI layer. If Ableton prompts to save
    the current set, the task aborts unless `discard_unsaved=True` (never
    silently discards a user's work).
    """
    args: list[Any] = ["--task", "open_set", "--file", file_path]
    if discard_unsaved:
        args.append("--discard-unsaved")
    if live:
        args.append("--live")
    result = run_automation(args, timeout=timeout)
    if not result.ok:
        raise UiaError(
            f"open_set failed (exit {result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()[-400:]}"
        )
    return result


def run_task(task: str, *, tracks: Sequence[int] = (), seconds: float | None = None,
             bpm: float | None = None, live: bool = False,
             timeout: float = 240.0) -> UiaResult:
    """Run one of the fixed --task recipes (arm_track, set_tempo, ...)."""
    args: list[Any] = ["--task", task]
    if tracks:
        args += ["--tracks", *[str(t) for t in tracks]]
    if seconds is not None:
        args += ["--seconds", str(seconds)]
    if bpm is not None:
        args += ["--bpm", str(bpm)]
    if live:
        args.append("--live")
    result = run_automation(args, timeout=timeout)
    if not result.ok:
        raise UiaError(
            f"UIA task {task!r} failed (exit {result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()[-400:]}"
        )
    return result
