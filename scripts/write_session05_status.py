"""Write status/agent_0X_status.json for session 05."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"L:/!Nova V2/status")
NOW = datetime.now(timezone.utc).isoformat()

AGENTS = [
    ("03", "audio_jury", "agent_03_audio_jury"),
    ("04", "3d_model_jury", "agent_04_3d_model_jury"),
    ("05", "gis_jury", "agent_05_gis_jury"),
    ("06", "cad_jury", "agent_06_cad_jury"),
    ("07", "narrative_jury", "agent_07_narrative_jury"),
    ("08", "character_art_jury", "agent_08_character_art_jury"),
    ("09", "illustration_jury", "agent_09_illustration_jury"),
]


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    for num, name, folder in AGENTS:
        payload = {
            "agent_number": num,
            "name": name,
            "folder": folder,
            "status": "built",
            "built_at": NOW,
            "deployed_at": None,
            "tests_passed": True,
            "v1_used": False,
            "fallback_used": True,
            "notes": "Session 05: FastAPI /review + pipeline_judge hook; n8n workflow includes nova-judge. Deployed_at set after Hetzner build.",
        }
        p = ROOT / f"agent_{num}_status.json"
        p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print("wrote", p)


if __name__ == "__main__":
    main()
