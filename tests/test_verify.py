from automation.verify import find_param


def _params(*names):
    return {"parameters": [{"name": n, "value": 0.5} for n in names]}


def test_substring_match():
    p = find_param(_params("MAX: Output Level", "MAX: Character"), "output level")
    assert p is not None and p["name"] == "MAX: Output Level"


def test_exact_preferred_over_substring():
    p = find_param(_params("Gain", "Input Gain"), "gain", exact=True)
    assert p is not None and p["name"] == "Gain"


def test_missing_returns_none():
    assert find_param(_params("Attack"), "release") is None
