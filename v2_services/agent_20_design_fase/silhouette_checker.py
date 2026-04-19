"""Silhouette recognizability at target sizes (PIL POC)."""
from __future__ import annotations

import base64
from io import BytesIO
from typing import Any, Dict, List

from PIL import Image


def check(image_base64: str, target_sizes: List[int]) -> Dict[str, Any]:
    img_data = base64.b64decode(image_base64)
    img = Image.open(BytesIO(img_data)).convert("RGBA")

    results: Dict[str, Any] = {}
    for size in target_sizes:
        small = img.resize((size, size), Image.NEAREST)
        mask = small.split()[3] if small.mode == "RGBA" else None

        if mask:
            visible_pixels = sum(1 for p in mask.getdata() if p > 128)
            total = size * size
            coverage = visible_pixels / total
        else:
            coverage = 1.0

        results[f"size_{size}"] = {
            "coverage": coverage,
            "recognizable": 0.1 < coverage < 0.8,
            "notes": "good" if 0.2 < coverage < 0.6 else "check_manually",
        }

    return {
        "size_results": results,
        "recommendation": "accept"
        if all(r["recognizable"] for r in results.values())
        else "review",
    }
