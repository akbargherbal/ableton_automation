"""automation.verify — numeric post-condition assertions.

Automation is only done when the outcome is confirmed by a value, not when a
command returned without error (mirrors the project's "verify, don't trust"
rule). These helpers read state back through the primary LOM channel.
"""

from __future__ import annotations

import time
from pathlib import Path

from .lom import LomClient


class VerificationFailed(AssertionError):
    """A post-condition was not met."""


def find_param(device_parameters: dict, name: str,
               exact: bool = False) -> dict | None:
    """Find one parameter by name (case-insensitive; substring unless exact)."""
    needle = name.strip().lower()
    candidates = []
    for p in device_parameters.get("parameters", []):
        pname = (p.get("name") or "").lower()
        if (pname == needle) if exact else (needle in pname):
            candidates.append(p)
    if not candidates:
        return None
    if not exact and len(candidates) > 1:
        exact_hits = [p for p in candidates if (p.get("name") or "").lower() == needle]
        if exact_hits:
            return exact_hits[0]
    return candidates[0]


def param_value(client: LomClient, track_index: int, device_index: int,
                name: str, *, chain_index: int | None = None) -> float | None:
    result = client.device_parameters(track_index, device_index, chain_index=chain_index)
    entry = find_param(result, name)
    return None if entry is None else float(entry.get("value"))


def assert_param_close(client: LomClient, track_index: int, device_index: int,
                       name: str, expected: float, tol: float = 0.02,
                       *, chain_index: int | None = None) -> float:
    """Assert a device parameter's normalized value is within `tol` of expected."""
    actual = param_value(client, track_index, device_index, name, chain_index=chain_index)
    if actual is None:
        raise VerificationFailed(
            f"parameter {name!r} not found on track {track_index} device {device_index}"
        )
    if abs(actual - expected) > tol:
        raise VerificationFailed(
            f"{name!r}: expected {expected:.4f} (+/-{tol}), reads {actual:.4f}"
        )
    return actual


def assert_track_volume(client: LomClient, track_index: int, expected: float,
                        tol: float = 0.01) -> float:
    actual = float(client.track_volume(track_index).get("volume"))
    if abs(actual - expected) > tol:
        raise VerificationFailed(
            f"track {track_index} volume: expected {expected:.4f}, reads {actual:.4f}"
        )
    return actual


def assert_file_ready(path: Path | str, min_bytes: int = 1024,
                      settle_seconds: float = 2.0,
                      timeout: float = 30.0) -> int:
    """Wait for a written file to exist, be non-trivial, and stop growing."""
    p = Path(path)
    deadline = time.time() + timeout
    last_size = -1
    stable_since = time.time()
    while time.time() < deadline:
        if p.exists():
            size = p.stat().st_size
            if size != last_size:
                last_size = size
                stable_since = time.time()
            elif size >= min_bytes and (time.time() - stable_since) >= settle_seconds:
                return size
        time.sleep(0.25)
    if not p.exists():
        raise VerificationFailed(f"expected output file was not created: {p}")
    raise VerificationFailed(
        f"output file {p} did not settle (last size {last_size} bytes, "
        f"minimum {min_bytes}) within {timeout}s"
    )
