import gzip

import pytest

from automation import plugin_profiles as pp
from automation.als import configure, read, snapshot

NAMED = [
    "Band 2 Gain",
    "Band 2 Frequency",
    "Band 1 Enabled",
    "Band 3 Threshold",
]

DECLARED = ["Band 1 Used", "Band 1 Enabled", "Band 2 Frequency", "Band 2 Gain",
            "Band 2 Q", "Band 3 Threshold"]


def _slot(i, name="", manual="0.1234567687"):
    return (
        f'<PluginFloatParameter Id="{i}">'
        f'<ParameterName Value="{name}"/>'
        f'<ParameterId Value="-1"/>'
        f'<VisualIndex Value="1073741823"/>'
        f'<ParameterValue><Manual Value="{manual}"/></ParameterValue>'
        f'<LastUserRange><First Value="-30"/><Last Value="30"/></LastUserRange>'
        f'</PluginFloatParameter>'
    )


def _make_als(path, *, device_name="Pro-Q 4", named=None, n=8, gzipped=True):
    named = named if named is not None else NAMED[: min(len(NAMED), n)]
    slots = "".join(
        _slot(i, named[i] if i < len(named) else "",
              "2.17616272" if i == 0 else "0.1234567687")
        for i in range(n)
    )
    xml = (
        '<Ableton MajorVersion="5" MinorVersion="12.0_12120" '
        'Creator="Ableton Live 12.1" Revision="deadbeef">'
        "<LiveSet><Tracks><AudioTrack Id=\"0\"><DeviceChain><DeviceChain><Devices>"
        f'<PluginDevice Id="1"><Vst3PluginInfo><Name Value="{device_name}"/>'
        f"</Vst3PluginInfo><ParameterList>{slots}</ParameterList></PluginDevice>"
        "</Devices></DeviceChain></DeviceChain></AudioTrack></Tracks></LiveSet>"
        "</Ableton>"
    ).encode("utf-8")
    data = gzip.compress(xml, mtime=0) if gzipped else xml
    path.write_bytes(data)
    return path


def test_read_metadata_and_devices(tmp_path):
    p = _make_als(tmp_path / "set.als")
    info = read.file_info(p)
    assert info["minor_version"] == "12.0_12120"
    assert info["revision"] == "deadbeef"

    dev = read.device(p)
    assert dev.name == "Pro-Q 4"
    assert dev.slot_count == 8
    assert dev.exposed_count == 0
    assert dev.slots[0].name == "Band 2 Gain"
    assert dev.slots[0].manual == "2.17616272"
    assert not dev.slots[0].exposed


def test_uncompressed_als_is_accepted(tmp_path):
    p = _make_als(tmp_path / "plain.als", gzipped=False)
    assert read.file_info(p)["gzip"] is False
    assert read.device(p).slot_count == 8


def test_resolve_exposures_maps_declared_index_and_free_slot(tmp_path):
    p = _make_als(tmp_path / "set.als", named=[], n=4)
    dev = read.device(p)
    expose = configure.resolve_exposures(dev, DECLARED, ["Band 2 Gain"])
    assert expose[0].slot == 0
    assert expose[0].parameter_id == DECLARED.index("Band 2 Gain") == 3
    assert expose[0].name == "Band 2 Gain"
    assert expose[0].visual_index == 0


def test_resolve_exposures_rejects_unknown(tmp_path):
    p = _make_als(tmp_path / "set.als")
    with pytest.raises(configure.AlsConfigError):
        configure.resolve_exposures(read.device(p), DECLARED, ["Nope"])


def test_write_dry_run_writes_nothing(tmp_path):
    src = _make_als(tmp_path / "src.als")
    out = tmp_path / "out.als"
    exp = configure.Exposure(slot=0, name="Band 2 Gain", parameter_id=3, visual_index=0)
    result = configure.write(src, out, [exp])
    assert result.applied is False
    assert result.exposed_after == 1
    assert not out.exists()
    assert read.device(src).exposed_count == 0  # source untouched


def test_write_apply_is_surgical_and_validates(tmp_path):
    src = _make_als(tmp_path / "src.als")
    out = tmp_path / "out.als"
    orig = src.read_bytes()
    exp = configure.Exposure(slot=3, name="Band 2 Gain", parameter_id=3, visual_index=0)
    result = configure.write(src, out, [exp], apply=True)
    assert result.applied and out.exists()
    assert result.sha256_output
    assert src.read_bytes() == orig  # source never edited

    dev = read.device(out)
    assert dev.exposed_count == 1
    assert dev.slots[3].exposed
    assert dev.slots[3].parameter_id == 3
    assert dev.slots[3].name == "Band 2 Gain"


def test_write_refuses_in_place_and_overwrite(tmp_path):
    src = _make_als(tmp_path / "src.als")
    with pytest.raises(configure.AlsConfigError):
        configure.write(src, src, [configure.Exposure(0, "x", 1, 0)])

    configured = tmp_path / "configured.als"
    configure.write(src, configured,
                    [configure.Exposure(0, "Band 1 Enabled", 1, 0)], apply=True)
    out = tmp_path / "out.als"
    with pytest.raises(configure.AlsConfigError):
        configure.write(configured, out,
                        [configure.Exposure(0, "Band 2 Gain", 3, 1)], apply=True)
    # overwrite=True re-points the already-exposed slot
    result = configure.write(configured, out,
                             [configure.Exposure(0, "Band 2 Gain", 3, 1)],
                             apply=True, overwrite=True)
    assert result.applied and result.sha256_output


def test_diff_detects_exposure_change(tmp_path):
    src = _make_als(tmp_path / "src.als")
    out = tmp_path / "out.als"
    configure.write(src, out,
                    [configure.Exposure(0, "Band 2 Gain", 3, 0)], apply=True)
    changes = read.diff(read.read(src), read.read(out))
    paths = {c["path"] for c in changes}
    assert "devices[0].slots[0].parameter_id" in paths
    assert "devices[0].slots[0].visual_index" in paths
    assert not changes == []


def test_snapshot_restore_roundtrip(tmp_path):
    target = _make_als(tmp_path / "target.als")
    original = target.read_bytes()
    snap = snapshot.snapshot(target, tmp_path / "snaps")
    assert snapshot.verify(snap.snapshot, snap.sha256)

    target.write_bytes(b"corrupted")
    result = snapshot.restore(snap.snapshot, target, apply=True, force=True)
    assert result.applied
    assert target.read_bytes() == original
    assert result.backup is not None


def test_restore_refuses_without_force_when_live(monkeypatch, tmp_path):
    target = _make_als(tmp_path / "target.als")
    snap = snapshot.snapshot(target, tmp_path / "snaps")
    monkeypatch.setattr(snapshot, "live_socket_open", lambda *a, **k: True)
    with pytest.raises(snapshot.AlsSnapshotError):
        snapshot.restore(snap.snapshot, target, apply=True)


def test_declared_profile_from_real_proq4():
    names = pp.declared_parameter_names("Pro-Q 4")
    assert names is not None and len(names) == 737
    assert pp.declared_parameter_index("Pro-Q 4", "Band 2 Gain") == 26
    assert pp.declared_profile_path("Pro-Q 4").name == "Pro-Q-4_parameter_names.json"


def test_describe_channel_ladder():
    lom = pp.describe_channels("EQ Eight", parameter_count=84)
    assert lom["lom"]["available"] and not lom["als"]["available"]
    gui = pp.describe_channels("Pro-Q 4", parameter_count=1)
    assert not gui["lom"]["available"]
    assert gui["als"]["available"] and gui["uia"]["available"]
