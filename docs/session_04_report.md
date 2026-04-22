# Sessie 04 rapport — Judge + self-heal laag

- **Timestamp:** 2026-04-22 (UTC, uitgevoerd na sessie 03)
- **Judge module:** gebouwd onder `v2_services/judge/` (`judge/nova_judge.py`, `judge_hook.py`, `worker_self_heal.py`, FastAPI `main.py`).
- **Tests:** **4/4 PASS** (`python -m pytest tests/ -v` vanuit `v2_services/judge`).
- **Self-heal worker:** `worker_loop_with_self_heal` toegevoegd zoals in sessiespecificatie (max 2 retries via `retry_count`).
- **Docker service `nova-judge`:** op Hetzner gebouwd en gestart (`docker compose build nova-judge`, `up -d` in `/docker/nova-v2`). Compose-blok staat ook in repo: `infrastructure/docker-compose.yml` (build `context: ../v2_services/judge`). Op de server is het equivalente YAML-blok toegevoegd vóór `volumes:` (eerste poging via inline Python gaf corrupte escapes; hersteld met `compose_nova_judge_snippet.yml` + replace-script op de host).
- **`/health`:** `docker exec nova-v2-judge curl -s http://localhost:8000/health` → `{"status":"ok","service":"nova-judge"}`. Compose healthcheck na opstarten: **healthy**.
- **Postgres `nova_assets`:** aangemaakt in database `n8n_v2` via `scripts/create_nova_assets.sql` (gekopieerd naar server, `psql -f` in container).
- **Status:** **SUCCESS** (deploy + health + DDL; compose op server handmatig gecorrigeerd na één mislukte patch — eindstaat gevalideerd).
- **Next:** sessie 05 — agent bouw batch 1 (juries 03–09).

## Opmerking

- Container publiceert poort **8000** alleen als `expose` op het Docker-netwerk; geen host-poort tenzij later toegevoegd. Agents op hetzelfde netwerk kunnen `http://nova-v2-judge:8000` gebruiken.
