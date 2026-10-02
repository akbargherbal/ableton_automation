import json

from automation.uia import _parse_events


def test_parses_event_lines_only():
    combined = "\n".join([
        "some noise",
        f"EVENT: {json.dumps({'type': 'action_start', 'label': 'x'})}",
        "more noise",
        f"EVENT: {json.dumps({'type': 'action_result', 'result': 'success'})}",
        "EVENT: not-json",
    ])
    events = _parse_events(combined)
    assert [e["type"] for e in events] == ["action_start", "action_result"]


def test_ignores_non_dict_payloads():
    assert _parse_events('EVENT: [1, 2, 3]') == []
