#!/usr/bin/env python3
"""
Generate POC FastAPI services for NOVA v2 agents from manifest (fallback stubs).
Run from repo root: python scripts/scaffold_remaining_agents.py
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "v2_services"
INF = ROOT / "infrastructure" / "services"

# Skip: already implemented (sprite uses infra/services/sprite_jury; others below)
SKIP_SLUGS = {"01_sprite_jury", "agent_02_code_jury", "agent_20_design_fase"}

MANIFEST: list[dict[str, object]] = [
    # (slug, port, webhook_path, display_name, agent_num)
    {"slug": "agent_10_game_balance_jury", "port": 8110, "webhook": "balance-review", "name": "Game Balance Jury", "num": "10", "full": True},
    {"slug": "agent_21_freecad_parametric", "port": 8121, "webhook": "freecad-parametric", "name": "FreeCAD Parametric", "num": "21"},
    {"slug": "agent_22_blender_renderer", "port": 8122, "webhook": "blender-render", "name": "Blender Game Renderer", "num": "22"},
    {"slug": "agent_23_aseprite_processor", "port": 8123, "webhook": "aseprite-process", "name": "Aseprite Processor", "num": "23"},
    {"slug": "agent_25_pyqt_assembly", "port": 8125, "webhook": "pyqt-assembly", "name": "PyQt Assembly", "num": "25"},
    {"slug": "agent_26_godot_import", "port": 8126, "webhook": "godot-import", "name": "Godot Import", "num": "26"},
    {"slug": "agent_11_monitor", "port": 8111, "webhook": "monitor", "name": "Monitor", "num": "11"},
    {"slug": "agent_17_error_handler", "port": 8117, "webhook": "error-handler", "name": "Error Handler", "num": "17"},
    {"slug": "agent_07_narrative_jury", "port": 8107, "webhook": "narrative-review", "name": "Narrative Jury", "num": "07"},
    {"slug": "agent_28_story_integration", "port": 8128, "webhook": "story-integration", "name": "Story Text Integration", "num": "28"},
    {"slug": "agent_13_pdok_downloader", "port": 8113, "webhook": "pdok-download", "name": "PDOK Downloader", "num": "13"},
    {"slug": "agent_15_qgis_processor", "port": 8115, "webhook": "qgis-process", "name": "QGIS Processor", "num": "15"},
    {"slug": "agent_14_blender_baker", "port": 8114, "webhook": "blender-bake", "name": "Blender Baker", "num": "14"},
    {"slug": "agent_05_gis_jury", "port": 8105, "webhook": "gis-review", "name": "GIS Jury", "num": "05"},
    {"slug": "agent_24_aseprite_anim_jury", "port": 8124, "webhook": "aseprite-anim-review", "name": "Aseprite Animation Jury", "num": "24"},
    {"slug": "agent_29_elevenlabs", "port": 8129, "webhook": "audio-generate", "name": "ElevenLabs Audio", "num": "29"},
    {"slug": "agent_03_audio_jury", "port": 8103, "webhook": "audio-review", "name": "Audio Jury", "num": "03"},
    {"slug": "agent_30_audio_asset_jury", "port": 8130, "webhook": "audio-asset-review", "name": "Audio Asset Jury", "num": "30"},
    {"slug": "agent_18_prompt_director", "port": 8118, "webhook": "prompt-direct", "name": "Prompt Director", "num": "18"},
    {"slug": "agent_16_cost_guard", "port": 8116, "webhook": "cost-track", "name": "Cost Guard", "num": "16"},
    {"slug": "agent_27_storyboard", "port": 8127, "webhook": "storyboard", "name": "Storyboard Visual", "num": "27"},
    {"slug": "agent_08_character_art_jury", "port": 8108, "webhook": "character-review", "name": "Character Art Jury", "num": "08"},
    {"slug": "agent_31_qgis_analysis", "port": 8131, "webhook": "qgis-analysis", "name": "QGIS Analysis", "num": "31"},
    {"slug": "agent_32_grass_gis", "port": 8132, "webhook": "grass-analysis", "name": "GRASS GIS", "num": "32"},
    {"slug": "agent_35_raster_2d", "port": 8135, "webhook": "raster-2d", "name": "Raster 2D Processor", "num": "35"},
    {"slug": "agent_09_illustration_jury", "port": 8109, "webhook": "illust-review", "name": "2D Illustration Jury", "num": "09"},
    {"slug": "agent_12_bake_orchestrator", "port": 8112, "webhook": "bake-orchestrate", "name": "Bake Orchestrator", "num": "12"},
    {"slug": "agent_04_3d_model_jury", "port": 8104, "webhook": "3d-review", "name": "3D Model Jury", "num": "04"},
    {"slug": "agent_06_cad_jury", "port": 8106, "webhook": "cad-review", "name": "CAD Jury", "num": "06"},
    {"slug": "agent_19_distribution", "port": 8119, "webhook": "distribute", "name": "Distribution", "num": "19"},
]


def stub_main_py(num: str, name: str, port: int) -> str:
    return textwrap.dedent(
        f'''
        """POC stub — {name} (Agent {num}). Replace with full implementation."""
        from __future__ import annotations

        from typing import Any, Dict

        from fastapi import FastAPI

        app = FastAPI(title="NOVA v2 Agent {num}", version="0.0.1-poc")

        @app.get("/health")
        def health() -> Dict[str, str]:
            return {{"status": "ok", "agent": "{num}", "mode": "poc_stub"}}

        @app.post("/invoke")
        def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
            return {{
                "agent": "{num}",
                "agent_name": "{name}",
                "received_keys": list(body.keys()) if isinstance(body, dict) else [],
                "note": "POC stub — upgrade per spec",
            }}
        '''
    ).strip()


def dockerfile(port: int) -> str:
    return textwrap.dedent(
        f'''
        FROM python:3.11-slim
        WORKDIR /app
        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt
        COPY main.py .
        ENV PYTHONUNBUFFERED=1
        EXPOSE {port}
        CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{port}"]
        '''
    ).strip()


REQ = "fastapi>=0.109.0\nuvicorn[standard]>=0.27.0\npydantic>=2.5.0\npytest>=7.4.0\nhttpx>=0.26.0\n"


def workflow_json(name: str, webhook: str, port: int, service_kebab: str) -> str:
    return json.dumps(
        {
            "name": name,
            "nodes": [
                {
                    "parameters": {
                        "httpMethod": "POST",
                        "path": webhook,
                        "responseMode": "responseNode",
                        "options": {},
                    },
                    "id": f"wb_{webhook}",
                    "name": "Webhook",
                    "type": "n8n-nodes-base.webhook",
                    "typeVersion": 2,
                    "position": [240, 300],
                    "webhookId": webhook,
                },
                {
                    "parameters": {
                        "method": "POST",
                        "url": f"http://{service_kebab}:{port}/invoke",
                        "sendBody": True,
                        "specifyBody": "json",
                        "jsonBody": "={{ JSON.stringify($json.body ?? $json) }}",
                        "options": {},
                    },
                    "id": "http_inv",
                    "name": "Call Agent",
                    "type": "n8n-nodes-base.httpRequest",
                    "typeVersion": 4.2,
                    "position": [520, 300],
                },
                {
                    "parameters": {
                        "respondWith": "json",
                        "responseBody": "={{ $json }}",
                        "options": {},
                    },
                    "id": "rsp",
                    "name": "Respond to Webhook",
                    "type": "n8n-nodes-base.respondToWebhook",
                    "typeVersion": 1.1,
                    "position": [800, 300],
                },
            ],
            "connections": {
                "Webhook": {"main": [[{"node": "Call Agent", "type": "main", "index": 0}]]},
                "Call Agent": {"main": [[{"node": "Respond to Webhook", "type": "main", "index": 0}]]},
            },
            "settings": {"executionOrder": "v1"},
        },
        indent=2,
    )


def test_py() -> str:
    return textwrap.dedent(
        '''
        from fastapi.testclient import TestClient
        from main import app

        def test_health():
            c = TestClient(app)
            r = c.get("/health")
            assert r.status_code == 200
            assert r.json().get("status") == "ok"
        '''
    ).strip()


def service_kebab(slug: str) -> str:
    return slug.replace("_", "-")


def compose_block(slug: str, port: int) -> str:
    key = service_kebab(slug)
    img = "nova-v2-" + slug.replace("_", "-") + ":poc"
    cname = "nova-v2-" + slug.replace("_", "-")
    return textwrap.dedent(
        f"""\
  {key}:
    build:
      context: ./services/{slug}
    image: {img}
    container_name: {cname}
    restart: unless-stopped
    expose:
      - "{port}"
    networks:
      - nova-v2-network
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:{port}/health')"]
      interval: 60s
      timeout: 15s
      retries: 3"""
    )


def emit_compose() -> str:
    blocks: list[str] = []
    for entry in MANIFEST:
        slug = str(entry["slug"])
        port = int(entry["port"])
        blocks.append(compose_block(slug, port))
    return "\n\n".join(blocks) + "\n"


def main() -> None:
    sc = 0
    for entry in MANIFEST:
        slug = str(entry["slug"])
        if slug in SKIP_SLUGS:
            continue
        if entry.get("full"):
            continue  # agent 10 hand-authored separately
        port = int(entry["port"])
        num = str(entry["num"])
        name = str(entry["name"])
        webhook = str(entry["webhook"])
        dst = V2 / slug
        dst.mkdir(parents=True, exist_ok=True)
        (dst / "main.py").write_text(stub_main_py(num, name, port) + "\n", encoding="utf-8")
        (dst / "requirements.txt").write_text(REQ, encoding="utf-8")
        (dst / "Dockerfile").write_text(dockerfile(port) + "\n", encoding="utf-8")
        sk = service_kebab(slug)
        (dst / "workflow.json").write_text(
            workflow_json(f"NOVA {name}", webhook, port, sk) + "\n", encoding="utf-8"
        )
        (dst / "tests").mkdir(exist_ok=True)
        (dst / "tests" / "test_stub.py").write_text(test_py() + "\n", encoding="utf-8")
        inf = INF / slug
        inf.mkdir(parents=True, exist_ok=True)
        for fn in ["main.py", "requirements.txt", "Dockerfile", "workflow.json"]:
            (inf / fn).write_text((dst / fn).read_text(encoding="utf-8"), encoding="utf-8")
        (inf / "tests").mkdir(exist_ok=True)
        (inf / "tests" / "test_stub.py").write_text((dst / "tests" / "test_stub.py").read_text(encoding="utf-8"), encoding="utf-8")
        sc += 1

    frag = ROOT / "infrastructure" / "compose_bulk_agents.fragment.yml"
    frag.write_text(emit_compose(), encoding="utf-8")

    print(f"Scaffolded {sc} stub agents. Wrote {frag.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
