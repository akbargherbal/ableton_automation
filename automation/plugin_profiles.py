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

from .verify import find_param

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
