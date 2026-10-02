"""automation.handoff — guided human steps ("90% automation").

Some steps are genuinely better done by the human: a modal dialog whose layout
drifts between versions, a plugin GUI with no LOM surface, an OS file picker.
Automation's job there is to do everything up to the step, hand over *precise*
instructions, then resume and verify the result.

A `Handoff` is a reusable instruction object. It is emitted as an
`EVENT: handoff_required` (with the exact steps) and printed for the user. In an
agent-mediated session the agent relays it and waits for the user; with
`interactive=True` the CLI blocks on Enter; in `unattended` batch mode it raises
`HandoffRequired` so the item is marked as needing a human rather than silently
skipped.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

TOOLTIP_HINT = "read the Info Panel tooltip before clicking"


@dataclass
class Handoff:
    id: str
    title: str
    steps: list[str] = field(default_factory=list)
    menu_path: str = ""
    anchor: str = ""
    tooltip: str = ""
    expected: str = ""
    verify: Callable[[], bool] | None = None


class HandoffRequired(RuntimeError):
    """Raised in unattended mode when a step needs a human."""

    def __init__(self, handoff: Handoff):
        self.handoff = handoff
        super().__init__(f"human step required: {handoff.title}")


def format_handoff(h: Handoff) -> str:
    lines = [f"ACTION NEEDED (human step): {h.title}"]
    if h.menu_path:
        lines.append(f"  Where: {h.menu_path}")
    if h.anchor:
        lines.append(f"  Anchor: {h.anchor}")
    if h.tooltip:
        lines.append(f"  Confirm: hover until the Info Panel says \"{h.tooltip}\"")
    for i, step in enumerate(h.steps, 1):
        lines.append(f"  {i}. {step}")
    if h.expected:
        lines.append(f"  Then confirm: {h.expected}")
    return "\n".join(lines)


def export_audio_handoff(*, out_path: str, file_type: str = "WAV",
                         bit_depth: str = "24", sample_rate: str = "44100",
                         render_track: str = "Main",
                         render_start: str = "1", render_length: str = "auto",
                         as_loop: bool = False) -> Handoff:
    """The export dialog has no LOM surface; guide the user through it."""
    steps = [
        f"Open Export with Ctrl+Shift+R (or File menu > Export Audio/Video).",
        f"Rendered Track: choose '{render_track}'.",
        f"Render Start: {render_start}; Render Length: {render_length}.",
        "Encoding: leave Encode PCM ON, and set:",
        f"    File Type = {file_type}",
        f"    Bit Depth = {bit_depth}",
        f"    Sample Rate = {sample_rate}",
        f"'Render as Loop' {'ON' if as_loop else 'OFF'}.",
        f"Set the output file name/location to: {out_path}",
        "Click Export and let the progress bar finish.",
    ]
    return Handoff(
        id="export_audio",
        title="Export Audio/Video",
        menu_path="File > Export Audio/Video  (Ctrl+Shift+R)",
        steps=steps,
        expected=f"the file appears at {out_path}",
    )


def freeze_flatten_handoff(*, track_name: str) -> Handoff:
    """Freeze/Flatten have no LOM command and no confirmed shortcut."""
    return Handoff(
        id="freeze_flatten",
        title=f"Freeze/Flatten track '{track_name}'",
        anchor=f"the track header for '{track_name}' (Arrangement or Session)",
        tooltip="Freeze Track / Flatten",
        steps=[
            f"Right-click the track header for '{track_name}'.",
            "Choose 'Freeze Track' (or 'Flatten' to commit the frozen audio).",
            "Wait for the freeze to complete.",
        ],
        expected=f"track '{track_name}' shows a frozen (grey) state",
    )
