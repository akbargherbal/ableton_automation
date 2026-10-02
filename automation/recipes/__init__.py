"""automation.recipes — named, parameterized tasks.

A recipe module exposes:
    NAME: str
    DESCRIPTION: str
    PARAMS: dict[str, type]        # parameter name -> python type
    run(driver, **kwargs) -> dict  # returns a summary dict
"""

from __future__ import annotations

from . import device_report, import_audio, set_tempo

RECIPES = {
    set_tempo.NAME: set_tempo,
    import_audio.NAME: import_audio,
    device_report.NAME: device_report,
}


def get(name: str):
    if name not in RECIPES:
        raise KeyError(
            f"Unknown recipe {name!r}. Available: {', '.join(sorted(RECIPES))}"
        )
    return RECIPES[name]
