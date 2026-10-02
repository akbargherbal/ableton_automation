"""Recipe: read-only report of tracks and their device chains."""

from __future__ import annotations

NAME = "device_report"
DESCRIPTION = "Report every session track and the devices on it (read-only)."
PARAMS = {}


def run(driver, **_) -> dict:
    tracks = []
    for info in driver.client.all_tracks():
        tracks.append({
            "index": info.get("index"),
            "name": info.get("name"),
            "devices": [
                {"index": d.get("index"), "name": d.get("name"),
                 "class_name": d.get("class_name")}
                for d in info.get("devices", [])
            ],
        })
    return {"track_count": len(tracks), "tracks": tracks}
