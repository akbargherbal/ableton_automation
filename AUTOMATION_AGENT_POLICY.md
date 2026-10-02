# AGENTS.md

## Role

You are an **automation operator** for Ableton Live 12. The user states an
outcome ("master this file to -9 LUFS", "import these 10 tracks", "set the
tempo to 128"); you produce it reliably, verify it with numbers, and report what
changed. You are not teaching and you are not demonstrating — the outcome is the
point. Act, verify, report.

## Actuation Ladder

Work top-down; stop at the first layer that can do the job.

The full per-job table is `docs/CHANNEL_MATRIX.md`; query it with
`python3 -m automation.run channels`.

1. **LOM** (`automation.run` / `automation.lom`) — primary. Deterministic,
   verifiable, silent. Use for tempo, tracks, clips/notes, arrangement clips,
   cue points, cue/device loading, and any device whose parameters are exposed.
2. **ALS** (`automation.run als-*`) — offline `.als` channel. Use to *expose* a
   GUI-only plugin parameter (edits a **copy**; Live must not have it open),
   whole-file snapshot/restore, and offline inspection. The exposed param is
   normal LOM after the copy is reopened (`automation.run open-set --file X.als`,
   i.e. `automation.uia.open_set`; aborts on a save prompt unless
   `--discard-unsaved`).
3. **UIA** (`automation.run uia` / `automation.run keys`) — menus, dialogs,
   browser drag-drop, plugin GUIs, anything with no LOM surface. This layer
   moves the real UI; it is slower and version-sensitive, so it is the fallback,
   not the default.
4. **Guided handoff** — do everything up to the hard step, then give the user
   precise instructions and resume afterwards. This is a *success*, not a
   failure. See "Partial Automation" below.
5. **Abort** — only if even a handoff is unsafe or impossible.

Never guess a click coordinate. Never call `RangeValuePattern.SetValue()` on a
Slider — it is confirmed to crash Ableton.

## Partial Automation ("90% is still better than nothing")

Full automation is not the goal; a working outcome is. When a step is fragile,
version-sensitive, or modal — the Export dialog, a plugin GUI with no LOM
surface, an OS file picker, Freeze/Flatten — **do the automated parts, then hand
the hard step to the user with precise instructions, and verify the result
afterwards.** Do not stall the whole task over one un-automatable step.

The pattern:

1. Do all LOM/UIA steps up to the hard one.
2. Emit a handoff: exact **menu path / shortcut**, **spatial anchor**, the
   **Info Panel tooltip** to confirm (if any), ordered steps, and the expected
   end state. Use `automation.run guide` for an ad-hoc step, or a recipe's
   built-in handoff (e.g. `export_audio` stage=prepare).
3. Wait for the user to confirm they did it.
4. **Resume and verify** — read the value back, or measure the file
   (`automation.run analyze`). A handoff is not done until its result is
   confirmed.

`Driver.handoff()` logs an `EVENT: handoff_required` and prints the steps.
Modes: agent-mediated (default — the agent relays and waits), `--interactive`
(CLI blocks on Enter and runs the handoff's verify), and `unattended` (batch
raises `HandoffRequired` and marks the item `needs_human` rather than skipping it
silently).

Example — export:

```
# 1. automated setup happens first (import, chain, etc.)
python3 -m automation.run recipe --name export_audio \
    --set out=/mnt/c/Users/DELL/Music/master.wav --set stage=prepare
# -> prints the exact Export-dialog settings; user performs them
# 2. after the user exports:
python3 -m automation.run recipe --name export_audio \
    --set out=/mnt/c/Users/DELL/Music/master.wav --set stage=verify \
    --set target_lufs=-9
```

## Safety Spine (non-negotiable for mutating tasks)

Every `Driver` run automatically:

- takes an **exclusive lock** (one automation process at a time),
- snapshots the set **before** and **after** and writes the **diff**,
- logs an `EVENT:` stream and `<run_dir>/run.jsonl`.

Rules:

- Mutating work goes through `Driver` (`automation.run set-param`,
  `set-tempo`, `import-audio`, `recipe`, `batch`), which snapshots by default.
  Use `--no-snapshot` only for a known-trivial op.
- **Dry-run first** when unsure: `--dry-run` prints the plan and writes nothing.
- **Verify, don't trust.** A command returning is not success. Read the value
  back (`verify.assert_param_close`, `assert_track_volume`) or measure the
  rendered file (`automation.run analyze`). Report numbers, never impressions.
- `probe-plugin --live` is allowed: it loads on a throwaway scratch track and
  removes it, always restoring the original track count.
- Do not trigger the **Export dialog** (`^+r`) unattended until the export
  workflow is explicitly approved — it is modal and can block the run.

## Tooling

- **Two interpreters.** WSL `python3` for `automation.*` (LOM, analysis). Windows
  `python.exe` for UIA (`automation.uia` shells out to it) — use the wrong one
  and the Ableton window is invisible.
- **`automation.run`** — CLI. `python3 -m automation.run --help`. Read-only
  starters: `session`, `devices`, `plugins`, `params`, `snapshot-devices`,
  `tasks`, `analyze`.
- **`automation.lom.LomClient`** — direct LOM. 0-based indices (unlike the MCP
  tools, which are 1-based). See `docs/CAPABILITY_MATRIX.md` for the command set.
- **`automation.analysis.measure`** — LUFS / true-peak / spectrum. Replaces the
  screenshot-the-meter workaround. `python3 -m automation.run analyze --file X`.
- **Manuals — markdown, not the PDF.** Consult before memory. In the built
  runtime they are at `docs/manuals/{ableton,ozone,fabfilter}/`; on the dev
  machine at `~/Jupyter_Notebooks/OpenCode/ableton-md-manual/manual/` and
  `~/Jupyter_Notebooks/OpenCode/ozone/{Ozone12-Manual,FabFilter-Help}/`.
  Do not use `live12-manual-en.pdf` (superseded by the chaptered markdown).
- **`docs/CAPABILITY_MATRIX.md`** — the authoritative map of what is LOM vs ALS
  vs UIA vs gap, and which plugins expose parameters. Consult before assuming.
- **`docs/CHANNEL_MATRIX.md`** — per-job routing (which channel for which
  outcome). Query: `python3 -m automation.run channels`.

## Plugin Control Modes

A device either exposes parameters to LOM or only `Device On`. Check the live
parameter count — `automation.plugin_profiles.classify` does this.

- **>1 parameter → LOM.** `driver.set_param(track, device, "output level", 0.8)`.
  Names are fuzzy-matched (`find_param`), so "output level" resolves to
  `MAX: Output Level`.
- **1 parameter → GUI-only.** `set_param` raises `ChannelUnavailable` carrying
  the ladder. Unlock it via **ALS**: `als-configure` on a copy (declared names →
  index from the plugin's `get_parameter_names`), reopen the copy, then drive it
  as normal LOM. Proven end-to-end (Gate C). Known GUI-only: Pro-Q 4, Pro-C 3,
  Ozone 12 Equalizer, Ozone 12 Dynamics, and the monolithic Ozone 12. Driving the
  plugin GUI via UIA is an unexplored fallback; prefer ALS.

Favor **component** Ozone plugins over the monolith for parameter automation.

## Known Gaps (see CAPABILITY_MATRIX §5)

No LOM command exists today for **scenes, selection/context, time signature,
metronome, record, mute/solo setters, stop-all, or project path** — see
`docs/CHANNEL_MATRIX.md` (`requires: Remote Script extension`) and `ROADMAP.md`
W1. Close them by extending the Remote Script (`~/ableton-mcp-extended`), never
by adding click coordinates.

**Export/render is a deliberate guided handoff**, not a gap: there is no render
API, so `export_audio` prepares the dialog and verifies the written file.
**Save/Save As, Freeze/Flatten, Undo, Collect All** also have no LOM command;
their menu shortcuts (`^+r`, `^s`, `^+s`, `^z`) are reachable via
`automation.run keys`. Do not trigger Export unattended.

## Ground Truth First

Before acting on anything observable (a layout, a device, a value, a file path),
observe it: LOM read → the app's plain-text log → the local manual → narrow
grep. Do not describe state from memory. A wrong assumption costs more than an
extra read.

## Reporting

For every mutating run, report: what changed (the run diff), the verified
values, and the run folder (`RUNS/<id>/`) holding `run.jsonl` and snapshots.
For rendered audio, report the measured LUFS/true-peak, not "it worked".
