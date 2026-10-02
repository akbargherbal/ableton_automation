# Phased Plan — Resolve the Unknowns, Unlock the Gates

**Status:** Phases 0–5 complete — Gates A, B, B2, C all GO; **product roadmap is
now `ROADMAP.md`** (this discovery plan is a completed record).
**Date:** 2026-10-02
**Purpose:** This is a *discovery / de-risking* plan, not the product plan. It is
sequenced to (a) answer every open question cheaply, (b) open the gates we can
open at low cost, and (c) isolate the one load-bearing unknown behind a single
explicit go/no-go. The real product roadmap is written in **Phase 5**, after the
facts are in.

**Supersedes:** `AUTOMATION_PLAN.md` (its Phases 0–6 are largely built; see §1).
**Companion:** `docs/CAPABILITY_MATRIX.md` (live-measured, authoritative).

---

## Resume here (next session)

**Done:** Phases 0, 1, 2, 3. Gates **A, B, B2, C all PASSED/GO**.
Committed: `ableton_automation` @ `bb5aa67`; MCP Remote Script @ `a8212fe`.

**Phase 3 shipped the `.als` channel as a package:**
- `automation/als/read.py` — parse/inspect/diff (promoted from `scripts/als_probe.py`).
- `automation/als/configure.py` — surgical copy-only exposure writer (backup +
  SHA-256 + atomic replace + re-parse validation), wired to `plugin_profiles`
  declared-name profiles.
- `automation/als/snapshot.py` — hashed whole-file backup/restore + guided
  close-swap-reopen handoff.
- `driver`: LOM → ALS → UIA ladder — `ChannelUnavailable` carries per-channel
  availability; `Driver(offline=True)` supports the offline channel without a
  live socket; `als_info/als_devices/als_configure/als_snapshot/als_restore`.
- CLI: `automation.run als-info | als-devices | als-configure | als-snapshot |
  als-restore`. `tests/test_als.py` (32 tests total pass).

**Gate C verified end-to-end (2026-10-02):** `als-configure` on `AASHA.als`
resolves `Band 2 Gain` → declared index **26** into free slot **8**
(`exposed 0→1`, 2 bytes changed). Opened the copy in Live via the new UIA
`open_set` task (Ctrl+O → type path → Enter); Pro-Q 4's LOM `parameter_count`
went **1 → 2** (`Device On`, `Band 2 Gain`), and `driver.set_param` drove it:
`+2.18 dB` (0.5363) → `0.75` → read-back **`+15.00 dB`**. The live ladder was
also confirmed separately (`set_param` on a fresh Pro-Q 4 raises
`ChannelUnavailable` with `als.available = true`). **Caveat:** a save-changes
prompt for the untitled current set preceded the Open dialog and was dismissed by
the operator; `open_set` now aborts on such a prompt unless `discard_unsaved` is
explicitly set (that auto-discard branch is coded but not yet live-verified).

**ALL DISCOVERY PHASES DONE.** The product plan is `ROADMAP.md` (W1–W7 + the
trigger-gated SDK future channel), built on `docs/CHANNEL_MATRIX.md`. Next
implementation session: start at **`ROADMAP.md` W1 (Remote Script extension
pack)** — it is the highest-leverage work and needs a full Ableton restart.

**Operational facts to remember:**
- The Remote Script Live **actually loads** is
  `C:\Users\DELL\OneDrive\Documents\Ableton\User Library\Remote Scripts\AbletonMCP\__init__.py`
  (Documents is OneDrive-redirected; the `%APPDATA%` copy is a decoy).
- Editing a Remote Script needs a **full Ableton restart** (reopening the set is not
  enough).
- The name→index mapping comes from `LomClient.get_parameter_names()` (Live must be
  running); index = position in Pro-Q 4's 737-name list.
- The `.als` writer edits a **copy**; ensure Live does not have that file open.
- Test artifact `AASHA_exposed_test.als` sits in the AASHA project folder — safe to
  delete.

---

## Status log (2026-10-02)

