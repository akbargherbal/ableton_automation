# Product Roadmap — General Ableton Automation (Live 12.1)

**Status:** current plan. Supersedes `AUTOMATION_PLAN.md` (now a pointer).
**Date:** 2026-10-02. **Baseline:** Live 12.1, Build `2024-09-25_bba251b1d9`, Windows 11.
**Companions:** `docs/CHANNEL_MATRIX.md` (routing, machine-readable in
`automation/channels.py`), `docs/CAPABILITY_MATRIX.md` (capability inventory),
`PHASED_PLAN.md` (the completed discovery/architecture plan).

This is the product plan the discovery phases were de-risking. It is written
*after* the facts (Phases 0–4) so it contains no guesses.

---

## 1. Objective and principles

**Objective (Q1):** general-purpose — *"I want to do this thing in Ableton; the
agent does it, verifies it, and reports what changed."* Not a mastering pipeline.
Coverage of doable outcomes drives the plan; the channel matrix measures it.

Principles, carried from the policy:

1. **LOM first.** Escalation ladder: LOM → ALS → UIA → handoff → abort.
2. **Verify numerically.** A channel worked only when a value reads back or a file
   is measured — never because a call returned.
3. **Snapshot before mutating.** The `Driver` lock/snapshot/diff/log spine is
   mandatory for mutating work.
4. **Handoff is a valid outcome.** 90% automated is success; a human step is
   marked, never silently skipped.
5. **12.1 is the target.** The Extensions SDK is a trigger-gated future channel,
   not a dependency.

---

## 2. Where we are (verified 2026-10-02)

**Harness in place:** `driver` (lock → snapshot → execute → verify → diff → log),
`lom`/`uia`/`als` channels, `batch` with resume, `analysis` (LUFS/true-peak/
spectrum), recipes, handoff, plugin profiles. 41 tests pass.

**Channel matrix (`automation.run channels`):** 44 jobs, 8 areas, 28 measured.

| Channel | Jobs | Character |
|---|---:|---|
| LOM | 30 | The bulk of session/track/clip/device/browser — deterministic |
| UIA | 6 | Menus, dialogs, arm/monitor, browser drag-drop |
| sdk_future | 3 | Trigger-gated (12.4.5+) |
| handoff | 2 | Export, Freeze/Flatten |
| ALS | 2 | Drives GUI-only plugin params; whole-file snapshot/restore |
| analysis | 1 | Offline measurement |

**Proven legs:**
- Wide LOM coverage; numeric read-back.
- **W1 Remote Script extension pack** (live smoke 2026-10-02, 25/25): project
  path, selection, transport read-back, time signature, metronome, track
  mute/solo/arm, scene create/rename/fire/delete, `stop_all_clips`,
  `trigger_session_record`.
- **ALS unlocks GUI-only plugins** (Gate C): expose a parameter offline → reopen →
  LOM set/read-back (`+2.18 dB → 0.75 → +15.00 dB`) with no plugin GUI.
- **Handoff export** (`export_audio` prepare/verify) + objective measurement.
- Batch mastering over the legacy Suno manifest (former example, still works).

**The real gaps (from the matrix):**
1. ~~LOM commands missing for session control and context (time signature,
   metronome, record, selection, mute/solo setters, scenes, stop-all, project
   path).~~ **Closed by W1 (2026-10-02)**: added to the Remote Script; only the
   count-in *setter* is deferred (LOM read-only).
2. Plugin coverage is per-plugin and manual; no at-scale classification/profiles.
3. ALS writer is proven for one param; not yet exercised broadly, and the reopen
   loop is a handoff.
4. Export/render is handoff-only by decision (fine) but the seam needs polish.
5. Recipes skew mastering; general-production recipes are thin.

---

## 3. Workstreams

Each workstream has concrete tasks, an **exit criterion**, and **verification**.
Workstream W1 is highest leverage: it converts fragile UIA jobs into deterministic
LOM and shrinks the "requires" column of the matrix.

