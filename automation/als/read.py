"""automation.als.read — read-only `.als` forensics.

Promoted from `scripts/als_probe.py` (Phase 1) into a package module so the
driver, the CLI and the tests share one parser. This module **never writes**.

An `.als` is a gzip-compressed UTF-8 XML document. Every VST instance carries a
`<PluginDevice>` with exactly 128 `<PluginFloatParameter>` slots. A slot is
*exposed* to the LOM when `ParameterId != -1` and `VisualIndex != 2**30-1`; the
exposure writer (configure.py) flips precisely those fields. See
`docs/ALS_FINDINGS.md`.
"""

from __future__ import annotations

import gzip
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

UNSET_PARAMETER_ID = -1
UNSET_VISUAL_INDEX = 2 ** 30 - 1  # 1073741823
SLOTS_PER_DEVICE = 128

_PLUGIN_INFO_TAGS = ("Vst3PluginInfo", "VstPluginInfo", "AuPluginInfo")


def strip_ns(tag: str) -> str:
    """Drop an XML namespace prefix (`{ns}Tag` -> `Tag`)."""
    return tag.split("}")[-1]


def _value(el: ET.Element | None) -> str | None:
    return None if el is None else el.attrib.get("Value")


def _as_int(value: str | None) -> int | None:
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None


# -- container ---------------------------------------------------------------

def load_raw(path: Path | str) -> bytes:
    return Path(path).read_bytes()


def decompress(raw: bytes) -> tuple[bytes, bool]:
    """Return (xml_bytes, was_gzip). Tolerates an uncompressed `.als`."""
    try:
        return gzip.decompress(raw), True
    except OSError:
        return raw, False


def load_xml(path: Path | str) -> bytes:
    """Return the decompressed XML payload of an `.als` (gzip or plain)."""
    return decompress(load_raw(path))[0]


def root_of(path: Path | str) -> ET.Element:
    return ET.fromstring(load_xml(path))


# -- model -------------------------------------------------------------------

@dataclass
class ParameterSlot:
    index: int | None
    name: str
    parameter_id: int | None
    visual_index: int | None
    manual: str | None
    user_range: dict[str, str] = field(default_factory=dict)

    @property
    def exposed(self) -> bool:
        return (self.parameter_id is not None
                and self.parameter_id != UNSET_PARAMETER_ID)

    def as_dict(self) -> dict:
        return {
            "index": self.index,
            "name": self.name,
            "parameter_id": self.parameter_id,
            "visual_index": self.visual_index,
            "manual": self.manual,
            "user_range": dict(self.user_range),
            "exposed": self.exposed,
        }


@dataclass
class PluginDevice:
    id: str | None
    name: str
    slots: list[ParameterSlot]

    @property
    def slot_count(self) -> int:
        return len(self.slots)

    @property
    def exposed_count(self) -> int:
        return sum(1 for s in self.slots if s.exposed)

    @property
    def exposed_names(self) -> list[str]:
        return [s.name for s in self.slots if s.exposed]

    def free_slots(self, *, prefer_unnamed: bool = True) -> list[ParameterSlot]:
        """Unexposed slots, unnamed ones first (the safe place to write)."""
        free = [s for s in self.slots if not s.exposed]
        if prefer_unnamed:
            free.sort(key=lambda s: (bool(s.name), s.index if s.index is not None else 0))
        return free

    def slot(self, index: int) -> ParameterSlot | None:
        for s in self.slots:
            if s.index == index:
                return s
        if 0 <= index < len(self.slots):
            return self.slots[index]
        return None

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slot_count": self.slot_count,
            "exposed_count": self.exposed_count,
            "exposed_names": self.exposed_names,
            "slots": [s.as_dict() for s in self.slots],
        }


@dataclass
class SetInfo:
    path: str
    compressed_bytes: int
    xml_bytes: int
    major_version: str | None
    minor_version: str | None
    creator: str | None
    revision: str | None
    devices: list[PluginDevice]

    def as_dict(self, *, slots: bool = True) -> dict:
        out = {
            "path": self.path,
            "compressed_bytes": self.compressed_bytes,
            "xml_bytes": self.xml_bytes,
            "major_version": self.major_version,
            "minor_version": self.minor_version,
            "creator": self.creator,
            "revision": self.revision,
            "device_count": len(self.devices),
            "devices": [
                d.as_dict() if slots else {
                    "id": d.id, "name": d.name, "slot_count": d.slot_count,
                    "exposed_count": d.exposed_count,
                }
                for d in self.devices
            ],
        }
        return out


# -- parsing -----------------------------------------------------------------

def _plugin_name(dev: ET.Element) -> str:
    for e in dev.iter():
        if strip_ns(e.tag) in _PLUGIN_INFO_TAGS:
            for c in e:
                if strip_ns(c.tag) == "Name":
                    return _value(c) or ""
    return ""