- **Phase 5 done (2026-10-02)** → `ROADMAP.md` (product roadmap: W1 Remote Script
  extension pack, W2 plugin coverage, W3 ALS hardening, W4 render seam, W5
  recipes/batch, W6 verification, W7 packaging; SDK as trigger-gated future).
  `AUTOMATION_PLAN.md` reduced to a superseded stub; `README.md`,
  `AUTOMATION_AGENT_POLICY.md`, repo `AGENTS.md`, `SYSTEM_MAP.md`,
  `CAPABILITY_MATRIX.md`, and `build_automation_env.sh` reconciled.
- **Phase 4.1 + 4.3 done (2026-10-02).** 4.1: `.als` writer verdict = **built
  bespoke** (`automation/als/`, stdlib-only; rationale in `ALS_FINDINGS.md` §5).
  4.3: export/render = **guided handoff** (`export_audio` prepare/verify); UIA
  dialog automation explicitly not pursued.
- **Phase 4.2 done (2026-10-02)** → `docs/CHANNEL_MATRIX.md` +
  `automation/channels.py` (`automation.run channels`). Every job mapped to a
  primary channel and fallbacks; `*` = measured. Backbone for the Phase 5 roadmap.
- **Phase 3 COMPLETE — GATE C = GO (2026-10-02).** Built the `automation/als/`
  package (`read`, `configure`, `snapshot`), wired `plugin_profiles` to saved
  declared-name profiles, added the LOM → ALS → UIA ladder to `driver`
  (`ChannelUnavailable`, `Driver(offline=True)`), and exposed five CLI commands.
  Offline proof on `AASHA.als`: `Band 2 Gain` → index 26, slot 8, `exposed 0→1`.
  Added a UIA `open_set` task (Ctrl+O → path → Enter); reopening the copy made
  Pro-Q 4 `parameter_count` go **1→2** and `set_param` drove `Band 2 Gain`
  `+2.18 dB` → `0.75` → **`+15.00 dB` read-back**. Live ladder also confirmed
  (`set_param` on a fresh Pro-Q 4 raises `ChannelUnavailable`, `als.available`).
  Tests: `tests/test_als.py` (all 32 pass).
- **Phase 0.1 done** → `docs/SYSTEM_MAP.md`.
- **Phase 0.2 done** → `docs/SDK_DECISION.md` (SDK reconfirmed beta-only, 12.4.5).
- **Phase 0.3 done** → writer mechanism extracted (subagent brief; folded into
  `docs/ALS_FINDINGS.md` §4). Build-vs-buy call: **build bespoke** `automation/als/`.
- **Phase 1 read done** → `docs/ALS_FINDINGS.md`, `scripts/als_probe.py`,
  `automation/profiles/als/forensics.json`. **GATE B (read level): PASSED.**
- **Phase 2 COMPLETE — GATE B2 = GO (2026-10-02).** Built
  `scripts/als_configure.py` (surgical, never-reserialize, copy-only, re-parse
  validated) and added the `get_parameter_names` command to our Remote Script
  (`~/ableton-mcp-extended`). Pro-Q 4's declared list = **737** names;
  `Band 2 Gain` = index 26. Exposing it in a copy made LOM `parameter_count`
  1→2 and the parameter drivable (`+2.18 dB` → `+15.00 dB`). The original set was
  untouched. The `.als` channel for GUI-only plugins is **real on 12.1**.
- **Phase 0.4 done** — answers below.

### Phase 0.4 answers (2026-10-02)

| Q | Answer | Consequence |
|---|---|---|
| **Q1 objective** | **General-purpose**: "I want to do this thing in Ableton; agent does it for me — anything doable." | Phase 5 roadmap must be **capability-general**, not a mastering pipeline. Coverage matrix drives it. |
| **Q4 workflow** | **Hybrid**: LOM live + `.als` offline | The planned architecture is confirmed; keep both channels first-class. |
| **Q5 rollback** | **Yes** — close Live & swap backup is fine | `.als` snapshot/restore is an accepted safety model. |
| **Q9 export** | **Guided handoff** is fine | No need to automate the Export dialog; keep it as `handoff`. |

**Q1 changes the framing:** the old `AUTOMATION_PLAN.md` optimized for Suno
batch mastering. The new roadmap must instead maximize *general* capability: for
each "thing doable in Ableton", which channel does it (LOM / `.als` / UIA /
handoff), and what is still impossible. The channel-selection matrix (Phase 4.2)
becomes the backbone of Phase 5.

