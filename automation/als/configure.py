"""automation.als.configure — expose plugin parameters by editing a copy.

The community "Configure" trick, proven end-to-end on Live 12.1 in Phase 2 of
`PHASED_PLAN.md`: fill exactly three fields on an *existing*
`<PluginFloatParameter>` slot so Live re-registers it with the LOM on reopen:

    ParameterName  -> the declared display name
    ParameterId    -> the plugin's real parameter index (not -1)
    VisualIndex    -> a unique strip position (not 2**30-1)

Nothing else is touched. Values are exposed, not set: after reopening the set the
parameter is drivable through the normal LOM channel (`driver.set_param`).

SAFETY (non-negotiable, inherited from the Phase 2 proof):
  * never edit in place -- output must differ from source;
  * never reserialize the XML -- surgical byte-level edits preserve every other
    byte (community finding: reserialization is unsafe);
  * dry-run by default; `apply=True` writes only after the result re-parses and
    the target slots read back exposed;
  * the prior output (if any) is backed up and the write is atomic;
  * SHA-256 of source and output is recorded.
"""

from __future__ import annotations

import gzip
import hashlib
import os
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

from . import read as als_read
from .read import UNSET_VISUAL_INDEX, PluginDevice

BLOCK_RE = re.compile(rb"<PluginFloatParameter\b.*?</PluginFloatParameter>", re.DOTALL)
DEVICE_RE = re.compile(rb"<PluginDevice\b.*?</PluginDevice>", re.DOTALL)


