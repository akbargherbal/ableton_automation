"""automation.run — command-line entry point.

    python3 -m automation.run session
    python3 -m automation.run devices
    python3 -m automation.run plugins [--query X] [--refresh]
    python3 -m automation.run params --track N --device M [--name X]
    python3 -m automation.run set-tempo --bpm 124 [--dry-run]
    python3 -m automation.run set-param --track N --device M --name X --value 0.5 [--dry-run]
    python3 -m automation.run import-audio --track N --file PATH [--beats 0]
    python3 -m automation.run recipe --name set_tempo --set bpm=124 [--dry-run]
    python3 -m automation.run uia --control ID --action set --value V [--live]
    python3 -m automation.run analyze --file OUT.wav [--target-lufs -14]
    python3 -m automation.run tasks

Track/device indices are 0-based throughout (matching --list-tracks and the
Remote Script / LOM), not the 1-based convention of the MCP tools.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import plugins as plugins_mod
from . import recipes as recipes_pkg
from . import uia
from .analysis import measure
from .driver import Driver
from .lom import LomClient, LomError


def _print(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


def _client() -> LomClient:
    return LomClient()


def cmd_session(args) -> int:
    with _client() as c:
        _print(c.session_info())
    return 0


def cmd_devices(args) -> int:
    with _client() as c:
        tracks = []
        for info in c.all_tracks():
            tracks.append({
                "index": info.get("index"),
                "name": info.get("name"),
                "devices": info.get("devices", []),
            })
        _print({"track_count": len(tracks), "tracks": tracks})
    return 0


def cmd_plugins(args) -> int:
    with _client() as c:
        found = plugins_mod.list_plugins(c, refresh=args.refresh)
        if args.query:
            q = plugins_mod.normalize(args.query)
            found = [p for p in found if q in plugins_mod.normalize(p["name"])]
        _print({"count": len(found), "plugins": found})
    return 0


def cmd_params(args) -> int:
    with _client() as c:
        result = c.device_parameters(args.track, args.device)
        params = result.get("parameters", [])
        if args.name:
            params = [p for p in params
                      if args.name.lower() in (p.get("name") or "").lower()]
        result["parameters"] = params
        result["parameter_count"] = len(params)
        if args.save:
            from pathlib import Path
            Path(args.save).parent.mkdir(parents=True, exist_ok=True)
            with open(args.save, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"saved {len(params)} params to {args.save}", file=sys.stderr)
        _print(result)
    return 0


def cmd_snapshot_devices(args) -> int:
    from .probe import snapshot_loaded_devices
    with _client() as c:
        _print(snapshot_loaded_devices(c, args.out))
    return 0


def cmd_probe_plugin(args) -> int:
    from .probe import probe_plugin
    with _client() as c:
        _print(probe_plugin(c, args.plugin, args.out, live=args.live))
    return 0


def cmd_set_tempo(args) -> int:
    with Driver(name="set_tempo", dry_run=args.dry_run,
                snapshot_on_enter=not args.no_snapshot) as d:
        result = d.set_tempo(args.bpm)
        _print(result)
    return 0


def cmd_set_param(args) -> int:
    with Driver(name="set_param", dry_run=args.dry_run,
                snapshot_on_enter=not args.no_snapshot) as d:
        result = d.set_param(args.track, args.device, args.name, args.value,
                             tol=args.tol)
        _print(result)
    return 0


def cmd_import_audio(args) -> int:
    with Driver(name="import_audio", dry_run=args.dry_run,
                snapshot_on_enter=not args.no_snapshot) as d:
        result = d.import_audio(args.track, args.file, args.beats)
        _print(result)
    return 0


def cmd_recipe(args) -> int:
    recipe = recipes_pkg.get(args.name)
    kwargs = {}
    for pair in args.set or []:
        if "=" not in pair:
            print(f"--set expects key=value, got {pair!r}", file=sys.stderr)
            return 2
        key, _, raw = pair.partition("=")
        key = key.strip()
        target_type = recipe.PARAMS.get(key)
        if target_type is None:
            print(f"recipe {args.name!r} has no parameter {key!r}; "
                  f"known: {sorted(recipe.PARAMS)}", file=sys.stderr)
            return 2
        kwargs[key] = target_type(raw)
    with Driver(name=args.name, dry_run=args.dry_run,
                snapshot_on_enter=not args.no_snapshot,
                interactive=args.interactive) as d:
        result = recipe.run(d, **kwargs)
        _print(result)
    return 0


def cmd_uia(args) -> int:
    result = uia.run_control(args.control, args.action, args.value, live=args.live)
    for event in result.events:
        print(f"EVENT: {json.dumps(event, default=str)}")
    return 0 if result.ok else 1


def cmd_keys(args) -> int:
    result = uia.send_keys(args.keys, live=args.live)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    for event in result.events:
        print(f"EVENT: {json.dumps(event, default=str)}")
    return 0 if result.ok else 1


def cmd_batch(args) -> int:
    from .batch import run_batch
    defaults = {}
    for pair in args.set or []:
        if "=" not in pair:
            print(f"--set expects key=value, got {pair!r}", file=sys.stderr)
            return 2
        k, _, v = pair.partition("=")
        defaults[k.strip()] = v
    _print(run_batch(args.recipe, args.manifest, out_dir=args.out,
                     resume=not args.no_resume, limit=args.limit,
                     dry_run=args.dry_run, defaults=defaults,
                     interactive=args.interactive))
    return 0


def cmd_guide(args) -> int:
    from .handoff import Handoff, format_handoff
    from .log import RunLog
    handoff = Handoff(id=args.id, title=args.title, menu_path=args.menu,
                      steps=args.step, expected=args.expect)
    log = RunLog(None)
    log.event("handoff_required", id=handoff.id, title=handoff.title,
              menu_path=handoff.menu_path, steps=handoff.steps,
              expected=handoff.expected)
    print(format_handoff(handoff))
    if args.interactive:
        try:
            input("  [enter when done, or Ctrl-C to abort] ")
        except EOFError:
            pass
    return 0


def cmd_analyze(args) -> int:
    _print(measure.analyze(args.file, target_lufs=args.target_lufs))
    return 0


def cmd_tasks(args) -> int:
    recipes = {name: mod.DESCRIPTION for name, mod in recipes_pkg.RECIPES.items()}
    uia_tasks = None
    try:
        uia_tasks = uia.list_tasks()
    except Exception as e:
        uia_tasks = {"error": str(e)}
    _print({"recipes": recipes, "uia_tasks": uia_tasks})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="automation.run", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("session", help="print session info")
    p.set_defaults(func=cmd_session)

    p = sub.add_parser("devices", help="list tracks and their devices")
    p.set_defaults(func=cmd_devices)

    p = sub.add_parser("plugins", help="list loadable external plugins")
    p.add_argument("--query", default="")
    p.add_argument("--refresh", action="store_true")
    p.set_defaults(func=cmd_plugins)

    p = sub.add_parser("params", help="list a device's parameters")
    p.add_argument("--track", type=int, required=True)
    p.add_argument("--device", type=int, required=True)
    p.add_argument("--name", default="")
    p.add_argument("--save", default=None, help="also write the result JSON here")
    p.set_defaults(func=cmd_params)

    p = sub.add_parser("snapshot-devices",
                       help="read-only: dump params for every loaded device")
    p.add_argument("--out", default="automation/profiles/loaded")
    p.set_defaults(func=cmd_snapshot_devices)

    p = sub.add_parser("probe-plugin",
                       help="load a plugin on a scratch track to learn its params")
    p.add_argument("--plugin", required=True)
    p.add_argument("--out", default="automation/profiles/probed")
    p.add_argument("--live", action="store_true",
                   help="actually load (default is a dry-run that just resolves)")
    p.set_defaults(func=cmd_probe_plugin)

    p = sub.add_parser("set-tempo", help="set tempo (verified)")
    p.add_argument("--bpm", type=float, required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-snapshot", action="store_true")
    p.set_defaults(func=cmd_set_tempo)

    p = sub.add_parser("set-param", help="set a device parameter (verified)")
    p.add_argument("--track", type=int, required=True)
    p.add_argument("--device", type=int, required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--value", type=float, required=True)
    p.add_argument("--tol", type=float, default=0.02)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-snapshot", action="store_true")
    p.set_defaults(func=cmd_set_param)

    p = sub.add_parser("import-audio", help="import an audio file to arrangement")
    p.add_argument("--track", type=int, required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--beats", type=float, default=0.0)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-snapshot", action="store_true")
    p.set_defaults(func=cmd_import_audio)

    p = sub.add_parser("recipe", help="run a named recipe")
    p.add_argument("--name", required=True)
    p.add_argument("--set", action="append", metavar="KEY=VALUE")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-snapshot", action="store_true")
    p.add_argument("--interactive", action="store_true",
                   help="block on Enter at a human handoff step")
    p.set_defaults(func=cmd_recipe)

    p = sub.add_parser("guide", help="emit precise instructions for a human step")
    p.add_argument("--id", default="guide")
    p.add_argument("--title", required=True)
    p.add_argument("--menu", default="", help="menu path / shortcut")
    p.add_argument("--step", action="append", required=True,
                   help="one instruction line (repeatable, in order)")
    p.add_argument("--expect", default="", help="what the user should confirm")
    p.add_argument("--interactive", action="store_true")
    p.set_defaults(func=cmd_guide)

    p = sub.add_parser("uia", help="UI-automation fallback (Windows layer)")
    p.add_argument("--control", required=True)
    p.add_argument("--action", choices=["click", "set"], required=True)
    p.add_argument("--value", default=None)
    p.add_argument("--live", action="store_true")
    p.set_defaults(func=cmd_uia)

    p = sub.add_parser("batch", help="run a recipe over a manifest, resumable")
    p.add_argument("--manifest", required=True,
                   help=".json / .jsonl / .csv; each row's keys map to recipe params")
    p.add_argument("--recipe", required=True)
    p.add_argument("--out", default=None)
    p.add_argument("--set", action="append", metavar="KEY=VALUE",
                   help="defaults applied to every row (row values win)")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--no-resume", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--interactive", action="store_true",
                   help="allow human handoff steps (default: fail the item)")
    p.set_defaults(func=cmd_batch)

    p = sub.add_parser("keys", help="send a raw keystroke sequence (menu shortcuts)")
    p.add_argument("--keys", required=True,
                   help="pywinauto sequence, e.g. '^+r' = Ctrl+Shift+R (Export)")
    p.add_argument("--live", action="store_true")
    p.set_defaults(func=cmd_keys)

    p = sub.add_parser("analyze", help="measure a rendered audio file")
    p.add_argument("--file", required=True)
    p.add_argument("--target-lufs", type=float, default=None)
    p.set_defaults(func=cmd_analyze)

    p = sub.add_parser("tasks", help="list recipes and UIA tasks")
    p.set_defaults(func=cmd_tasks)

    return parser


def main(argv: list[str] | None = None) -> int:
    from .handoff import HandoffRequired
    from .verify import VerificationFailed
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except HandoffRequired as e:
        print(f"NEEDS HUMAN: {e.handoff.title}", file=sys.stderr)
        return 3
    except (LomError, FileNotFoundError, ValueError, LookupError,
            NotImplementedError, VerificationFailed) as e:
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
