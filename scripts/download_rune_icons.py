"""Download the 10 generated PixelLab rune icons.

Archive: L:\\ZZZZZZ ZZ PROMPTS\\Assets\\aetherion\\pixellab\\icons\\runes\\{slug}_{id8}.png
Game:    aetherion_segment_01\\assets\\icons\\icon_{rune_id}.png

Re-runnable: skips files that already exist and are valid PNGs.
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
ARCHIVE = Path(r"L:\ZZZZZZ ZZ PROMPTS\Assets\aetherion\pixellab\icons\runes")
GAME_ICONS = Path(r"L:\! 2 Nova v2  OUTPUT !\Z Aetherion\blockout\aetherion_segment_01\assets\icons")

RUNES = {
    "rune_of_might": "f3b85b56-bbc5-423f-99f5-42973eb6a68f",
    "rune_of_warding": "68432a04-6701-4601-9665-ad20c556a0cc",
    "rune_of_swiftness": "9b0d6701-aa8a-4c6b-8751-c8debfab3625",
    "rune_of_vigor": "3b2acd7c-bd64-42e4-b913-772e37e1dbb4",
    "rune_of_mind": "baf399e7-09ac-432e-8e7a-dec83b514b02",
    "rune_of_light": "24508795-681e-4b20-9b1c-24b81d21fe8a",
    "rune_of_flame": "87cef36a-a4d2-429f-a387-a6686719c904",
    "rune_of_frost": "e142f37e-9110-4621-9031-86b2ab8b4456",
    "rune_of_storms": "a7c7447a-77d6-40ab-a594-c691e39ba9d3",
    "rune_of_shadows": "292fc82b-5bcf-4706-8d3d-3182bd428dfa",
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
    GAME_ICONS.mkdir(parents=True, exist_ok=True)
    ok = failed = skipped = 0
    for rune_id, oid in RUNES.items():
        arch = ARCHIVE / f"{rune_id}_{oid[:8]}.png"
        game = GAME_ICONS / f"icon_{rune_id}.png"
        if valid_png(arch) and valid_png(game):
            skipped += 1
            continue
        data = b""
        for attempt in range(5):
            try:
                req = Request(DL.format(oid), headers={"Authorization": f"Bearer {key}"})
                with urlopen(req, timeout=60) as resp:
                    data = resp.read()
                if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) > 250:
                    break
                data = b""
            except Exception as exc:  # noqa: BLE001 — retry then report
                print(f"  attempt {attempt+1} {rune_id}: {exc}")
            time.sleep(12)
        if not data:
            print(f"FAIL {rune_id} ({oid[:8]})")
            failed += 1
            continue
        arch.write_bytes(data)
        game.write_bytes(data)
        print(f"ok   {rune_id} -> {arch.name} + {game.name} ({len(data)} bytes)")
        ok += 1
    print(f"done ok={ok} failed={failed} skipped={skipped}")


if __name__ == "__main__":
    main()