class AlsConfigError(RuntimeError):
    """The requested `.als` edit is unsafe or impossible."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# -- model -------------------------------------------------------------------

@dataclass
class Exposure:
    slot: int
    name: str
    parameter_id: int
    visual_index: int

    def as_dict(self) -> dict:
        return {"slot": self.slot, "name": self.name,
                "parameter_id": self.parameter_id, "visual_index": self.visual_index}


@dataclass
class ConfigureResult:
    source: str
    output: str
    applied: bool
    exposures: list[Exposure]
    exposed_before: int
    exposed_after: int
    changed_bytes: int
    sha256_source: str
    sha256_output: str | None = None
    backup: str | None = None
    device_index: int = 0
    device_name: str = ""
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "source": self.source, "output": self.output, "applied": self.applied,
            "device_index": self.device_index, "device_name": self.device_name,
            "exposures": [e.as_dict() for e in self.exposures],
            "exposed_before": self.exposed_before,
            "exposed_after": self.exposed_after,
            "changed_bytes": self.changed_bytes,
            "sha256_source": self.sha256_source,
            "sha256_output": self.sha256_output,
            "backup": self.backup,
            "notes": list(self.notes),
        }


# -- name resolution ---------------------------------------------------------

def _find_declared_index(names: list[str], friendly: str) -> int | None:
    """Exact (case-insensitive) match wins; else a unique substring match."""
    needle = friendly.strip().lower()
    exact = [i for i, n in enumerate(names) if n.lower() == needle]
    if exact:
        return exact[0]
    subs = [i for i, n in enumerate(names) if needle and needle in n.lower()]
    if len(subs) == 1:
        return subs[0]
    return None


def resolve_exposures(dev: PluginDevice, declared_names: list[str],
                      requested: list[str], *,
                      slot_indices: list[int] | None = None,
                      start_visual: int | None = None) -> list[Exposure]:
    """Map friendly parameter names to free slots + declared indices.

    `declared_names` is the plugin's own parameter list (`get_parameter_names`).
    Raises `AlsConfigError` with a precise reason for any name that cannot be
    resolved uniquely.
    """
    if not declared_names:
        raise AlsConfigError(
            "no declared parameter names supplied; run get_parameter_names on "
            "the running plugin and save it to automation/profiles/als/"
        )
    free = dev.free_slots(prefer_unnamed=True)
    if slot_indices is not None:
        chosen = [dev.slot(i) for i in slot_indices]
        missing = [i for i, s in zip(slot_indices, chosen) if s is None]
        if missing:
            raise AlsConfigError(f"slot(s) out of range: {missing}")
        free = [s for s in chosen if s is not None]
    if len(requested) > len(free):
        raise AlsConfigError(
            f"need {len(requested)} free slot(s) but device {dev.name!r} has "
            f"{len(free)} (capacity is one parameter set per instance)"
        )

    used_visuals = {s.visual_index for s in dev.slots
                    if s.visual_index not in (None, UNSET_VISUAL_INDEX)}
    visual = 0 if start_visual is None else start_visual
    exposures: list[Exposure] = []
    for i, friendly in enumerate(requested):
        idx = _find_declared_index(declared_names, friendly)
        if idx is None:
            raise AlsConfigError(
                f"parameter {friendly!r} not found (or ambiguous) in "
                f"{dev.name!r}; {len(declared_names)} declared names"
            )
        while visual in used_visuals:
            visual += 1
        slot = free[i]
        used_visuals.add(visual)
        exposures.append(Exposure(slot=slot.index if slot.index is not None else i,
                                  name=declared_names[idx],
                                  parameter_id=idx, visual_index=visual))
        visual += 1
    return exposures


# -- surgical writer ---------------------------------------------------------

def _set_attr(block: bytes, tag: str, value: str) -> tuple[bytes, bool]:
    """Replace the Value attribute of the FIRST `<tag ...>` inside block."""
    pat = re.compile(rb"(<" + tag.encode() + rb"\b[^>]*?\bValue=\")[^\"]*(\")")
    new, n = pat.subn(lambda m: m.group(1) + str(value).encode() + m.group(2),
                      block, count=1)
    return new, n == 1


def _validate(xml: bytes, device_index: int, exposures: list[Exposure]) -> PluginDevice:
    root = ET.fromstring(xml)
    devs = [e for e in root.iter() if als_read.strip_ns(e.tag) == "PluginDevice"]
    if device_index >= len(devs):
        raise AlsConfigError(f"device {device_index} missing after edit")
    parsed = als_read._parse_device(devs[device_index])
    for exp in exposures:
        slot = parsed.slot(exp.slot)
        if slot is None:
            raise AlsConfigError(f"slot {exp.slot} missing after edit")
        if slot.parameter_id != exp.parameter_id:
            raise AlsConfigError(
                f"slot {exp.slot} ParameterId reads {slot.parameter_id!r}, "
                f"expected {exp.parameter_id}"
            )
        if slot.name != exp.name:
            raise AlsConfigError(
                f"slot {exp.slot} name reads {slot.name!r}, expected {exp.name!r}"
            )
        if not slot.exposed:
            raise AlsConfigError(f"slot {exp.slot} not exposed after edit")
    return parsed


def write(source: Path | str, output: Path | str, exposures: list[Exposure], *,
          device: int = 0, apply: bool = False, backup: bool = True,
          overwrite: bool = False) -> ConfigureResult:
    """Inject `exposures` into a copy of `source` at `output`.

    Dry-run unless `apply=True`. `output` must differ from `source`; an existing
    `output` is backed up before being replaced. Returns a `ConfigureResult`.
    """
    src, out = Path(source), Path(output)
    if src == out:
        raise AlsConfigError("output must differ from source (never edit in place)")
    if not src.exists():
        raise FileNotFoundError(f"source set not found: {src}")
    if not exposures:
        raise AlsConfigError("no exposures requested")

    raw = src.read_bytes()
    xml, was_gz = als_read.decompress(raw)
    digest_src = sha256(raw)

    devs = list(DEVICE_RE.finditer(xml))
    if not devs:
        raise AlsConfigError(f"no <PluginDevice> in {src}")
    if device >= len(devs):
        raise AlsConfigError(f"device {device} out of range ({len(devs)})")
    dev_bytes = devs[device].group(0)
    slots = list(BLOCK_RE.finditer(dev_bytes))

    before_dev = _validate(xml, device, [])  # parse-only sanity of source
    exposed_before = before_dev.exposed_count

    new_dev = dev_bytes
    for exp in exposures:
        if exp.slot < 0 or exp.slot >= len(slots):
            raise AlsConfigError(f"slot {exp.slot} out of range ({len(slots)})")
        s = slots[exp.slot]
        block = s.group(0)
        already = before_dev.slot(exp.slot)
        if already is not None and already.exposed and not overwrite:
            raise AlsConfigError(
                f"slot {exp.slot} is already exposed as {already.name!r}; "
                "pass overwrite=True to re-point it"
            )
        new_block = block
        for tag, value in (("ParameterName", exp.name),
                           ("ParameterId", exp.parameter_id),
                           ("VisualIndex", exp.visual_index)):
            new_block, ok = _set_attr(new_block, tag, str(value))
            if not ok:
                raise AlsConfigError(f"<{tag}> not found in slot {exp.slot}")
        new_dev = new_dev[:s.start()] + new_block + new_dev[s.end():]

    new_xml = xml[:devs[device].start()] + new_dev + xml[devs[device].end():]
    parsed = _validate(new_xml, device, exposures)
    exposed_after = parsed.exposed_count

    result = ConfigureResult(
        source=str(src), output=str(out), applied=False, exposures=list(exposures),
        exposed_before=exposed_before, exposed_after=exposed_after,
        changed_bytes=len(new_xml) - len(xml), sha256_source=digest_src,
        device_index=device, device_name=parsed.name,
        notes=["dry-run: pass apply=True to write"] if not apply else [],
    )
    if not apply:
        return result

    backup_path: Path | None = None
    if out.exists():
        if backup:
            backup_path = out.with_name(f"{out.name}.{_utc_stamp()}.bak")
            shutil.copy2(out, backup_path)
        else:
            raise AlsConfigError(
                f"{out} already exists and backup=False; refusing to overwrite"
            )

    out.parent.mkdir(parents=True, exist_ok=True)
    out_bytes = (gzip.compress(new_xml, compresslevel=6, mtime=0)
                 if was_gz else new_xml)
    fd, tmp_name = tempfile.mkstemp(dir=str(out.parent), prefix=out.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(out_bytes)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, out)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise

    result.applied = True
    result.sha256_output = sha256(out_bytes)
    result.backup = str(backup_path) if backup_path else None
    result.notes = ["reopen the set in Live to expose the parameter(s)"]
    return result
