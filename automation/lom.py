"""automation.lom — thin, dependency-free TCP client for the AbletonMCP
Remote Script.

The Remote Script (installed as an Ableton control surface) listens on
localhost:9877 and speaks a simple framed-JSON protocol:

    request:  {"type": "<command>", "params": {...}}
    response: {"status": "success"|"error", "result": {...}, "message": ...}

This is the same protocol MCP_Server/server.py uses; we talk to it directly so
the automation driver can run as a plain WSL `python3` process without going
through an MCP host.

Indexing convention
-------------------
The MCP *tools* accept 1-based indices and subtract 1 before sending. At this
layer we deliberately use **0-based** indices, matching the Remote Script and
the Live Object Model exactly. Callers above this layer are responsible for any
1-based translation.
"""

from __future__ import annotations

import json
import os
import socket
import time
from typing import Any

DEFAULT_HOST = os.environ.get("ABLETON_MCP_HOST", "localhost")
DEFAULT_PORT = int(os.environ.get("ABLETON_MCP_PORT", "9877"))
DEFAULT_TIMEOUT = float(os.environ.get("ABLETON_MCP_TIMEOUT", "20.0"))

STATE_MODIFYING = frozenset({
    "create_midi_track", "create_audio_track", "set_track_name",
    "create_clip", "add_notes_to_clip", "set_clip_name",
    "set_tempo", "fire_clip", "stop_clip", "set_device_parameter",
    "start_playback", "stop_playback", "load_instrument_or_effect",
    "set_song_time", "set_arrangement_loop", "jump_to_cue",
    "create_cue_point", "delete_cue_point",
    "create_arrangement_clip", "create_arrangement_audio_clip",
    "duplicate_to_arrangement", "delete_arrangement_clip",
    "set_arrangement_clip_property",
    "set_view", "control_arrangement_view", "manage_clip_automation",
    "add_notes_to_arrangement_clip", "set_device_enabled",
    "delete_device", "delete_track", "navigate_preset",
    "set_track_volume", "set_track_panning",
    # W1 Remote Script extension pack
    "set_time_signature", "set_metronome", "set_count_in",
    "create_scene", "delete_scene", "set_scene_name",
    "fire_scene", "stop_all_clips",
    "set_track_mute", "set_track_solo", "set_track_arm",
    "trigger_session_record",
})


class LomError(RuntimeError):
    """A command reached Ableton but the Remote Script returned an error."""


class LomConnectionError(LomError):
    """The socket to the Remote Script could not be established/kept."""


