# Capability Matrix — what automation can and cannot do

**Verified:** 2026-10-02 against the live Ableton Live 12 session, the installed
`AbletonMCP` Remote Script (`~/ableton-mcp-extended`), and the Windows UIA layer.
This is the Phase 0 "reality sync" deliverable from `AUTOMATION_PLAN.md`; it
supersedes the stale claims in `README.md` (see "Corrected claims" below).

Three layers exist. Prefer them in this order: **LOM → UIA → human**.

| Layer | Runs where | Mechanism | Use for |
|---|---|---|---|
| LOM | WSL `python3` | TCP `localhost:9877` to the Remote Script | Everything the Live Object Model exposes |
| UIA | Windows `python.exe` | pywinauto, `scripts/automate_ableton_task.py` | Menus, dialogs, browser drag-drop, plugin GUIs, anything with no LOM surface |
| Human | — | Level-4 instructions | Genuine gaps |

The driver package (`automation/`) is the LOM-first actuator; `automation.run`
is the CLI. `automation.uia` shells out to the proven click primitives.

---

## 1. LOM capabilities (available today)

Read and/or write through `automation.lom.LomClient`:

| Domain | Commands |
|---|---|
| Session/transport | `get_session_info`, `set_tempo`, `start_playback`, `stop_playback`, `set_song_time`, `set_arrangement_loop` |
| Tracks | `get_track_info`, `create_midi_track`, `delete_track`, `set_track_name`, `get_track_volume`, `set_track_volume`, `set_track_panning` |
| Clips/notes | `create_clip`, `add_notes_to_clip`, `set_clip_name`, `fire_clip`, `stop_clip` |
| Arrangement | `get_arrangement_info`, `create_arrangement_midi_clip`, `create_arrangement_audio_clip`, `duplicate_to_arrangement`, `delete_arrangement_clip`, `set_arrangement_clip_property`, `manage_clip_automation` |
| Cue points | `get_cue_points`, `create_cue_point`, `delete_cue_point`, `jump_to_cue` |
| Devices | `load_instrument_or_effect`, `load_browser_item`, `get_device_parameters`, `set_device_parameter`, `set_device_enabled`, `delete_device`, `navigate_preset`, `get_chain_info`, `get_drum_pad_info` |
| Browser | `get_browser_tree`, `get_browser_items_at_path` |
| View | `set_view`, `control_arrangement_view` |

Verified live: `set_tempo` 120→124→120 with snapshot/diff/verify round-trip;
device load + parameter dump + device delete; session track create/delete.

## 2. Device parameter control — the important finding

A device either exposes all its parameters to LOM or only `Device On`. The live
`parameter_count` is the authority (`automation.plugin_profiles.classify`).

Measured on 2026-10-02:

| Device | Class | LOM params | Drivable via `set_device_parameter`? |
|---|---|---|---|
| EQ Eight (native) | PluginDevice | **84** | ✅ yes |
| Ozone 12 Maximizer | PluginDevice | **20** | ✅ yes |
| Ozone 12 Vintage Limiter | PluginDevice | **13** | ✅ yes |
| FabFilter Pro-L 2 | PluginDevice | **17** | ✅ yes |
| Ozone 12 Equalizer | PluginDevice | 1 | ❌ GUI-only |
| Ozone 12 Dynamics | PluginDevice | 1 | ❌ GUI-only |
| FabFilter Pro-Q 4 | PluginDevice | 1 | ❌ GUI-only |
| FabFilter Pro-C 3 | PluginDevice | 1 | ❌ GUI-only |

**Consequences**

- Native devices and *some* third-party plugins are fully automatable through
  LOM; parameter names are descriptive and fuzzy-resolvable
  (e.g. "output level" → `MAX: Output Level`).
- A plugin exposing only 1 param is **not** LOM-drivable. `driver.set_param`
  raises `NotImplementedError` rather than silently failing. Those need the
  plugin GUI via UIA, or preset loading.
