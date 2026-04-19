"""Design consistency POC (histogram proxy; Qdrant deferred)."""
from __future__ import annotations

import base64
from io import BytesIO
from typing import Any, Dict, List, Optional

from PIL import Image


def check(
    concept_image_base64: str,
    faction: str,
    reference_assets: Optional[List[str]],
) -> Dict[str, Any]:
    _ = reference_assets
    img_data = base64.b64decode(concept_image_base64)
    img = Image.open(BytesIO(img_data)).convert("RGB")

    small = img.resize((50, 50))
    pixels = list(small.getdata())

    color_buckets: Dict[tuple[int, int, int], int] = {}
    for p in pixels:
        bucket = (p[0] // 32, p[1] // 32, p[2] // 32)
        color_buckets[bucket] = color_buckets.get(bucket, 0) + 1

    dominant_count = sum(1 for v in color_buckets.values() if v > 50)

    return {
        "faction": faction,
        "consistency_score": 0.75 if dominant_count < 5 else 0.5,
        "dominant_color_count": dominant_count,
        "outlier_aspects": [],
        "recommendation": "accept" if dominant_count < 5 else "review",
    }
