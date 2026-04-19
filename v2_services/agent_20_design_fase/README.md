# Agent 20 — Design Fase (POC)

FastAPI service: master palette generation, delta-E validation, silhouette and consistency checks (fallback / deterministic).

## Endpoints

- `GET /health`
- `POST /palette/create`
- `POST /palette/validate`
- `POST /silhouette/check`
- `POST /consistency/check`

Internal port: **8120**  
V2 webhook (via n8n): `http://178.104.207.194:5680/webhook/design-fase`

## Local

```powershell
cd L:\!Nova V2\v2_services\agent_20_design_fase
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest tests/ -v
```

## Docker

```powershell
docker build -t nova-v2-agent-20-design-fase:poc .
```
