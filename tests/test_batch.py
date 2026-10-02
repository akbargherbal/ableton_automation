import json

from automation import batch
from automation.recipes import get as get_recipe


def test_load_json_list(tmp_path):
    p = tmp_path / "m.json"
    p.write_text(json.dumps([{"bpm": 122}, {"bpm": 124}]))
    rows, fmt = batch.load_manifest(p)
    assert fmt == "json" and len(rows) == 2


def test_load_json_items(tmp_path):
    p = tmp_path / "m.json"
    p.write_text(json.dumps({"items": [{"bpm": 122}]}))
    rows, fmt = batch.load_manifest(p)
    assert fmt == "json" and rows[0]["bpm"] == 122


def test_save_roundtrip_jsonl(tmp_path):
    p = tmp_path / "m.jsonl"
    rows = [{"bpm": 122, "_status": "done"}]
    batch.save_manifest(p, rows, "jsonl")
    loaded, fmt = batch.load_manifest(p)
    assert fmt == "jsonl" and loaded[0]["_status"] == "done"


def test_kwargs_only_known_params():
    recipe = get_recipe("set_tempo")
    kwargs = batch._kwargs_for({"bpm": "124", "junk": "x"}, recipe)
    assert kwargs == {"bpm": 124.0}
