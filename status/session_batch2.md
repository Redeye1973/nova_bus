# NOVA V2 — Batch 2 report

Date: 2026-04-19
Scope: replace POC stubs of three Fase-1 agents with real implementations,
deploy to Hetzner, import + activate n8n workflow, run E2E webhook test,
update status JSON, commit.

## Summary

| Agent | Name              | Status | Fallback | Workflow ID         | Webhook                                                       | Validator |
|------:|-------------------|--------|----------|---------------------|---------------------------------------------------------------|-----------|
| 11    | monitor           | active | false    | 1QNapcDCCL7ji6Ho    | http://178.104.207.194:5680/webhook/monitor                   | OK        |
| 17    | error_handler     | active | false    | SWQEhqMpwd6ouatV    | http://178.104.207.194:5680/webhook/error-handler             | OK        |
| 21    | freecad_parametric| active | true     | IZ6cFzgA8NCprt5H    | http://178.104.207.194:5680/webhook/freecad-parametric        | OK        |

3 / 3 deployed. 0 failed. 1 in fallback (Agent 21).

## Per-agent test result

### Agent 11 — Monitor

- Pytest local: 4/4 (`tests/test_agent.py`)
- Webhook payload: `{"action":"sweep"}`
- Response: `targets_checked=32 up=32 down=0 alerts=0`
- Endpoints implemented: `/health /status /alerts /metrics /invoke`
- Notes: monitor scans all sister-agent `/health` URLs on internal Compose
  network and emits Prometheus-style `/metrics`. POC keeps state
  in-memory (no Postgres/Telegram); spec'd dashboards can plug into `/metrics`
  directly.

### Agent 17 — Error Handler

- Pytest local: 5/5 (`tests/test_agent.py`)
- Webhook payload: `{"action":"report","payload":{"service":"ollama_client","message":"ConnectionError to ollama on 11434"}}`
- Response: classification `ollama_connection_refused`, severity `high`,
  retry plan `attempt=1 delay_seconds=2 strategy=exponential_backoff`.
- Endpoints implemented: `/health /error/report /error/resolve /repair/history /invoke`
- Pattern library: `patterns.yaml` shipped in image with 9 patterns
  (Ollama, PDOK rate-limit, Blender OOM, Godot null-ref, disk full, Python
  syntax, generic timeout, Postgres, Redis).
- Notes: in-memory ledger, no Postgres in this POC. Easy upgrade path: swap
  the `ERRORS`/`HISTORY` stores for SQLAlchemy models.

### Agent 21 — FreeCAD Parametric (fallback)

- Pytest local: 5/5 (`tests/test_agent.py`)
- Webhook payload: `{"action":"generate","payload":{"base_model":{"category":"fighter"},"parameter_matrix":{"length":[8.0,12.0,16.0]}}}`
- Response: `variant_count=3 accepted=3 primitive=capsule`; per-variant jury
  scores `robustness/dimensional/export_quality` all 10/10, verdict `accept`.
- Endpoints implemented: `/health /model/build-base /variants/generate /components/assemble /invoke`
- Status: `fallback_mode=true`, `fallback_reason=freecad_not_installed`,
  `engine=trimesh`.

## Failed items

None.

## Architectural note: FreeCAD on Hetzner

FreeCAD is not present on the Hetzner host and not installable as a thin
container dependency (FreeCAD CLI is ~1.2 GB and would dwarf the rest of
this stack). For the parametric base/variant/assemble workflow we therefore
use `trimesh` to generate the same primitives (box / cylinder / capsule /
sphere) and report STL + GLB instead of STEP. The contract returned by the
endpoints matches the spec shape (jury blocks, judge verdict, file paths,
metrics) so downstream consumers (Blender Game Renderer 22, CAD Jury 06)
can accept either backend.

If full STEP-export and proper boolean assembly are needed later, options are:

1. Add FreeCAD as its own service container (`coin-or/freecad` images
   exist around 1.5 GB) and have agent 21 RPC into it.
2. Run FreeCAD on a workstation/host and expose it via SSH or a tiny REST
   shim; agent 21 then proxies requests.
3. Switch the parametric backend to OpenSCAD (smaller, easier to package).

This is documented in `agent_21_status.json` as `fallback_reason`.

## Recommendation for batch 3

Baseline of "active" Fase-1 operational + producer agents is now: 01, 02,
10, 11, 17, 20, 21 — i.e. monitor + error + design + a parametric producer
are all live. Logical batch 3 candidates:

- **Producers (Fase 1 finish-up):** 22 Blender Game Renderer (will hit the
  same external-tool problem as 21, plan ahead for the same fallback
  pattern), 23 Aseprite Processor, 25 PyQt Assembly, 26 Godot Import.
- **Operationals:** 12 Bake Orchestrator, 13 PDOK Downloader, 14 Blender
  Baker (external tool again), 16 Cost Guard.
- **Jury batch:** 03 Audio Jury, 04 3D Model Jury, 05 GIS Jury, 06 CAD
  Jury, 07 Narrative Jury, 08 Character Art Jury, 09 Illustration Jury.

Suggested next batch (3 agents, low risk, no external tool blocker):
- **12 Bake Orchestrator**
- **16 Cost Guard**
- **03 Audio Jury** (mock-mode if no live audio sources)

This keeps the orchestrator + budget tracker landing before more producers
come online, and adds one more jury so Monitor (11) can register more
"up" targets in real life rather than test-only sweeps.
