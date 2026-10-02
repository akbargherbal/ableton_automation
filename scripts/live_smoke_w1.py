#!/usr/bin/env python3
"""live_smoke_w1 — numeric read-back smoke test for the W1 Remote Script pack.

Run this from the repo root with Ableton Live running and the *extended*
AbletonMCP Remote Script loaded:

    python3 scripts/live_smoke_w1.py

It connects straight to the Remote Script socket (localhost:9877) and, for each
W1 capability, performs a mutation and reads the value back. Mutable state
(tempo signature, metronome, track mute/solo/arm, scenes) is snapshotted and
restored, and `stop_all_clips` is exercised last.

RUN THIS ON A SCRATCH SET. It stops session playback and briefly toggles track
flags. It never saves the set.

Exit codes: 0 = all checks passed (deferrals allowed), 1 = a check failed,
2 = the Remote Script is not reachable.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from automation.lom import LomClient, LomConnectionError  # noqa: E402


class Smoke:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.failed: list[str] = []
        self.deferred: list[str] = []
        self.skipped: list[str] = []

    def check(self, label: str, ok: bool, detail: str = "") -> bool:
        line = f"{label}{(' — ' + detail) if detail else ''}"
        (self.passed if ok else self.failed).append(line)
        print(f"  {'PASS' if ok else 'FAIL'}  {line}")
        return ok

    def defer(self, label: str, detail: str) -> None:
        self.deferred.append(f"{label} — {detail}")
        print(f"  DEFER {label} — {detail}")

    def skip(self, label: str, detail: str) -> None:
        self.skipped.append(f"{label} — {detail}")
        print(f"  SKIP  {label} — {detail}")

    @property
    def ok(self) -> bool:
        return not self.failed


def _playing_tracks(tracks: list[dict]) -> list[int]:
    """Track indices with a Session clip actually playing (playing_slot_index >= 0)."""
    return [int(t["index"]) for t in tracks
            if isinstance(t.get("playing_slot_index"), int)
            and t["playing_slot_index"] >= 0]


def _wait_playing(client: LomClient, want: bool, timeout: float = 3.0) -> bool:
    deadline = time.time() + timeout
    while True:
        playing = bool(_playing_tracks(client.all_tracks()))
        if playing == want:
            return True
        if time.time() > deadline:
            return False
        time.sleep(0.1)


def _wait_record(client: LomClient, before: int, timeout: float = 6.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if int(client.transport_info()["session_record_status"]) != before:
            return True
        time.sleep(0.1)
    return False


def _record(client: LomClient, s: Smoke) -> None:
    print("[session record]")
    before_tracks = client.track_count()
    before_status = int(client.transport_info()["session_record_status"])
    if [t for t in client.all_tracks() if t.get("arm")]:
        s.skip("session record", "a track was already armed; not disturbing it")
        return
    if before_status != 0:
        s.skip("session record", f"already recording (status {before_status})")
        return
    temp = None
    try:
        temp = int(client.create_midi_track(-1)["index"])
        client.set_track_arm(temp, True)
        s.check("track arm read-back (record test)",
                bool(client.track_info(temp)["arm"]), f"track {temp}")
        client.trigger_session_record()
        s.check("trigger_session_record starts recording",
                _wait_record(client, before_status),
                f"status was {before_status}")
    finally:
        if temp is not None:
            try:
                client.trigger_session_record()  # stop the take
            except Exception:
                pass
            client.stop_all_clips(False)
            client.delete_track(temp)
            s.check("session record temp track removed",
                    client.track_count() == before_tracks,
                    f"track_count={client.track_count()}")


def _first_clip(client: LomClient) -> tuple[int, int] | None:
    for info in client.all_tracks():
        for slot in info.get("clip_slots", []):
            if slot.get("has_clip"):
                return int(info["index"]), int(slot["index"])
    return None


def _read_only(client: LomClient, s: Smoke) -> None:
    print("[read-only]")
    project = client.project_path()
    s.check("get_project_path returns file_path/name",
            "file_path" in project and "name" in project,
            f"file_path={project.get('file_path')!r} saved={project.get('saved')}")

    selection = client.selection()
    s.check("get_selection returns track/scene context",
            "selected_track_index" in selection
            and "selected_scene_index" in selection,
            f"track={selection.get('selected_track_name')!r} "
            f"scene={selection.get('selected_scene_index')}")

    transport = client.transport_info()
    required = {"is_playing", "record_mode", "session_record_status",
                "current_position_beats", "position_unit", "metronome",
                "count_in_duration", "signature_numerator"}
    s.check("get_transport_info returns read-back fields",
            required <= set(transport),
            f"position_unit={transport.get('position_unit')} "
            f"is_playing={transport.get('is_playing')}")

    scenes = client.scenes()
    s.check("get_scenes returns a scene list",
            "scene_count" in scenes and isinstance(scenes.get("scenes"), list),
            f"scene_count={scenes.get('scene_count')}")


def _session_control(client: LomClient, s: Smoke) -> None:
    print("[session control setters]")
    original = client.transport_info()
    orig_sig = (int(original["signature_numerator"]),
                int(original["signature_denominator"]))
    try:
        num, den = (3, 4) if orig_sig != (3, 4) else (4, 4)
        client.set_time_signature(num, den)
        actual = client.transport_info()
        s.check("set_time_signature read-back",
                (int(actual["signature_numerator"]),
                 int(actual["signature_denominator"])) == (num, den),
                f"{num}/{den} -> {actual['signature_numerator']}/"
                f"{actual['signature_denominator']}")
    finally:
        client.set_time_signature(*orig_sig)
        restored = client.transport_info()
        s.check("time signature restored",
                (int(restored["signature_numerator"]),
                 int(restored["signature_denominator"])) == orig_sig,
                f"restored {orig_sig[0]}/{orig_sig[1]}")

    orig_metro = bool(original["metronome"])
    try:
        client.set_metronome(not orig_metro)
        actual = bool(client.transport_info()["metronome"])
        s.check("set_metronome read-back", actual == (not orig_metro),
                f"requested {not orig_metro}, read {actual}")
    finally:
        client.set_metronome(orig_metro)
        s.check("metronome restored",
                bool(client.transport_info()["metronome"]) == orig_metro,
                f"restored {orig_metro}")

    # count_in_duration is get+observe only in the Live 12.1 LOM: record a
    # deferral rather than a failure if the write is rejected.
    orig_count = int(original["count_in_duration"])
    target = (orig_count + 1) % 4
    client.set_count_in(target)
    read_back = int(client.transport_info()["count_in_duration"])
    if read_back == target:
        s.check("set_count_in read-back", True, f"index {target}")
        client.set_count_in(orig_count)
    else:
        s.defer("set_count_in",
                f"Live 12.1 LOM marks count_in_duration get+observe; "
                f"requested {target}, read {read_back}")


def _track_flags(client: LomClient, s: Smoke) -> None:
    print("[track mute / solo / arm setters]")
    tracks = client.all_tracks()
    if not tracks:
        s.skip("track flags", "no session tracks")
        return

    mute_target = tracks[0]
    ti = int(mute_target["index"])
    for flag in ("mute", "solo"):
        original = bool(client.track_info(ti)[flag])
        try:
            getattr(client, f"set_track_{flag}")(ti, not original)
            actual = bool(client.track_info(ti)[flag])
            s.check(f"set_track_{flag} read-back", actual == (not original),
                    f"track {ti}: requested {not original}, read {actual}")
        finally:
            getattr(client, f"set_track_{flag}")(ti, original)
            s.check(f"track {flag} restored",
                    bool(client.track_info(ti)[flag]) == original,
                    f"restored {original}")

    armable = [t for t in tracks if t.get("arm") is not None]
    if not armable:
        s.skip("set_track_arm", "no armable session tracks")
        return
    arm_track = int(armable[0]["index"])
    original = bool(client.track_info(arm_track)["arm"])
    try:
        client.set_track_arm(arm_track, not original)
        actual = bool(client.track_info(arm_track)["arm"])
        s.check("set_track_arm read-back", actual == (not original),
                f"track {arm_track}: requested {not original}, read {actual}")
    finally:
        client.set_track_arm(arm_track, original)
        s.check("track arm restored",
                bool(client.track_info(arm_track)["arm"]) == original,
                f"restored {original}")


def _scenes(client: LomClient, s: Smoke) -> None:
    print("[scenes / stop-all-clips]")
    before = int(client.scenes()["scene_count"])
    created_index = None
    try:
        created = client.create_scene(-1)
        created_index = int(created["index"])
        after = client.scenes()
        s.check("create_scene read-back",
                after["scene_count"] == before + 1
                and 0 <= created_index < after["scene_count"],
                f"index={created_index} count={after['scene_count']}")

        client.set_scene_name(created_index, "W1_SMOKE")
        name = client.scenes()["scenes"][created_index]["name"]
        s.check("set_scene_name read-back", name == "W1_SMOKE", f"name={name!r}")

        # Fire: an empty scene may never report is_triggered. Prefer a non-empty
        # scene if one exists, else just confirm the command round-trips.
        scenes = client.scenes()["scenes"]
        non_empty = [sc for sc in scenes if not sc.get("is_empty")]
        fire_index = int(non_empty[0]["index"]) if non_empty else created_index
        fired = client.fire_scene(fire_index)
        if non_empty:
            triggered = bool(fired.get("is_triggered")) or any(
                sc.get("is_triggered") for sc in client.scenes()["scenes"])
            s.check("fire_scene is_triggered read-back", triggered,
                    f"scene {fire_index}")
        else:
            s.check("fire_scene command round-trip", bool(fired.get("fired")),
                    "empty scene; is_triggered not asserted")

        # Strong stop-all test: fire a real clip then stop it, but only when
        # nothing is playing now, so the set is left in its original state.
        if _playing_tracks(client.all_tracks()):
            s.skip("stop_all_clips strong test",
                   "clips were already playing before the smoke")
        else:
            clip = _first_clip(client)
            temp_track = None
            try:
                if clip is None:
                    # No clips in the set: build a disposable MIDI track/clip
                    # so the stop path is exercised, then delete the track.
                    created_track = client.create_midi_track(-1)
                    temp_track = int(created_track["index"])
                    client.create_clip(temp_track, 0, 1.0)
                    client.add_notes_to_clip(temp_track, 0, [
                        {"pitch": 60, "start_time": 0.0, "duration": 1.0,
                         "velocity": 100, "mute": False}])
                    ti, ci = temp_track, 0
                else:
                    ti, ci = clip
                client.fire_clip(ti, ci)
                s.check("fire_clip starts playback read-back",
                        _wait_playing(client, True), f"track {ti} slot {ci}")
                client.stop_all_clips(False)
                s.check("stop_all_clips stops a playing clip",
                        _wait_playing(client, False),
                        f"still playing: {_playing_tracks(client.all_tracks())}")
            finally:
                if temp_track is not None:
                    client.delete_track(temp_track)
                    s.check("temporary smoke track removed",
                            client.track_count() == temp_track,
                            f"track_count={client.track_count()} "
                            f"(expected {temp_track})")
    finally:
        # Stop playback before tidying up, independent of launch quantization.
        client.stop_all_clips(False)
        playing = _playing_tracks(client.all_tracks())
        s.check("stop_all_clips read-back", not playing,
                f"still playing: {playing}")
        if created_index is not None:
            try:
                client.delete_scene(created_index)
                final = int(client.scenes()["scene_count"])
                s.check("delete_scene read-back", final == before,
                        f"count={final} (was {before})")
            except Exception as e:  # pragma: no cover - live only
                s.check("delete_scene read-back", False, repr(e))


def run() -> int:
    s = Smoke()
    try:
        client = LomClient().connect()
    except LomConnectionError as e:
        print(f"Remote Script not reachable: {e}", file=sys.stderr)
        return 2
    try:
        _read_only(client, s)
        _session_control(client, s)
        _track_flags(client, s)
        _record(client, s)
        _scenes(client, s)
    finally:
        client.close()

    print("\n--- W1 live smoke summary ---")
    print(f"passed={len(s.passed)} failed={len(s.failed)} "
          f"deferred={len(s.deferred)} skipped={len(s.skipped)}")
    if s.deferred:
        print("\ndeferred:")
        for d in s.deferred:
            print(f"  - {d}")
    if s.skipped:
        print("\nskipped:")
        for d in s.skipped:
            print(f"  - {d}")
    if s.failed:
        print("\nfailed:")
        for d in s.failed:
            print(f"  - {d}")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
