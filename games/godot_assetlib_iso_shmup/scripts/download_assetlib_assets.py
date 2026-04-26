"""Download Asset Library assets via official API (User-Agent required). No Kenney."""
from __future__ import annotations

import io
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path

UA = "Mozilla/5.0 (compatible; NOVA-assetlib-bootstrap/1.0)"
ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "third_party"
GLTF_DST = ROOT / "vendor" / "kaykit_gltf"

ASSETS = (
    ("2124", "KayKit-Space-Base-Bits.zip"),
    ("2318", "GodotParadise-ProjectileComponent.zip"),
)


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def main() -> None:
    TP.mkdir(parents=True, exist_ok=True)
    for aid, name in ASSETS:
        meta = json.loads(
            http_get(f"https://godotengine.org/asset-library/api/asset/{aid}").decode("utf-8")
        )
        url = meta["download_url"]
        data = http_get(url)
        zpath = TP / name
        zpath.write_bytes(data)
        out = TP / name.replace(".zip", "")
        if out.exists():
            shutil.rmtree(out)
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            zf.extractall(out)
        print(f"OK asset {aid} -> {zpath}")

    # Minimal glTF subset for game (all from #2124)
    src = next(TP.glob("**/addons/kaykit_space_base_bits/Assets/gltf"))
    GLTF_DST.mkdir(parents=True, exist_ok=True)
    for fname in (
        "spacetruck.gltf",
        "spacetruck.bin",
        "structure_low.gltf",
        "structure_low.bin",
        "solarpanel.gltf",
        "solarpanel.bin",
        "spacebits_texture.png",
    ):
        shutil.copy2(src / fname, GLTF_DST / fname)
    print("Copied glTF subset to", GLTF_DST)


if __name__ == "__main__":
    main()