### W1 — Remote Script extension pack (LOM coverage)  ← highest priority — DONE 2026-10-02
- [x] `get_project_path` (`Song.file_path`; kills the `ABLETON_SET_PATH` fallback).
- [x] Selection getters: selected track / clip / scene / view / slot / device.
- [x] Scenes: create / delete / rename / fire; **stop-all**.
- [x] Session control setters: time signature, metronome; track
      `mute`/`solo`/`arm`; `trigger_session_record`.
- [x] Transport read-back: is-playing, record state, current position units
      (`position_unit: "beats"`).
- [~] `set_count_in` **deferred**: `count_in_duration` is get+observe (read-only)
      in the Live 12.1 LOM; the getter is exposed in `get_transport_info`.
- [x] Extended `LomClient` + `driver` + CLI; live smoke script
      `scripts/live_smoke_w1.py` (25 checks pass, 1 explicit deferral).
- **Exit:** every session-control `lom` job is implemented except the count-in
  setter, which is deferred with the LOM access-mode reason; `track.mute_solo`
  and `session.record` are LOM primaries with UIA fallbacks.
- **Verify:** `scripts/live_smoke_w1.py` asserts numeric read-back after every
  set (mutations restored); matrix rows updated via `automation.run channels`.
- **Note:** requires a full Ableton restart to load. Install path is the OneDrive
  `User Library` Remote Script, not `%APPDATA%`.

### W2 — Plugin parameter coverage at scale
- [ ] Enumerate installed plugins (48) and classify each (LOM vs GUI-only) live;
      cache in `plugin_profiles`.
