import numpy as np
import pytest

from automation.analysis import measure


@pytest.fixture
def tone(tmp_path):
    sr = 44100
    t = np.linspace(0, 2, 2 * sr, endpoint=False)
    x = 0.1 * np.sin(2 * np.pi * 1000 * t)
    path = tmp_path / "tone.wav"
    import soundfile as sf
    sf.write(str(path), np.stack([x, x], axis=1), sr)
    return path


def test_measures_integrated_lufs(tone):
    result = measure.analyze(tone)
    assert result["sample_rate"] == 44100
    assert result["channels"] == 2
    assert result["integrated_lufs"] == pytest.approx(-20.04, abs=0.5)
    assert result["spectral_bands_percent"]["mid"] > 90


def test_target_lufs_reports_gain(tone):
    result = measure.analyze(tone, target_lufs=-14)
    assert result["delta_lu"] > 0
    assert result["suggested_gain_db"] == pytest.approx(result["delta_lu"])
