#!/usr/bin/env python3
"""als_configure — low-level CLI over `automation.als.configure`.

Promoted in Phase 3. Exposes a plugin parameter by editing a COPY of a set.
SAFETY: never in place, never reserializes, dry-run by default, backup + atomic
replace + re-parse validation on write. See `automation/als/configure.py`.

Usage:
  python3 scripts/als_configure.py IN.als --out OUT.als \
      --device 0 --slot 0 --name "Band 2 Gain" --param-id 26 --visual 0 [--apply]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from automation.als import configure as als_configure  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--out", required=True, help="output path (must differ from input)")
    ap.add_argument("--device", type=int, default=0, help="which PluginDevice (0-based)")
    ap.add_argument("--slot", type=int, required=True, help="slot index (0-based)")
    ap.add_argument("--name", required=True, help="ParameterName (display name)")
    ap.add_argument("--param-id", dest="param_id", type=int, required=True,
                    help="ParameterId (real plugin index)")
    ap.add_argument("--visual", type=int, default=0,
                    help="VisualIndex (unique, != 1073741823)")
    ap.add_argument("--overwrite", action="store_true",
                    help="allow re-pointing an already-exposed slot")
    ap.add_argument("--apply", action="store_true",
                    help="write the output (default dry-run)")
    args = ap.parse_args(argv)

    exposure = als_configure.Exposure(slot=args.slot, name=args.name,
                                      parameter_id=args.param_id,
                                      visual_index=args.visual)
    try:
        result = als_configure.write(args.input, args.out, [exposure],
                                     device=args.device, apply=args.apply,
                                     overwrite=args.overwrite)
    except als_configure.AlsConfigError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"input : {result.source}  sha256={result.sha256_source[:16]}…")
    print(f"device: {result.device_index} ({result.device_name!r})  "
          f"slot: {args.slot}  (of 128)")
    for e in result.exposures:
        print(f"  ParameterName  -> {e.name!r}")
        print(f"  ParameterId    -> {e.parameter_id}")
        print(f"  VisualIndex    -> {e.visual_index}")
    print(f"exposed slots: {result.exposed_before} -> {result.exposed_after}"
          f"  changed bytes: {result.changed_bytes}")
    if not result.applied:
        print(f"\n[dry-run] would write {result.output}. Re-run with --apply.")
        return 0
    print(f"\nwrote {result.output}  sha256={result.sha256_output[:16]}…")
    if result.backup:
        print(f"backed up previous output to {result.backup}")
    print("Reopen the set in Live to expose the parameter.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
