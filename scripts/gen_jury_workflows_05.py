"""Generate workflow.json for jury agents 04-09 (sessie 05)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"L:/!Nova V2/v2_services")
SPECS = [
    (
        "agent_04_3d_model_jury",
        "NOVA 3D Model Jury",
        "3d-model-review",
        "http://agent-04-3d-model-jury:8104/review",
        "04_3d_model_jury",
    ),
    (
        "agent_05_gis_jury",
        "NOVA GIS Jury",
        "gis-review",
        "http://agent-05-gis-jury:8105/review",
        "05_gis_jury",
    ),
    (
        "agent_06_cad_jury",
        "NOVA CAD Jury",
        "cad-review",
        "http://agent-06-cad-jury:8106/review",
        "06_cad_jury",
    ),
    (
        "agent_07_narrative_jury",
        "NOVA Narrative Jury",
        "narrative-review",
        "http://agent-07-narrative-jury:8107/review",
        "07_narrative_jury",
    ),
    (
        "agent_08_character_art_jury",
        "NOVA Character Art Jury",
        "character-art-review",
        "http://agent-08-character-art-jury:8108/review",
        "08_character_art_jury",
    ),
    (
        "agent_09_illustration_jury",
        "NOVA Illustration Jury",
        "illustration-review",
        "http://agent-09-illustration-jury:8109/review",
        "09_illustration_jury",
    ),
]


def build_workflow(name: str, path: str, url: str, tag: str) -> dict:
    judge_body = (
        "={{ JSON.stringify({ task_result: { status: 'success', agent: '%s', jury: $json }, "
        "logs: ['entrypoint=v1','dispatch=v2','agent=%s'] }) }}" % (tag, tag)
    )
    review_body = (
        "={{ JSON.stringify({ job_id: $json.body?.job_id || 'n8n', "
        "artifact: $json.body?.artifact ?? $json.body, context: $json.body?.context ?? {} }) }}"
    )
    return {
        "name": name,
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": path,
                    "responseMode": "responseNode",
                    "options": {},
                },
                "id": "wb",
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": [240, 300],
                "webhookId": path,
            },
            {
                "parameters": {
                    "method": "POST",
                    "url": url,
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": review_body,
                    "options": {},
                },
                "id": "rev",
                "name": "Jury Review",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [520, 300],
            },
            {
                "parameters": {
                    "method": "POST",
                    "url": "http://nova-judge:8000/evaluate",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": judge_body,
                    "options": {},
                },
                "id": "jg",
                "name": "Pipeline Judge",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [760, 300],
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
                "position": [1000, 300],
            },
        ],
        "connections": {
            "Webhook": {"main": [[{"node": "Jury Review", "type": "main", "index": 0}]]},
            "Jury Review": {"main": [[{"node": "Pipeline Judge", "type": "main", "index": 0}]]},
            "Pipeline Judge": {"main": [[{"node": "Respond to Webhook", "type": "main", "index": 0}]]},
        },
        "settings": {"executionOrder": "v1"},
    }


def main() -> None:
    for folder, title, path, url, tag in SPECS:
        wf = build_workflow(title, path, url, tag)
        out = ROOT / folder / "workflow.json"
        out.write_text(json.dumps(wf, indent=2), encoding="utf-8")
        print("wrote", out)


if __name__ == "__main__":
    main()
