"""automation.batch — manifest-driven, resumable batch runs.

A manifest is a JSON list, a JSONL file, or a CSV. Each row's keys are matched
to the recipe's PARAMS; unrecognized keys are ignored. Bookkeeping keys written
back by the runner are prefixed with `_`:

    _status      pending | running | done | failed
    _run_dir     per-item run folder
    _error       failure message
    _finished_at ISO-8601

`--resume` skips rows whose `_status` is `done`. The manifest is rewritten
after every item so a crash loses at most one item's bookkeeping.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from .driver import Driver
from .recipes import get as get_recipe


class ManifestError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_manifest(path: Path | str) -> tuple[list[dict], str]:
    p = Path(path)
    if not p.exists():
        raise ManifestError(f"manifest not found: {p}")
    suffix = p.suffix.lower()
    if suffix == ".jsonl":
        rows = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
        return rows, "jsonl"
    if suffix == ".csv":
        with open(p, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f)), "csv"
    if suffix == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "items" in data:
            return list(data["items"]), "json"
        if isinstance(data, list):
            return data, "json"
        raise ManifestError("JSON manifest must be a list or {'items': [...]}")
    raise ManifestError(f"unsupported manifest type: {suffix} (use .json/.jsonl/.csv)")


def save_manifest(path: Path | str, rows: list[dict], fmt: str) -> None:
    p = Path(path)
    tmp = p.with_suffix(p.suffix + ".tmp")
    if fmt == "csv":
        fieldnames: list[str] = []
        for row in rows:
            for k in row:
                if k not in fieldnames:
                    fieldnames.append(k)
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    elif fmt == "jsonl":
        tmp.write_text("\n".join(json.dumps(r, default=str) for r in rows) + "\n",
                       encoding="utf-8")
    else:
        tmp.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    tmp.replace(p)


def _coerce(value, target_type):
    if target_type is float:
        return float(value)
    if target_type is int:
        return int(value)
    if target_type is bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("1", "true", "yes", "on")
    return str(value)


def _kwargs_for(row: dict, recipe) -> dict:
    kwargs = {}
    for name, typ in recipe.PARAMS.items():
        if name in row and row[name] not in (None, ""):
            kwargs[name] = _coerce(row[name], typ)
    return kwargs


def run_batch(recipe_name: str, manifest_path: Path | str, *,
              out_dir: Path | str | None = None, resume: bool = True,
              limit: int | None = None, dry_run: bool = False,
              defaults: dict | None = None) -> dict:
    recipe = get_recipe(recipe_name)
    rows, fmt = load_manifest(manifest_path)
    out_root = Path(out_dir) if out_dir else Path(manifest_path).parent / f"batch_{recipe_name}"
    out_root.mkdir(parents=True, exist_ok=True)

    summary = {"recipe": recipe_name, "total": len(rows), "done": 0,
               "failed": 0, "skipped": 0, "results": []}
    processed = 0

    for i, row in enumerate(rows):
        status = str(row.get("_status", "pending"))
        if resume and status in ("done", "running"):
            summary["skipped"] += 1
            continue
        if limit is not None and processed >= limit:
            break

        kwargs = dict(defaults or {})
        kwargs.update(_kwargs_for(row, recipe))
        item_dir = out_root / f"item_{i:04d}"
        row["_status"] = "running"
        row["_run_dir"] = str(item_dir)
        save_manifest(manifest_path, rows, fmt)

        try:
            with Driver(run_dir=item_dir, name=f"batch_{recipe_name}_{i}",
                        dry_run=dry_run) as d:
                result = recipe.run(d, **kwargs)
            row["_status"] = "done"
            row["_result"] = result
            row.pop("_error", None)
            summary["done"] += 1
            summary["results"].append({"index": i, "status": "done", "result": result})
        except Exception as e:
            row["_status"] = "failed"
            row["_error"] = f"{type(e).__name__}: {e}"
            summary["failed"] += 1
            summary["results"].append({"index": i, "status": "failed",
                                       "error": row["_error"]})
        row["_finished_at"] = _now()
        save_manifest(manifest_path, rows, fmt)
        processed += 1

    return summary
