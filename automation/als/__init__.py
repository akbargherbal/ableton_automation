"""automation.als — the offline `.als` channel.

Ableton's `.als` files are gzip-compressed XML. Editing them offline lets us do
things the Live Object Model cannot, above all *exposing* a GUI-only plugin's
parameters so the LOM can then drive them (the community "Configure" trick,
proven on Live 12.1 in Phases 1-2 of `PHASED_PLAN.md`).

Layers:
    read.py       — parse, inspect, diff. Never writes.
    configure.py  — surgical, copy-only exposure writer (backup + hash + atomic).
    snapshot.py   — file-level backup/restore with SHA-256 (Live must be closed).

The channel is offline: writes require the target set not to be open in Live, and
take effect only on reopen. `automation.driver` is the orchestrator that decides
when this channel applies (see the LOM -> ALS -> UIA ladder).
"""

from __future__ import annotations

from . import configure, read, snapshot

__all__ = ["read", "configure", "snapshot"]
