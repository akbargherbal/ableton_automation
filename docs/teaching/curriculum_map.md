# Curriculum → Control Reference Map

> **Scope note (added in the mastering-course phased plan, Phase 5):** this file
> documents the **click-automation UI-grounding course** (see `README.md` /
> `docs/course_outline.txt`) — it is still live and authoritative _for that course_.
> It is **not** the curriculum for the separate Suno-mastering course. If you're
> working on the mastering course, use `docs/suno-mastering-course-breakdown.md`
> (authoritative spec) and `docs/suno-mastering-curriculum.md` (leaner operating
> version) instead — see `SUNO_MASTERING_AGENT_POLICY.md`'s "Curriculum" section.

A **lookup reference only** — for each module in `docs/course_outline.txt`, this lists
candidate `automation_id`s from `scripts/dumps/control_catalog.json` and matching
`TASK_REGISTRY` entries in `scripts/automate_ableton_task.py`. It deliberately stops at
"here are the relevant controls": no scripted sequence, no narration, no phrasing.

**How to read a write-back status tag:**

- `write=proven` — a verified write path exists (`set_checkbox_by_id` for CheckBox,
  `set_slider_by_id` for Slider, `set_combobox_by_id` for ComboBox).
- `write=none` — only a read path exists, or the control is unverified for writing.
- `read=proven` — a live read-back path is confirmed (ToggleState / RangeValue /
  ValuePattern).
- `gap` — no usable `automation_id` exists in the catalog for this topic (honestly
  marked, not guessed).

Verified spot-check date: 2026-08-09 (all listed IDs confirmed present in
`control_catalog.json`; write/read statuses reflect the current
`automate_ableton_task.py` WRITE-BACK STATUS note and Phase 2–3 proof runs).

---

## Module 1 — Introduction to Ableton Live 12

| Topic                                               | Relevant automation_ids                                                                                      | Tasks / notes                                                                                                             |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| Ableton workflow / Session View vs Arrangement View | `SessionView.Track[N].Slot[M]`, `SessionView.Track[N].Mixer.*`, `ArrangementView.*`                          | view-level; Slot is a Group (clip slot), write=none                                                                       |
| Transport (Play/Stop/Tempo)                         | `Transport.Play`, `Transport.Stop`, `Transport.Tempo`                                                        | `Transport.Tempo` write=proven via `set_tempo`; Play/Stop read=none (click-and-trust gap), used by `solo_one`/`solo_tour` |
| Metronome                                           | `Transport.Metronome`                                                                                        | write=proven via `set_checkbox_by_id` (used in `idiom_demo` Idiom 1)                                                      |
| Browser                                             | —                                                                                                            | **gap** (Phase E UNMAPPED — `browser:*` contexts are UNMAPPED)                                                            |
| Packs                                               | —                                                                                                            | **gap** (lives in Browser, Phase E UNMAPPED)                                                                              |
| Preferences                                         | —                                                                                                            | **gap** (no catalog entry; menu-only)                                                                                     |
| Audio Interface basics                              | —                                                                                                            | **gap** (menu-only, no catalog entry)                                                                                     |
| File management                                     | `ManageSet`, `LessonViewCloseButton`, `LessonViewBackButton`, `LessonViewNextButton`, `LessonViewHomeButton` | File-Manager section controls; write=none (buttons, unverified)                                                           |
| Lab: Create first Live Set / Import song / Navigate | `Transport.Play`, `Transport.Stop`, `SessionView.Track[N].Slot[M]`                                           | import is a drag/drop Browser action → **gap** for the import itself                                                      |

## Module 2 — Working with Audio

| Topic                   | Relevant automation_ids                                                                                                | Tasks / notes                                                                                                                                                            |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Audio Clips / Clip View | `ClipDetailView.*`                                                                                                     | Clip Detail section is MAPPED; e.g. `ClipDetailView.Header.PowerSwitch` (CheckBox, write=none), `ClipDetailView.MainProperties.RegionProperties.LoopOnButton` (CheckBox) |
| Warp                    | `TrackView.Device[0].Details.Sample.Warp.IsWarped`, `TrackView.Device[0].Details.Sample.Warp.WarpMode`                 | read/write=none (unverified on this control), present in catalog (Simpler sample warp)                                                                                   |
| Looping                 | `ClipDetailView.MainProperties.RegionProperties.LoopOnButton`, `.LoopStart.Bars`, `.LoopLength.Bars`, `.DuplicateLoop` | sliders write=none (not yet exercised); LoopOnButton is CheckBox shape                                                                                                   |
| Crop / Consolidate      | —                                                                                                                      | **gap** (menu operations, no catalog entry)                                                                                                                              |
| Fade Handles            | —                                                                                                                      | **gap** (no catalog entry)                                                                                                                                               |
| Gain                    | `TrackView.Device[0].Details.Sample.SampleGain.SampleVolume` (Simpler); clip-level gain **gap**                        | Slider shape, write=none                                                                                                                                                 |
| Tempo Matching          | `Transport.Tempo`                                                                                                      | write=proven via `set_tempo`                                                                                                                                             |

