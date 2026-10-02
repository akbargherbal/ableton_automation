# KNOWN_ISSUES.md — Mastering Course Friction Log

**Purpose:** a lean record of *systemic* snags — cases where a bad assumption
baked into `AGENTS.md`, the scripts, or the docs cost real time or nearly
caused a wrong action, and would keep costing it in future sessions if left
alone. This is not a session diary and not a bug tracker for one-off
glitches.

**This file stays short.** If it's growing fast, the bar below isn't being
applied strictly enough — go re-read it before adding the next row.

---

## What qualifies (all three must be true)

1. **It's structural, not circumstantial.** The cause lives in `AGENTS.md`,
   a script, or a doc in this folder — not in a particular track's audio, a
   particular learner mistake, or a one-off environment hiccup (e.g. Ableton
   was slow to launch that one time).
2. **It will recur** unless something in this folder changes. Ask: *if the
   next session hits this exact situation again, will the same thing go
   wrong?* If no, it doesn't belong here.
3. **Fixing it at the root is cheap relative to what it costs left alone.**
   A five-minute wording fix in `AGENTS.md` that prevents a recurring
   10-minute detour every session clears the bar. A one-time fluke does not,
   no matter how annoying it was in the moment.

## What does NOT qualify — do not log these

- Ordinary teaching friction: the learner was confused, needed a concept
  re-explained, or disagreed with an ear-only judgment call.
- A single track's audio being unusually noisy, quiet, or weird — that's
  the material, not the agent.
- A mistake you made once and immediately corrected, with no reason to
  think it'll happen again.

## Format

One row per **distinct root cause**. If the same root cause shows up again,
don't add a new row — bump `Times Seen` and `Last Seen` on the existing one.

`Root Cause / Bad Assumption` may honestly say `Unknown` while an entry is
still under investigation — this log tracks suspected structural problems
from the moment they're first suspected, not only once they're fully
root-caused. `Root Fix` for such a row should describe the next confirm/
refute step, not a finished fix.

| Date First Seen | Times Seen | Last Seen | Symptom | Root Cause / Bad Assumption | Root Fix (what to change, and where) | Status |
|---|---|---|---|---|---|---|
| 2026-08-08 | 2 | 2026-08-08 | Toggling the Groove Pool panel (Ctrl+Alt+6) crashed Ableton Live 12 twice, same fault bucket (`0xc0000409` in `ucrtbase.dll`) | Unknown — not yet isolated whether it's the specific toggle sequence, window state at the time, or something else in Ableton itself. Not part of this curriculum, so hasn't been prioritized to chase further. | The automated call path was removed as a precaution (Phase 0, `scripts/keyboard_shortcuts.py` — `groove_pool_toggle` no longer exists, `load_shortcut` raises a plain `KeyError`), not because the root cause was confirmed. Next step to actually close this: a deliberate, isolated manual test (open Groove Pool by hand, nothing else running) to confirm or refute the toggle sequence itself as the trigger. | Open |

**Status** is one of: `Open` (not yet fixed) · `Fixed` (root fix applied —
keep the row, don't delete, so the history of what was wrong survives) ·
`Wontfix` (considered, deliberately not worth fixing — say why in Root Fix).
