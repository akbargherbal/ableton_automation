# context.md — Project Digest

**Purpose of this file:** a standalone summary of where things stand and
what happens next, so a new session doesn't have to re-derive it from
scratch. This file replaces the previous `context.md` entirely — that one
was written for a specific debloat project (`PHASED_PLAN.md`'s Phases
0–3), which is now **done**. This file is a one-time handoff note, not a
living doc: once real feedback starts coming in from the phase described
below, expect this file (and likely a new `PHASED_PLAN.md`) to be replaced
again, the same way this one replaced its predecessor.

---

## 1. Where things stand

The debloat project is closed. All of `PHASED_PLAN.md`'s phases (0, 0b, 1,
2, 3) are done:

- The Groove Pool crash has no callable path left anywhere in the code
  (`scripts/keyboard_shortcuts.py`) — it's tracked as an open,
  unconfirmed-root-cause investigation in
  `docs/teaching/MASTERING_COURSE_KNOWN_ISSUES.md` instead of a standing warning in
  the policy.
- Host-process liveness detection exists (`AbletonProcessGone`,
  `is_ableton_alive()`) so a crashed Ableton process is caught cleanly
  instead of producing confusing downstream failures.
- `docs/teaching/MASTERING_COURSE_KNOWN_ISSUES.md` now accepts open/unconfirmed
  entries, not just settled facts.
- `SUNO_MASTERING_AGENT_POLICY.md` (shipped as `AGENTS.md` in the runtime
  folder) has been rewritten: no incident history, no phase bookkeeping,
  no cross-references to dev-only files the runtime agent never sees. It
  should read in one pass as a set of plain operating rules.
- `build_mastering_env.sh` matches the rewritten policy — it no longer
  generates `mastering_progress.md` (removed entirely, by explicit
  decision; sessions are stateless and nothing reads that file anymore).

Nothing about the click-automation sibling course changed in this project;
see `README.md` for that.

## 2. What happens next

This project is moving from **building** to **using and observing**. The
plan is:

- Run real mastering sessions in Ableton with the rebuilt `AGENTS.md`, and
  separately, deliberately test specific mechanisms in isolation (the MCP
  read-back path, the screenshot fallback, the escalation rule, whether
  the Known-Issues log actually gets written to when something qualifies).
- Report back observations — what worked, what felt off, what the agent
  got wrong or handled clumsily, what a rule should have said instead.
- Each round of feedback gets triaged and turned into a concrete fix
  (wording, code, or both), the same working pattern as the debloat
  project, just driven by live findings instead of a pre-written plan.

There is no fixed checklist for this phase yet — it starts from
observation, not from a known set of tasks. If a recurring pattern of
fixes emerges, that's the point to write a fresh `PHASED_PLAN.md` for it.

## 3. Specific things worth paying attention to while testing

These aren't known bugs — they're the parts of the rebuilt policy most
likely to surface something worth reporting, because they were recent
changes or were already flagged as open when the debloat project closed:

- **Groove Pool** — still an open, unconfirmed-root-cause row in
  `docs/teaching/MASTERING_COURSE_KNOWN_ISSUES.md`. Not part of this curriculum, so
  no need to seek it out, but if it comes up incidentally, that's useful
  signal for the log.
- **The Youlean LUFS workaround** — screenshot the meter, read the number
  directly, cross-check against your own read. Worth reporting whether
  this actually feels smooth in a real lesson or becomes a friction point.
- **The relaxed re-demonstration rule** — the agent should now demonstrate
  an idiom again if you ask to see it again, not just push you to do it
  solo the second time. Worth confirming it actually behaves that way.
- **MCP-only device loading** — the policy never attempts a UI click for
  loading a device onto a track; it goes straight to MCP. This was kept
  as a firm default (Browser list items have no automation_id, so clicking
  can't resolve them), not a preference — but real usage may still surface
  something worth reporting if it feels wrong in practice.
- **The escalation rule generally** — first-time demonstrate, screenshot
  on a resolve failure, Level 4 plain instructions as last resort. Worth
  noting any point where the agent seems to skip a step, loop, or escalate
  too early/late.

## 4. How to report back

Plain observations are enough — what you were doing, what happened, what
you expected instead. No need to pre-diagnose root cause or propose the
fix yourself; that triage happens on the next pass through this file.
