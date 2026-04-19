"""Master palette generator using color theory (POC / fallback)."""
from __future__ import annotations

import colorsys
from typing import Any, Dict, List


def generate_master_palette(theme: str, faction_count: int, restrictions: Dict[str, Any]) -> Dict[str, Any]:
    """32-color master palette with faction sub-palettes (5 colors each where possible)."""
    _ = restrictions  # reserved for future constraints

    theme_hues = {
        "space_noir": 220,
        "industrial": 30,
        "alien": 150,
        "neutral": 0,
    }
    base_hue = theme_hues.get(theme, 220)

    master_palette: List[str] = []
    for i in range(32):
        hue_deg = (base_hue + i * 11) % 360
        h = hue_deg / 360.0
        saturation = min(1.0, 0.6 + (i % 4) * 0.1)
        lightness = min(1.0, 0.3 + (i // 4) * 0.08)
        rgb = colorsys.hls_to_rgb(h, lightness, saturation)
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(rgb[0] * 255),
            int(rgb[1] * 255),
            int(rgb[2] * 255),
        )
        master_palette.append(hex_color)

    faction_palettes: Dict[str, List[str]] = {}
    for i in range(faction_count):
        start_idx = (i * 5) % 27  # avoid reading past 32 when slicing 5
        chunk = master_palette[start_idx : start_idx + 5]
        if len(chunk) < 5:
            chunk = master_palette[:5]
        faction_palettes[f"faction_{i}"] = chunk

    return {
        "master_palette": master_palette,
        "faction_palettes": faction_palettes,
        "theme": theme,
        "color_count": 32,
    }
