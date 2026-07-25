"""Download PixelLab game-polish assets: 5 shop icons + city wall ring pieces.

Writes to:
1. Archive (verplicht): L:\\ZZZZZZ ZZ PROMPTS\\Assets\\aetherion\\pixellab\\{cat}\\
2. Project: aetherion_segment_01/assets/icons/icon_{id}.png en
   assets/buildings/city_walls/pixellab/{name}.png

Usage: python download_game_polish_assets.py
Re-runnable; pending objects worden gerapporteerd en overgeslagen.
"""

import ssl
import urllib.request
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context

KEY_PATHS = [
    Path(r"L:\ZZZZZZ ZZ PROMPTS\Project Aetherion\Secret pixellab ai key\key.txt"),
    Path(r"L:\Nova\Key's\PixelLab.txt"),
]

ARCHIVE_ROOT = Path(r"L:\ZZZZZZ ZZ PROMPTS\Assets\aetherion\pixellab")
PROJECT = Path(r"L:\! 2 Nova v2  OUTPUT !\Z Aetherion\blockout\aetherion_segment_01")
ICONS_DIR = PROJECT / "assets" / "icons"
WALLS_DIR = PROJECT / "assets" / "buildings" / "city_walls" / "pixellab"

ICONS = {
    "torch_longburn": "afdd63e8-51d4-4f15-a248-9613d74c1e8c",
    "spell_ward": "1afb3ee6-5055-4201-ad89-633956faa921",
    "spell_regen": "13ec745e-d147-488e-813c-04e92594ce3e",
    "key_dungeon_iron": "be45d6e0-84ea-48d8-bfc6-26529f6237c6",
    "key_gate_cipher": "93f2b58a-7f03-4903-8dda-e7652807aaff",
}

WALL_PIECES = {
    "wall_segment": "c351bf2a-a849-4ac5-9bc6-87e0ec382be0",
    "tower": "ec7fdda0-af56-4c8f-bfee-a0562f51862b",
    "gate": "a1f1bdff-f01d-47a1-9336-51659690b017",
}

ENTRANCES = {
    "cave": "78ec4cd8-c804-4b83-9440-78b92ff5f1e1",
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


def grab(tok: str, key: str, obj_id: str, category: str, project_path: Path) -> bool:
    try:
        data = fetch(f"{API}/map-objects/{obj_id}/download", tok)
    except Exception as exc:  # noqa: BLE001 — report and continue batch
        print(f"PENDING/FAIL {key}: {exc}")
        return False
    arch_dir = ARCHIVE_ROOT / category
    arch_dir.mkdir(parents=True, exist_ok=True)
    (arch_dir / f"{key}_{obj_id[:8]}.png").write_bytes(data)
    project_path.parent.mkdir(parents=True, exist_ok=True)
    project_path.write_bytes(data)
    print(f"OK {key}: {len(data)} bytes -> {project_path.name}")
    return True


def main() -> None:
    tok = token()
    missing = []
    for key, obj_id in ICONS.items():
        if not grab(tok, key, obj_id, "icons", ICONS_DIR / f"icon_{key}.png"):
            missing.append(key)
    for key, obj_id in WALL_PIECES.items():
        if not grab(tok, key, obj_id, "buildings", WALLS_DIR / f"{key}.png"):
            missing.append(key)
    entr_dir = PROJECT / "assets" / "props" / "entrances"
    for key, obj_id in ENTRANCES.items():
        if not grab(tok, key, obj_id, "landmarks", entr_dir / f"{key}.png"):
            missing.append(key)
    if missing:
        print(f"MISSING ({len(missing)}): {', '.join(missing)} — rerun later")


if __name__ == "__main__":
    main()
