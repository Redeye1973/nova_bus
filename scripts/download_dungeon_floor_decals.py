"""Download PixelLab dungeon floor decals (cracked slab + broken hole).

Writes to:
1. Archive (verplicht): L:\\ZZZZZZ ZZ PROMPTS\\Assets\\aetherion\\pixellab\\tiles\\
2. Project: aetherion_segment_01/assets/dungeon/props/floor_{crack,hole}.png

Usage: python download_dungeon_floor_decals.py
"""

import ssl
import urllib.request
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context

KEY_PATHS = [
    Path(r"L:\ZZZZZZ ZZ PROMPTS\Project Aetherion\Secret pixellab ai key\key.txt"),
    Path(r"L:\Nova\Key's\PixelLab.txt"),
]

ARCHIVE_DIR = Path(r"L:\ZZZZZZ ZZ PROMPTS\Assets\aetherion\pixellab\tiles")
PROPS_DIR = Path(
    r"L:\! 2 Nova v2  OUTPUT !\Z Aetherion\blockout\aetherion_segment_01"
    r"\assets\dungeon\props"
)

DECALS = {
    "floor_crack": "8e95b517-fc6a-463d-94ca-499c9c90aaa2",
    "floor_hole": "93e2778d-45e9-4f84-a244-7ca6d4707fe0",
}

API = "https://api.pixellab.ai/mcp"


def token() -> str:
    for p in KEY_PATHS:
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
    raise SystemExit("no pixellab key found")


def fetch(url: str, tok: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {tok}",
            "User-Agent": "Mozilla/5.0 (NOVA asset sync)",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def main() -> None:
    tok = token()
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    PROPS_DIR.mkdir(parents=True, exist_ok=True)
    for key, obj_id in DECALS.items():
        data = fetch(f"{API}/map-objects/{obj_id}/download", tok)
        (ARCHIVE_DIR / f"dungeon_{key}_{obj_id[:8]}.png").write_bytes(data)
        (PROPS_DIR / f"{key}.png").write_bytes(data)
        print(f"OK {key}: {len(data)} bytes -> archive + {key}.png")


if __name__ == "__main__":
    main()
