# Automation Pivot Plan

**Status:** proposal, for review
**Date:** 2026-10-02
**Supersedes (eventually):** the teaching orientation in `README.md`, `context.md`,
`SUNO_MASTERING_AGENT_POLICY.md`

---

## 0. Thesis in one paragraph

The repo was built so the agent *demonstrates procedure on screen* while the human
learns by watching. Automation inverts that: the human states an outcome and the
agent *just produces it*, reliably, repeatably, and safely — ideally unattended.
The single most important consequence is that the **actuation priority flips**.
In teaching, a visible mouse click is the whole point and a silent LOM call is the
last resort. In automation, the deterministic LOM/MCP call is the first choice and
a UI click is only the reach tool for things LOM cannot touch (menus, export
dialogs, browser drag-drop, some plugin GUIs). The hard-won UIA layer we already
have does not get thrown away — it becomes the **reach + evidence layer** instead
of the teaching layer.

The second consequence is that automation needs things teaching never did:
a task executor, plugin parameter maps, a render/export path, state snapshots and
rollback, batch/resume, and **objective verification** (numbers, not a learner's
ear). Those are the bulk of the work below.

---

## 1. Inventory — what is actually in place (verified 2026-10-02)

### 1.1 Two sibling courses sharing one click engine
- **Click-automation UI-grounding course** — `README.md`, `docs/curriculum_map.md`,
  `docs/course_outline.txt`, `orchestrate.sh`, `LABS/`.
- **Suno mastering course** — `context.md`, `PHASED_PLAN.md`,
  `SUNO_MASTERING_AGENT_POLICY.md`, `build_mastering_env.sh`,
  `docs/suno-mastering-*.md`, `docs/MASTERING_COURSE_KNOWN_ISSUES.md`.

### 1.2 Click/UI layer (`scripts/automate_ableton_task.py`, 1,885 lines)
- Proven write mechanisms: `set_checkbox_by_id` (click+verify+retry),
  `set_slider_by_id` (double-click+type+Enter; **`SetValue()` permanently banned —
  it crashed Ableton twice**), `set_combobox_by_id` (click-open + click-item).
- Generic invocation: `call_control(window, auto_id, action, value=...)` /
  `--control <id> --action <click|set> --value <v>`; dispatches by live UIA
  `control_type`; refuses anything but CheckBox/Slider/ComboBox.
- Structured `EVENT:` stream (schema v1) for orchestrator consumption.
- Host-liveness checks (`AbletonProcessGone` / `is_ableton_alive`) via psutil.
- `scripts/dump_ableton_pywinauto.py` — read-only tree walker + canonical
  `ensure_window_ready` + process-liveness helpers.
- `scripts/keyboard_shortcuts.py` — Level-2 shortcut lookup.
- `orchestrate.sh` — one single-action task, screenshot after every action event.
- `take_shot.sh` — window restore/focus/maximize + capture.

### 1.3 MCP/LOM layer (`~/ableton-mcp-extended`, custom fork — **the real prize**)
The installed server (`MCP_Server/server.py`, 2,179 lines) exposes far more than
the setup doc claims. Verified tool surface:

| Domain | Tools |
|---|---|
| Session/transport | `get_session_info`, `set_tempo`, `start_playback`, `stop_playback`, `set_song_time`, `set_arrangement_loop` |
| Tracks | `create_midi_track`, `get_track_info`, `set_track_name`, `get_track_volume`, `set_track_volume`, `set_track_panning`, `delete_track`, `get_track_deletion_status` |
| Clips/notes | `create_clip`, `add_notes_to_clip`, `set_clip_name`, `fire_clip`, `stop_clip` |
| Arrangement | `get_arrangement_info`, `create_arrangement_midi_clip`, `create_arrangement_audio_clip`, `duplicate_clip_to_arrangement`, `delete_arrangement_clip`, `set_arrangement_clip_property`, `manage_clip_automation`, `control_arrangement_view`, `set_ableton_view` |
| Cue points | `get_cue_points`, `create_cue_point`, `delete_cue_point`, `jump_to_cue_point` |
| Devices | `load_instrument_or_effect`, `load_drum_kit`, `get_device_parameters`, `set_device_parameter`, `enable_device`, `disable_device`, `delete_device`, `navigate_device_preset`, `get_chain_info`, `get_drum_pad_info` |
| Plugins | `list_external_plugins`, `load_external_plugin` |
| Browser | `get_browser_tree`, `get_browser_items_at_path` |