- [ ] Auto-generate declared-name profiles for GUI-only plugins from
      `get_parameter_names` (already used for Pro-Q 4's 737 names).
- [ ] Friendly alias/param names for the LOM-capable ones (Ozone components,
      Pro-L 2, EQ Eight, …) with fuzzy `find_param` and **hard-fail on ambiguity**.
- [ ] One-command GUI-only unlock: `als-configure` → `open_set` → drive.
- **Exit:** `set-param` works for every LOM-capable installed plugin; every
  GUI-only plugin is unlockable by one documented flow.
- **Verify:** read-back per plugin in a generated report under `RUNS/`.

### W3 — ALS channel hardening
- [ ] Expose multiple params across multiple devices in one pass.
- [ ] Writer guards: idempotent re-runs, already-exposed detection, slot exhaustion
      errors, re-parse validation (exists) + tests.
- [ ] Snapshot/restore UX: dry-run default, atomic restore, `restore_handoff`
      polish, refuse-while-running unless forced (exists).
- [ ] Close the reopen loop as much as possible (`open_set` + save-prompt policy),
      documenting the remaining human step honestly.
- [ ] Delete stale Phase 2 artifact `AASHA_exposed_test.als`.
- **Exit:** a recipe can expose an N-parameter set for a GUI-only plugin and drive
  it after reopen; restore is exercised.
- **Verify:** extended `tests/test_als.py` + one live Gate-C-style pass.

### W4 — Render/export seam (handoff)
- [ ] Polish `export_audio`: output naming/versioning, per-stem export, target
      LUFS in the verify stage.
- [ ] Completion detection by watching the output file and/or `Log.txt` (never a
      dialog click).
- [ ] Freeze/Flatten and Collect-All handoffs wired into recipes.
- **Exit:** "make X, then render, then verify" completes end-to-end with the human
  involved only at the modal dialog.
- **Verify:** the rendered file is measured (LUFS/true-peak); run log records it.

### W5 — General-purpose recipes and batch
- [ ] Recipe registry cleanup; idempotency/reversibility tags.
- [ ] Non-mastering recipes: arrangement assembly, MIDI/drum-groove build,
      sound-design chain, import/normalize, mix-prep.
- [ ] Batch: manifest + resume (exists) extended to arbitrary recipes;
      `needs_human` handling for handoffs in batch.
- **Exit:** ≥3 non-mastering recipes run end-to-end; batch resume proven on a
  handoff-containing manifest.
- **Verify:** run diffs + logs; one scripted end-to-end example per recipe.

### W6 — Verification, tests, safety
- [ ] Checked-in golden scratch set (or a bootstrap recipe that generates it).
- [ ] Opt-in **live** smoke suite (skipped without a running Live).
- [ ] Snapshot-diff regression: recipe run vs recorded expectation.
- [ ] Preflight: plugin presence, Ableton liveness, project loaded.
- [ ] Rollback drill on a disposable copy.
- **Exit:** `pytest tests/` green offline; live suite green when opted in;
  rollback documented and exercised.
- **Verify:** the suites themselves.

### W7 — Packaging and docs
- [ ] `build_automation_env.sh`: whitelist `docs/CHANNEL_MATRIX.md` (and any new
      runtime docs); confirm `automation/als/` and `channels.py` ship.
- [ ] Reconcile `README.md`, `AUTOMATION_AGENT_POLICY.md` (→ runtime `AGENTS.md`),
      and the repo `AGENTS.md` with the LOM → ALS → UIA → handoff ladder and the
      `channels` command.
- **Exit:** a fresh runtime folder built from the repo can do the documented jobs.
- **Verify:** run the build; grep the runtime for stale claims.

### Future channel — Extensions SDK (trigger-gated)
- **Trigger:** Live upgraded to **12.4.5+** **and** Suite **and** Centercode Beta
  enrollment.
- **Then:** event hooks, transaction-level undo, deep integration beyond the LOM.
- **Not now:** unavailable on 12.1; the upgrade would **not** unlock GUI-only
  plugins (`insertDevice` is built-in-only). Do not gate the roadmap on it.

---

## 4. Sequencing

| Milestone | Contents | Why this order |
|---|---|---|
| **M1** | W1 (LOM coverage) + W7 partial | Converts fragile UIA to LOM; unblocks the rest |
| **M2** | W2 (plugin coverage) + W3 (ALS hardening) | Makes device control broad and reliable |
| **M3** | W4 (export seam) + W5 (recipes/batch) | Delivers end-to-end outcomes |
| **M4** | W6 (verification/hardening) + W7 finish | Makes it durable and shippable |

W1 and W2 can run in parallel by different sessions; W7's doc pass should trail
each milestone, not wait for the end.

---

## 5. Success criteria

- The matrix has no *unresolved* `requires: Remote Script extension` row among
  session-control jobs (implemented or explicitly deferred with a reason).
- Every installed LOM-capable plugin is drivable by name with read-back; every
  GUI-only plugin has a one-command unlock.
- A non-mastering outcome (e.g. "build an 8-bar drum groove and render it")
  completes end-to-end.
- Every mutating run is verified numerically and leaves a `RUNS/<id>/` artifact.

---

## 6. Out of scope (documented, not chased)

- SDK-dependent features until the trigger fires.
- UIA automation of the Export dialog — handoff is the deliberate choice.
- Real-time DSP / live signal processing (Max for Live is a different lane).
- Teaching/tutoring content (archived under `docs/teaching/`).

---

## 7. Open decisions

| # | Decision | Default if unanswered |
|---|---|---|
| D1 | Autonomy for destructive batch (confirmation gate before render/save?) | Require snapshot + dry-run; gate before render |
| D2 | Which plugins to profile first | Ozone components + FabFilter Pro-Q 4 / Pro-C 3 / Pro-L 2 |
| D3 | Upgrade Live for the SDK? | No — not until a use case demands event hooks/true undo |

---

## Appendix — relationship to the old plan

`AUTOMATION_PLAN.md` (the pivot draft) was written before the facts landed. Its
thesis (invert the ladder, partial automation is valid, LOM-first) survives here.
Its phase table, "0 plugins" and "Arrangement incomplete" claims, and its
SDK/render assumptions are **stale** and are replaced by this roadmap and the
measured `docs/CAPABILITY_MATRIX.md`. The inventory and design detail in the old
file remain in git history; the operational summary lives in `docs/SYSTEM_MAP.md`.
