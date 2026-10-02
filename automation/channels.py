"""automation.channels — the authoritative channel-selection matrix.

Every "thing doable in Ableton" maps to exactly one *primary* channel (and
optional fallbacks). This is the single source of truth behind
`docs/CHANNEL_MATRIX.md` and the Phase 5 roadmap; consult it (or run
`python3 -m automation.run channels`) before reaching for a lower channel.

Channels, in the order they should be tried:

    lom         Live Object Model, via the Remote Script socket. Deterministic,
                verifiable, and preferred for everything it exposes.
    als         Offline `.als` edit (`automation/als/`). Live must be closed for
                writes; the effect appears on reopen. Used to *expose* GUI-only
                plugin parameters so LOM can then drive them, and for whole-file
                snapshot/restore.
    uia         Windows UI automation (`pywinauto`). Menus, dialogs, plugin
                GUIs, file open/save -- anything with no LOM surface.
    handoff     A guided human step (precise instructions + verify). Used when a
                step is modal/version-sensitive and automating it is not worth
                the fragility.
    analysis    Offline measurement of a rendered file (LUFS / true peak /
                spectrum). No DAW involved; used to verify an outcome.
    sdk_future  Live Extensions SDK. Beta, Live 12.4.5+, Suite + Centercode.
                Not available on 12.1; a future channel with an upgrade trigger.

`requires` records a precondition or an engineering gap. A job whose `requires`
mentions a Remote Script extension is still a `lom` job -- it just needs the
command added first (preferred over UI automation when the LOM exposes the
object).
"""

from __future__ import annotations

from dataclasses import dataclass

CHANNELS = ("lom", "als", "uia", "handoff", "analysis", "sdk_future")


@dataclass(frozen=True)
class Job:
    id: str
    area: str
    outcome: str
    primary: str
    fallbacks: tuple[str, ...] = ()
    verified: bool = False       # measured on this repo (2026-10-02)
    requires: str = ""           # precondition / known gap
    notes: str = ""

    def as_dict(self) -> dict:
        return {
            "id": self.id, "area": self.area, "outcome": self.outcome,
            "primary": self.primary, "fallbacks": list(self.fallbacks),
            "verified": self.verified, "requires": self.requires,
            "notes": self.notes,
        }


def _job(*args, **kwargs) -> Job:
    return Job(*args, **kwargs)