## Module 3 — MIDI & Instruments

| Topic                               | Relevant automation_ids                                                                                                                                                                                                                             | Tasks / notes                                                                          |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| MIDI Clips / Piano Roll             | —                                                                                                                                                                                                                                                   | **gap** (note editing is not exposed via automation_id)                                |
| Drum Rack                           | `TrackView.Device[0].TitleBar.ShowSwapBar`; device internals **gap**                                                                                                                                                                                | Drum-Rack device mostly collapsed in dump                                              |
| Simpler                             | `TrackView.Device[0].PlaybackMode`, `PlaybackMode.Classic/One-Shot/Slicing`, `Details.Sample.SampleGain.SampleVolume`, `Details.Sample.Warp.IsWarped`, `Details.Sample.Warp.WarpMode`, `Fingers.Filter.Freq`, `Fingers.Filter.Res`, `Fingers.LFO.*` | all read/write=none (unverified), present in catalog                                   |
| Instrument Rack                     | `TrackView.Device[0]` (container); macro controls **gap**                                                                                                                                                                                           | macro knobs not in catalog                                                             |
| Browser Sounds                      | —                                                                                                                                                                                                                                                   | **gap** (Phase E UNMAPPED — `browser:sounds` is UNMAPPED)                              |
| Recording MIDI                      | `Transport.GlobalRecord`, `SessionView.Track[N].Mixer.Arm`                                                                                                                                                                                          | Arm write=proven via `arm_track`; GlobalRecord CheckBox write=none                     |
| Quantization                        | `Transport.GlobalQuantization`                                                                                                                                                                                                                      | read=proven + **write=proven** via `set_combobox_by_id` (used in `idiom_demo` Idiom 3) |
| Lab: drums / bass / edit MIDI notes | —                                                                                                                                                                                                                                                   | note editing **gap**; Drum Rack internals **gap**                                      |

## Module 4 — Creative Editing & Arrangement

| Topic                              | Relevant automation_ids                                                                                 | Tasks / notes            |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------ |
| Arrangement View                   | `ArrangementView.*`                                                                                     | section MAPPED           |
| Scenes                             | `SessionView.MainTrack.SceneControl`, `SessionView.MainTrack.SceneControl.Title`                        | write=none               |
| Markers / Locators                 | `ArrangementView.SetDeleteLocator`                                                                      | Button, write=none       |
| Automation                         | `ArrangementView.AutomationModeButton`, `ArrangementView.LockEnvelopes`, `Transport.AutomationArm`      | CheckBoxes, write=none   |
| Clip Automation / Track Automation | `ArrangementView.Track[N].Header.AddAutomationLane`, `.Header.EnvelopeChooser`, `.Header.DeviceChooser` | write=none               |
| Follow Actions                     | `SessionView.MainTrack.Mixer.EnableFollowActions`                                                       | CheckBox, write=none     |
| Consolidation                      | —                                                                                                       | **gap** (menu operation) |

## Module 5 — Effects & Sound Design Basics

| Topic                   | Relevant automation_ids                                                                                                                                        | Tasks / notes                                                                                  |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| EQ Eight                | `TrackView.Device[0].Freq`, `.Gain`, `.Q`, `.Band0.Selector`…`.Band7.Selector`, `.Audition`, `.Analyze`, `.AdaptiveQ`, `TrackView.Device[0].TitleBar.DeviceOn` | **Freq write=proven** via `set_slider_by_id` (used in `idiom_demo` Idiom 2); Gain/Q write=none |
| Compressor              | `TrackView.Device[0].Makeup`, `.Lookahead`, `.Envelope`, `.Model.Buttons[0..2]`, `.ViewMode.*`, `.ActivityCurve.Buttons[0..1]`                                 | write=none                                                                                     |
| Reverb                  | `TrackView.Device[0].Tab.BottomControls.IRChooser.Dropdowns.IRCategory`, `.IRFile`                                                                             | ComboBoxes, write=none                                                                         |
| Delay                   | `TrackView.Device[0].DryWet`                                                                                                                                   | Slider, write=none                                                                             |
| Saturator               | `TrackView.Device[0].TitleBar.ExtendViewButton`, `TitleBar.DeviceOn`                                                                                           | write=none (device internals mostly collapsed)                                                 |
| Utility                 | `TrackView.Device[0].StereoWidth`                                                                                                                              | Slider, write=none (only StereoWidth exposed in the dump — Gain/Mute not present in catalog)   |
| Limiter                 | `TrackView.Device[0].GainRed.Ceiling`                                                                                                                          | Slider, write=none                                                                             |
| Effect Chains / Presets | —                                                                                                                                                              | **gap** (chain/save controls not in catalog)                                                   |

