---
id: 20260419_002_host_bridge_wired
in_reply_to: null
agent: cursor
status: complete
created: 2026-04-19T20:25:00Z
title: Host bridge wired; Agent 21 promoted to real FreeCAD
---

# Result Summary

NOVA Host Bridge is live op de PC en Agent 21 produceert nu **echte FreeCAD STEP files** via Tailscale ipv trimesh fallback. End-to-end pad geverifieerd vanaf Hetzner-container.

## What runs

| Component | Where | URL | Status |
|-----------|-------|-----|--------|
| nova_host_bridge | PC `alex-main-1` (PID 37800) | `http://0.0.0.0:8500` | live, FreeCAD 1.0.2 + QGIS 3.40.13 LTR detected |
| Bridge over Tailscale | Hetzner -> PC | `http://100.64.0.2:8500` / `http://alex-main-1:8500` | reachable, ~120 ms RTT |
| Agent 21 v0.2.0 | Hetzner container `nova-v2-agent-21-freecad-parametric` | image tag `:bridge` | health: `engine=freecad_via_bridge`, fallback_mode=false |

## E2E proof points

1. **PC bridge subprocess test**
   - `POST /freecad/parametric` capsule(L=14, R=1.5) → 533 ms, FCStd (2.4 KB) + STEP (4.4 KB) + STL (425 KB), volume 91.89 mm³, watertight ✓
   - `POST /qgis/run native:buffer` op 2 EPSG:28992 punten met DISTANCE=250 → 4.35 s, GeoPackage 98 KB output

2. **Hetzner -> PC bridge raw**
   - `curl http://alex-main-1:8500/health` van Hetzner → 200 in 119 ms
   - `curl http://100.64.0.2:8500/tools` → freecad available, qgis available

3. **Hetzner agent webhook -> bridge -> FreeCAD**
   - n8n webhook `POST /webhook/freecad-parametric` body `{"action":"build_base","payload":{"category":"vehicle","dimensions":{...4.5 1.8 1.6}}}` → 200
   - Response: `engine_used=freecad_via_bridge`, `bridge_elapsed_ms=559.55`, `volume=12.96 mm³` (= 4.5×1.8×1.6 ✓), `watertight=true`
   - STEP URL `http://100.64.0.2:8500/jobs/freecad_a5d46bb3a22b/files/base_vehicle.step` downloadable, header `ISO-10303-21` ✓

# Issues encountered (all resolved)

| Issue | Symptom | Fix |
|-------|---------|-----|
| `freecadcmd.exe` interpreteerde `--spec`/`--result` als files | `FileNotFoundError: result.json`, exit 0, geen result file | Switched to env vars `FC_SPEC` / `FC_RESULT` / `FC_WORKDIR` (commit) |
| `__name__ == "__main__"` was False onder freecadcmd | Script stil, geen output, geen result file | Roep `main()` direct aan op module-load (zonder guard) |
| `cmd /c "C:\Program Files\..."` parsing met spaties | `'C:\Program' is not recognized as an internal or external command` | `_run()` helper met `shell=True` + `subprocess.list2cmdline()` voor .bat |
| Bridge file URLs corrupt vanaf Linux container | `http://...jobs/L:\!Nova V2\...\freecad_xxx/files/...` (hele pad als segment) | `PureWindowsPath` voor splitsing, niet `Path` (PosixPath ziet `\` niet als sep) |

# Code changes (delta)

## New
- `nova_host_bridge/` — FastAPI 8500, FreeCAD + QGIS adapters, headless `freecad_parametric.py`, `start_bridge.ps1`, README, tests
- `nova_config.yaml` — host_bridge URL/bind/port, tailnet IPs/hostnames, host_tools paths

## Modified
- `v2_services/agent_21_freecad_parametric/main.py` v0.1.0 → **v0.2.0**:
  - Reads `HOST_BRIDGE_URL` / `BRIDGE_TOKEN` / `HOST_BRIDGE_TIMEOUT_S` env
  - `_bridge_call_freecad()`, `_bridge_probe()` cached, `_bridge_file_urls()` met `PureWindowsPath`
  - `/health`: nieuw `bridge` veld, `engine` switcht tussen `freecad_via_bridge` en `trimesh`
  - `/model/build-base`: bridge-first met trimesh fallback
  - `/variants/generate`: per-variant bridge call + jury op bridge-metrics; `engines_used` counter in response
- `v2_services/agent_21_freecad_parametric/tests/test_agent.py`: bijgewerkt voor v0.2 health shape (5 tests pass zonder bridge)
- `status/agent_21_status.json`: `engine: freecad_via_bridge`, `fallback_mode: false`, `bridge: {...}`
- Hetzner `/docker/nova-v2/docker-compose.yml`: `agent-21` krijgt `environment.HOST_BRIDGE_URL`, image tag `:bridge`
- `bridge/nova_bridge/handoff/shared_state/current_baseline.md`: 7 actieve agents incl. 21 met real FreeCAD
- `bridge/nova_bridge/handoff/shared_state/decisions.md`: 2 nieuwe entries (bridge architectuur + freecadcmd quirk)

# Tests

- Local pytest agent 21: **5/5 pass** (zonder HOST_BRIDGE_URL → trimesh path)
- Local pytest nova_host_bridge: pass (health, tools, auth, validation)
- Manual bridge smoke (TestClient + bridge env): bridge path actief, real STEP URLs
- E2E webhook Hetzner → bridge → FreeCAD: PASS, real STEP file downloadable
- agent_validator.py --agent 21: **OK 1/1**

# Operational notes

- Bridge draait nu handmatig (foreground uvicorn). Voor productie: Task Scheduler op PC (script `start_bridge.ps1`).
- Geen Windows Firewall tweak nodig: Tailscale interface accepteert bind 0.0.0.0:8500 default.
- `BRIDGE_TOKEN` env var is leeg → geen auth. Voor publiek tailnet zou ik token zetten en agent 21 zelfde token meegeven.
- Bridge-files leven op PC `L:\!Nova V2\nova_host_bridge\jobs\`. Voor cross-Hetzner artifact-handoff later naar MinIO uploaden (of bridge → MinIO sync endpoint).

# Recommendations for next batch

1. **Bridge auto-start** als Windows Service of Task Scheduler entry zodra setup stabiel.
2. **Agent 22 (Blender Renderer)**: zelfde patroon — adapter in `nova_host_bridge/adapters/blender.py`, headless render via `blender -b -P script.py`. Vereist Blender installatie op PC.
3. **Agent 28 (QGIS terrain)**: bridge heeft al `/qgis/run` endpoint, agent 28 kan direct hetzelfde route-of-fallback patroon overnemen.
4. **MinIO upload-on-completion** in bridge: zodra job klaar is, upload artifacts naar MinIO `freecad-artifacts/<job_id>/` zodat tweede Hetzner agent (b.v. simulator) ze kan ophalen zonder bridge-roundtrip.
5. **Token rotatie**: zet `BRIDGE_TOKEN` in Hetzner `.env` en PC env; agent 21 stuurt `Authorization: Bearer ...`.

Klaar voor batch 3 of een dedicated Blender/QGIS adapter sessie.
