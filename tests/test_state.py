from automation import state


def _snap(tempo, tracks):
    return {"session": {"tempo": tempo, "track_count": len(tracks),
                        "master_track": {"volume": 0.85}}, "tracks": tracks}


def test_no_changes_is_empty():
    snap = _snap(120, [{"index": 0, "name": "A", "volume": 0.85, "devices": []}])
    assert state.diff(snap, snap) == []


def test_detects_tempo_and_track_changes():
    before = _snap(120, [{"index": 0, "name": "A", "volume": 0.85, "devices": []}])
    after = _snap(124, [{"index": 0, "name": "A", "volume": 0.70, "devices": []}])
    paths = {c["path"] for c in state.diff(before, after)}
    assert "session.tempo" in paths
    assert "tracks[0].volume" in paths


def test_detects_device_chain_change():
    before = _snap(120, [{"index": 0, "name": "A", "devices": []}])
    after = _snap(120, [{"index": 0, "name": "A", "devices": [{"name": "EQ Eight"}]}])
    change = [c for c in state.diff(before, after) if c["path"] == "tracks[0].devices"]
    assert change and change[0]["after"] == ["EQ Eight"]
