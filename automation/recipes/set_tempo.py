"""Recipe: set the session tempo, verified via LOM read-back."""

from __future__ import annotations

NAME = "set_tempo"
DESCRIPTION = "Set the project tempo (BPM), verified by read-back."
PARAMS = {"bpm": float}


def run(driver, *, bpm: float) -> dict:
    result = driver.set_tempo(float(bpm))
    return {"tempo": None if result is None else result.get("tempo")}