## Module 6 — Mixing Essentials

| Topic                      | Relevant automation_ids                                                                                                             | Tasks / notes                                                                                                                          |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Mixer / Volume / Pan       | `SessionView.Track[N].Mixer.Volume`, `.Pan`, `.PeakLevel`, `ArrangementView.MainTrack.Mixer.Volume`, `.Pan`                         | Sliders, write=none (read-only proven for Solo/Arm)                                                                                    |
| Gain Staging               | `SessionView.Track[N].Mixer.Volume`                                                                                                 | see above                                                                                                                              |
| Sends & Returns            | `SessionView.Track[N].Mixer.Send[0]`, `.Send[1]`, `SessionView.ReturnTrack[N].Mixer.*`, `SessionView.ReturnTrack[N].Mixer.Send[0]`  | sliders, write=none                                                                                                                    |
| Buses (Group Tracks)       | `SessionView.GroupTrack[0].Mixer.*`, `SessionView.GroupTrack[0].Track[N].Mixer.*`                                                   | MAPPED                                                                                                                                 |
| Metering                   | `SessionView.Track[N].Mixer.PeakLevel`, `Transport.CombinedOverloadMeter`, `TrackView.Device[0].PeakInLevel/PeakOutLevel/PeakLevel` | read-only meters                                                                                                                       |
| Spectrum                   | `TrackView.Device[0].TitleBar.DeviceOn`, `TitleBar.ExtendViewButton` (Spectrum device)                                              | write=none; spectrum display itself not a control                                                                                      |
| Reference Tracks           | —                                                                                                                                   | **gap** (workflow concept; no dedicated control)                                                                                       |
| Lab: mix / balance / depth | Solo (write=proven), Volume/Pan/Sends (write=none)                                                                                  | `solo_one`/`solo_tour`/`read_solo_states`/`probe_toggle` cover the Solo idiom; **volume/pan/send write is the next unproven frontier** |

## Module 7 — Final Project & Export

| Topic                  | Relevant automation_ids    | Tasks / notes                          |
| ---------------------- | -------------------------- | -------------------------------------- |
| Workflow recap         | —                          | —                                      |
| Project organization   | `ManageSet` (File Manager) | write=none                             |
| Freeze Track / Flatten | —                          | **gap** (no catalog entry)             |
| Collect All and Save   | —                          | **gap** (menu operation)               |
| Export Audio/Video     | —                          | **gap** (Export dialog not in catalog) |
| File formats (WAV/MP3) | —                          | **gap** (export dialog)                |
| Sharing online         | —                          | **gap** (out of DAW)                   |

---

## Proven-write controls (the actual automation surface that is verified)

These are the only `automation_id`s with a proven, verified write path today. Point
students at these for hands-on automation; everything else above is reference-only
or a documented gap.

| Control             | automation_id                                      | Write mechanism                   | Proven via                              |
| ------------------- | -------------------------------------------------- | --------------------------------- | --------------------------------------- |
| Track Solo          | `SessionView.Track[N].Mixer.Solo`                  | CheckBox click+verify             | `solo_one`, `solo_tour`, `probe_toggle` |
| Track Arm           | `SessionView.Track[N].Mixer.Arm`                   | CheckBox click+verify             | `arm_track`                             |
| Track Monitoring    | `SessionView.Track[N].Mixer.Monitoring.Buttons[0]` | RadioButton click+verify          | `arm_track`                             |
| Metronome           | `Transport.Metronome`                              | CheckBox click+verify             | `idiom_demo` Idiom 1                    |
| Tempo               | `Transport.Tempo`                                  | Slider double-click+type+Enter    | `set_tempo`                             |
| EQ Eight Freq       | `TrackView.Device[0].Freq`                         | Slider double-click+type+Enter    | `idiom_demo` Idiom 2                    |
| Global Quantization | `Transport.GlobalQuantization`                     | ComboBox click-to-open+click-item | `idiom_demo` Idiom 3                    |

## Honest gaps (no reference available yet)

- **Browser** (module 1, 3 — Browser Sounds/Packs): Phase E is UNMAPPED. `browser:*` contexts exist in the catalog but are status `UNMAPPED`. Do not guess item-level IDs.
- **Piano Roll / MIDI note editing** (module 3): no automation_id surface exists for note editing.
- **Crop / Consolidate / Fade Handles / Freeze / Flatten / Export / Collect All and Save** (modules 2, 4, 7): menu operations, no catalog entry.
- **Effect Chains / presets, Instrument Rack macros** (module 5): not exposed in the catalog.
