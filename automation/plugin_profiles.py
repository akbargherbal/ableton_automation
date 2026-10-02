"""automation.plugin_profiles — which layer controls which plugin.

Empirical finding (2026-10-02, verified live):

    Native Ableton devices        expose all parameters via LOM   (EQ Eight: 84)
    Ozone 12 *component* plugins  expose their module params       (Maximizer: 20)
    FabFilter Pro-L 2             exposes its params               (17)
    FabFilter Pro-Q 4 / Pro-C 3   expose ONLY "Device On"          (1)

Every VST is wrapped as class_name == "PluginDevice". A plugin that reports a
single parameter ("Device On") is not LOM-drivable: there is nothing for
set_device_parameter to write. Those must be driven by a different layer
(plugin GUI via UIA, or preset loading) -- never silently treated as a normal
device, because a fuzzy name like "output gain" would match nothing and fail
loudly, which at least is honest.

This module classifies a device at runtime and resolves friendly parameter
names against whatever parameters the plugin *does* expose.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .verify import find_param

PROFILES_DIR = Path(__file__).resolve().parent / "profiles" / "als"


def profile_slug(device_name: str) -> str:
    """`Pro-Q 4` -> `Pro-Q-4` (matches the saved `<slug>_parameter_names.json`)."""
    return re.sub(r"[^0-9A-Za-z._-]+", "-", (device_name or "").strip()).strip("-")

# Confirmed live (2026-10-02), names normalized to lowercase vendor-less form.
# These are HINTS for offline planning only -- classify() always prefers the
# live parameter_count, which is authoritative.
LOM_CAPABLE: set[str] = {
    "ozone 12 maximizer",       # 20 params
    "ozone 12 vintage limiter",  # 13 params
    "pro-l 2",                   # 17 params
}

# Confirmed live to expose ONLY "Device On" (1 param) -> need the GUI/preset
# path. Ozone's component plugins are NOT uniformly LOM-capable: Maximizer and
# Vintage Limiter are, but Equalizer and Dynamics are GUI-only.
GUI_ONLY: set[str] = {
    "pro-q 4", "pro-c 3",
    "ozone 12 equalizer", "ozone 12 dynamics",
    "ozone 12",  # the monolithic chain is treated as GUI/preset-driven
}


def classify(device_name: str, parameter_count: int | None = None) -> str:
    """Return "lom" or "gui".

    The live parameter_count is authoritative: a PluginDevice exposing only
    "Device On" (1 parameter) cannot be driven by set_device_parameter, full
    stop. The known sets are only a fallback for when the count isn't known yet
    (e.g. offline planning).
    """
    if parameter_count is not None:
        return "lom" if parameter_count > 1 else "gui"
    key = (device_name or "").strip().lower()
    if key in GUI_ONLY:
        return "gui"
    return "lom"


def is_gui_only(device_name: str, parameter_count: int | None = None) -> bool:
    return classify(device_name, parameter_count) == "gui"


def resolve_parameter(device_parameters: dict, friendly: str) -> dict | None:
    """Resolve a friendly parameter name against a device's live parameters."""
    return find_param(device_parameters, friendly)


def parameter_names(device_parameters: dict) -> list[str]:
    return [p.get("name", "") for p in device_parameters.get("parameters", [])]


# -- declared parameter profiles (the `.als` ParameterId source) -------------

def declared_profile_path(device_name: str,
                          profiles_dir: Path | str | None = None) -> Path:
    base = Path(profiles_dir) if profiles_dir else PROFILES_DIR
    return base / f"{profile_slug(device_name)}_parameter_names.json"


def declared_parameter_names(device_name: str,
                             profiles_dir: Path | str | None = None) -> list[str] | None:
    """The plugin's own declared parameter list, saved from `get_parameter_names`.

    This is the authoritative source for a `.als` slot's `ParameterId`: the
    value is the *index into this list*. Returns None when no profile exists.
    """
    path = declared_profile_path(device_name, profiles_dir)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    names = data.get("names") if isinstance(data, dict) else None
    return list(names) if names else None


def declared_parameter_index(device_name: str, friendly: str,
                             profiles_dir: Path | str | None = None) -> int | None:
    """Resolve a friendly name to its declared index (exact, then unique sub)."""
    names = declared_parameter_names(device_name, profiles_dir)
    if not names:
        return None
    needle = friendly.strip().lower()
    exact = [i for i, n in enumerate(names) if n.lower() == needle]
    if exact:
        return exact[0]
    subs = [i for i, n in enumerate(names) if needle and needle in n.lower()]
    return subs[0] if len(subs) == 1 else None


def describe_channels(device_name: str, parameter_count: int | None = None
                      ) -> dict[str, dict]:
    """Which actuation channel applies, for the LOM -> ALS -> UIA ladder.

    `lom` is tried first. A GUI-only device has two deterministic fallbacks:
    the offline `.als` exposure (then values are set through LOM after reopen)
    or live plugin-GUI automation via UIA.
    """
    mode = classify(device_name, parameter_count)
    if mode == "lom":
        return {"lom": {"available": True},
                "als": {"available": False, "reason": "already LOM-drivable"},
                "uia": {"available": False, "reason": "already LOM-drivable"}}
    has_profile = declared_parameter_names(device_name) is not None
    return {
        "lom": {"available": False,
                "reason": f"exposes only {parameter_count} LOM param(s)"},
        "als": {"available": has_profile,
                "requires": "close the set, run als.configure, reopen",
                "reason": None if has_profile else
                "no declared-parameter profile saved (run get_parameter_names)"},
        "uia": {"available": True,
                "requires": "plugin window open; driven via pywinauto"},
    }
