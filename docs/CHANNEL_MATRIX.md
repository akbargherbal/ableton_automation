# Channel-Selection Matrix

**Phase 4.2 deliverable** of `PHASED_PLAN.md`. **Verified:** 2026-10-02.
This is the backbone of the Phase 5 roadmap: for each thing doable in Ableton,
which channel does it and why.

The machine-readable authority lives in `automation/channels.py`; query it with:

```
python3 -m automation.run channels              # whole matrix, grouped by area
python3 -m automation.run channels --job ID     # one job
python3 -m automation.run channels --channel als
python3 -m automation.run channels --json
```

The tables below mirror that registry. `*` = **verified on this repo** (live
measurement or test), not merely implemented.

## The ladder

Try channels top-down. Use the **primary** channel unless it is unavailable, then
a **fallback**; a **handoff** is a first-class outcome, not a failure.

| # | Channel | Runs where | Mechanism | Use for |
|---|---|---|---|---|
| 1 | **LOM** | WSL `python3` | Remote Script socket `:9877` | Everything the Live Object Model exposes |
| 2 | **ALS** | WSL `python3`, Live closed for writes | `automation/als/` | Expose GUI-only plugin params; whole-file snapshot/restore; offline inspection |
| 3 | **UIA** | Windows `python.exe` | pywinauto (`automate_ableton_task.py`) | Menus, dialogs, plugin GUIs, open/save, anything with no LOM surface |
| 4 | **Handoff** | human | precise instructions + verify | Modal/version-sensitive steps where automation is fragile |
| — | **Analysis** | WSL `python3` | `automation/analysis/` | Measure a rendered file (LUFS / true peak / spectrum); no DAW |
| F | **SDK-future** | (unavailable on 12.1) | Live Extensions SDK | True undo, event hooks, deep integration; needs 12.4.5+ beta + Suite |

`requires` = a precondition or an engineering gap. "Remote Script extension" is
still a **LOM** job — add the command (preferred over UIA) when the LOM exposes
the object.

---

## Session / transport

| Job | Outcome | Primary | Fallback | * | Requires / notes |
|---|---|---|---|:--:|---|
| `session.tempo` | Set project tempo | lom | | * | |
| `session.transport` | Play / stop / locate | lom | | * | |
| `session.loop_region` | Set/enable arrangement loop | lom | | * | |
| `session.cue_points` | Create/delete/jump cue points | lom | | * | |
| `session.view` | Switch view; zoom/scroll arrangement | lom | | * | |
| `session.time_signature` | Set time signature | lom | | | Remote Script extension |
| `session.metronome` | Toggle metronome / count-in | lom | | | Remote Script extension |
| `session.record` | Arm + start recording | uia | lom | | LOM path needs an extension |
| `session.selected_context` | Read selected track / clip / view | lom | | | Remote Script extension |

## Tracks

| Job | Outcome | Primary | Fallback | * | Requires / notes |
|---|---|---|---|:--:|---|
| `track.create_delete` | Create / delete tracks | lom | | * | |
| `track.rename` | Rename a track | lom | | * | |
| `track.volume_pan` | Set volume / panning | lom | | * | |
| `track.mute_solo` | Mute / solo / activator | uia | lom | | LOM setter not implemented |
| `track.arm_monitor` | Arm track + set monitor mode | uia | | * | `arm_track` task |
| `track.freeze_flatten` | Freeze / flatten | handoff | uia | | Context menu; no confirmed shortcut |

## Clips / arrangement

| Job | Outcome | Primary | Fallback | * | Requires / notes |
|---|---|---|---|:--:|---|
| `clip.create_midi` | Create MIDI clip + add notes | lom | | * | |
| `clip.arrangement` | Place / duplicate / delete arrangement clips | lom | | | |
| `clip.audio_import` | Import audio to arrangement | lom | | | Lands; landing not read-back verified yet |
| `clip.properties` | Clip gain / pitch / warp / loop / color | lom | | | |
| `clip.automation` | Create/clear clip automation envelopes | lom | | | |
| `clip.fire_stop` | Fire / stop session clips | lom | | * | |

## Devices / plugin parameters

