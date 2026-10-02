# `.als` Findings — the offline channel on Live 12.1

**Verified:** 2026-10-02 on real Live 12.1 sets, plus the community writer source.
**Phase 1 deliverable** of `PHASED_PLAN.md`; answers Q2 (read half) and Q7.

> **Gate B (read): PASSED.** Live 12.1 produces exactly the parameter-slot array
> the exposure mechanism depends on.
> **Gate B2 (write): PASSED (2026-10-02).** On a throwaway copy, exposing
> `Band 2 Gain` (declared index 26, from `get_parameter_names`) made it appear to
> the LOM and controllable: `+2.18 dB` → set → `+15.00 dB`.

## 0. Verified end-to-end (2026-10-02)

The full GUI-free pipeline works on Live 12.1 / Windows:

1. `LomClient.get_parameter_names(track, device)` → Pro-Q 4's **737** declared
   parameter names; `Band 2 Gain` = index **26**.
2. `scripts/als_configure.py` writes `ParameterName`/`ParameterId=26`/
   `VisualIndex=0` into empty slot 8 of a **copy** of `AASHA.als` (surgical,
   `exposed` 0→1 in the file).
3. Reopen the copy in Live → Pro-Q 4 `parameter_count` goes **1 → 2**:
   `Device On`, `Band 2 Gain`.
4. `set_device_parameter("Band 2 Gain", 0.75)` → read-back `+15.00 dB`.

The original `.als` was never modified. Declared names are saved to
`automation/profiles/als/Pro-Q-4_parameter_names.json`.

## 1. Container and schema

- An `.als` is a **gzip-compressed UTF-8 XML** document.
- Header (real 12.1 file): `<Ableton MajorVersion="5" MinorVersion="12.0_12120"
  Creator="Ableton Live 12.1" Revision="bba251b1d93c8c617204c1398fbaba1f4dd3b9f5">`.
  The Revision matches the running build — so both the file and the app are
  from the same 12.1 build.
- Example: `sabeel_almajd.als` = 340,025 bytes compressed → 894,866 bytes XML.

## 2. The parameter-slot array

A `<PluginDevice>` contains `<ParameterList>` with **exactly 128
`<PluginFloatParameter>` slots** (Live allocates them up front, per instance).
Each slot:

| Field | Meaning |
|---|---|
| `ParameterName` | display name of the parameter |
| `ParameterId` | plugin parameter index; **`-1` = unset / not exposed** |
| `ParameterIdFlankBool` | not used for exposure |
| `VisualIndex` | strip position; **`1073741823` (2³⁰−1) = unset / not exposed** |
| `ParameterValue` → `Manual` | stored value (real units, not normalized) |
| `LastUserRange` / `LastInternalRange` | display ranges |

**Unset markers:** `ParameterId == -1` and `VisualIndex == 1073741823`.

The plugin's own state is a single opaque hex blob: `ProcessorState` was
**635,706 hex chars** in the Ozone 12 set. It is **not** needed for exposure and
is not human-editable — this is why editing the plugin's sound directly is out.

## 3. What the local sets actually contain

Probed with `scripts/als_probe.py batch`:

| Set | Plugin | Slots | Exposed (`ParameterId != -1`) |
|---|---|---|---|
| `AASHA.als` | FabFilter Pro-Q 4 | 128 | **0** |
| `sabeel_almajd.als` | iZotope Ozone 12 (monolith) | 128 | **0** |
| `amro_sal.als` | iZotope Ozone 12 (monolith) | 128 | **0** |

All three are plugins the LOM also classifies as GUI-only, and the file agrees:
**0 exposed**. This is the first local confirmation that the file's exposure
state matches the LOM's behaviour.

**Notable nuance:** "not exposed" does **not** imply empty names, and the shape
varies by plugin:

- **Ozone 12** (`sabeel`): **61 of 128 slots named**, many with real values
  (e.g. `EQ: Stereo/Main Frequency 1` = 200); 67 empty. Every `ParameterId = -1`.
- **Pro-Q 4** (`AASHA`): **8 of 128 slots named** — `Band 2 Gain`,
  `Band 2 Frequency`, `Band 1 Enabled`, `Band 3 Threshold`, `Band 3 Used`,
  `Band 3 Side Chain Low Frequency`, `Band 3 Side Chain High Frequency`,
  `Band 3 Spectral Tilt`; 120 empty. Only `Band 2 Gain` (2.176…) and
  `Band 2 Frequency` (11.98…) hold real values; the rest are the placeholder
  `0.1234567687`. Every `ParameterId = -1`.

