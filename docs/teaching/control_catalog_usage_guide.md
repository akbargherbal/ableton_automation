# Using `control_catalog.json` — Reference Guide

Analysis based on the current survey pass (`mapping-ableton`, see `coverage_summary.md` and `survey_checklist.md` for the live record):
105 contexts, 97 MAPPED / 6 UNMAPPED / 2 OPAQUE.

---

## 1. What this file actually is (and isn't)

**Is:** A static, offline index that answers one question: *"Does this
part of Ableton's UI have a stable identifier (`automation_id`) the
agent can click on with confidence?"* — for every device and view that
was surveyed.

**Isn't:** An executor. It doesn't click anything, doesn't open
Ableton, doesn't know your project's current state. It's a design/risk
reference to consult **before** writing a lesson, not while running one.

---

## 2. Direct practical uses (no Ableton required)

### A. Feasibility screening before writing any lesson
Run `check_lesson_coverage.py` (from the earlier session) against any
planned lesson step → get back MAPPED / PARTIAL / GAP immediately.
Saves hours of writing content for a lesson that turns out to be
partly unbuildable.

### B. Curriculum build-order prioritization
Contexts marked MAPPED are the cheapest to build on (less verification
needed, less risk). Start there. UNMAPPED/OPAQUE areas should be
deferred, or designed from the start around human-instruction fallback
(Level 4) rather than waiting on a technical fix.

### C. Safety/risk reference (the most important one)
Any context with status **OPAQUE** is an explicit red flag. You
currently have two (`Groove Pool`, `Info View`) — and `Groove Pool` is
confirmed to actually crash Ableton (documented in
`coverage_summary.md`). **Any future lesson touching these areas needs
an explicit rule blocking it**, independent of any later technical fix.

### D. Quick lookup reference for a developer (you, or a future agent)
Writing a new `task_` function in `automate_ableton_task.py`? Search
the catalog for the right `automation_id` instead of opening Ableton
and exploring manually.

---

## 3. Its limits — what it can't do

- **No coordinates (`bounding_rect`) or per-control interaction
  patterns** — those live only in the raw `scripts/dumps/device_*.json`
  files, not the merged catalog. Go back to the raw files if you need
  them.
- **A static snapshot at a point in time** — if Ableton updates
  (new version) or your project changes (track names, scene count),
  the catalog can drift out of accuracy.
- **Doesn't cover everything** — File menu items (`Export`, `Freeze`,
  `Flatten`, `Collect All and Save`) and the Preferences dialog were
  **never surveyed at all** (zero hits on search) — not because they're
  impossible, but because menus don't expose their items until actually
  opened, and that was outside this survey's scope entirely.

---

## 4. Full feasibility map — all 7 modules (20 hours)

Built from actual searches against the catalog, not guesswork.

| # | Module | Overall verdict | Details |
|---|---|---|---|
| 1 | Intro to Ableton (2h) | 🟡 PARTIAL | Session View basics: strongly **MAPPED**. Browser chrome (search/filters): MAPPED, but **selecting a file by name = confirmed GAP**. "New Live Set" and Preferences: **never surveyed at all** (menus weren't opened during the scan). |
| 2 | Working with Audio (3h) | 🟠 Weakest module | Warp controls exist, but only inside the Simpler device (sample-level warping), **not** in ordinary audio-clip editing (Clip Detail's Phase F summary doesn't mention Warp at all). Needs direct verification or should be designed around Level 4 from the start. |
| 3 | MIDI & Instruments (3h) | 🟢 Mostly strong | Drum Rack, Simpler, Instrument Rack: **fully MAPPED** (Phase A). Quantize: **MAPPED** (109 hits, global menu). Piano Roll: partial via Clip Detail (NoteTools present, fine-grained detail unconfirmed). Browser Sounds: **GAP**, same issue as Module 1. |
| 4 | Creative Editing & Arrangement (3h) | 🟢 Strong | Arrangement View: **fully MAPPED**, richly detailed (Phase D). Automation Mode: **MAPPED**. Follow Actions: **MAPPED at the global level** (enable/disable); per-clip settings unconfirmed. |
| 5 | Effects & Sound Design (3h) | 🟢 Strongest by far | EQ Eight, Compressor, Reverb, Delay/Echo, Saturator, Utility, Limiter, Glue Compressor — **all MAPPED** (Phase A covered them explicitly by name). Best module to start with if you resume. |
| 6 | Mixing Essentials (3h) | 🟢 Strong | Volume/Pan/Sends: **MAPPED** (recurs in every context). Return Tracks: **MAPPED**. Group Tracks: **MAPPED** (with a documented structural difference: no Arm/Input Type). Spectrum device: **MAPPED**, exists as a real Ableton device. |
| 7 | Final Project & Export (3h) | 🔴 Weakest | Freeze Track: **GAP** (zero real hits). Flatten: **GAP** (zero). Export Audio/Video: **GAP** (zero). Collect All and Save: possibly partial via `section:File-Manager` (contains a `ManageSet` id), but not confirmed to be the same command. **This module specifically needs a focused re-survey if you come back — not a full re-scan, just this.** |

### Visual summary
```
Strong (start here if resuming):    Module 5 > Module 6 ≈ Module 4 > Module 3
Weak (needs more work):             Module 1 (Browser) > Module 2 (Warp) > Module 7 (whole thing)
```

---

## 5. Quick checklist for whenever you come back

- [ ] Start with Module 5 (strongest coverage) as the first full proof-of-concept lesson.
- [ ] Before Module 7, do a small **focused** survey of just the File
      menu items (Export, Freeze, Flatten, Collect All) — a narrow scope,
      not a full re-scan.
- [ ] Before Module 1/3 (Browser), test the "live name-based tree walk"
      hypothesis on one simple example before generalizing it.
- [ ] ~~Add an explicit rule to `ABLETON_AGENT_POLICY.md` blocking Groove
      Pool~~ — moot: that file was a placeholder and has been deleted
      (2026-08-27, this course has no policy file currently). The Groove
      Pool guard now belongs to the mastering course; see `PHASED_PLAN.md`
      Phase 0 in the repo root for the actual code-level fix
      (`scripts/keyboard_shortcuts.py`).
