#!/usr/bin/env python3
"""als_configure — expose third-party plugin parameters by editing a .als.

Phase 2 tool. EXPERIMENTAL. Implements the community "Configure" exposure trick:
fill exactly three attributes on an *existing* `<PluginFloatParameter>` slot —
`ParameterName` (non-empty), `ParameterId` (real plugin index, not -1),
`VisualIndex` (unique, not 1073741823) — and change nothing else. Live must be
restarted / the set reopened for the change to appear.

SAFETY (non-negotiable):
  * never edits in place — `--out` must differ from the input;
  * never reserializes the XML — surgical byte-level string edits only, so every
    untouched byte is preserved (community finding: reserialization is unsafe);
  * `--apply` writes the OUTPUT only, after re-parsing and validating it;
  * dry-run is the default; it prints the proposed change and writes nothing.

Usage:
  # dry-run: propose exposing plugin=device 0, slot 0 as id 0, visual 0
  python3 scripts/als_configure.py IN.als --out OUT.als \
      --device 0 --slot 0 --name "Band 2 Gain" --param-id 0 --visual 0

  # actually write the output copy
  python3 scripts/als_configure.py IN.als --out OUT.als ... --apply
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import re
import sys
import xml.etree.ElementTree as ET

BLOCK_RE = re.compile(rb"<PluginFloatParameter\b.*?</PluginFloatParameter>",
                      re.DOTALL)
DEVICE_RE = re.compile(rb"<PluginDevice\b.*?</PluginDevice>", re.DOTALL)


def _decompress(raw: bytes) -> tuple[bytes, bool]:
    try:
        return gzip.decompress(raw), True
    except OSError:
        return raw, False


def _set_attr(block: bytes, tag: str, value: str) -> tuple[bytes, bool]:
    """Replace the Value attribute of the FIRST <tag ...> inside block."""
    pat = re.compile(rb"(<" + tag.encode() + rb"\b[^>]*?\bValue=\")[^\"]*(\")")
    new, n = pat.subn(lambda m: m.group(1) + value.encode() + m.group(2),
                      block, count=1)
    return new, n == 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--out", required=True, help="output path (must differ from input)")
    ap.add_argument("--device", type=int, default=0, help="which PluginDevice (0-based)")
    ap.add_argument("--slot", type=int, required=True, help="slot index (0-based)")
    ap.add_argument("--name", default=None, help="ParameterName (skip to leave as-is)")
    ap.add_argument("--param-id", dest="param_id", default=None,
                    help="ParameterId (real plugin index)")
    ap.add_argument("--visual", default=None, help="VisualIndex (unique, != 1073741823)")
    ap.add_argument("--apply", action="store_true", help="write the output (default dry-run)")
    args = ap.parse_args(argv)

    if args.input == args.out:
        print("refusing: --out must differ from input (never edit in place)", file=sys.stderr)
        return 2

    raw = open(args.input, "rb").read()
    xml, was_gz = _decompress(raw)
    print(f"input : {args.input} ({len(raw)} bytes, gzip={was_gz})")

    devices = list(DEVICE_RE.finditer(xml))
    if not devices:
        print("no <PluginDevice> found", file=sys.stderr)
        return 1
    if args.device >= len(devices):
        print(f"device {args.device} out of range ({len(devices)} devices)", file=sys.stderr)
        return 1
    dev = devices[args.device]
    dev_bytes = dev.group(0)

    slots = list(BLOCK_RE.finditer(dev_bytes))
    if args.slot >= len(slots):
        print(f"slot {args.slot} out of range ({len(slots)} slots)", file=sys.stderr)
        return 1
    s = slots[args.slot]
    block = s.group(0)

    new_block = block
    edits = []
    for tag, value in (("ParameterName", args.name),
                       ("ParameterId", args.param_id),
                       ("VisualIndex", args.visual)):
        if value is None:
            continue
        new_block, ok = _set_attr(new_block, tag, value)
        edits.append((tag, value, ok))
        if not ok:
            print(f"warning: <{tag}> not found in slot {args.slot}", file=sys.stderr)

    if new_block == block:
        print("no changes requested (pass --name/--param-id/--visual)")
        return 0

    new_dev = dev_bytes[:s.start()] + new_block + dev_bytes[s.end():]
    new_xml = xml[:dev.start()] + new_dev + xml[dev.end():]

    # validate the modified document parses and the slot reads back as exposed
    root = ET.fromstring(new_xml)
    strip = lambda t: t.split("}")[-1]
    devs = [e for e in root.iter() if strip(e.tag) == "PluginDevice"]
    slots_el = [e for e in devs[args.device].iter()
                if strip(e.tag) == "PluginFloatParameter"]
    exposed = sum(
        1 for sl in slots_el
        for g in sl if strip(g.tag) == "ParameterId" and g.attrib.get("Value") != "-1"
    )

    print(f"device: {args.device}  slot: {args.slot}  (of {len(slots)})")
    for tag, value, ok in edits:
        print(f"  {tag:<14} -> {value!r}  {'ok' if ok else 'MISSING'}")
    print(f"re-parse: OK  ·  exposed slots in device after edit: {exposed}")
    print(f"changed bytes: {len(new_xml) - len(xml)}")

    if not args.apply:
        print(f"\n[dry-run] would write {args.out}. Re-run with --apply to write.")
        return 0

    out_bytes = gzip.compress(new_xml, compresslevel=6, mtime=0) if was_gz else new_xml
    with open(args.out, "wb") as f:
        f.write(out_bytes)
    digest = hashlib.sha256(out_bytes).hexdigest()
    print(f"\nwrote {args.out} ({len(out_bytes)} bytes) sha256={digest[:16]}…")
    print("Reopen the set in Live to expose the parameter.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
