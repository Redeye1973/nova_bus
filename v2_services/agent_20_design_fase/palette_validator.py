"""Validate palettes for distinguishability (delta-E76 in Lab, no colormath/numpy2 issues)."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


def hex_to_rgb255(hex_color: str) -> Tuple[float, float, float]:
    hex_color = hex_color.lstrip("#")
    return (
        float(int(hex_color[0:2], 16)),
        float(int(hex_color[2:4], 16)),
        float(int(hex_color[4:6], 16)),
    )


def _srgb_channel_to_linear(c: float) -> float:
    c = c / 255.0
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def rgb255_to_lab(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """sRGB D65 -> CIE Lab."""
    r_lin = _srgb_channel_to_linear(r)
    g_lin = _srgb_channel_to_linear(g)
    b_lin = _srgb_channel_to_linear(b)

    x = r_lin * 0.4124564 + g_lin * 0.3575761 + b_lin * 0.1804375
    y = r_lin * 0.2126729 + g_lin * 0.7151522 + b_lin * 0.0721750
    z = r_lin * 0.0193339 + g_lin * 0.1191920 + b_lin * 0.9503041

    x_n, y_n, z_n = 0.95047, 1.0, 1.08883
    x /= x_n
    y /= y_n
    z /= z_n

    def f(t: float) -> float:
        delta = 6 / 29
        if t > delta**3:
            return t ** (1 / 3)
        return t / (3 * delta**2) + 4 / 29

    fx, fy, fz = f(x), f(y), f(z)
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b_ = 200 * (fy - fz)
    return L, a, b_


def delta_e_76(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))


def validate(palette: List[str], faction_names: List[str]) -> Dict[str, Any]:
    _ = faction_names
    issues: List[Dict[str, Any]] = []

    if len(palette) < 2:
        return {"valid": True, "issues": [], "palette_size": len(palette)}

    labs: List[Tuple[float, float, float]] = []
    for c in palette:
        r, g, b = hex_to_rgb255(c)
        labs.append(rgb255_to_lab(r, g, b))

    for i in range(len(labs)):
        for j in range(i + 1, len(labs)):
            delta = delta_e_76(labs[i], labs[j])
            if delta < 15:
                issues.append(
                    {
                        "colors": [palette[i], palette[j]],
                        "delta_e": round(delta, 4),
                        "issue": "too_similar",
                    }
                )

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "palette_size": len(palette),
    }
