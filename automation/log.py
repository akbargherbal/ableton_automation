"""automation.log — structured run logging.

Emits the same `EVENT: {...}` single-line JSON convention the UI-automation
script uses, so an orchestrator can consume both with one parser, and also
appends to a per-run JSONL file for audit.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from . import RUN_SCHEMA_VERSION

EVENT_PREFIX = "EVENT: "


class RunLog:
    """Writes events to stdout as `EVENT: ...` and to `<run_dir>/run.jsonl`."""

    def __init__(self, run_dir: Path | str | None = None, run_id: str | None = None):
        self.run_dir = Path(run_dir) if run_dir else None
        if self.run_dir:
            self.run_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self._jsonl = (self.run_dir / "run.jsonl") if self.run_dir else None

    def event(self, event_type: str, **fields) -> dict:
        payload = {
            "v": RUN_SCHEMA_VERSION,
            "type": event_type,
            "run_id": self.run_id,
            "ts": time.time(),
            **fields,
        }
        print(f"{EVENT_PREFIX}{json.dumps(payload, default=str)}", flush=True)
        if self._jsonl:
            with open(self._jsonl, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, default=str) + "\n")
        return payload

    def info(self, message: str) -> None:
        print(message, flush=True)
        if self._jsonl:
            with open(self._jsonl, "a", encoding="utf-8") as f:
                f.write(json.dumps(
                    {"v": RUN_SCHEMA_VERSION, "type": "log", "run_id": self.run_id,
                     "ts": time.time(), "message": message}, default=str) + "\n")

    def error(self, message: str) -> None:
        print(message, file=sys.stderr, flush=True)
        self.event("error", message=message)
