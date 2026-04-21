# NOVA v2 — Docker / n8n stack

Bron: `nova_v2_infrastructure_final.zip` (uitgepakt en hier neergezet met **platte layout**).

## Layout (lokaal)

| Pad | Inhoud |
|-----|--------|
| `docker-compose.yml` | Stack: Postgres, Redis, n8n main/worker/webhook, MinIO, Qdrant |
| `.env.template` | Kopieer naar `.env` op de server en vul secrets |
| `scripts/deploy.sh` | Deploy op **Hetzner** onder `/docker/nova-v2/` (zie script) |
| `scripts/init-postgres.sh` | DB-init (mount in compose) |
| `config/n8n-custom/` | Optionele n8n custom files |

## Deploy op server

1. Kopieer deze map naar bv. `/docker/nova-v2/` (inhoud: `docker-compose.yml`, `.env`, `scripts/`, `config/`).
2. `cp .env.template .env` en vul alle waarden (geen `CHANGE_ME`).
3. `chmod +x scripts/*.sh`
4. `docker compose pull && docker compose up -d` **of** `bash scripts/deploy.sh` (past pad `/docker/nova-v2` toe).

**Poorten (host):** 5679 (n8n UI), 5680 (webhooks), 6333/6334 (Qdrant). v1 n8n op **5678** niet aanraken.

## MinIO poortafwijking (belangrijk)

Standaard MinIO gebruikt poorten 9000 (S3 API) en 9001 (console). Op deze Hetzner-server zijn die hostpoorten al bezet door een andere Docker-service. Daarom zijn de **host**-poorten in `docker-compose.yml` gezet op:

| Host (extern) | Container (intern) | Functie |
|---------------|-------------------|---------|
| 19000 | 9000 | MinIO S3 API |
| 19001 | 9001 | MinIO webconsole |

Container-intern blijft MinIO op 9000/9001 luisteren; alleen de Docker port mapping naar de host wijkt af.

**URLs (Hetzner `178.104.207.194`):**

- MinIO S3 API: `http://178.104.207.194:19000`
- MinIO Console: `http://178.104.207.194:19001`

Aangepaste bestanden met deze poorten: `docker-compose.yml`, `scripts/deploy.sh`, `scripts/hetzner_fase_5_8.py` (UFW/curl).

## Configuratie notities

### HTTP zonder TLS (development)

`N8N_SECURE_COOKIE=false` staat aan alle N8n services omdat we HTTP gebruiken zonder TLS. Voor productie: setup Caddy reverse proxy met Let's Encrypt en zet `N8N_SECURE_COOKIE` weer op default (true).

## Prompts

- `CURSOR_DEPLOY_PROMPT.md` — autonome Cursor-deploy
- `MASTER_DEPLOY_PROMPT.md` — master flow
- `SIMPLE_CURSOR_PROMPT.md` — korte variant
- `README_INFRA_PACKAGE.md` — uitgebreide package-README uit de zip
