# SDK Decision — Extensions SDK vs the current stack

**Status checked live:** 2026-10-02, at `https://ableton.github.io/extensions-sdk/`.
**Phase 0.2 deliverable** of `PHASED_PLAN.md`; answers Q6.

## The fact

> "The Extensions SDK is available exclusively in the **Live 12.4.5 public
> beta**. It does not work with any earlier version of Live."

Enrollment requires the Centercode Beta Program; Live **Suite**; Node v24+;
packaged as one `.ablx` installed in Settings; user-invoked from a right-click
context menu (runs once, then stops).

**Our machine runs Live 12.1.** The SDK is therefore unavailable without both an
upgrade and beta enrollment.

## What the SDK would add

- A **supported** (not reverse-engineered) in-Live control surface.
- **Undo via transactions** — one undo step for a whole batch. We currently have
  no undo path at all.
- **UI primitives**: progress dialogs and modal webviews.
- `renderPreFxAudio(track, start, end)` (pre-FX, audio tracks only) and
  `importIntoProject()`.
- Typed JS/TS API for song/tracks/clips/devices/rack/mixer.

## What the SDK would NOT add

- **GUI-only third-party plugin parameters** (`insertDevice` is built-in Live
  devices only; it sees the same exposed parameter strip as the LOM). This is our
  single biggest gap — the SDK does **not** close it.
- Export/render of the master, Freeze/Flatten, real-time DSP, automation
  envelopes, CC, clip-gain, routing.

## Decision

**Do not upgrade for the SDK.** Keep the current stack:

- **LOM / Remote Script** for live control (already working, already ours).
- **`.als` offline editing** for the GUI-only plugin gap (see `ALS_FINDINGS.md`)
  and offline snapshots — a route the SDK does not provide either.

Treat the SDK as a **future optional channel**.

**Trigger to revisit:** we need one of its unique capabilities (batch undo,
pre-FX render, in-Live UI) **and** the user upgrades to Live 12.4.5b+ Suite and
joins the beta. Until then it is redundant for every job we care about.

## Upgrade calculus (if considering it anyway)

| Upgrade buys | Upgrade does not buy |
|---|---|
| Supported live control | GUI-only plugin automation |
| Batch undo | Master export / render |
| Pre-FX render, import | Freeze/Flatten, real-time DSP |
| Progress/modal UI | Anything on 12.1 today |

Net: an upgrade would add convenience and undo, but the plugin-parameter gap
would still require the `.als` channel. So the `.als` work is on the critical
path regardless of the SDK.