class LomClient:
    """Connects to the Remote Script and sends LOM commands."""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                 timeout: float = DEFAULT_TIMEOUT) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: socket.socket | None = None

    def connect(self) -> "LomClient":
        if self._sock is not None:
            return self
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
        except OSError as e:
            raise LomConnectionError(
                f"Could not connect to AbletonMCP Remote Script at "
                f"{self.host}:{self.port} ({e}). Is Ableton running with "
                "AbletonMCP selected as a Control Surface?"
            ) from e
        self._sock = sock
        return self

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def __enter__(self) -> "LomClient":
        return self.connect()

    def __exit__(self, *exc: Any) -> None:
        self.close()

    @property
    def connected(self) -> bool:
        return self._sock is not None

    def _receive(self) -> bytes:
        assert self._sock is not None
        chunks: list[bytes] = []
        while True:
            chunk = self._sock.recv(8192)
            if not chunk:
                if not chunks:
                    raise LomConnectionError("Remote Script closed the connection before replying")
                break
            chunks.append(chunk)
            data = b"".join(chunks)
            try:
                json.loads(data.decode("utf-8"))
                return data
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
        data = b"".join(chunks)
        try:
            json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise LomConnectionError(f"Incomplete/invalid JSON from Remote Script: {data[:200]!r}") from e
        return data

    def send(self, command_type: str, **params: Any) -> Any:
        """Send one command; return its `result` (or raise LomError)."""
        self.connect()
        assert self._sock is not None
        command = {"type": command_type, "params": params}
        try:
            self._sock.sendall(json.dumps(command).encode("utf-8"))
            if command_type in STATE_MODIFYING:
                time.sleep(0.1)
            raw = self._receive()
        except (OSError, socket.timeout) as e:
            self.close()
            raise LomConnectionError(f"Connection to Ableton lost during {command_type!r}: {e}") from e
        try:
            response = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self.close()
            raise LomError(f"Invalid JSON response to {command_type!r}: {raw[:200]!r}") from e
        if response.get("status") == "error":
            raise LomError(f"{command_type}: {response.get('message', 'unknown error')}")
        return response.get("result", {})

    # -- session / transport -------------------------------------------------

    def session_info(self) -> dict:
        return self.send("get_session_info")

    def track_count(self) -> int:
        return int(self.session_info()["track_count"])

    def set_tempo(self, tempo: float) -> dict:
        return self.send("set_tempo", tempo=float(tempo))

    def start_playback(self) -> dict:
        return self.send("start_playback")

    def stop_playback(self) -> dict:
        return self.send("stop_playback")

    def set_song_time(self, time_beats: float) -> dict:
        return self.send("set_song_time", time=float(time_beats))

    def set_view(self, view: str) -> dict:
        return self.send("set_view", view_name=view)

    # -- W1 session context / control ---------------------------------------

    def project_path(self) -> dict:
        """Current Live Set path/name (empty until saved)."""
        return self.send("get_project_path")

    def selection(self) -> dict:
        """Selected track / scene / clip / slot / device."""
        return self.send("get_selection")

    def transport_info(self) -> dict:
        """Transport read-back: playing, record state, position (beats)."""
        return self.send("get_transport_info")

    def set_time_signature(self, numerator: int, denominator: int) -> dict:
        return self.send("set_time_signature", numerator=int(numerator),
                         denominator=int(denominator))

    def set_metronome(self, enabled: bool) -> dict:
        return self.send("set_metronome", enabled=bool(enabled))

    def set_count_in(self, duration: int) -> dict:
        return self.send("set_count_in", duration=int(duration))

    def scenes(self) -> dict:
        return self.send("get_scenes")

    def create_scene(self, index: int = -1) -> dict:
        return self.send("create_scene", index=int(index))

    def delete_scene(self, index: int) -> dict:
        return self.send("delete_scene", index=int(index))

    def set_scene_name(self, index: int, name: str) -> dict:
        return self.send("set_scene_name", index=int(index), name=name)

    def fire_scene(self, index: int, force_legato: bool = False,
                   can_select_scene_on_launch: bool = True) -> dict:
        return self.send("fire_scene", index=int(index),
                         force_legato=bool(force_legato),
                         can_select_scene_on_launch=bool(can_select_scene_on_launch))

    def stop_all_clips(self, quantized: bool = True) -> dict:
        return self.send("stop_all_clips", quantized=bool(quantized))

    # -- tracks --------------------------------------------------------------

    def track_info(self, track_index: int) -> dict:
        return self.send("get_track_info", track_index=int(track_index))

    def track_volume(self, track_index: int) -> dict:
        return self.send("get_track_volume", track_index=int(track_index))

    def set_track_volume(self, track_index: int, volume: float) -> dict:
        return self.send("set_track_volume", track_index=int(track_index), volume=float(volume))

    def set_track_panning(self, track_index: int, panning: float) -> dict:
        return self.send("set_track_panning", track_index=int(track_index), panning=float(panning))

    def set_track_name(self, track_index: int, name: str) -> dict:
        return self.send("set_track_name", track_index=int(track_index), name=name)

    def set_track_mute(self, track_index: int, mute: bool) -> dict:
        return self.send("set_track_mute", track_index=int(track_index),
                         mute=bool(mute))

    def set_track_solo(self, track_index: int, solo: bool) -> dict:
        return self.send("set_track_solo", track_index=int(track_index),
                         solo=bool(solo))

    def set_track_arm(self, track_index: int, arm: bool) -> dict:
        return self.send("set_track_arm", track_index=int(track_index),
                         arm=bool(arm))

    def trigger_session_record(self, record_length: float | None = None) -> dict:
        params: dict[str, Any] = {}
        if record_length is not None:
            params["record_length"] = float(record_length)
        return self.send("trigger_session_record", **params)

    def create_midi_track(self, index: int = -1) -> dict:
        return self.send("create_midi_track", index=int(index))

    def delete_track(self, track_index: int) -> dict:
        return self.send("delete_track", track_index=int(track_index))

    def all_tracks(self) -> list[dict]:
        """Convenience: info for every session track (0-based)."""
        count = self.track_count()
        return [self.track_info(i) for i in range(count)]

    # -- devices / params ----------------------------------------------------

    def device_parameters(self, track_index: int, device_index: int,
                          chain_index: int | None = None,
                          show_all: bool = True) -> dict:
        params: dict[str, Any] = {
            "track_index": int(track_index),
            "device_index": int(device_index),
            "show_all": bool(show_all),
        }
        if chain_index is not None:
            params["chain_index"] = int(chain_index)
        return self.send("get_device_parameters", **params)

    def get_parameter_names(self, track_index: int, device_index: int,
                            chain_index: int | None = None) -> dict:
        """Return a plugin's OWN declared parameter list (not just the exposed
        strip), via the Remote Script's `get_parameter_names` command.

        The index into the returned `names` list is the value that belongs in an
        `.als` slot's `ParameterId`. May report `method_present: false` if the
        Live version/device does not expose it.
        """
        params: dict[str, Any] = {
            "track_index": int(track_index),
            "device_index": int(device_index),
        }
        if chain_index is not None:
            params["chain_index"] = int(chain_index)
        return self.send("get_parameter_names", **params)

    def set_device_parameter(self, track_index: int, device_index: int,
                             value: float, parameter_name: str | None = None,
                             parameter_index: int | None = None,
                             chain_index: int | None = None) -> dict:
        params: dict[str, Any] = {
            "track_index": int(track_index),
            "device_index": int(device_index),
            "value": float(value),
        }
        if parameter_name is not None:
            params["parameter_name"] = parameter_name
        if parameter_index is not None:
            params["parameter_index"] = int(parameter_index)
        if chain_index is not None:
            params["chain_index"] = int(chain_index)
        return self.send("set_device_parameter", **params)

    def set_device_enabled(self, track_index: int, device_index: int,
                           enabled: bool, chain_index: int | None = None) -> dict:
        params: dict[str, Any] = {
            "track_index": int(track_index),
            "device_index": int(device_index),
            "enabled": bool(enabled),
        }
        if chain_index is not None:
            params["chain_index"] = int(chain_index)
        return self.send("set_device_enabled", **params)

    def delete_device(self, track_index: int, device_index: int) -> dict:
        return self.send("delete_device", track_index=int(track_index),
                         device_index=int(device_index))

    def load_instrument_or_effect(self, track_index: int, uri: str) -> dict:
        return self.send("load_instrument_or_effect", track_index=int(track_index),
                         uri=uri)

    def load_browser_item(self, track_index: int, item_uri: str) -> dict:
        return self.send("load_browser_item", track_index=int(track_index),
                         item_uri=item_uri)

    def load_external_plugin(self, track_index: int, plugin_name: str) -> dict:
        return self.send("load_external_plugin", track_index=int(track_index),
                         plugin_name=plugin_name)

    def navigate_preset(self, track_index: int, device_index: int,
                        direction: str = "next") -> dict:
        return self.send("navigate_preset", track_index=int(track_index),
                         device_index=int(device_index), direction=direction)

    # -- clips ---------------------------------------------------------------

    def create_clip(self, track_index: int, clip_index: int, length: float = 4.0) -> dict:
        return self.send("create_clip", track_index=int(track_index),
                         clip_index=int(clip_index), length=float(length))

    def fire_clip(self, track_index: int, clip_index: int) -> dict:
        return self.send("fire_clip", track_index=int(track_index),
                         clip_index=int(clip_index))

    def stop_clip(self, track_index: int, clip_index: int) -> dict:
        return self.send("stop_clip", track_index=int(track_index),
                         clip_index=int(clip_index))

    def add_notes_to_clip(self, track_index: int, clip_index: int,
                          notes: list[dict]) -> dict:
        return self.send("add_notes_to_clip", track_index=int(track_index),
                         clip_index=int(clip_index), notes=notes)

    def create_arrangement_audio_clip(self, track_index: int, file_path: str,
                                      position: float) -> dict:
        return self.send("create_arrangement_audio_clip",
                         track_index=int(track_index), file_path=file_path,
                         position=float(position))

    def get_arrangement_info(self, track_index: int | None = None) -> dict:
        params = {} if track_index is None else {"track_index": int(track_index)}
        return self.send("get_arrangement_info", **params)

    # -- cue points ----------------------------------------------------------

    def get_cue_points(self) -> list:
        return self.send("get_cue_points")

    # -- browser -------------------------------------------------------------

    def browser_items_at_path(self, path: str) -> dict:
        return self.send("get_browser_items_at_path", path=path)

    def browser_tree(self, category_type: str = "all") -> dict:
        return self.send("get_browser_tree", category_type=category_type)


