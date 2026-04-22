"""Simple spectral band balance (numpy FFT), no librosa."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

import numpy as np


@dataclass
class SpectralResult:
    score: float
    low_db: float
    mid_db: float
    high_db: float
    warnings: Tuple[str, ...]


def _to_mono(x: np.ndarray) -> np.ndarray:
    if x.ndim == 1:
        return x.astype(np.float32, copy=False)
    return x.mean(axis=1).astype(np.float32, copy=False)


def analyze(samples: np.ndarray, sample_rate: int) -> SpectralResult:
    x = _to_mono(samples)
    n = len(x)
    if n < 256:
        return SpectralResult(7.0, 0.0, 0.0, 0.0, ("too_short_for_fft",))
    # Use up to ~0.5s for FFT stability
    use = min(n, max(512, sample_rate // 2))
    seg = x[:use] * np.hanning(use).astype(np.float32)
    spec = np.abs(np.fft.rfft(seg))
    freqs = np.fft.rfftfreq(use, 1.0 / float(sample_rate))
    eps = 1e-12
    db = lambda m: float(10.0 * np.log10(m + eps))

    def band_energy(lo: float, hi: float) -> float:
        m = (freqs >= lo) & (freqs < hi)
        if not np.any(m):
            return eps
        return float(np.mean(spec[m] ** 2) + eps)

    low_e = band_energy(20, 250)
    mid_e = band_energy(250, 4000)
    high_e = band_energy(4000, min(20000, sample_rate / 2 - 1))
    low_db, mid_db, high_db = db(low_e), db(mid_e), db(high_e)
    mx = max(low_db, mid_db, high_db)
    spread = mx - min(low_db, mid_db, high_db)
    warnings: list[str] = []
    if spread > 18.0:
        warnings.append("extreme_spectral_imbalance")
    score = 10.0 - min(spread * 0.25, 6.0)
    score = float(max(0.0, min(10.0, score)))
    return SpectralResult(score=score, low_db=low_db, mid_db=mid_db, high_db=high_db, warnings=tuple(warnings))


def to_jury_dict(r: SpectralResult) -> Dict[str, Any]:
    return {
        "member": "frequency_balance",
        "score": r.score,
        "spectrum_summary": {"low_db": r.low_db, "mid_db": r.mid_db, "high_db": r.high_db},
        "warnings": list(r.warnings),
    }
