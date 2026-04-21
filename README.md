# NOVA v2

Werkmap voor de nieuwe NOVA-generatie (gescheiden van `L:\Nova` legacy).

## Structuur

| Map | Inhoud |
|-----|--------|
| `infrastructure/` | **n8n v2 + Docker** (Hetzner): compose, `.env.template`, deploy-scripts, deploy-prompts |
| `!Prompts/` | Zip-bronnen en uitpakmappen |
| `agents/` | Nieuwe agents (Python/CLI) |
| `pipelines/` | Pipelines en entrypoints |
| `docs/` | Documentatie en runbooks |
| `integrations/` | Koppelingen naar externe tools |

Zie **`infrastructure/README.md`** voor deploy en **`infrastructure/CURSOR_DEPLOY_PROMPT.md`** voor autonome uitrol.

## Access URLs (Hetzner v2)

| Service | URL |
|--------|-----|
| N8n v2 UI | http://178.104.207.194:5679 |
| N8n v2 webhooks | http://178.104.207.194:5680 |
| MinIO console | http://178.104.207.194:19001 |

MinIO S3 API (host): `http://178.104.207.194:19000` — zie `infrastructure/README.md` voor uitleg over de afwijkende poorten.

## Relatie

- Bestaande projecten blijven onder o.a. `L:\Nova\` staan tot je bewust migreert.
