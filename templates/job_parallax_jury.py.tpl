"""SM_Part1 — Parallax Agent 36 jury + judge review."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(r"@@PROJECT_DIR@@")
JOBS = Path(r"@@JOBS_DIR@@")
JURY = "@@JURY_URL@@"
THRESHOLD = @@THRESHOLD@@


def main() -> int:
    bible_path = r"@@JOBS_DIR@@\agents\art_direction_bible.yaml"
    payload = {
        "job_id": f"parallax_review_{int(datetime.now(timezone.utc).timestamp())}",
        "project_path": str(ROOT),
        "layer_count": 5,
        "art_direction_bible_path": bible_path,
    }
    lines = [
        "Parallax Agent 36 — jury + judge",
        f"Timestamp UTC: {datetime.now(timezone.utc).isoformat()}",
        f"Jury: {JURY}/review",
        f"Project: {ROOT}",
        f"Art bible: {bible_path}",
        f"Regen threshold: < {THRESHOLD}",
        "",
    ]
    try:
        resp = requests.post(f"{JURY}/review", json=payload, timeout=60)
        data = resp.json() if resp.content else {}
    except Exception as exc:
        lines.append(f"ERROR: {exc}")
        JOBS.mkdir(parents=True, exist_ok=True)
        (JOBS / "parallax_jury_rapport.txt").write_text(chr(10).join(lines), encoding="utf-8")
        return 1

    check = data.get("check") if isinstance(data.get("check"), dict) else {}
    judge = data.get("judge") if isinstance(data.get("judge"), dict) else {}
    score = float(check.get("score", 0))
    verdict = str(judge.get("verdict", check.get("verdict", "?")))
    regen = bool(judge.get("regen", score < THRESHOLD))
    lines.append(f"Overall score: {score}")
    lines.append(f"Verdict: {verdict}")
    lines.append(f"Regen needed: {regen}")
    lines.append(f"z_order_ok: {check.get('z_order_ok')}")
    lines.append(f"script_ok: {check.get('script_ok')}")
    lines.append(f"tile_loop_ok: {check.get('tile_loop_ok')}")
    lines.append("")
    for layer in check.get("layer_scores") or []:
        if not isinstance(layer, dict):
            continue
        lines.append(
            f"- {layer.get('name')}: score={layer.get('score')} issues={layer.get('issues')}"
        )
    lines.append("")
    lines.append(json.dumps(data, ensure_ascii=True, indent=2)[:6000])
    JOBS.mkdir(parents=True, exist_ok=True)
    (JOBS / "parallax_jury_rapport.txt").write_text(chr(10).join(lines), encoding="utf-8")
    return 0 if score >= THRESHOLD else 2


if __name__ == "__main__":
    raise SystemExit(main())
