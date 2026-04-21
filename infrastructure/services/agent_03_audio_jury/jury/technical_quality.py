"""Clipping, DC offset, RMS, silence ratio — numpy only."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

import numpy as np


@dataclass
class TechnicalResult:
    score: float
    clipping_fraction: float
    dc_offset: float
    peak_linear: float
    rms_dbfs: float
    silence_ratio: float
    issues: Tuple[str, ...]


def _to_mono_f32(samples: np.ndarray) -> np.ndarray:
    if samples.ndim == 1:
        x = samples.astype(np.float32, copy=False)
    else:
        x = samples.mean(axis=1).astype(np.float32, copy=False)
    peak = float(np.max(np.abs(x)) + 1e-12)
    if peak > 1.0:
        x = x / peak
    return x


def analyze(samples: np.ndarray, sample_rate: int) -> TechnicalResult:
    """samples: shape (n,) or (n, ch) int16 or float32 linear ~[-1,1]."""
    _ = sample_rate
    x = _to_mono_f32(samples)
    peak = float(np.max(np.abs(x)))
    rms = float(np.sqrt(np.mean(np.square(x)) + 1e-20))
    rms_dbfs = float(20.0 * np.log10(rms + 1e-9))
    dc = float(np.mean(x))
    clip = float(np.mean(np.abs(x) >= 0.999))
    silence = float(np.mean(np.abs(x) < 1e-4))
    issues: list[str] = []
    if clip > 1e-4:
        issues.append("clipping_detected")
    if abs(dc) > 0.02:
        issues.append("dc_offset_elevated")
    if silence > 0.95:
        issues.append("mostly_silence")
    if peak < 1e-5:
        issues.append("near_zero_signal")

    score = 10.0
    score -= min(clip * 5000, 6.0)
    score -= min(abs(dc) * 80, 3.0)
    score -= max(0.0, -rms_dbfs - 3) * 0.15
    if silence > 0.95:
        score -= 4.0
    score = float(max(0.0, min(10.0, score)))

    return TechnicalResult(
        score=score,
        clipping_fraction=clip,
        dc_offset=dc,
        peak_linear=peak,
        rms_dbfs=rms_dbfs,
        silence_ratio=silence,
        issues=tuple(issues),
    )


def to_jury_dict(r: TechnicalResult) -> Dict[str, Any]:
    return {
        "member": "technical_quality",
        "score": r.score,
        "clipping_fraction": r.clipping_fraction,
        "dc_offset": r.dc_offset,
        "peak_linear": r.peak_linear,
        "rms_dbfs": r.rms_dbfs,
        "silence_ratio": r.silence_ratio,
        "issues": list(r.issues),
    }