def discover_plugins(client: LomClient, roots: tuple[str, ...] = ("plugins", "vst3", "vst2"),
                     max_depth: int = 8, max_visited: int = 2000) -> list[dict]:
    """Walk browser roots and return loadable external plugins.

    Mirrors the MCP server's discovery so the driver can load third-party
    plugins without a running MCP host.
    """
    for root in roots:
        stack: list[tuple[str, int]] = [(root, 0)]
        visited: set[str] = set()
        found: list[dict] = []
        root_ok = False
        while stack:
            current, depth = stack.pop()
            if current in visited or len(visited) > max_visited:
                continue
            visited.add(current)
            try:
                result = client.browser_items_at_path(current)
            except LomError:
                continue
            if not isinstance(result, dict) or "items" not in result:
                continue
            root_ok = True
            for item in result.get("items", []):
                name = (item.get("name") or "").strip()
                if not name:
                    continue
                child = f"{current}/{name}"
                if item.get("is_loadable") and item.get("uri"):
                    found.append({
                        "name": name,
                        "uri": item.get("uri"),
                        "path": child,
                        "is_device": bool(item.get("is_device", False)),
                        "root": root,
                    })
                if item.get("is_folder") and depth < max_depth:
                    stack.append((child, depth + 1))
        if found:
            found.sort(key=lambda p: p["name"].lower())
            return found
        if root_ok:
            return []
    return []
