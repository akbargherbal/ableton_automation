"""Recipe: import an audio file into the arrangement at a given position.

Converts the WSL path to a Windows path before handing it to Ableton. Does not
yet verify the clip landed (the Remote Script's create_audio_clip returns the
position, not a handle); a follow-up arrangement read is the verification step.
"""

from __future__ import annotations

from pathlib import Path

NAME = "import_audio"
DESCRIPTION = "Import an audio file onto a track in the arrangement."
PARAMS = {"track_index": int, "file": str, "position_beats": float}


def run(driver, *, track_index: int, file: str, position_beats: float = 0.0) -> dict:
    src = Path(file)
    if not src.exists():
        raise FileNotFoundError(f"audio file not found: {src}")
    return driver.import_audio(int(track_index), str(src), float(position_beats))
