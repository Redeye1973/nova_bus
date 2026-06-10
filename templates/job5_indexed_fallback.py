"""SM_Part1 Job 5 — Aseprite batch or PIL indexed fallback via NOVA."""
from __future__ import annotations

import shutil
import subprocess
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(r"L:\ZZZ ZZ NOVA GAME OUTPUT\31-05-2026\SM_Part1")
JOBS = Path(r"L:\ZZZZZ ZZ 31-05-2026")
CLEANUP_LUA = ROOT / "tools" / "cleanup.lua"
ASE_PATHS = [
    "aseprite",
    r"C:\Program Files\Aseprite\Aseprite.exe",
    r"C:\Program Files (x86)\Aseprite\Aseprite.exe",
]


def find_aseprite() -> str | None:
    for c in ASE_PATHS:
        found = shutil.which(c)
        if found:
            return found
        p = Path(c)
        if p.is_file():
            return str(p)
    local = Path(r"C:\Users\awsme\AppData\Local")
    if local.is_dir():
        for exe in local.rglob("Aseprite.exe"):
            return str(exe)
    return None


def pil_indexed(path: Path) -> tuple[int, int]:
    before = path.stat().st_size
    img = Image.open(path).convert("RGBA")
    img = img.convert("RGB").quantize(colors=256, method=Image.Quantize.FASTOCTREE)
    img = img.convert("RGBA")
    buf = BytesIO()
    img.save(buf, format="PNG")
    path.write_bytes(buf.getvalue())
    return before, path.stat().st_size


def main() -> int:
    CLEANUP_LUA.parent.mkdir(parents=True, exist_ok=True)
    CLEANUP_LUA.write_text(
        'local spr = app.activeSprite\nif spr then\n  spr.colorMode = ColorMode.INDEXED\n  app.command.SaveFileAs{ filename=spr.filename, ui=false }\nend\n',
        encoding="utf-8",
    )
    ase = find_aseprite()
    lines = [
        "Job 5 — Aseprite batch polish",
        f"Timestamp: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"Aseprite executable: {ase or 'NOT FOUND'}",
        f"cleanup.lua created: {CLEANUP_LUA}",
    ]
    processed = []
    dirs = [ROOT / "assets" / "sprites", ROOT / "assets" / "backgrounds"]
    pngs = []
    for d in dirs:
        if d.is_dir():
            pngs.extend(sorted(d.glob("*.png")))
    if ase:
        for png in pngs:
            ok = False
            for attempt in range(1, 3):
                cmd = [ase, "-b", str(png), "--script", str(CLEANUP_LUA)]
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                ok = r.returncode == 0
                if ok:
                    break
            processed.append(f"- {png.name}: aseprite attempt status={'ok' if ok else 'failed'}")
    else:
        lines.append("Fallback: PIL indexed quantization (Aseprite CLI unavailable)")
        for png in pngs:
            b, a = pil_indexed(png)
            processed.append(f"- {png.name}: {b} -> {a} bytes (indexed_fallback_pil)")
    lines.append(f"Processed PNG count: {len(pngs)}")
    lines.extend(processed)
    JOBS.mkdir(parents=True, exist_ok=True)
    (JOBS / "job5_done.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
