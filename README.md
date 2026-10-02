# Ableton Live 12 Automation Suite

An LOM-first automation system for **Ableton Live 12**. The user states an
outcome; the agent produces it, verifies it with numbers, and reports what
changed. This repo previously hosted two teaching/tutoring courses — those are
archived under `docs/teaching/` and `SUNO_MASTERING_AGENT_POLICY.md`. See
`ROADMAP.md` for the plan and `docs/CHANNEL_MATRIX.md` for per-job channel routing.

---

## Philosophy: invert the ladder

The old project was built so the agent *demonstrated procedure on screen* while
a human learned by watching — visible mouse clicks first, silent API calls last.
Automation flips that:

| Priority | Teaching (old) | Automation (this repo) |
|---|---|---|
| 1 | Mouse UI click (visible) | **LOM call** (deterministic, verifiable) |
| 2 | Keyboard shortcut | Keyboard/menu shortcut |
| 3 | MCP/LOM (silent) | **UI click** (only for LOM-unreachable things) |
| 4 | Human instructions | Human instructions / abort |

The hard-won UI-automation layer is kept — it's the fallback/reach layer for
menus, dialogs, browser drag-drop, and plugin GUIs that LOM cannot touch.

## Architecture

```
                 ┌─────────────────────────────────────────┐
                 │            Task / Recipe                  │
                 └────────────────────┬────────────────────┘
                                      ▼
                 ┌─────────────────────────────────────────┐
                 │        automation.driver.Driver           │
                 │  • lom      (TCP :9877 → Remote Script)   │
                 │  • als      (offline .als: expose/restore) │
                 │  • uia      (python.exe → pywinauto)       │
                 │  • state    (snapshot / diff / backup)     │
                 │  • verify   (numeric post-conditions)      │
                 │  • lock / log                              │
                 └────────────────────┬────────────────────┘
                                      ▼
                          Ableton Live 12 (Windows)
```

- **LOM** — `automation.lom.LomClient`, a dependency-free TCP client for the
  `AbletonMCP` Remote Script. Primary actuator.
- **ALS** — `automation/als/` edits a *copy* of the `.als` offline (Live closed)
  to expose GUI-only plugin parameters, then LOM drives them after reopen. Also
  whole-file snapshot/restore. The third rung: LOM → **ALS** → UIA → handoff.
- **UIA** — `automation.uia` shells out to `scripts/automate_ableton_task.py`
  (Windows `python.exe`). Fallback/reach.
- **Analysis** — `automation.analysis.measure` (LUFS / true-peak / spectrum),
  pure Python. Closes the verification loop on rendered audio.

Per-job routing lives in `docs/CHANNEL_MATRIX.md`; query it with
`python3 -m automation.run channels`.

## Partial automation (guided handoff)

Not everything needs to be 100% automated. For fragile/modal steps — the Export
dialog, GUI-only plugin parameters, Freeze/Flatten — the driver does all the
automated work, emits precise human instructions, waits, then **resumes and
verifies**. 90% automated is a success, not a failure.

```bash
# emit instructions for a human step (ad-hoc)
python3 -m automation.run guide --title "Freeze 'Guitar'" \
    --menu "right-click the track header" \
    --step "Right-click the 'Guitar' track header" \
    --step "Choose Freeze Track" --expect "track is grey/frozen"

# hybrid export: prepare (guided dialog) then verify (measured)
python3 -m automation.run recipe --name export_audio \
    --set out=/mnt/c/Users/DELL/Music/master.wav --set stage=prepare
#   ...user performs the Export dialog...
python3 -m automation.run recipe --name export_audio \
    --set out=/mnt/c/Users/DELL/Music/master.wav --set stage=verify --set target_lufs=-9
```

In batch runs, a handoff item is marked `needs_human` (not silently skipped);
`--interactive` lets a terminal user complete it.

## Quick start

Run from the repo root with **WSL `python3`**:

```bash
python3 -m automation.run session                 # session info
python3 -m automation.run devices                 # tracks + device chains
python3 -m automation.run plugins --query ozone   # loadable external plugins
python3 -m automation.run params --track 0 --device 0
python3 -m automation.run snapshot-devices        # read-only chain inventory
python3 -m automation.run probe-plugin --plugin "Ozone 12 Maximizer" --live
python3 -m automation.run set-tempo --bpm 124 --dry-run
python3 -m automation.run set-param --track 0 --device 0 --name "output level" --value 0.8
python3 -m automation.run analyze --file out.wav --target-lufs -14
python3 -m automation.run batch --manifest tracks.csv --recipe set_tempo --dry-run
python3 -m automation.run channels                # per-job channel matrix
python3 -m automation.run als-info --path X.als   # offline .als inspection
python3 -m automation.run tasks                   # recipes + UIA tasks
```

Track/device indices are **0-based** (matching `--list-tracks` and the Remote
Script). The MCP *tools* the agent sees are 1-based; the driver is not.

## Safety spine

Every mutating run through `Driver`:

1. acquires an **exclusive lock** (one automation process at a time),
2. snapshots the set **before** and **after**, and writes the **diff**,
3. logs an `EVENT:` stream plus `<run_dir>/run.jsonl`.

`RUNS/<id>/` holds the snapshots and log (gitignored). Mutations are verified by
reading the value back — a command returning is not success. Use `--dry-run`
first when unsure.

## Plugin control modes (important)

A device exposes its parameters to LOM, or only `Device On`. The live parameter
count decides (`automation.plugin_profiles.classify`). Measured 2026-10-02:

| Device | LOM params | Drivable? |
|---|---|---|
| EQ Eight (native) | 84 | ✅ |
| Ozone 12 Maximizer | 20 | ✅ |
| Ozone 12 Vintage Limiter | 13 | ✅ |
| FabFilter Pro-L 2 | 17 | ✅ |
| Ozone 12 Equalizer / Dynamics | 1 | 🔓 ALS-unlockable |
| FabFilter Pro-Q 4 / Pro-C 3 | 1 | 🔓 ALS-unlockable |

GUI-only plugins raise `ChannelUnavailable` carrying the ladder rather than
silently failing. Unlock a parameter offline with `als-configure` (edits a
**copy**), reopen it with `python3 -m automation.run open-set --file X.als`, then
drive it normally — LOM `set_param` with read-back. Gate C set Pro-Q 4
`Band 2 Gain` `+2.18 dB → 0.75 → +15.00 dB` without the plugin GUI. Favor Ozone
**component** plugins over the monolith.
Full map: `docs/CAPABILITY_MATRIX.md`.

## Known gaps

The open LOM gaps are tracked per-job in `docs/CHANNEL_MATRIX.md` (search
`requires: Remote Script extension`): **scenes, selection/context, time
signature, metronome, record, mute/solo setters, stop-all, project path**. They
are closed by extending the Remote Script (`~/ableton-mcp-extended`) — see
`ROADMAP.md` W1 — never by adding click coordinates.

**Export/render is a deliberate guided handoff** (no render API exists; the dialog
is modal). The `export_audio` recipe prepares the dialog, then verifies the file
it writes. **Save/Save As, Freeze/Flatten, Undo, Collect All** have no LOM command
either; menu shortcuts are reachable via `python3 -m automation.run keys` (`^+r`
export, `^s` save, `^+s` save-as, `^z` undo).

## Repository structure

```
ROADMAP.md                    # product roadmap (current plan)
PHASED_PLAN.md                # discovery/architecture plan (complete)
AUTOMATION_PLAN.md            # superseded stub -> ROADMAP.md
AUTOMATION_AGENT_POLICY.md    # runtime policy (shipped as AGENTS.md)
build_automation_env.sh       # assembles the automation runtime folder
automation/                   # the driver package
  lom.py uia.py state.py verify.py lock.py log.py driver.py run.py probe.py batch.py
  channels.py                 # channel-selection matrix (LOM/ALS/UIA/handoff/...)
  als/                        # offline .als channel: read / configure / snapshot
  analysis/measure.py         # LUFS / true-peak / spectrum
  recipes/                    # named, parameterized tasks
  profiles/                   # probed device inventories + declared-name profiles
scripts/                      # Windows UIA layer + catalog
  automate_ableton_task.py    # click/keys primitives (Windows python.exe)
  dump_ableton_pywinauto.py   # read-only UIA tree walker
  keyboard_shortcuts.py
  dumps/control_catalog.json
docs/
  CHANNEL_MATRIX.md           # per-job routing (query: automation.run channels)
  CAPABILITY_MATRIX.md        # LOM vs ALS vs UIA vs gap (read before assuming)
  ALS_FINDINGS.md             # the offline .als channel
  SYSTEM_MAP.md               # what runs where
  opencode-ableton-mcp-setup.md
  teaching/                   # archived courses
tests/                        # pytest, pure-Python
RUNS/                         # runtime output (gitignored)
```

## Environment

- Windows 10/11 with Ableton Live 12; repo and MCP server in WSL2 (mirrored
  networking). See `docs/opencode-ableton-mcp-setup.md`.
- Windows Python needs `pywinauto` + `psutil`:
  `pip install pywinauto psutil`.
- WSL Python needs `pyloudnorm soundfile numpy scipy` for analysis.
- The `AbletonMCP` Remote Script must be selected as a Control Surface; the
  driver connects to it on `localhost:9877`.

### Building the runtime

```bash
./build_automation_env.sh [target_dir]   # default: ../ableton-automation-runtime
```

Point OpenCode's working directory at the target; its `AGENTS.md` is generated
from `AUTOMATION_AGENT_POLICY.md`.

## Tests

```bash
python3 -m pytest tests/
```

## License & attribution

Educational/automation framework for Ableton Live 12. Uses `pywinauto` for
Windows UI Automation. Extended from `uisato/ableton-mcp-extended` for the LOM
MCP bridge.
