# AGENTS.md

Operating instructions for the agent working in **this** repository.

## What this repo is

Ableton Live 12 automation. The user states an outcome; the agent produces it
via the Live Object Model (LOM) first, UI automation second. The previous
teaching/tutoring orientation is archived under `docs/teaching/`.

Read first:

- `ROADMAP.md` — the **current product roadmap** (W1–W7 + SDK trigger); the
  discovery plan `PHASED_PLAN.md` is a completed record (Phases 0–5, Gates A–C).
- `docs/CAPABILITY_MATRIX.md` — what is LOM vs ALS vs UIA vs gap, and which
  plugins are parameter-drivable. Consult before assuming something is impossible.
- `docs/CHANNEL_MATRIX.md` — per-job routing: which channel (LOM/ALS/UIA/handoff/
  analysis/SDK-future) for which outcome. Query: `automation.run channels`.
- `docs/ALS_FINDINGS.md` — the offline `.als` channel (exposing GUI-only params).
- `AUTOMATION_AGENT_POLICY.md` — the runtime policy (shipped as `AGENTS.md` in
  the built runtime by `build_automation_env.sh`).

## Toolchain

- **WSL `python3`** — `automation.*` (LOM, driver, analysis). Run from the repo
  root: `python3 -m automation.run --help`.
- **Windows `python.exe`** — the UIA layer only
  (`scripts/automate_ableton_task.py`). `automation.uia` invokes it for you.
- **AbletonMCP Remote Script** — `~/ableton-mcp-extended`; the driver talks to
  its socket on `localhost:9877` directly.

## Key facts (verified 2026-10-02)

- Mutating work goes through `automation.driver.Driver`: it locks, snapshots
  before/after, diffs, and logs. Verify with read-back, never "the call returned".
- Device parameters are LOM-writable only when the plugin exposes them. FabFilter
  Pro-Q 4 / Pro-C 3 and Ozone 12 Equalizer / Dynamics expose only `Device On`
  (GUI-only). See `automation/plugin_profiles.py`.
- GUI-only plugins are unlocked offline: `automation.als.configure` exposes a
  parameter by editing a *copy* of the `.als` (dry-run default, backup + SHA-256 +
  atomic), then the param is normal LOM after reopen. Ladder: LOM → ALS → UIA.
  CLI: `automation.run als-configure --source X.als --out Y.als --request NAME`.
  `driver.set_param` raises `ChannelUnavailable` with the ladder for these devices;
  reopen the configured copy with `automation.uia.open_set(win_path)` (UIA Ctrl+O;
  aborts on a save prompt unless `discard_unsaved=True`), then drive it normally
  through LOM. Gate C verified 2026-10-02: Pro-Q 4 `Band 2 Gain` `+2.18 dB` →
  `0.75` → `+15.00 dB` read-back.
- Export/Save/Freeze/Flatten/Undo have no LOM command; menu shortcuts exist and
  are reachable via `automation.run keys` (`^+r`, `^s`, `^+s`, `^z`).

## Conventions

- Runtime output goes to `RUNS/<id>/` (gitignored). Probe output to
  `automation/profiles/`.
- Local manuals beat memory: markdown at
  `~/Jupyter_Notebooks/OpenCode/ableton-md-manual/manual/` and
  `~/Jupyter_Notebooks/OpenCode/ozone/{Ozone12-Manual,FabFilter-Help}/`
  (prefer these over `live12-manual-en.pdf`).
- Tests: `pytest tests/` (see `tests/`).