### 1.4 Verification/vision
- `take_shot.sh` + the `vision` skill/subagents in OpenCode for screenshots.
- `Live <ver>/Preferences/Log.txt` treated as ground truth for OS/device facts.

### 1.5 Environment
- Ableton Live 12 on Windows; repo + MCP server in WSL2 (mirrored networking).
- `~/.config/opencode/opencode.json` registers `AbletonMCP` via `python
  /home/akbar/ableton-mcp-extended/MCP_Server/server.py`.
- MCP currently connects and reads live state (4 tracks, 2 returns, 120 BPM, empty set).
- UIA scripts must run under Windows `python.exe`; MCP runs under WSL `python`.

---

## 2. Reality check — what changed since the project was written

1. **48 external plugins are now installed**, not zero. Families:
   - **iZotope Ozone 12** (full suite + 20 component modules)
   - **FabFilter** (Pro-Q 4, Pro-C 3, Pro-L 2, Pro-MB, Pro-R 2, Pro-DS, Pro-G,
     Pro-DS, Saturn 2, Timeless 3, Twin 3, Volcano 3, Simplon, Micro, One)
   - **MuseFX** (Chorus, Compress, De-Ess, Delay, Harmonise, Master, Noise Gate,
     PitchFix, Pro EQ, Reverb, Rotary, Simple EQ)
   - **Tokyo Dawn Labs TDR Nova**
2. **The MCP server is a much larger fork than the docs assume** — arrangement
   clips, cue points, plugin loading, device parameter R/W, track deletion all
   exist. The setup doc's "Arrangement is planned, not complete" and "automation
   points behave oddly" limits are stale and must be re-tested, not trusted.
3. **Stale claims that now actively mislead:**
   - `README.md` "Phase B Plug-Ins — verified 0 third-party plugins": false.
   - `SUNO_MASTERING_AGENT_POLICY.md` "Owns Ableton Live only — no paid plugins":
     false.
   - "Device loading always goes through MCP, never UI clicking": true for device
     loading, but there is now a plugin-specific loader (`load_external_plugin`)
     that the policy doesn't mention.
4. **`control_catalog.json` is a Session-view snapshot with no plugin controls**
   and no Arrangement prefix. It cannot answer "what automation_id is Ozone's
   Maximizer threshold" because the plugin didn't exist at survey time.
5. **`plugin_aliases.py` only knows Serum.** Ozone/FabFilter params will come
   back from LOM with raw names (often opaque/generic for VST3), so friendly-name
   control does not exist yet.

---

## 3. Target operating model

### 3.1 Inverted escalation ladder

| Priority | Teaching ladder (old) | Automation ladder (new) |
|---|---|---|
| 1 (primary) | Mouse UI click (visible) | **MCP/LOM call** (deterministic, verifiable) |
| 2 | Keyboard shortcut | MCP browser path / direct socket command |
| 3 | MCP/LOM (silent fallback) | **UI click** via `automate_ableton_task.py` (only LOM-unreachable) |
| 4 (last) | Human instructions | Human instructions / abort + report |

The existing `click_by_id()` intentionally has no MCP tier; automation must add
one — but as *level 1*, not level 3.

### 3.2 Task lifecycle (every automation task)

```
intake → plan → preflight → snapshot → execute → verify → report
                                                  ↘ rollback on failure
```

