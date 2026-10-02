"""automation — LOM-first task execution layer for Ableton Live 12.

This package replaces the teaching-oriented, click-first orientation with an
outcome-oriented, LOM-first one. See AUTOMATION_PLAN.md for the design.

Layers:
    lom.py     — TCP client for the AbletonMCP Remote Script (primary actuator)
    uia.py     — subprocess wrapper around the Windows UI-automation scripts
    state.py   — set snapshot / diff / backup
    verify.py  — numeric post-condition assertions
    lock.py    — single-run lock
    log.py     — structured run log (JSONL + EVENT: stream)
    driver.py  — ties the above together
    run.py     — CLI entry point
"""

RUN_SCHEMA_VERSION = 2
__all__ = ["RUN_SCHEMA_VERSION"]