def _parse_slot(s: ET.Element) -> ParameterSlot:
    out = ParameterSlot(index=_as_int(s.attrib.get("Id")), name="",
                        parameter_id=None, visual_index=None, manual=None)
    for g in s:
        t = strip_ns(g.tag)
        if t == "ParameterName":
            out.name = _value(g) or ""
        elif t == "ParameterId":
            out.parameter_id = _as_int(_value(g))
        elif t == "VisualIndex":
            out.visual_index = _as_int(_value(g))
        elif t == "ParameterValue":
            for gg in g:
                if strip_ns(gg.tag) == "Manual":
                    out.manual = _value(gg)
        elif t == "LastUserRange":
            out.user_range = {strip_ns(gg.tag): _value(gg) for gg in g}
    return out


def _parse_device(dev: ET.Element) -> PluginDevice:
    slots = [_parse_slot(s) for s in dev.iter()
             if strip_ns(s.tag) == "PluginFloatParameter"]
    return PluginDevice(id=dev.attrib.get("Id"), name=_plugin_name(dev), slots=slots)


def devices(path: Path | str) -> list[PluginDevice]:
    """All `<PluginDevice>` instances in the set, in document order."""
    root = root_of(path)
    return [_parse_device(dev) for dev in root.iter()
            if strip_ns(dev.tag) == "PluginDevice"]


def read(path: Path | str) -> SetInfo:
    """Parse a set into a structured `SetInfo` (metadata + plugin devices)."""
    p = Path(path)
    raw = load_raw(p)
    xml, _ = decompress(raw)
    root = ET.fromstring(xml)
    return SetInfo(
        path=str(p),
        compressed_bytes=len(raw),
        xml_bytes=len(xml),
        major_version=root.attrib.get("MajorVersion"),
        minor_version=root.attrib.get("MinorVersion"),
        creator=root.attrib.get("Creator"),
        revision=root.attrib.get("Revision"),
        devices=[_parse_device(dev) for dev in root.iter()
                 if strip_ns(dev.tag) == "PluginDevice"],
    )


def device(path: Path | str, index: int = 0) -> PluginDevice | None:
    devs = devices(path)
    return devs[index] if 0 <= index < len(devs) else None


# -- diff --------------------------------------------------------------------

def diff(a: SetInfo, b: SetInfo) -> list[dict]:
    """Changes between two parsed sets, focused on plugin devices and slots.

    Complements `automation.state.diff` (which is LOM-only and therefore blind
    to anything the LOM does not expose, including `.als` slot edits).
    """
    changes: list[dict] = []
    for key in ("major_version", "minor_version", "creator", "revision"):
        if getattr(a, key) != getattr(b, key):
            changes.append({"path": f"set.{key}",
                            "before": getattr(a, key), "after": getattr(b, key)})

    for i in range(max(len(a.devices), len(b.devices))):
        da = a.devices[i] if i < len(a.devices) else None
        db = b.devices[i] if i < len(b.devices) else None
        if da is None or db is None:
            changes.append({"path": f"devices[{i}]", "before": da and da.as_dict(),
                            "after": db and db.as_dict()})
            continue
        if da.name != db.name:
            changes.append({"path": f"devices[{i}].name",
                            "before": da.name, "after": db.name})
        if da.slot_count != db.slot_count:
            changes.append({"path": f"devices[{i}].slot_count",
                            "before": da.slot_count, "after": db.slot_count})
        for j in range(max(len(da.slots), len(db.slots))):
            sa = da.slots[j] if j < len(da.slots) else None
            sb = db.slots[j] if j < len(db.slots) else None
            if sa is None or sb is None:
                changes.append({"path": f"devices[{i}].slots[{j}]",
                                "before": sa and sa.as_dict(),
                                "after": sb and sb.as_dict()})
                continue
            for key in ("name", "parameter_id", "visual_index", "manual"):
                va, vb = getattr(sa, key), getattr(sb, key)
                if va != vb:
                    changes.append({"path": f"devices[{i}].slots[{j}].{key}",
                                    "before": va, "after": vb})
    return changes


def file_info(path: Path | str) -> dict:
    """Container-level metadata without building the full model."""
    p = Path(path)
    raw = load_raw(p)
    xml, was_gz = decompress(raw)
    root = ET.fromstring(xml)
    return {
        "path": str(p),
        "compressed_bytes": len(raw),
        "xml_bytes": len(xml),
        "gzip": was_gz,
        "root": strip_ns(root.tag),
        "major_version": root.attrib.get("MajorVersion"),
        "minor_version": root.attrib.get("MinorVersion"),
        "creator": root.attrib.get("Creator"),
        "revision": root.attrib.get("Revision"),
        "mtime": os.path.getmtime(p),
    }
