"""Download the 7 PixelLab shop-type keepers.

Archive: L:\\ZZZZZZ ZZ PROMPTS\\Assets\\aetherion\\pixellab\\characters\\shopkeeper\\{slug}_{id8}.png
Game:    aetherion_segment_01\\assets\\sprites\\npc\\shopkeeper\\keeper_{type}.png

Re-runnable: skips valid existing files.
"""
from __future__ import annotations

import ssl
import time
from pathlib import Path
from urllib.request import Request, urlopen

ssl._create_default_https_context = ssl._create_unverified_context

DL = "https://api.pixellab.ai/mcp/objects/{}/download"
KEY_PATHS = [
    Path(r"L:\ZZZZZZ ZZ PROMPTS\Project Aetherion\Secret pixellab ai key\key.txt"),
    Path(r"L:\Nova\Key's\PixelLab.txt"),
]
ARCHIVE = Path(r"L:\ZZZZZZ ZZ PROMPTS\Assets\aetherion\pixellab\characters\shopkeeper")
GAME_DIR = Path(r"L:\! 2 Nova v2  OUTPUT !\Z Aetherion\blockout\aetherion_segment_01\assets\sprites\npc\shopkeeper")

KEEPERS = {
    "blacksmith": "328e7e02-1743-47c0-bc25-a712e5a66d73",
    "weapons": "a9ca20bb-b9ee-4759-a341-a5540f7f462e",
    "armor": "28634844-eb66-4d1d-a82c-7ad5133502ee",
    "potions": "8ac0dcd5-9943-435b-9b51-81c887c73079",
    "spells": "5e87f222-7147-4996-90aa-ee4409b31ef0",
    "jewelry": "d14e5c29-1287-40de-8440-fa28e1d7edba",
    "general": "78a985b3-943d-4fed-86ab-5f5861d2fd30",
}


def load_key() -> str:
    for p in KEY_PATHS:
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
    raise SystemExit("no pixellab key")


def valid_png(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 250 and path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def main() -> None:
    key = load_key()
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    GAME_DIR.mkdir(parents=True, exist_ok=True)
    ok = failed = skipped = 0
    for shop_type, oid in KEEPERS.items():
        arch = ARCHIVE / f"keeper_{shop_type}_{oid[:8]}.png"
        game = GAME_DIR / f"keeper_{shop_type}.png"
        if valid_png(arch) and valid_png(game):
            skipped += 1
            continue
        data = b""
        for attempt in range(6):
            try:
                req = Request(DL.format(oid), headers={"Authorization": f"Bearer {key}"})
                with urlopen(req, timeout=60) as resp:
                    data = resp.read()
                if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) > 250:
                    break
                data = b""
            except Exception as exc:  # noqa: BLE001 — retry then report
                print(f"  attempt {attempt+1} {shop_type}: {exc}")
            time.sleep(15)
        if not data:
            print(f"FAIL {shop_type} ({oid[:8]})")
            failed += 1
            continue
        arch.write_bytes(data)
        game.write_bytes(data)
        print(f"ok   {shop_type} -> {game.name} ({len(data)} bytes)")
        ok += 1
    print(f"done ok={ok} failed={failed} skipped={skipped}")


if __name__ == "__main__":
    main()
