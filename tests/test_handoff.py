from automation.handoff import Handoff, HandoffRequired, export_audio_handoff, format_handoff


def test_format_handoff_contains_everything():
    h = Handoff(id="x", title="Do the thing", menu_path="File > Thing",
                steps=["First", "Second"], expected="thing is done")
    text = format_handoff(h)
    assert "Do the thing" in text
    assert "File > Thing" in text
    assert "1. First" in text and "2. Second" in text
    assert "thing is done" in text


def test_export_handoff_pins_dialog_settings():
    h = export_audio_handoff(out_path=r"C:\out.wav", file_type="WAV",
                             bit_depth="24", sample_rate="44100")
    joined = "\n".join(h.steps)
    assert h.id == "export_audio"
    assert "Ctrl+Shift+R" in joined
    assert "Bit Depth = 24" in joined
    assert r"C:\out.wav" in joined


def test_handoff_required_carries_handoff():
    h = Handoff(id="y", title="Needs a human")
    err = HandoffRequired(h)
    assert err.handoff is h