- **intake**: task is natural language ("master this file to -9 LUFS") or a named
  recipe.
- **plan**: resolve to a recipe/step list; decide actuators.
- **preflight**: Ableton alive, project loaded, required plugins present (via
  `list_external_plugins`), single-run lock held.
- **snapshot**: copy the `.als` + dump LOM state to JSON (see §5.G).
- **execute**: run steps through the unified driver.
- **verify**: numeric post-conditions only (device params via MCP, LUFS via
  analysis, waveform/file existence). Never "the click returned".
- **report/rollback**: write a run log + evidence screenshots; on failure restore
  snapshot or leave the set explicitly marked.

### 3.3 Three layers, one driver

```
                 ┌─────────────────────────────────────────┐
                 │            Task / Recipe                  │
                 └────────────────────┬────────────────────┘
                                      ▼
                 ┌─────────────────────────────────────────┐
                 │        ableton_driver (WSL python)       │
                 │  • lom_client  (MCP/socket, primary)     │
                 │  • uia_client  (python.exe subprocess)   │
                 │  • evidence    (take_shot.sh)            │
                 │  • state       (snapshot/restore)        │
                 │  • verify      (post-conditions)         │
                 └────────────────────┬────────────────────┘
                                      ▼
                        Ableton Live 12 (Windows)
```

---

## 4. What we need to change — by area

### A. Policy & role
- **New `AUTOMATION_AGENT_POLICY.md`** (dev), shipped as `AGENTS.md` by the new
  builder. Role = "operations executor", not instructor. Encodes: inverted
  ladder, task lifecycle, project-safety rules, "never run destructive steps
  without a snapshot", "report numbers, not impressions", "one automation process
  at a time".
- Keep the good operational DNA from the current policy (Ground Truth First,
  Live-Only Reporting, host-liveness, `SetValue()` ban).

### B. Orchestration engine (the biggest missing piece)
Today `orchestrate.sh` runs *one fixed click task*. Automation needs a real
executor. Proposed package:

```
automation/
  driver.py        # unified actuator: lom / uia / evidence / state
  lom.py           # talks to the MCP Remote Script socket (or wraps MCP CLI)
  uia.py           # subprocess wrapper around python.exe automate_ableton_task.py
  state.py         # snapshot(), restore(), diff(), transaction log
  verify.py        # assertion helpers (param ==, lufs ∈ range, file exists)
  recipes/         # named, parameterized task definitions
    master_track.py
    import_audio.py
    build_drums.py
    export.py
  run.py           # CLI: run --recipe X --arg y | run --plan plan.json
  lock.py          # single-run lock (only one automation session at a time)
  log.py           # structured run log + EVENT-parity with existing schema
tests/
```

Design constraints:
- Reuse the existing `EVENT:` schema so `orchestrate.sh` and any consumer keep
  working; bump to schema v2 additively.
- `uia.py` shells out to Windows `python.exe`, same as today. Do not reimplement
  the click primitives.
- Recipes are **idempotent where possible**; a recipe declares `readonly`,
  `reversible`, or `destructive`.

### C. MCP / Remote Script extensions (gap list, verified by grep)
The installed server has **no** tools for any of these. They are the automation
blockers:

| Missing capability | Why it blocks automation | Likely approach |
|---|---|---|
| **Export / render audio** (`Export Audio/Video`) | Cannot produce a deliverable without it. Mastering ends in a file. | LOM has no render API → UI-automate the File menu + Export dialog (needs a menu survey) |
| **Save / Save As / versioned backup** | No safe checkpoint before destructive ops | UI (Ctrl+Shift+S) + filesystem copy of `.als` |
| **Freeze / Flatten** | Standard mastering/bounce steps | UI (menu / context) |
| **Undo / Redo** | Cheap rollback | UI (Ctrl+Z) — but do not rely on it as the only safety net |
| **Scene management** (create/delete/rename/fire) | Post says README claims it; server has none | Extend Remote Script (LOM `song.create_scene`, etc.) |
| **Get selected track / clip / view** | Driver must know context | Extend Remote Script (`song.view.selected_track`, `selected_scene`) |
| **Set time signature, metronome, record** | Session control | Extend Remote Script |
| **Stop all clips / stop-all** | Batch cleanup | Extend Remote Script |
| **Audio import from arbitrary file path** | `create_arrangement_audio_clip` exists; verify session-clip import | Verify + extend if needed |
| **Marker/loop + transport position read** | Reliable arrangement automation | Partially exists; verify |