JOBS: dict[str, Job] = {j.id: j for j in (
    # -- session / transport -------------------------------------------------
    _job("session.tempo", "session", "Set the project tempo (BPM)", "lom",
         verified=True),
    _job("session.transport", "session", "Play / stop / locate (song position)",
         "lom", verified=True),
    _job("session.loop_region", "session", "Set/enable the arrangement loop",
         "lom", verified=True),
    _job("session.cue_points", "session", "Create/delete/jump cue points",
         "lom", verified=True),
    _job("session.view", "session", "Switch view, zoom/scroll arrangement",
         "lom", verified=True),
    _job("session.time_signature", "session", "Set time signature", "lom",
         verified=True, notes="W1: Remote Script `set_time_signature`."),
    _job("session.metronome", "session", "Toggle metronome / count-in", "lom",
         verified=True,
         notes="W1: metronome set/verify via `set_metronome`; `count_in_duration` "
               "is get+observe only in the Live 12.1 LOM (setter deferred)."),
    _job("session.record", "session", "Arm + start recording", "lom",
         fallbacks=("uia",), verified=True,
         notes="W1: `set_track_arm` + `trigger_session_record`; UIA arm_track "
               "remains the fallback."),
    _job("session.selected_context", "session",
         "Read selected track / clip / scene / view", "lom",
         verified=True, notes="W1: Remote Script `get_selection`."),
    _job("session.scenes", "session",
         "Create / delete / rename / fire scenes; stop all clips", "lom",
         verified=True,
         notes="W1: `create_scene`/`delete_scene`/`set_scene_name`/`fire_scene`/"
               "`stop_all_clips`."),

    # -- tracks --------------------------------------------------------------
    _job("track.create_delete", "tracks", "Create / delete tracks", "lom",
         verified=True),
    _job("track.rename", "tracks", "Rename a track", "lom", verified=True),
    _job("track.volume_pan", "tracks", "Set track volume / panning", "lom",
         verified=True),
    _job("track.mute_solo", "tracks", "Mute / solo / activator toggles", "lom",
         fallbacks=("uia",), verified=True,
         notes="W1: LOM `set_track_mute`/`set_track_solo` with read-back; UIA "
               "CheckBox path is the fallback."),
    _job("track.arm_monitor", "tracks", "Arm track + set monitor mode", "uia",
         fallbacks=("lom",), verified=True,
         notes="arm now via LOM `set_track_arm`; monitor mode has no LOM surface, "
               "so UIA remains primary."),
    _job("track.freeze_flatten", "tracks", "Freeze / flatten a track", "handoff",
         fallbacks=("uia",), notes="Context menu; no confirmed shortcut."),

    # -- clips / arrangement -------------------------------------------------
    _job("clip.create_midi", "clips", "Create a MIDI clip and add notes", "lom",
         verified=True),
    _job("clip.arrangement", "clips",
         "Place / duplicate / delete arrangement clips", "lom"),
    _job("clip.audio_import", "clips", "Import an audio file to arrangement",
         "lom", notes="Lands, but landing is not yet read-back verified."),
    _job("clip.properties", "clips",
         "Set clip gain / pitch / warp / loop / color", "lom"),
    _job("clip.automation", "clips", "Create/clear clip automation envelopes",
         "lom"),
    _job("clip.fire_stop", "clips", "Fire / stop session clips", "lom",
         verified=True),

    # -- devices / plugin parameters ----------------------------------------
    _job("device.load_native", "devices",
         "Load a native instrument/effect", "lom", verified=True),
    _job("device.load_plugin", "devices", "Load a third-party VST/AU", "lom",
         verified=True),
    _job("device.param_lom", "devices",
         "Set a parameter of a LOM-capable device", "lom", verified=True),
    _job("device.param_gui_only", "devices",
         "Set a parameter of a GUI-only plugin (Pro-Q 4, Ozone EQ, ...)",
         "als", fallbacks=("uia",), verified=True,
         requires="expose via .als, then reopen",
         notes="Gate C: expose offline -> open_set -> LOM set/verify "
               "(+2.18 dB -> 0.75 -> +15.00 dB)."),
    _job("device.enable_bypass", "devices", "Enable / bypass / delete a device",
         "lom", verified=True),
    _job("device.preset", "devices", "Navigate device presets", "lom"),
    _job("device.chain_read", "devices",
         "Inspect racks / chains / drum pads", "lom"),
    _job("device.build_rack", "devices",
         "Build or restructure an instrument/drum rack", "lom",
         notes="Partially exposed; deep rack editing is thin via LOM."),

    # -- browser -------------------------------------------------------------
    _job("browser.list", "browser", "List browser categories/items", "lom",
         verified=True),
    _job("browser.load", "browser", "Load a browser item onto a track", "lom",
         verified=True),
    _job("browser.drag_drop", "browser", "Deep browser drag/drop interactions",
         "uia"),

    # -- files / render ------------------------------------------------------
    _job("file.open_set", "files", "Open a .als set", "uia", verified=True,
         requires="Windows UI layer",
         notes="Ctrl+O + path; aborts on a save prompt unless discard_unsaved. "
               "Auto-discard branch coded, not yet live-verified."),
    _job("file.save", "files", "Save / Save As / versioned checkpoint", "uia",
         fallbacks=("als",),
         notes="Ctrl+S / Ctrl+Shift+S; .als snapshot is the safer checkpoint."),
    _job("file.backup_restore", "files", "Whole-file backup and rollback",
         "als", verified=True, requires="Live closed to restore",
         notes="SHA-256 snapshot + atomic restore + close-swap-reopen handoff."),
    _job("file.export_render", "files", "Render/export audio to a file",
         "handoff", fallbacks=("uia",), verified=False,
         requires="Export dialog is modal",
         notes="No render API in LOM/.als. export_audio recipe = guided dialog "
               "then measure the output."),
    _job("file.collect_all_save", "files",
         "Collect All and Save (gather assets)", "uia",
         notes="File menu; no LOM command."),
    _job("file.undo", "files", "Undo / redo", "uia",
         notes="Ctrl+Z; never a substitute for snapshots."),
    _job("project.path", "files", "Read the current project file path", "lom",
         verified=True,
         notes="W1: `Song.file_path` via `get_project_path`; "
               "$ABLETON_SET_PATH is only a fallback for an older Remote Script."),

    # -- offline analysis ----------------------------------------------------
    _job("analysis.measure", "analysis",
         "Measure LUFS / true peak / spectrum of a rendered file", "analysis",
         verified=True),

    # -- future SDK ----------------------------------------------------------
    _job("ext.true_undo", "extensions", "Transaction-level undo across channels",
         "sdk_future", requires="Live 12.4.5+ beta + Suite enrollment"),
    _job("ext.event_hooks", "extensions",
         "React to Live events (transport, selection, device changes)",
         "sdk_future", requires="Live 12.4.5+ beta + Suite enrollment"),
    _job("ext.deep_integration", "extensions",
         "Custom device/transport integration not in the LOM", "sdk_future",
         requires="Live 12.4.5+ beta + Suite enrollment",
         notes="insertDevice is built-in-only; does not unlock GUI-only params."),
)}


def select(job_id: str) -> Job:
    """Return the Job for `job_id`; raises KeyError with the known ids."""
    if job_id not in JOBS:
        known = ", ".join(sorted(JOBS))
        raise KeyError(f"unknown job {job_id!r}. Known: {known}")
    return JOBS[job_id]


def by_channel(channel: str, *, include_fallbacks: bool = False) -> list[Job]:
    """Jobs for which `channel` is primary (or also a fallback)."""
    if channel not in CHANNELS:
        raise ValueError(f"unknown channel {channel!r}; expected one of {CHANNELS}")
    out = []
    for job in JOBS.values():
        if job.primary == channel or (include_fallbacks and channel in job.fallbacks):
            out.append(job)
    return out


def matrix() -> list[dict]:
    """The whole matrix as JSON-serializable dicts, sorted by area then id."""
    return [j.as_dict() for j in
            sorted(JOBS.values(), key=lambda j: (j.area, j.id))]


def areas() -> list[str]:
    return sorted({j.area for j in JOBS.values()})


def validate() -> None:
    """Structural self-check: channels valid, ids unique, no empty fields."""
    seen: set[str] = set()
    for job in JOBS.values():
        assert job.id not in seen, f"duplicate job id {job.id!r}"
        seen.add(job.id)
        assert job.primary in CHANNELS, f"{job.id}: bad primary {job.primary!r}"
        for ch in job.fallbacks:
            assert ch in CHANNELS, f"{job.id}: bad fallback {ch!r}"
            assert ch != job.primary, f"{job.id}: fallback duplicates primary"