| Job | Outcome | Primary | Fallback | * | Requires / notes |
|---|---|---|---|:--:|---|
| `device.load_native` | Load native instrument/effect | lom | | * | |
| `device.load_plugin` | Load third-party VST/AU | lom | | * | |
| `device.param_lom` | Set a LOM-capable device parameter | lom | | * | |
| `device.param_gui_only` | Set a GUI-only plugin parameter | als | uia | * | Expose offline → `open_set` → LOM set/verify (Gate C) |
| `device.enable_bypass` | Enable / bypass / delete device | lom | | * | |
| `device.preset` | Navigate device presets | lom | | | |
| `device.chain_read` | Inspect racks / chains / drum pads | lom | | | |
| `device.build_rack` | Build/restructure instrument/drum racks | lom | | | Deep rack editing is thin via LOM |

`device.param_gui_only` is the load-bearing case: Gate C set Pro-Q 4 `Band 2 Gain`
`+2.18 dB` → `0.75` → **`+15.00 dB`** read-back, entirely without the plugin GUI.

## Browser

| Job | Outcome | Primary | Fallback | * | Requires / notes |
|---|---|---|---|:--:|---|
| `browser.list` | List browser categories/items | lom | | * | |
| `browser.load` | Load a browser item onto a track | lom | | * | |
| `browser.drag_drop` | Deep browser drag/drop | uia | | | |

## Files / render

| Job | Outcome | Primary | Fallback | * | Requires / notes |
|---|---|---|---|:--:|---|
| `file.open_set` | Open a `.als` | uia | | * | Ctrl+O + path; aborts on save prompt unless `discard_unsaved` |
| `file.save` | Save / Save As / checkpoint | uia | als | | `^s` / `^+s`; `.als` snapshot is safer |
| `file.backup_restore` | Whole-file backup & rollback | als | | * | Requires Live closed to restore |
| `file.export_render` | Render/export audio | handoff | uia | | Modal dialog; no render API. `export_audio` recipe |
| `file.collect_all_save` | Collect All and Save | uia | | | File menu |
| `file.undo` | Undo / redo | uia | | | `^z`; never the only safety net |
| `project.path` | Read current project path | lom | | | Remote Script extension, or `$ABLETON_SET_PATH` |

## Offline analysis

| Job | Outcome | Primary | Fallback | * | Requires / notes |
|---|---|---|---|:--:|---|
| `analysis.measure` | LUFS / true peak / spectrum of a file | analysis | | * | No DAW |

## Future SDK (documented, not chased)

| Job | Outcome | Primary | * | Requires |
|---|---|---|:--:|---|
| `ext.true_undo` | Transaction-level undo across channels | sdk_future | | 12.4.5+ beta + Suite |
| `ext.event_hooks` | React to Live events | sdk_future | | 12.4.5+ beta + Suite |
| `ext.deep_integration` | Custom integration beyond the LOM | sdk_future | | 12.4.5+ beta + Suite |

---

## Rules of thumb

1. **LOM first.** If the LOM exposes it, never use UIA — UIA is fragile and
   version-sensitive.
2. **ALS before UIA for parameters.** GUI-only plugin params are unlocked
   *offline and deterministically* by exposure, then driven by LOM after reopen
   (Gate C). Reach for UIA only when the set cannot be closed/reopened.
3. **Handoff is valid.** Export, Freeze/Flatten, and asset collection are
   deliberately human-in-the-loop; automation does everything up to and after
   them, with numeric verification.
4. **Extend the Remote Script before clicking.** For the `requires` gaps above,
   adding a LOM command is the durable fix; UIA is the interim.
5. **Verify numerically.** A channel "worked" only when a value reads back (or a
   file is measured), never because a call returned.

## Consequences for Phase 5

- LOM already covers the large majority of session/track/clip/device/browser
  jobs; the roadmap should assume those are available and spend effort on the
  covered-by-ALS and handoff seams instead.
- The only true *coverage* gaps are: Remote-Script-extension commands (time
  signature, metronome, record, selection, mute/solo setters, project path) and
  the render/export seam (handoff). Everything else has a working channel.
- SDK items are explicitly out of scope on 12.1 and must not gate the roadmap.