Extending the Remote Script (`AbletonMCP_Remote_Script/__init__.py`) is preferred
over UI automation wherever LOM exposes the object — always check LOM first.

### D. Control catalog v2
- **Regenerate with plugins loaded** and with a representative project, so plugin
  and device contexts exist.
- Add **Arrangement-view contexts** (`ArrangementView.*`) alongside the existing
  Session-view snapshot.
- Re-run Phase B (Plug-Ins) and Phase E/F with reality; replace the false
  "0 plugins" record.
- Do a **focused survey of the File menu and Export dialog** (`Export`, `Freeze`,
  `Flatten`, `Collect All and Save`) — currently zero coverage and now critical.
- Add a live `--index-live` path to the driver (wraps `build_automation_id_index`)
  as the authority; the catalog becomes an offline hint, not ground truth.

### E. Plugin parameter workflows (Ozone / FabFilter / MuseFX / TDR)
- MCP `get_device_parameters` already reads any device via LOM
  `device.parameters`, including VSTs — but names are raw/opaque and values are
  normalized 0.0–1.0.
- Build:
  1. `scripts/snapshot_device_parameters.py` — dump every param of a loaded
     device to `scripts/dumps/device_<name>_params.json` (index, name, min, max,
     display, normalized, quantized, value_items).
  2. **Alias profiles** in `plugin_aliases.py` for Ozone 12, Pro-Q 4, Pro-C 3,
     Pro-L 2, Pro-R 2, Pro-MB, Saturn 2, TDR Nova, and the MuseFX set — friendly
     name → raw LOM name + parameter categories, generated from the snapshots.
  3. A `find_parameter` fallback that does fuzzy matching when no alias exists,
     and a hard failure (never a silent wrong-param write) when ambiguous.
- Decide per-plugin which are automation-friendly: Ozone's individual component
  plugins (`Ozone 12 Equalizer`, `Ozone 12 Maximizer`, …) are likely easier to
  drive than the monolithic `Ozone 12` (many params, internal signal chain).
  Favor component plugins for deterministic control.

### F. Render / export pipeline
- Build the missing export path (see §C) and make it a first-class recipe:
  `export(track/file, format, bit_depth, realtime?)`.
- Parse `Live .../Preferences/Log.txt` and/or watch the output directory for the
  written file as completion evidence (never trust a dialog click).
- Support both: (a) master-bus export of a finished mix, (b) per-stem
  freeze/flatten where stems exist (note the learner's Suno material is a single
  stereo file — see §H).

### G. Safety, snapshots, rollback
- `state.snapshot()`: copy the project `.als` to a run-specific backup and dump a
  JSON of every track/device/parameter.
- `state.diff(before, after)`: human-readable change report per run.
- Transaction log (JSONL) inside the run's lab folder.
- `uia.py` keeps the existing host-liveness guard; the driver adds a
  **preflight** that refuses to run destructive recipes without a snapshot and a
  live-Ableton check.
- Single-run `lock.py` so two automations can't fight over one Ableton instance.
- Explicit rule: `SetValue()` on Sliders stays banned; use the proven click+type
  path or MCP `set_device_parameter` (which writes `param.value` via LOM, not the
  crashy UIA pattern).

