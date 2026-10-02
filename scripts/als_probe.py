#!/usr/bin/env python3
"""als_probe — thin CLI over `automation.als.read` (read-only `.als` forensics).

Promoted in Phase 3: the parsing lives in `automation/als/read.py`; this script
keeps the original command surface for ad-hoc shell use. Never writes.

Usage:
    python3 scripts/als_probe.py info    <set.als>
    python3 scripts/als_probe.py devices <set.als>
    python3 scripts/als_probe.py slots   <set.als> [--device N] [--json]
    python3 scripts/als_probe.py batch   <dir> [<dir> ...] [--json]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from automation.als import read as als_read  # noqa: E402


def _print_devices(path: str, devs) -> None:
    print(f"{os.path.basename(path)}: {len(devs)} plugin device(s)")
    for d in devs:
        print(f"  [{d.id}] {d.name!r}  slots={d.slot_count} "
              f"exposed={d.exposed_count}")
        for s in d.slots[:8]:
            mark = "*" if s.exposed else " "
            print(f"    {mark} {str(s.index):>3} {str(s.name)[:36]:<38} "
                  f"pid={str(s.parameter_id):<6} vis={str(s.visual_index):<12} "
                  f"val={s.manual}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_info = sub.add_parser("info")
    p_info.add_argument("path")
    p_dev = sub.add_parser("devices")
    p_dev.add_argument("path")
    p_slots = sub.add_parser("slots")
    p_slots.add_argument("path")
    p_slots.add_argument("--device", type=int, default=0)
    p_slots.add_argument("--json", action="store_true")
    p_batch = sub.add_parser("batch")
    p_batch.add_argument("roots", nargs="+")
    p_batch.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd == "info":
        print(json.dumps(als_read.file_info(args.path), indent=2))
    elif args.cmd == "devices":
        _print_devices(args.path, als_read.devices(args.path))
    elif args.cmd == "slots":
        devs = als_read.devices(args.path)
        if args.json:
            print(json.dumps([d.as_dict() for d in devs], indent=2))
        elif devs:
            _print_devices(args.path, [devs[args.device]])
        else:
            print("no plugin devices")
    elif args.cmd == "batch":
        files = []
        for r in args.roots:
            files += glob.glob(os.path.join(r, "**", "*.als"), recursive=True)
        files = sorted(set(f for f in files if "Backup" not in f))
        report = {}
        if not args.json:
            print(f"{len(files)} set(s)")
        for f in files:
            try:
                devs = als_read.devices(f)
            except Exception as e:  # noqa: BLE001 - probe must not die on one bad file
                report[f] = {"error": f"{type(e).__name__}: {e}"}
                continue
            report[f] = [d.as_dict() for d in devs]
            if not args.json:
                if devs:
                    _print_devices(f, devs)
                else:
                    print(f"{os.path.basename(f)}: no plugins")
        if args.json:
            print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
