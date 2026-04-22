#!/usr/bin/env python3
"""Generate three N8n master workflow JSON files under pipelines/ (session 08).

Run from repo root:
  python scripts/gen_pipeline_master_workflows.py

Uses Docker Compose DNS names on the nova-v2-network. Import each JSON in N8n
or upload via /api/v1/workflows with N8N_V2_API_KEY.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "pipelines"

# Minimal valid PNG (1x1) twice — Agent 24 needs ≥2 frames for /animate/review.
_TINY_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
_SHMUP_FRAMES_BODY = json.dumps({"frames_b64": [_TINY_PNG, _TINY_PNG], "fps_hint": 12.0})


def _node(
    nid: str,
    name: str,
    ntype: str,
    type_version: float,
    position: Tuple[int, int],
    parameters: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "parameters": parameters,
        "id": nid,
        "name": name,
        "type": ntype,
        "typeVersion": type_version,
        "position": list(position),
    }


def _connect_linear(names: List[str]) -> Dict[str, Any]:
    con: Dict[str, Any] = {}
    for i in range(len(names) - 1):
        a, b = names[i], names[i + 1]
        con[a] = {"main": [[{"node": b, "type": "main", "index": 0}]]}
    return con


def build_shmup() -> Dict[str, Any]:
    y = 260
    x0, dx = 200, 260
    nodes: List[Dict[str, Any]] = []
    names: List[str] = []

    def add(nm: str, http_params: Dict[str, Any]) -> None:
        nonlocal y
        nid = nm.lower().replace(" ", "_")
        nodes.append(_node(f"n_{nid}", nm, "n8n-nodes-base.httpRequest", 4.2, (x0 + dx * len(names), y), http_params))
        names.append(nm)

    nodes.append(
        _node(
            "wh_shmup",
            "Webhook",
            "n8n-nodes-base.webhook",
            2,
            (x0, y),
            {
                "httpMethod": "POST",
                "path": "pipeline-shmup-master",
                "responseMode": "responseNode",
                "options": {},
            },
        )
    )
    names.append("Webhook")

    add(
        "Agent20 Design",
        {
            "method": "POST",
            "url": "http://agent-20-design-fase:8120/palette/create",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ theme: $json.body.style || 'retro pulp', faction_count: 4, restrictions: { ship_concept: $json.body.ship_concept, faction: $json.body.faction } }) }}",
            "options": {"timeout": 120000},
        },
    )
    add(
        "Agent21 FreeCAD",
        {
            "method": "POST",
            "url": "http://agent-21-freecad-parametric:8121/model/build-base",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ category: 'fighter', dimensions: { length: 10, radius: 1.2 } }) }}",
            "options": {"timeout": 300000},
        },
    )
    add(
        "Agent22 Blender",
        {
            "method": "POST",
            "url": "http://agent-22-blender-renderer:8122/render",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({}) }}",
            "options": {"timeout": 60000},
        },
    )
    add(
        "Agent23 Aseprite",
        {
            "method": "POST",
            "url": "http://agent-23-aseprite-processor:8123/process",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({}) }}",
            "options": {"timeout": 60000},
        },
    )
    add(
        "Agent24 Anim Jury",
        {
            "method": "POST",
            "url": "http://agent-24-aseprite-anim-jury:8124/animate/review",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": _SHMUP_FRAMES_BODY,
            "options": {"timeout": 120000},
        },
    )
    add(
        "Agent25 PyQt",
        {
            "method": "POST",
            "url": "http://agent-25-pyqt-assembly:8125/assemble",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({}) }}",
            "options": {"timeout": 60000},
        },
    )
    add(
        "Agent01 Sprite Jury",
        {
            "method": "POST",
            "url": "http://sprite-jury-v2:8101/v1/verdict",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ pixel_integrity: 8.0, jury_scores: [7.5, 8.0] }) }}",
            "options": {"timeout": 60000},
        },
    )
    add(
        "Agent26 Godot",
        {
            "method": "POST",
            "url": "http://agent-26-godot-import:8126/import",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ assets: [], type: 'sprite' }) }}",
            "options": {"timeout": 300000},
        },
    )

    nodes.append(
        _node(
            "rsp_shmup",
            "Respond to Webhook",
            "n8n-nodes-base.respondToWebhook",
            1.1,
            (x0 + dx * len(names), y),
            {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}},
        )
    )
    names.append("Respond to Webhook")

    con = _connect_linear(names)
    return {
        "name": "pipeline_shmup_master",
        "nodes": nodes,
        "connections": con,
        "settings": {"executionOrder": "v1"},
        "meta": {"templateCredsSetupCompleted": True, "nova_session": "08", "pipeline": "shmup"},
    }


def build_bake() -> Dict[str, Any]:
    y = 260
    x0, dx = 200, 260
    nodes: List[Dict[str, Any]] = []
    names: List[str] = []

    def add(nm: str, http_params: Dict[str, Any]) -> None:
        nid = nm.lower().replace(" ", "_")
        nodes.append(_node(f"n_{nid}", nm, "n8n-nodes-base.httpRequest", 4.2, (x0 + dx * len(names), y), http_params))
        names.append(nm)

    nodes.append(
        _node(
            "wh_bake",
            "Webhook",
            "n8n-nodes-base.webhook",
            2,
            (x0, y),
            {
                "httpMethod": "POST",
                "path": "pipeline-bake-master",
                "responseMode": "responseNode",
                "options": {},
            },
        )
    )
    names.append("Webhook")

    add(
        "Agent13 PDOK",
        {
            "method": "POST",
            "url": "http://agent-13-pdok-downloader:8113/download",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ postcode: $json.body.postcode, layers: $json.body.layers || ['buildings','roads'] }) }}",
            "options": {"timeout": 120000},
        },
    )
    add(
        "Agent15 QGIS",
        {
            "method": "POST",
            "url": "http://agent-15-qgis-processor:8115/process",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ operation: 'buffer', geojson: null }) }}",
            "options": {"timeout": 120000},
        },
    )
    add(
        "Agent31 QGIS Analysis",
        {
            "method": "POST",
            "url": "http://agent-31-qgis-analysis:8131/analyze",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({}) }}",
            "options": {"timeout": 60000},
        },
    )
    add(
        "Agent32 GRASS",
        {
            "method": "POST",
            "url": "http://agent-32-grass-gis:8132/analyze",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({}) }}",
            "options": {"timeout": 60000},
        },
    )
    add(
        "Agent14 Blender Bake",
        {
            "method": "POST",
            "url": "http://agent-14-blender-baker:8114/bake",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ region: $json.body.area_name || 'Hoogeveen' }) }}",
            "options": {"timeout": 300000},
        },
    )
    add(
        "Agent04 3D Jury",
        {
            "method": "POST",
            "url": "http://agent-04-3d-model-jury:8104/review",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ job_id: 'bake-pipeline', artifact: { mesh_format: 'gltf', vertices: 1200 }, context: {} }) }}",
            "options": {"timeout": 120000},
        },
    )
    add(
        "Agent05 GIS Jury",
        {
            "method": "POST",
            "url": "http://agent-05-gis-jury:8105/review",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ job_id: 'bake-pipeline', artifact: { crs: 'EPSG:28992', layer_count: 2 }, context: {} }) }}",
            "options": {"timeout": 120000},
        },
    )
    add(
        "Agent19 Distribution",
        {
            "method": "POST",
            "url": "http://agent-19-distribution:8119/invoke",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ asset_id: 'bake-gltf-demo', consumer_id: 'nova-pipeline', consumer_key: $json.body.distribution_key || 'pipeline-dev-key', changelog: 'session08' }) }}",
            "options": {"timeout": 60000},
        },
    )

    nodes.append(
        _node(
            "rsp_bake",
            "Respond to Webhook",
            "n8n-nodes-base.respondToWebhook",
            1.1,
            (x0 + dx * len(names), y),
            {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}},
        )
    )
    names.append("Respond to Webhook")

    return {
        "name": "pipeline_bake_master",
        "nodes": nodes,
        "connections": _connect_linear(names),
        "settings": {"executionOrder": "v1"},
        "meta": {"templateCredsSetupCompleted": True, "nova_session": "08", "pipeline": "bake"},
    }


def build_story() -> Dict[str, Any]:
    y = 260
    x0, dx = 200, 240
    nodes: List[Dict[str, Any]] = []
    names: List[str] = []

    def add(nm: str, http_params: Dict[str, Any]) -> None:
        nodes.append(_node(f"n_{len(names)}", nm, "n8n-nodes-base.httpRequest", 4.2, (x0 + dx * len(names), y), http_params))
        names.append(nm)

    nodes.append(
        _node(
            "wh_story",
            "Webhook",
            "n8n-nodes-base.webhook",
            2,
            (x0, y),
            {
                "httpMethod": "POST",
                "path": "pipeline-story-master",
                "responseMode": "responseNode",
                "options": {},
            },
        )
    )
    names.append("Webhook")

    add(
        "Agent28 Story",
        {
            "method": "POST",
            "url": "http://agent-28-story-integration:8128/canon/search",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ query: ($json.body.scene_outline || '') + ' ' + ($json.body.canon || '') }) }}",
            "options": {"timeout": 60000},
        },
    )
    add(
        "Agent07 Narrative",
        {
            "method": "POST",
            "url": "http://agent-07-narrative-jury:8107/invoke",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ job_id: 'story-pipeline', text: $json.body.scene_outline, canon_hits: 2, voice_profile_matched: true }) }}",
            "options": {"timeout": 120000},
        },
    )
    add(
        "Agent27 Storyboard",
        {
            "method": "POST",
            "url": "http://agent-27-storyboard:8127/storyboard/generate",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ scene_description: $json.body.scene_outline, style_bible: $json.body.mood, panel_count: 2 }) }}",
            "options": {"timeout": 120000},
        },
    )
    add(
        "Agent08 Character Jury",
        {
            "method": "POST",
            "url": "http://agent-08-character-art-jury:8108/review",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ job_id: 'story-pipeline', artifact: { image_base64: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==' }, context: { characters: $json.body.characters } }) }}",
            "options": {"timeout": 120000},
        },
    )
    add(
        "Agent09 Illustration",
        {
            "method": "POST",
            "url": "http://agent-09-illustration-jury:8109/review",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ job_id: 'story-pipeline', artifact: { image_base64: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==' }, context: {} }) }}",
            "options": {"timeout": 120000},
        },
    )
    add(
        "Agent29 Register Voice",
        {
            "method": "POST",
            "url": "http://agent-29-elevenlabs:8129/voices/register",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ voice_id: 'v_story', label: 'Story pipeline', character_id: 'pipeline' }) }}",
            "options": {"timeout": 30000},
        },
    )
    add(
        "Agent29 ElevenLabs TTS",
        {
            "method": "POST",
            "url": "http://agent-29-elevenlabs:8129/invoke",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ action: 'tts', voice_id: 'v_story', text: 'Line read for pipeline validation.' }) }}",
            "options": {"timeout": 120000},
        },
    )
    add(
        "Agent30 Audio Jury",
        {
            "method": "GET",
            "url": "http://agent-30-audio-asset-jury:8130/health",
            "sendBody": False,
            "options": {"timeout": 30000},
        },
    )
    add(
        "Agent11 Monitor",
        {
            "method": "POST",
            "url": "http://agent-11-monitor:8111/feedback",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ message: 'pipeline_story_master completed', source: 'n8n', metadata: { pipeline: 'story' } }) }}",
            "options": {"timeout": 30000},
        },
    )

    nodes.append(
        _node(
            "rsp_story",
            "Respond to Webhook",
            "n8n-nodes-base.respondToWebhook",
            1.1,
            (x0 + dx * len(names), y),
            {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}},
        )
    )
    names.append("Respond to Webhook")

    return {
        "name": "pipeline_story_master",
        "nodes": nodes,
        "connections": _connect_linear(names),
        "settings": {"executionOrder": "v1"},
        "meta": {"templateCredsSetupCompleted": True, "nova_session": "08", "pipeline": "story"},
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    specs = [
        ("pipeline_shmup_master.json", build_shmup()),
        ("pipeline_bake_master.json", build_bake()),
        ("pipeline_story_master.json", build_story()),
    ]
    for fname, data in specs:
        path = OUT_DIR / fname
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print("wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
