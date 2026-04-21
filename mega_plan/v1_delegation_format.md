# V1 Delegation Format — Hoe V1 Tasks Ontvangt

Specificatie van het delegatie protocol tussen Cursor en V1 orchestrator.

## Delegation API

Cursor stuurt tasks naar V1 orchestrator via HTTP POST.

**Endpoint:**
```
POST http://178.104.207.194:5678/webhook/nova_v2_build_task
```

**Headers:**
```
Content-Type: application/json
X-N8N-API-KEY: <v1_api_key>
X-Task-Source: cursor_mega_build
X-Task-Priority: normal|high
```

**Payload structure:**
```json
{
  "task_id": "build_agent_01_sprite_jury_<timestamp>",
  "task_type": "build_v2_agent",
  "v2_agent": {
    "number": "01",
    "name": "sprite_jury",
    "category": "jury_judge",
    "spec_file": "L:/!Nova V2/agents/nova_v2_agents/jury_judge/01_sprite_jury.md",
    "target_directory": "L:/!Nova V2/v2_services/sprite_jury/"
  },
  "requirements": {
    "language": "python",
    "python_version": "3.11",
    "framework": "FastAPI",
    "async": true,
    "include_tests": true,
    "include_dockerfile": true,
    "include_n8n_workflow": true
  },
  "dependencies": {
    "ollama": true,
    "postgres": false,
    "redis": false,
    "minio": true,
    "qdrant": true
  },
  "output_format": {
    "method": "return_inline",
    "structure": "zip_or_folder",
    "include_readme": true
  },
  "deadline_minutes": 30,
  "escalation_contact": "cursor_webhook_receiver"
}
```

## V1 Response Format

V1 orchestrator responds met:

**Success:**
```json
{
  "task_id": "build_agent_01_sprite_jury_<timestamp>",
  "status": "completed",
  "started_at": "2026-04-19T12:00:00Z",
  "completed_at": "2026-04-19T12:18:32Z",
  "duration_seconds": 1112,
  "agents_used": [
    "v1_code_generator_python",
    "v1_fastapi_scaffolder",
    "v1_test_writer",
    "v1_docker_builder"
  ],
  "output": {
    "files": [
      {
        "path": "main.py",
        "size_bytes": 4523,
        "purpose": "FastAPI service entry"
      },
      {
        "path": "jury/pixel_integrity.py",
        "size_bytes": 2341,
        "purpose": "Jury member 1"
      }
    ],
    "dockerfile": "...",
    "docker_compose_addition": "...",
    "n8n_workflow_json": "{...}",
    "test_suite": "...",
    "readme": "..."
  },
  "warnings": [],
  "next_steps": [
    "Deploy to V2 infrastructure",
    "Import N8n workflow",
    "Run integration tests"
  ]
}
```

**Failure:**
```json
{
  "task_id": "build_agent_01_sprite_jury_<timestamp>",
  "status": "failed",
  "error_type": "capability_missing",
  "error_message": "V1 does not have agent capable of generating Ollama vision prompts",
  "retry_possible": false,
  "fallback_recommendation": "cursor_handles_this_agent_directly",
  "partial_output": {
    "completed_files": ["main.py", "Dockerfile"],
    "missing": ["ollama_jury_members", "integration_tests"]
  }
}
```

## Alternatieve: Webhook Callback

Als V1 async werkt (heeft tijd nodig), gebruik callback pattern:

**Cursor registreert callback endpoint:**
```
POST http://<cursor_local_tunnel>/agent_build_complete
```

(Cursor opent tunnel via ngrok of gelijkwaardig naar lokale webhook)

**V1 initieert async, retourneert task_id:**
```json
{
  "task_id": "...",
  "status": "queued",
  "estimated_duration_minutes": 25,
  "callback_url_confirmed": true
}
```

**V1 belt callback als klaar:**
```
POST http://<cursor_local_tunnel>/agent_build_complete
Body: <success response zoals boven>
```

## V1 Orchestrator Workflow Setup

Als V1 nog geen workflow heeft voor deze taken:

**Cursor creëert workflow via V1 API:**

```bash
curl -X POST \
  -H "X-N8N-API-KEY: <v1_key>" \
  -H "Content-Type: application/json" \
  -d @v1_orchestrator_workflow.json \
  http://178.104.207.194:5678/api/v1/workflows
```

`v1_orchestrator_workflow.json` bevat:
- Webhook trigger (listens voor Cursor POSTs)
- Switch node op task_type
- Sub-workflow calls naar bestaande V1 agents
- Aggregation node
- Response to Cursor

## Fallback: Direct V1 Agent Invocation

Als geen orchestrator maar wel individual agents:

Cursor stuurt parallel naar meerdere V1 agents:

```python
# Pseudocode voor Cursor
tasks = [
    {"agent": "code_generator", "input": spec},
    {"agent": "fastapi_scaffolder", "input": spec},
    {"agent": "test_writer", "input": spec}
]

results = await asyncio.gather(*[
    call_v1_agent(task) for task in tasks
])

# Cursor combineert outputs zelf
combined = merge_agent_outputs(results)
```

## Communication Security

- Alle calls over HTTPS (setup via Caddy reverse proxy, later)
- Nu: HTTP met API key voldoende voor interne Hetzner communicatie
- Cursor moet HTTPS hebben naar buitenwereld als callbacks nodig
- API keys roteren elke 90 dagen (niet nu maar plannen)

## Rate Limiting

V1 heeft 68 agents, kan parallel werken, maar:
- Max 5 concurrent build tasks (anders overload V1)
- Cursor houdt queue, pusht 5 tegelijk
- Poll status elke 30 seconden

Als V1 overloaded signal:
- Cursor reduceert naar 2 concurrent
- Wacht op completions voor volgende

## Monitoring V1 Health Tijdens Build

Cursor check elke 10 minuten:
- V1 orchestrator responsive? (ping /health)
- V1 agent workers running? (count active workers)
- V1 error rate acceptabel? (< 10% error in last hour)
- V1 productie workflows nog werken? (niet alleen v2 build)

Als V1 degrades:
- Pauzeer v2 build
- Escaleer naar gebruiker
- V1 productie gaat voor v2 bouw

## Failure Modes

**V1 capability missing:**
- Sommige agent specs vragen capabilities die V1 niet heeft
- V1 moet dit detecteren, retourneren met status="capability_missing"
- Cursor skipped naar fallback mode voor die specifieke agent

**V1 output kwaliteit slecht:**
- Code compileert niet
- Tests falen trivial
- Cursor code jury (als al gebouwd) reviewt output
- Feedback terug naar V1 voor revisie (max 2x)
- Dan fallback naar Cursor zelf

**V1 te traag:**
- Task > 30 min zonder progress
- Cursor timeout
- Check V1 status, restart task of fallback
