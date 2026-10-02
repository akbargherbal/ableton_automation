"""automation.analysis.measure — measure a rendered audio file objectively.

Replaces the old "screenshot the LUFS meter and read it" workaround with real
numbers: integrated loudness (LUFS), true-peak estimate (dBTP), sample peak,
RMS, and coarse spectral band energy. Pure Python (soundfile + pyloudnorm +
numpy, scipy for the true-peak estimate); no Ableton involvement.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

try:
    import pyloudnorm as pyln
except ImportError:  # pragma: no cover
    pyln = None

try:
    from scipy.signal import resample_poly
except ImportError:  # pragma: no cover
    resample_poly = None

BANDS = {
    "sub": (20.0, 60.0),
    "low": (60.0, 250.0),
    "low_mid": (250.0, 800.0),
    "mid": (800.0, 2500.0),
    "high_mid": (2500.0, 6000.0),
    "high": (6000.0, 20000.0),
}


def _db(x: float) -> float:
    return float(20.0 * np.log10(max(x, 1e-12)))


def load_mono(path: Path | str) -> tuple[np.ndarray, int]:
    data, sr = sf.read(str(path), always_2d=True, dtype="float64")
    return np.asarray(data), int(sr)


def integrated_lufs(data: np.ndarray, sr: int) -> float | None:
    if pyln is None or data.size == 0:
        return None
    meter = pyln.Meter(sr)
    return float(meter.integrated_loudness(data))


def true_peak_dbtp(data: np.ndarray, oversample: int = 4) -> float | None:
    """Estimate true peak by oversampling before taking the sample peak."""
    if data.size == 0:
        return None
    if resample_poly is not None and oversample > 1:
        peak = 0.0
        for ch in range(data.shape[1]):
            up = resample_poly(data[:, ch], oversample, 1)
            peak = max(peak, float(np.max(np.abs(up))) if up.size else 0.0)
        return _db(peak)
    return _db(float(np.max(np.abs(data))))


def spectral_bands(data: np.ndarray, sr: int) -> dict[str, float]:
    if data.size == 0:
        return {}
    mono = data.mean(axis=1)
    windowed = mono * np.hanning(len(mono)) if len(mono) > 1 else mono
    spec = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(len(windowed), d=1.0 / sr)
    total = float(np.sum(spec ** 2))
    out: dict[str, float] = {}
    for band, (lo, hi) in BANDS.items():
        mask = (freqs >= lo) & (freqs < hi)
        energy = float(np.sum(spec[mask] ** 2))
        out[band] = 100.0 * energy / total if total > 0 else 0.0
    return out


def analyze(path: Path | str, target_lufs: float | None = None) -> dict:
    """Measure `path`; optionally report the gain needed to hit target_lufs."""
    data, sr = load_mono(path)
    duration = float(len(data) / sr) if sr else 0.0
    lufs = integrated_lufs(data, sr)
    tp = true_peak_dbtp(data)
    sample_peak = _db(float(np.max(np.abs(data)))) if data.size else None
    rms = _db(float(np.sqrt(np.mean(data ** 2)))) if data.size else None

    result: dict = {
        "file": str(path),
        "sample_rate": sr,
        "channels": int(data.shape[1]) if data.ndim == 2 else 0,
        "duration_seconds": round(duration, 3),
        "integrated_lufs": None if lufs is None else round(lufs, 2),
        "true_peak_dbtp": None if tp is None else round(tp, 2),
        "sample_peak_dbfs": None if sample_peak is None else round(sample_peak, 2),
        "rms_dbfs": None if rms is None else round(rms, 2),
        "spectral_bands_percent": {k: round(v, 2) for k, v in spectral_bands(data, sr).items()},
    }
    if target_lufs is not None and lufs is not None:
        result["target_lufs"] = target_lufs
        result["delta_lu"] = round(target_lufs - lufs, 2)
        result["suggested_gain_db"] = round(target_lufs - lufs, 2)
    return result


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Measure a rendered audio file.")
    parser.add_argument("file")
    parser.add_argument("--target-lufs", type=float, default=None)
    args = parser.parse_args()
    result = analyze(args.file, target_lufs=args.target_lufs)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
