"""SM_Part1 Job 6 — Nova Sprite Jury validation."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(r"C:\GODOT_PROJECTS\SM_Part1\assets\sprites")
JOBS = Path(r"L:\ZZZZZ ZZ 31-05-2026")
JURY = "http://127.0.0.1:8101"
THRESHOLD = 6.0


def main() -> int:
    lines = [
        "Job 6 — Nova Sprite Jury validatie",
        f"Timestamp UTC: {datetime.now(timezone.utc).isoformat()}",
        "Context: raptor_style_shmup_top_down",
        f"Jury base: {JURY} (fallback /v1/pixel-check)",
        f"Score drempel regeneratie: < {THRESHOLD}",
        "",
    ]
    for png in sorted(ROOT.glob("*.png")):
        score = 0.0
        verdict = "unknown"
        action = "geen"
        try:
            with png.open("rb") as fh:
                resp = requests.post(
                    f"{JURY}/v1/pixel-check",
                    files={"file": (png.name, fh, "image/png")},
                    timeout=30,
                )
            data = resp.json() if resp.content else {}
            score = float(data.get("score", 0))
            verdict = str(data.get("verdict", "unknown"))
            action = "geen" if score >= THRESHOLD else "regenerate (skipped — manual regen via job2)"
        except Exception as exc:
            action = f"jury error: {exc}"
        lines.extend([
            f"Bestandsnaam: {png.name}",
            f"  Score: {score}",
            f"  Verdict: {verdict}",
            f"  Actie: {action}",
            "",
        ])
    JOBS.mkdir(parents=True, exist_ok=True)
    (JOBS / "job6_jury_rapport.txt").write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
