#!/usr/bin/env python3
"""als_probe — read-only forensics for Ableton `.als` project files.

Phase 1 artifact of PHASED_PLAN.md. Never writes to any file. Parses the
gzip-compressed XML, locates plugin devices, and reports the parameter-slot
array (the mechanism that governs LOM exposure).

Usage:
    python3 scripts/als_probe.py info    <set.als>
    python3 scripts/als_probe.py devices <set.als>
    python3 scripts/als_probe.py slots   <set.als> [--device N] [--json]
    python3 scripts/als_probe.py batch   <dir> [<dir> ...] [--json]

Background: every VST instance gets 128 <PluginFloatParameter> slots. When
`ParameterId == -1` and `VisualIndex == 1073741823` (2**30-1) the slot is
"unset" / not exposed to the LOM. See docs/ALS_FINDINGS.md.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import sys
import xml.etree.ElementTree as ET

UNSET_ID = "-1"
UNSET_VISUAL = "1073741823"


def _strip(tag: str) -> str:
    return tag.split("}")[-1]


def _val(el: ET.Element) -> str | None:
    return el.attrib.get("Value")


def load_xml(path: str) -> bytes:
    raw = open(path, "rb").read()
    try:
        return gzip.decompress(raw)
    except OSError:
        return raw


def root_of(path: str) -> ET.Element:
    return ET.fromstring(load_xml(path))


def _plugin_name(dev: ET.Element) -> str | None:
    for e in dev.iter():
        if _strip(e.tag) in ("Vst3PluginInfo", "VstPluginInfo", "AuPluginInfo"):
            for c in e:
                if _strip(c.tag) == "Name":
                    return _val(c)
    return None


def _slot(s: ET.Element) -> dict:
    out = {"index": s.attrib.get("Id"), "name": None, "parameter_id": None,
           "visual_index": None, "manual": None, "user_range": None}
    for g in s:
        t = _strip(g.tag)
        if t == "ParameterName":
            out["name"] = _val(g)
        elif t == "ParameterId":
            out["parameter_id"] = _val(g)
        elif t == "VisualIndex":
            out["visual_index"] = _val(g)
        elif t == "ParameterValue":
            for gg in g:
                if _strip(gg.tag) == "Manual":
                    out["manual"] = _val(gg)
        elif t == "LastUserRange":
            rng = {}
            for gg in g:
                rng[_strip(gg.tag)] = _val(gg)
            out["user_range"] = rng
    out["exposed"] = out["parameter_id"] not in (None, UNSET_ID)
    return out


def devices(path: str) -> list[dict]:
    root = root_of(path)
    found = []
    for dev in root.iter():
        if _strip(dev.tag) != "PluginDevice":
            continue
        slots = [_slot(s) for s in dev.iter()
                 if _strip(s.tag) == "PluginFloatParameter"]
        found.append({
            "id": dev.attrib.get("Id"),
            "name": _plugin_name(dev),
            "slot_count": len(slots),
            "exposed_count": sum(1 for s in slots if s["exposed"]),
            "slots": slots,
        })
    return found


def info(path: str) -> dict:
    xml = load_xml(path)
    root = ET.fromstring(xml)
    return {
        "path": path,
        "compressed_bytes": os.path.getsize(path),
        "xml_bytes": len(xml),
        "root": root.tag,
        "major_version": root.attrib.get("MajorVersion"),
        "minor_version": root.attrib.get("MinorVersion"),
        "creator": root.attrib.get("Creator"),
        "revision": root.attrib.get("Revision"),
    }


def _print_devices(path: str, devs: list[dict]) -> None:
    print(f"{os.path.basename(path)}: {len(devs)} plugin device(s)")
    for d in devs:
        print(f"  [{d['id']}] {d['name']!r}  slots={d['slot_count']} "
              f"exposed={d['exposed_count']}")
        for s in d["slots"][:8]:
            mark = "*" if s["exposed"] else " "
            print(f"    {mark} {str(s['index']):>3} {str(s['name'])[:36]:<38} "
                  f"pid={s['parameter_id']:<6} vis={s['visual_index']:<12} "
                  f"val={s['manual']}")


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
        print(json.dumps(info(args.path), indent=2))
    elif args.cmd == "devices":
        _print_devices(args.path, devices(args.path))
    elif args.cmd == "slots":
        devs = devices(args.path)
        if args.json:
            print(json.dumps(devs, indent=2))
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
                devs = devices(f)
            except Exception as e:  # noqa: BLE001 - probe must not die on one bad file
                report[f] = {"error": f"{type(e).__name__}: {e}"}
                continue
            report[f] = devs
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
