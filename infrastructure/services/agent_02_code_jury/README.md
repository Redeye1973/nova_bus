# Agent 02 — Code Jury (POC)

FastAPI reviews Python (ast, radon, pycodestyle, bandit) and GDScript (heuristic syntax/style/security; no Godot binary in image).

## Endpoints

- `GET /health`
- `POST /review/python` — `{ "code": "...", "base64_encoded": false }`
- `POST /review/gdscript`
- `POST /review/batch` — `{ "files": [ { "language", "code", "path?" } ] }`
- `POST /review` — `{ "language": "python"|"gdscript", "code": "..." }` (n8n)

Port **8102**. Webhook: `http://178.104.207.194:5680/webhook/code-review`

## Local

```powershell
cd L:\!Nova V2\v2_services\agent_02_code_jury
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest tests/ -v
```