### H. Batch / bulk runner
- The user has ~600 Suno tracks. Automation's highest-value use is batch:
  `run.py batch --manifest tracks.csv --recipe master_track --resume`.
- Needs: import audio → apply chain → render → write result + verify LUFS →
  mark manifest row done. Resumable, idempotent, with per-item run folders.
- Reuses `LABS/` convention under a new `RUNS/` or `BATCH/` root.

### I. Closed-loop audio analysis (objective verification)
Teaching used the learner's ear and a screenshot of Youlean. Automation must
measure:
- Add `analysis/` with **pyloudnorm** (integrated LUFS, true peak), **numpy/scipy**
  (spectrum/band energy), **soundfile** (I/O), optional **matchering** (reference
  match), **librosa** (optional).
- Feeds both verification (`verify.measure_file(...)`) and closed-loop control
  (e.g. adjust Ozone Maximizer threshold until integrated LUFS target is hit).
- This removes the LUFS-screenshot workaround entirely and is a pure-Python
  addition (no Ableton needed).

### J. Verification harness / tests
- Golden scratch project `.als` checked in (or generated by a bootstrap recipe).
- MCP tool smoke tests (read-only) + a `--rehearsal` mode that performs a recipe
  on scratch and auto-reverts.
- Snapshot-diff regression: run a recipe, assert the parameter diff matches a
  recorded expectation.
- Keep a `RUNS/<id>/evidence/` convention (screenshots + JSON) for every run.

### K. Runtime build & docs
- `build_automation_env.sh` — sibling of `build_mastering_env.sh`; whitelists the
  automation runtime (driver package, policy, catalog v2, plugin aliases,
  `take_shot.sh`, UIA scripts, analysis) and seeds `AGENTS.md`.
- Rewrite `README.md` around automation; move teaching docs to `docs/teaching/`.
- Replace `context.md` with an automation digest; use the currently-empty
  `PHASED_PLAN.md` for the resumable implementation plan.

### L. Deprecate / repurpose teaching assets
- `docs/course_outline.txt`, `curriculum_map.md`, `suno-mastering-*` → archive.
- Keep the click engine and its probes; they are now infrastructure.
- The "demonstrate for the learner" rules are removed, not just de-emphasized —
  leaving them in would make the agent narrate instead of act.

---

## 5. Tools we will need

| Tool | Purpose | Build vs install | Notes |
|---|---|---|---|
| Extended Remote Script commands | export, save, freeze/flatten, undo, scenes, selection, transport | **Build** (edit `AbletonMCP_Remote_Script/__init__.py`) | Prefer LOM; UI fallback where LOM exposes nothing |
| `automation/` driver package | Unified actuator + lifecycle | **Build** | Core new code |
| `scripts/snapshot_device_parameters.py` | Plugin/device param dumps | **Build** | Reuses MCP `get_device_parameters` |
| Plugin alias profiles | Friendly Ozone/FabFilter param names | **Build** (extend `plugin_aliases.py`) | Auto-generate from snapshots |
| Menu/Export dialog survey | Make export clickable | **Build** (survey + catalog) | Focused re-scan, not full |
| `analysis/` (pyloudnorm, soundfile, scipy, numpy, matchering) | Objective verify + closed loop | **Install** | WSL python; matchering optional |
| `pytest` | Tests | **Install** | ± existing `tests/` in MCP repo |
| `run.py` batch + resume | Bulk processing | **Build** | Manifest-based |
| Single-run lock | Prevent concurrency | **Build** | File lock |
| Structured run log | Auditability | **Build** | JSONL + existing `EVENT:` v2 |
| `build_automation_env.sh` | Runtime packaging | **Build** | Mirrors mastering builder |
| Vision subagents | Evidence/verification screenshots | **Existing** | Already available in OpenCode |
| Direct LOM socket client | Bypass MCP where faster/bulkier | **Build (optional)** | MCP already wraps the same socket |

---

## 6. Phased roadmap

