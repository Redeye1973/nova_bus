# NOVA Host Bridge

Single multi-tool HTTP service that runs on the developer PC and exposes
host-installed tools (FreeCAD, QGIS, future Blender / GIMP / Krita /
Inkscape / GRASS / Aseprite / Godot) to Hetzner-deployed NOVA v2 agents
over the existing Tailscale mesh.

## Why

Agents on Hetzner (Linux containers) can't run Windows-only or
heavy-install tools cheaply. Instead of bloating the Hetzner stack with
+1.5 GB containers per tool, we relay tool jobs over Tailscale to this
single FastAPI service on the dev PC, which owns the tool subprocesses.

## Architecture

```
Hetzner agent_21_freecad_parametric (container)
        │
        │  POST http://100.64.0.2:8500/freecad/parametric
        ▼
Tailscale (existing mesh: nova-hetzner ↔ alex-main-1)
        ▼
nova_host_bridge (this service, FastAPI on PC, 0.0.0.0:8500)
        │
        ├── adapters/freecad.py  -> subprocess freecadcmd.exe + scripts/freecad_parametric.py
        ├── adapters/qgis.py     -> subprocess qgis_process-qgis-ltr.bat
        ▼
host tool produces files under jobs/<job_id>/, agent fetches via
GET /jobs/<job_id>/files/<filename>
```

## Endpoints

| Method | Path                                   | Notes                                   |
|--------|----------------------------------------|-----------------------------------------|
| GET    | /health                                | liveness + auth-required flag           |
| GET    | /tools                                 | adapter availability + version          |
| POST   | /freecad/parametric                    | build a parametric primitive            |
| POST   | /qgis/run                              | run a Processing algorithm by name      |
| GET    | /qgis/algorithms?limit=N               | list available algorithms               |
| GET    | /jobs/{job_dir}/files/{filename}       | download produced file                  |
| DELETE | /jobs/{job_dir}                        | cleanup job working directory           |

## Configuration

`nova_config.yaml` at the project root:

```yaml
host_bridge:
  url: http://100.64.0.2:8500    # Tailscale IP of dev PC
  bind: 0.0.0.0
  port: 8500
host_tools:
  freecad:
    bin: 'C:\Program Files\FreeCAD 1.0\bin'
  qgis:
    bin: 'C:\Program Files\QGIS 3.40.13\bin'
```

Override via env: `NOVA_CONFIG_PATH`, `FREECAD_BIN`, `QGIS_BIN`,
`BRIDGE_WORKDIR`, `BRIDGE_TOKEN`.

## Auth

Optional bearer token via `BRIDGE_TOKEN` env var. If unset, no auth is
enforced (Tailscale is the trust boundary). For shared environments set
`BRIDGE_TOKEN` and have agents pass `Authorization: Bearer <token>`.

## Run

```powershell
cd L:\!Nova V2\nova_host_bridge
pip install -r requirements.txt
.\start_bridge.ps1
# or: python -m uvicorn main:app --host 0.0.0.0 --port 8500
```

Healthcheck:

```powershell
Invoke-RestMethod http://127.0.0.1:8500/health
Invoke-RestMethod http://127.0.0.1:8500/tools
```

From Hetzner, after the bridge is running on the PC:

```bash
ssh root@hetzner 'curl -s http://100.64.0.2:8500/health'
```

## Tailscale exposure

Both nodes are already on the tailnet:

| Node          | Tailscale IP   | Hostname    |
|---------------|----------------|-------------|
| dev PC        | 100.64.0.2     | alex-main-1 |
| Hetzner       | 100.64.0.1     | nova-hetzner|

The bridge binds `0.0.0.0:8500` so any tailnet peer can reach it. No
public-internet exposure. Windows Firewall may need a one-time inbound
rule for port 8500 (PowerShell, admin):

```powershell
New-NetFirewallRule -DisplayName "NOVA Host Bridge 8500" `
    -Direction Inbound -LocalPort 8500 -Protocol TCP -Action Allow `
    -Profile Private
```

## Adding a new tool

1. Add an adapter under `adapters/<tool>.py` with `is_available()` and
   one or more `run_*()` functions.
2. Register import in `adapters/__init__.py`.
3. Add a route block in `main.py`.
4. Extend `nova_config.yaml.host_tools.<tool>.bin`.
5. Update Hetzner agent code to call the new endpoint when
   `HOST_BRIDGE_URL` env is set.
