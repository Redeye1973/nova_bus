# Sessie H04 Rapport — CI/CD via GitHub Actions

- **Datum:** 2026-04-25
- **Status:** **SUCCESS**

## Wat is gebouwd

### Test workflow (`.github/workflows/test.yml`)
- **Trigger:** push naar main of cursor/* branches + pull requests
- **Auto-discovery:** vindt dynamisch alle agents in `v2_services/`
- **Per agent:** install deps + pytest (of import check als geen tests)
- **Lint:** ruff check op E/W/F errors
- **Secret scan:** zoekt naar API key patterns in codebase
- **Matrix:** fail-fast=false (één falende agent blokkeert anderen niet)

### Deploy workflow (`.github/workflows/deploy.yml`)
- **Trigger:** push naar main (na tests groen) + manual dispatch
- **Stappen:** rsync agents + compose → build → rolling deploy → health check
- **SSH:** via `webfactory/ssh-agent` met `HETZNER_SSH_KEY` secret
- **Health check:** verify 4 core containers healthy na deploy

## Vereiste GitHub Secrets (handmatig door Alex)
- `HETZNER_SSH_KEY`: private SSH key voor root@178.104.207.194
- Settings → Secrets → Actions → New repository secret

## Status badges (voor README)
```markdown
![Tests](https://github.com/Redeye1973/nova_bus/actions/workflows/test.yml/badge.svg)
![Deploy](https://github.com/Redeye1973/nova_bus/actions/workflows/deploy.yml/badge.svg)
```
