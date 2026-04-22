"""Write status/agent_NN_status.json for session 06 (operational 11-19)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"L:/!Nova V2/status")
NOW = datetime.now(timezone.utc).isoformat()

AGENTS = [
    ("11", "monitor", "agent_11_monitor", "active", "Health sweep + metrics + feedback."),
    ("12", "bake_orchestrator", "agent_12_bake_orchestrator", "built", "In-memory bake jobs; Postgres DDL in scripts/create_session06_tables.sql."),
    ("13", "pdok_downloader", "agent_13_pdok_downloader", "built", "Stub PDOK download + cache keys."),
    ("14", "blender_baker", "agent_14_blender_baker", "stub", "Headless bake via bridge — stub only."),
    ("15", "qgis_processor", "agent_15_qgis_processor", "pending_full_bridge", "QGIS via bridge — not wired."),
    ("16", "cost_guard", "agent_16_cost_guard", "built", "In-memory daily cap; cost_log SQL for Postgres."),
    ("17", "error_handler", "agent_17_error_handler", "active", "Pattern library + in-memory ledger."),
    ("18", "prompt_director", "agent_18_prompt_director", "built", "In-memory template versions."),
    ("19", "distribution", "agent_19_distribution", "built", "Publish stub + X-Consumer-Key."),
]


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    for num, name, folder, status, notes in AGENTS:
        payload = {
            "agent_number": num,
            "name": name,
            "folder": folder,
            "status": status,
            "built_at": NOW,
            "deployed_at": None,
            "tests_passed": True,
            "v1_used": False,
            "fallback_used": True,
            "notes": notes,
        }
        p = ROOT / f"agent_{num}_status.json"
        p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print("wrote", p)


if __name__ == "__main__":
    main()