- The monolith `Ozone 12` (whole chain) is treated as GUI/preset-driven; use the
  individual Ozone **component** plugins for parameter automation.
- Ozone components are *not uniform*: Maximizer/Vintage Limiter are LOM-capable,
  Equalizer/Dynamics are not. Never assume from the vendor; probe.

Reproduce/extend: `python3 -m automation.run probe-plugin --plugin "<name>" --live`
(writes to `automation/profiles/probed/`). Read-only inventory of a loaded chain:
`python3 -m automation.run snapshot-devices`.

## 3. External plugin discovery

48 plugins discovered live via the browser tree (Ozone 12 ×21, FabFilter ×15,
MuseFX ×12, TDR Nova). Resolve/load with vendor-aware matching (the vendor lives
in the browser path, not the name):

```
python3 -m automation.run plugins --query fabfilter
python3 -m automation.run recipes   # or: automation.run tasks
```

Loading is `load_browser_item` with the plugin URI, e.g.
`query:Plugins#VST3:iZotope:Ozone%2012%20Maximizer`.

## 4. UIA capabilities

Proven write primitives (CheckBox / Slider / ComboBox) via
`scripts/automate_ableton_task.py`; generic `--control <automation_id>` path.
New: `--keys "<sequence>"` sends a raw pywinauto keystroke to the window, for
menu commands with no `automation_id`.

Known-good shortcuts (from `~/Jupyter_Notebooks/OpenCode/ableton-md-manual`):

| Command | Shortcut | Notes |
|---|---|---|
| Export Audio/Video | `Ctrl+Shift+R` (`^+r`) | Opens a modal dialog — needs a follow-up step |
| Save / Save As | `Ctrl+S` (`^s`) / `Ctrl+Shift+S` (`^+s`) | |
| Undo / Undo History | `Ctrl+Z` (`^z`) / `Ctrl+Alt+Z` | |
| Bounce to New Track | `Ctrl+B` (`^b`) | |
| Split clip / note | `Ctrl+E` | |
| Freeze / Flatten | track context menu | No shortcut confirmed; right-click UI |

## 5. Gaps (no LOM surface, must use UIA or human)

| Gap | Impact | Path |
|---|---|---|
| **Export/render audio** | Can't produce a deliverable without it | UI: `^+r` opens dialog; dialog handling not yet surveyed |
| **Save / Save As** | No checkpoint via LOM | UI: `^s`/`^+s`; `.als` backup also via `ABLETON_SET_PATH` |
| **Freeze / Flatten** | Standard bounce steps | UI context menu (needs survey) |
| **Undo** | Rollback | UI `^z`; not a substitute for snapshot |
| **Scene management** | Post claims it; server has none | Extend Remote Script |
| **Get selected track/clip/view** | Driver context awareness | Extend Remote Script |
| **Time signature, metronome, record** | Session control | Extend Remote Script |
| **Plugin GUI-only params** (Pro-Q 4, Pro-C 3, Ozone EQ/Dynamics) | Can't set params via LOM | Plugin-window UIA (not yet surveyed) or presets |
| **Project file path** | `.als` backup | Extend Remote Script with `get_project_path`, or `ABLETON_SET_PATH` |

## 6. Corrected claims from the old README/policy

- ~~"Phase B Plug-Ins: verified 0 third-party plugins"~~ → 48 plugins installed.
- ~~"Owns Ableton Live only — no paid plugins"~~ → Ozone 12 + FabFilter + MuseFX + TDR.
- ~~"Arrangement View is a planned, not complete, feature"~~ → arrangement clip
  and cue-point commands exist and read live; automation-envelope placement
  still flagged unreliable upstream.
- "Device loading always through MCP, never UI" → still true, and now also
  works from the driver via `load_browser_item`.
- The `control_catalog.json` "0 plugins" Phase B record is stale; it also has no
  `ArrangementView.*` contexts and no plugin contexts. Treat it as an offline
  hint; the live tree (`--list-tracks`) is the authority.