### Phase 0 — Reality sync (small, do first)
- [ ] Regenerate `control_catalog.json` with plugins + Arrangement prefix; delete
      the false "0 plugins" claim.
- [ ] Re-test the upstream "unreliable" claims: `manage_clip_automation`,
      arrangement clips, transport positions.
- [ ] Write the MCP capability matrix (what's LOM-reachable vs UI-only).
- **Exit:** an honest, current map of what can be automated and by which layer.

### Phase 1 — Driver + safety spine
- [ ] Build `automation/{driver,lom,uia,state,verify,lock,log}.py`.
- [ ] `state.snapshot()/diff()` and the `.als` backup.
- [ ] Port one existing task (`set_tempo` / `solo`) through the driver to prove
      the abstraction end-to-end.
- [ ] Add MCP as L1 in `click_by_id` (and/or a driver-level router).
- **Exit:** a task can be expressed once and executed with snapshot + verify + log.

### Phase 2 — Plugin control
- [ ] `snapshot_device_parameters.py`; snapshot Ozone components, Pro-Q 4,
      Pro-C 3, Pro-L 2, Pro-R 2, TDR Nova, MuseFX.
- [ ] Generate alias profiles; wire fuzzy `find_parameter` with hard-fail on
      ambiguity.
- [ ] Prove one real chain end-to-end (e.g. Pro-Q 4 EQ + Pro-C 3 comp + Ozone
      Maximizer) on a scratch track with parameter read-back.
- **Exit:** "load these plugins and set these named params" works deterministically.

### Phase 3 — Render/export
- [ ] Survey File menu + Export dialog (`Export Audio/Video`, Freeze, Flatten,
      Collect All and Save).
- [ ] Implement export recipe + completion detection (log watch / file watch).
- [ ] Implement save/save-as + versioned `.als` backup.
- **Exit:** a track can be mastered and a WAV rendered + verified, unattended.

### Phase 4 — Batch + dogfood on the Suno library
- [ ] `run.py batch` with manifest, resume, per-item run folders.
- [ ] Master a small batch (5–10 tracks) end-to-end; measure failure modes.
- **Exit:** a repeatable batch mastering run with a pass/fail report.

### Phase 5 — Closed-loop analysis
- [ ] `analysis/` with LUFS/true-peak/spectrum; `verify.measure_file`.
- [ ] Feed measurements back into the chain (target LUFS, tonal match).
- **Exit:** the pipeline hits objective targets without human listening.

### Phase 6 — Harden
- [ ] Rollback on failure; run-level resume after Ableton crash.
- [ ] Golden-project tests + snapshot regression.
- [ ] `AUTOMATION_AGENT_POLICY.md` + `build_automation_env.sh` + README rewrite.
- [ ] Archive the teaching docs.
- **Exit:** another session can pick this up from `PHASED_PLAN.md` alone.

---

## 7. Decisions needed from you

1. **Automation scope:** mastering/batch only, or general production (arrangement,
   MIDI/drum programming, sound design) too? This changes Phase 4 priorities.
2. **Export strategy:** are you willing to UI-automate the Export dialog (fragile,
   version-sensitive), or should we invest in extending the Remote Script / an
   alternative render bridge first?
3. **Plugin strategy:** drive the individual Ozone component plugins (cleaner
   params) or the monolithic Ozone 12 (one device, opaque params)?
4. **Autonomy level:** should the agent be allowed to run destructive batch jobs
   unattended, or always require a confirmation gate before render/save?
5. **Keep or archive the teaching courses?** (Plan assumes archive; content is
   preserved either way.)

---

## 8. Immediate next step (recommended)

Do **Phase 0 only** as a first commit: regenerate the catalog with the current
plugin set, re-test the stale MCP limits, and produce the capability matrix. It is
low-risk, needs no new architecture, and it will tell us definitively which of
Phases 1–5 actually need UI automation versus pure LOM — which is the biggest
budget unknown in this plan.