This matters because live-maestro's writer treats an **empty `ParameterName`** as
the free slot to fill — so it would work on Pro-Q 4's 120 empty slots, but must
target specific slots on Ozone. Exposure is keyed purely on
`ParameterId` / `VisualIndex`.

## 4. The exposure mechanism (how the community does it)

From `live-maestro` `src/live_maestro/als/write.py` (`configure_plugin_parameters`)
and `docs/limits.md` §3 — the "Configure" analog done offline:

- It fills **exactly three attributes** on **already-existing** slots — nothing
  is inserted:
  1. `ParameterName` → non-empty display name,
  2. `ParameterId` → the **real plugin parameter index** (e.g. `"17"`), replacing `-1`,
  3. `VisualIndex` → a **unique** strip position, not `1073741823`.
- **Nothing else is touched**: not `ProcessorState`, `ParametersListWrapper`,
  `Pointee`, `ParameterIdFlankBool`, `LomId`, `AutomationTarget`,
  `ModulationTarget`, or `Manual`/`MidiControllerRange`.
- It takes effect only on **reopen/restart** of Live.
- Guards: set must be **closed** (refuses if Live is running unless overridden),
  timestamped backup + SHA-256, atomic replace, post-write re-parse, auto-restore
  on invalid output.
- **Per-instance:** the mapping lives in the set, so a second instance of the
  same plugin starts unexposed.
- **Capacity:** max 128 configured parameters per instance.
- **Version drift:** the main track is `MasterTrack` (Live 11) vs `MainTrack`
  (Live 12) — hand-written paths must handle both.
- **Values are real units**, not normalized (unlike LOM's 0–1).

**Corroboration:** our local 12.1 file shows the exact unset markers this
mechanism keys on (`-1`, `1073741823`). The community measured on 12.4.3/12.4.5;
12.1 matches structurally.

## 5. Build vs. port vs. adopt

| Option | Verdict |
|---|---|
| **live-maestro** (`als/read.py` 73KB, `write.py` 45KB) | Python, but a large MCP product; borrow the 3-field approach, don't depend on it |
| **kevinkirsten/ableton-als** | JS/TS, macOS-measured, general `.als` editor — **does not do param exposure**; skip |
| **offlinemark/dawtool** | Python, **read-only**; useful reference only |
| **Bespoke `automation/als/`** | **Recommended** — stdlib `gzip` + `xml.etree`, matches the existing package, Windows-testable, no new runtime |

## 6. What this channel gives us — and does not

**Gives:** offline parameter inspection (read all 128 names/values of any
plugin), full-fidelity snapshots without a DAW, and (if Phase 2 passes) the
ability to make GUI-only plugins LOM-drivable.

**Does not:** execute anything in Live (offline only), render/export, or edit the
plugin's actual sound state directly (opaque blob).

## 7. Phase 2 crux (the remaining unknown)

To expose `EQ: Stereo/Main Frequency 1`, the writer needs that parameter's **real
plugin index** for `ParameterId`. The names are in the file; the index is not
obviously derivable from slot order. Resolving the **name → ParameterId** mapping
is the central empirical question of Phase 2. Likely sources: the plugin's
declared parameter order, a probe of the running plugin, or live-maestro's
catalog.

**The index source (found 2026-10-02):** live-maestro's `limits.md` §3 records
that a PluginDevice answers **`get_parameter_names()`** — the plugin's *own*
declared parameter list, independent of the exposed strip — and that
`ParameterId` is **the index into that list**. It is confirmed on Live 12.4.5 and
unverified on 12.1. We added this command to our own Remote Script
(`~/ableton-mcp-extended/.../__init__.py`, `_get_parameter_names`, exposed via
`automation.lom.LomClient.get_parameter_names`); it reports `method_present`
rather than raising when absent. Once Live is restarted, querying Pro-Q 4 gives
the exact name→index mapping and makes the `.als` write deterministic — no GUI
Configure needed.

**Positive control (optional):** a set with a LOM-capable plugin (Ozone 12
Maximizer, 20 LOM params) would show what a *configured* slot looks like in the
file. If `get_parameter_names` works on 12.1 this becomes unnecessary.

## 8. Evidence

- Probe: `python3 scripts/als_probe.py info|devices|slots|batch <path>`.
- Parse: Python stdlib only (`gzip`, `xml.etree.ElementTree`); no writes.
- Writer source: `romanstark/live-maestro` `als/write.py`, `als/read.py`,
  `docs/limits.md` (fetched and quoted; measured by them on 12.4.x).
