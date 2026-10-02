"""Recipe: hybrid export.

Export has no LOM surface and its dialog is modal, so it is done as a guided
handoff:

    stage=prepare  -> emit precise Export-dialog instructions, then return
    stage=verify   -> wait for the rendered file and measure it

The agent runs `prepare`, relays the instructions to the user, waits for them to
finish, then runs `verify`. `out` must be a path this (WSL) side can see, e.g.
/mnt/c/Users/DELL/Music/out.wav; the Windows equivalent is shown to the user.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .. import verify as verify_mod
from ..handoff import export_audio_handoff
from ..paths import to_windows_path

NAME = "export_audio"
DESCRIPTION = "Export the set (prepare = guided dialog; verify = measure the file)."
PARAMS = {
    "out": str, "stage": str, "target_lufs": float, "timeout": float,
    "file_type": str, "bit_depth": str, "sample_rate": str,
}


def run(driver, *, out: str, stage: str = "prepare", target_lufs: float | None = None,
        timeout: float = 120.0, file_type: str = "WAV", bit_depth: str = "24",
        sample_rate: str = "44100") -> dict:
    out_path = Path(out).expanduser()
    if stage == "prepare":
        win_path = to_windows_path(out_path)
        if win_path.lower().startswith("\\\\wsl"):
            print(f"WARNING: {win_path} is a WSL UNC path; Ableton on Windows "
                  "writes those slowly/reliably-unpredictably. Prefer a "
                  "Windows-visible location like /mnt/c/Users/<you>/Music/...",
                  file=sys.stderr)
        handoff = export_audio_handoff(
            out_path=win_path, file_type=file_type,
            bit_depth=bit_depth, sample_rate=sample_rate,
        )
        driver.handoff(handoff)
        return {"stage": "prepare", "handoff": handoff.id, "out": str(out_path)}

    if stage == "verify":
        size = verify_mod.assert_file_ready(out_path, min_bytes=1024,
                                            settle_seconds=1.0, timeout=float(timeout))
        result = driver.analyze(out_path, target_lufs=target_lufs)
        passed = True
        if target_lufs is not None:
            actual = result.get("integrated_lufs")
            passed = actual is not None and abs(actual - target_lufs) <= 1.0
        return {"stage": "verify", "file": str(out_path), "bytes": size,
                "target_met": passed, **result}

    raise ValueError(f"stage must be 'prepare' or 'verify', got {stage!r}")