## 1. Ground truth as of this plan (verified 2026-10-02)

- **Live is 12.1**, Build `2024-09-25_bba251b1d9`, on Windows 11 Pro 25H2.
- **Extensions SDK is still public beta for Live 12.4.5 only** (re-checked live
  during this plan's drafting). Not available on 12.1. Off the table unless
  upgraded *and* enrolled in the Beta Program.
- **The automation spine already exists** — `automation/` contains
  `driver.py`, `lom.py`, `uia.py`, `state.py`, `verify.py`, `lock.py`, `log.py`,
  `batch.py`, `handoff.py`, `plugin_profiles.py`, `recipes/` (import_audio,
  export_audio, set_tempo, device_report), `analysis/measure.py`. The old plan's
  Phases 1–5 are substantially done.
- **No `.als` code exists anywhere** — grep for `gzip|PluginDevice|ParameterId|
  VisualIndex|als_read|als_write` finds only `PluginDevice` as a *device_class
  string* in probe JSON. The `.als` channel is greenfield.
- **GUI-only plugins confirmed live:** Ozone 12 Equalizer (1 param), Ozone 12
  Dynamics (1), Pro-Q 4 (1), Pro-C 3 (1). LOM-capable: EQ Eight (84), Ozone
  Maximizer (20), Vintage Limiter (13), Pro-L 2 (17).
- **Objective (confirmed Phase 0.4):** **general-purpose** — "I want to do this
  thing in Ableton; the agent does it for me — anything doable." The old Suno
  mastering framing is superseded (kept only as a former example).

### Evidence tiers used below
- **Measured** — read from the user's machine/repo this session.
- **Read** — taken from a repo doc or source file.
- **Claimed** — a web/community assertion, *not yet verified locally*.
The `.als` Configure mechanism is currently **claimed** (live-maestro, measured
on 12.4.5, never on 12.1/Windows). Phase 2 exists to convert that to *measured*.

---

## 2. Question → Phase index

| # | Open question | Answered in |
|---|---|---|
| Q1 | What outcome(s) are we automating? | Phase 0.4 (confirm) / Phase 5 |
| Q2 | Does the `.als` Configure trick work on 12.1/Windows? | **Phase 1 (read) + Phase 2 (write)** |
| Q3 | Repo inventory, topology, provenance? | Phase 0.1 |
| Q4 | Offline-first or live-session-first? | Phase 0.4 / Phase 5 |
| Q5 | Is "close–swap–reopen" acceptable rollback? | Phase 0.4 |
| Q6 | Is the SDK stable / do we want to upgrade? | Phase 0.2 (status) + 0.4 |
| Q7 | Do Configure params expose the *meaningful* controls? | Phase 1.2 / Phase 2.3 |
| Q8 | Build vs. port vs. adopt the `.als` writer? | Phase 0.3 + Phase 4.1 |
| Q9 | Is a UI/handoff render path acceptable? | Phase 0.4 + Phase 4.3 |

---

## Phase 0 — Ground-truth sweep (read-only, zero risk)

**Goal:** close every question that costs nothing to close, and scope the one
that costs something.

- [x] **0.1 System map.** DONE → `docs/SYSTEM_MAP.md`. Covers:
  - `automation/` module inventory: what is implemented vs. stubbed.
  - Topology: relationship between the `AbletonMCP` server, `automation.lom`,
    and the Remote Script socket (`localhost:9877`, `~/ableton-mcp-extended`).
    Are these one fork, or two?
  - Provenance: is `~/ableton-mcp-extended` a fork of `ahujasid/ableton-mcp`?
    (drives the build-vs-adopt call in Phase 4).
  - **Answers Q3.**
- [x] **0.2 SDK status + upgrade tradeoff.** DONE → `docs/SDK_DECISION.md`.
  current status (beta, 12.4.5, Centercode, Suite), the exact capability delta,
  and the explicit finding that **the upgrade would *not* unlock GUI-only
  plugins** (`insertDevice` is built-in-only; same exposed param strip). Record
  the recommendation: do not upgrade for the SDK alone.
  - **Answers Q6.**
- [x] **0.3 Read the `.als` writer sources** — DONE; mechanism in
  `docs/ALS_FINDINGS.md` §4. live-maestro's `als_read`/
  `als_write`, `kevinkirsten/ableton-als`, `offlinemark/dawtool`. Extract the
  *actual* Configure mechanism (node names, slot count, ID semantics) and what is
  portable to Python on Windows. Produce `docs/ALS_CHANNEL.md` with a provisional
  build-vs-port-vs-adopt recommendation.
  - **Answers Q8 (provisional).**
- [x] **0.4 Decision questionnaire to the user** — DONE (answers above):
  (no tech dependency; can be answered in parallel with 0.1–0.3):
  - Q1 — confirm the objective (Suno batch mastering?) and whether general
    production is in scope.
  - Q4 — offline-first (edit file, open, render) or live-session-first?
  - Q5 — is recovery-by-closing-Live-and-swapping the `.als` acceptable?
  - Q9 — is a UI/handoff export path acceptable, or must export be unattended?

**Deliverables:** `docs/SYSTEM_MAP.md`, `docs/SDK_DECISION.md`,
`docs/ALS_CHANNEL.md`, and the user's questionnaire answers.
**Cost:** ~hours, read-only. **Risk:** none.

**GATE A — proceed if:** the `.als` mechanism in 0.3 is concrete enough to test
(it should be), and Q1 is confirmed or strongly assumed.

---

## Phase 1 — `.als` read-only forensics (zero risk)

**Goal:** convert the Configure claim to *measured* at the read level, on a real
12.1 set. Nothing is written.

- [x] **1.1 Obtain a target set.** DONE — 9 local sets found; 3 carry a plugin
  (Pro-Q 4, Ozone 12 ×2). A saved Live 12.1 project containing at least
  one GUI-only plugin (Pro-Q 4 or Ozone 12 Equalizer). Either an existing set or
  a purpose-built scratch set. Set is **closed** in Live; work on a *copy*.
- [x] **1.2 Parse it with the Python stdlib only** (`gzip` + `xml.etree`). DONE:
  - Locate the `PluginDevice` node for the target plugin.
  - Enumerate the parameter-slot nodes; capture `ParameterName`, `ParameterId`,
    `VisualIndex`, slot count.
  - Compare the slot count to the live LOM count (expect 1). This is the first
    hard test of the whole premise.
- [x] **1.3 Characterize the plugin state blob.** DONE — opaque hex
  `ProcessorState` (~636 KB). is it XML, base64, or opaque
  binary? (Tests the "opaque blob" assumption; if parseable, it reorders
  strategy.)
- [x] **1.4 Differential probe.** DONE — 3 plugin sets cross-compared (all 128
  slots / 0 exposed). The "positive control" became unnecessary once
  `get_parameter_names` supplied the declared index list; the write proof in
  Phase 2 then confirmed the mechanism. See `docs/ALS_FINDINGS.md` §7.

**Deliverables:** `automation/profiles/als/<device>.json`,
`docs/ALS_FINDINGS.md`.
**Answers:** Q2 (read half), Q7 (structure).
**Cost:** ~hours. **Risk:** none (copies only).

**GATE B — PASSED (read level, 2026-10-02).** Live 12.1 exposes 128 named
`PluginFloatParameter` slots per instance with `ParameterId`/`VisualIndex` unset
markers identical to the community writer's model. Proceed to Phase 2.

---

## Phase 2 — `.als` controlled write proof (the one decisive gate)

**Goal:** prove or disprove that a written mapping produces a working, LOM-
drivable parameter on reopen. This is the pivot's load-bearing gate. Done on a
**throwaway set**, Live closed for the edit.

- [x] **2.1** Create scratch set: one track + one GUI-only plugin, save, quit.
- [x] **2.2** `state.backup_set()` a copy; hash it. Inject one known mapping
  (e.g. Pro-Q 4 band frequency) into the slot list.
- [x] **2.3** Reopen in Live; read via LOM. Success = the injected parameter now
  appears (`parameter_count` > 1) and `driver.set_param` changes it.
- [x] **2.4** Round-trip: set a value → save → reopen → confirm persistence.
- [x] **2.5** Corruption study, **on disposable copies only**: what does Live do
  with a malformed edit? Record the failure mode so the real module can guard
  against it.

**Deliverable:** a minimal `automation/als/` prototype + a `RUNS/<id>/` report
with before/after evidence.
**Answers:** Q2 (write half), Q7 (fully).

**GATE B2 (GO/NO-GO for the pivot) — RESULT: GO (2026-10-02).**
- **GO** → the `.als` channel is real on 12.1; proceed to Phase 3.
- **NO-GO** → document precisely why; the GUI-only gap has no deterministic
  unlock on this version, and the product roadmap must plan around UIA/handoff.

---

## Phase 3 — Open the cheap gates (only after GATE B2 = GO)

**Goal:** turn the proven mechanism into a safe, reusable capability and take the
easy wins it unlocks.

- [x] **3.1 `automation/als/read.py`** — parse + diff, no writes. DONE.
  Full-fidelity snapshots *without* the DAW open, offline inspection, and a real
  `.als` `diff()` keyed on devices/slots to complement the shallow LOM capture.
- [x] **3.2 `automation/als/configure.py`** — deterministic exposure injection
  (`resolve_exposures` maps declared names → free slots + `ParameterId`), with
  backup + SHA-256 + atomic replace + re-parse validation. Wired into
  `plugin_profiles` (`declared_parameter_names`, `declared_parameter_index`).
- [x] **3.3 LOM → ALS → UIA ladder** in `driver`. `set_param` still tries LOM
  first; a GUI-only device raises `ChannelUnavailable` carrying per-channel
  availability (`describe_channels`). `Driver(offline=True)` runs the offline
  channel without a live socket. `SetValue()` stays banned; read-back verified.
- [x] **3.4 Snapshot/restore** — `automation/als/snapshot.py`: hashed whole-file
  backup, atomic restore (refuses while Live's socket is open unless forced),
  and `restore_handoff()` for the quit-Live → swap → reopen model.

**Deliverable:** `automation/als/` package + driver integration + CLI + tests.
**Answers:** the *practical* form of Q5 (rollback UX).

**GATE C — GO (2026-10-02), driven end-to-end.** Offline: `als-configure`
resolves Pro-Q 4 `Band 2 Gain` to declared index 26 / free slot 8 on a copy of
`AASHA.als` (`exposed 0→1`). Live: the new UIA `open_set` task reopened the copy;
LOM reported `parameter_count` 1→2 and `driver.set_param` set `0.75`, read back as
`+15.00 dB` (was `+2.18 dB`). The `.als` channel is now the first-class offline
actuator for GUI-only plugins; `open_set` closes the reopen loop. (Phase 2 did
this by hand; Phase 3 makes it deterministic and agent-runnable.)

---

## Phase 4 — Settle the architecture decisions

**Goal:** close the remaining "how", informed by Phases 1–3.

- [x] **4.1 Build vs. port vs. adopt** — **BUILT BESPOKE**, shipped as
  `automation/als/` (Phase 3). Verdict table + rationale in
  `docs/ALS_FINDINGS.md` §5. Chosen because it is stdlib-only (`gzip` +
  `xml.etree`), adds no runtime/dependency, is Windows-testable, and matches the
  `automation/` package; the alternatives are a large MCP product (live-maestro),
  macOS-measured JS that does not expose params (kevinkirsten), or read-only
  (dawtool). Proven by Gates B2 and C — no revisit needed.
- [x] **4.2 Channel-selection matrix** — DONE → `docs/CHANNEL_MATRIX.md`,
  backed by `automation/channels.py` (machine-readable registry + `validate()`),
  CLI `automation.run channels [--job/--channel/--json]`, tests
  `tests/test_channels.py`. 43 jobs across 8 areas; 21 measured (`*`).
  Rules of thumb: LOM first; ALS before UIA for GUI-only params; handoff is a
  valid outcome; extend the Remote Script before clicking; verify numerically.
- [x] **4.3 Export/render decision** — **GUIDED HANDOFF** (per Q9). There is no
  render API in the LOM or `.als`; the Export dialog is modal and
  version-sensitive, so it is a first-class handoff, not an automation target.
  Reference: `automation/recipes/export_audio.py` (`stage=prepare` emits the exact
  dialog settings via `handoff.export_audio_handoff`; `stage=verify` waits for the
  file and measures it) + `automation.run guide`. `automation.run keys ^+r` is an
  optional accelerator; unattended export stays disallowed. UIA automation of the
  dialog is explicitly **not** pursued.

---

## Phase 5 — Write the product roadmap (the original ask)

**Goal:** now that facts are known, rewrite the real implementation plan.
**DONE (2026-10-02)** → `ROADMAP.md` (product roadmap, W1–W7 + SDK trigger).

- [x] Replaced `AUTOMATION_PLAN.md`'s stale sections with **`ROADMAP.md`**, built
  on the channel-selection matrix and targeting the confirmed general objective
  (Q1). `AUTOMATION_PLAN.md` is now a superseded stub (full text in git history).
- [x] Re-baselined against **Live 12.1** (Windows); no 12.4.5-derived finding is
  load-bearing. Stale claims (0 plugins, Arrangement incomplete) removed.
- [x] SDK folded in as a **trigger-gated future channel** (`ROADMAP.md` W-future):
  activation requires Live 12.4.5+ **and** Suite **and** Centercode; not a
  dependency, and the upgrade would not unlock GUI-only params.
- [x] Reconciled `README.md`, `AUTOMATION_AGENT_POLICY.md` (→ runtime `AGENTS.md`),
  and the repo `AGENTS.md`; `build_automation_env.sh` whitelists
  `docs/CHANNEL_MATRIX.md`.

---

## Decisions needed from you (can answer any time)

| Q | Decision | Why it gates |
|---|---|---|
| Q1 | Confirm objective: Suno batch mastering only, or general production too? | Sizes Phase 5 |
| Q4 | Offline-first (edit file → open → render) or live-session-first? | Architecture |
| Q5 | Is close-Live-and-swap-`.als` acceptable as rollback? | Safety model |
| Q9 | Is a UI/handoff export path acceptable? | Only route to a deliverable |

---

## Gates we cannot open cheaply (document, do not chase)

| Gate | Why closed | Trigger to revisit |
|---|---|---|
| Extensions SDK | Beta, Live 12.4.5+, Suite, Centercode | User upgrades + enrolls |
| Export/render via API | No render API in LOM or `.als` | Phase 4.3 decision (UI/handoff) |
| True undo across channels | LOM has none; SDK would (unavailable) | `.als` snapshot restore is the substitute |
| Third-party plugin *insertion* | Built-in-only everywhere | Not needed if presets/`.als` used |
| Real-time / signal processing | Different lane (Max for Live) | Only if a use case demands it |

---

## Phase 2 prerequisites & procedure (COMPLETED — reference only)

> Phase 2 is done and Gate B2 = GO. Kept so the next session can see how the
> write proof was set up.

To run the decisive write proof we need:

1. A **scratch Live set**: one audio track + one GUI-only plugin (Pro-Q 4 first),
   saved as a throwaway `.als`.
2. A **positive control**: one LOM-capable plugin (Ozone 12 Maximizer, 20 params)
   saved, so we can see what a *configured* slot looks like in the file.
3. **Live closed** on the scratch set (the writer refuses to edit a running Live).
4. Phase 0.4 answers.

Procedure (all reversible):

- `python3 scripts/als_probe.py devices <scratch>.als` → baseline.
- Back up + SHA-256 the file (mirror live-maestro's guard).
- Fill `ParameterName` / `ParameterId` / `VisualIndex` on 1–2 slots only.
- Reopen in Live; read back via LOM (`parameter_count`, `set_device_parameter`).
- Round-trip: set value → save → reopen → confirm persistence.
- Corruption study on disposable copies only.

## Done so far (updated 2026-10-02)

**Phases 0–5 complete; Gates A, B, B2, C PASSED/GO.** Phases 0–3 committed in
`ableton_automation` @ `bb5aa67` and the MCP Remote Script @ `a8212fe`; Phases 4–5
(4.1/4.2/4.3 + roadmap) are the current uncommitted work. Next actions are in
**`ROADMAP.md`** (W1 onward); this file is now a completed record.
