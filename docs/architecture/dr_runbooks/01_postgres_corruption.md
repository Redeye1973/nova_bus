---
title: DR Runbook — Postgres Corruption
severity: critical
expected_time: 30-60 min
---

# Postgres Data Corruption / Loss

## Detectie
- Agent health checks falen op database connectivity
- Uptime Kuma alert: NOVA Postgres v2 DOWN
- Application errors: "connection refused" of "relation does not exist"

## Stappen

1. **Stop alle schrijvende services**
   ```bash
   cd /docker/nova-v2
   docker compose stop agent-11-monitor agent-16-cost-guard agent-12-bake-orchestrator agent-60-memory-curator
   ```

2. **Controleer Postgres status**
   ```bash
   docker logs nova-v2-postgres --tail 50
   docker exec nova-v2-postgres pg_isready
   ```

3. **Als container crashed: restart**
   ```bash
   docker compose restart postgres-v2
   sleep 10
   docker exec nova-v2-postgres pg_isready
   ```

4. **Als data corrupt: restore van backup**
   ```bash
   # Stop postgres
   docker compose stop postgres-v2
   
   # Verwijder huidige data
   docker volume rm nova-v2-postgres-data
   
   # Restore van Borg
   export BORG_REPO='u583230@u583230.your-storagebox.de:nova-v2-backup'
   borg list
   # Kies meest recente archive
   borg extract ::ARCHIVE_NAME docker/nova-v2/postgres-dump/
   
   # Recreate en import
   docker compose up -d postgres-v2
   sleep 10
   docker exec -i nova-v2-postgres psql -U postgres < postgres-dump/latest.sql
   ```

5. **Herstart services**
   ```bash
   docker compose up -d
   ```

## Verificatie
- `docker exec nova-v2-postgres psql -U postgres -d n8n_v2 -c "SELECT COUNT(*) FROM pipeline_checkpoints"`
- Alle agent health checks groen
- Uptime Kuma monitor groen

## Rollback
- Als restore mislukt: gebruik vorige Borg archive
- Laatste redmiddel: handmatige pg_dump van v1 Postgres als referentie
