---
title: DR Runbook — Bridge Offline
severity: medium
expected_time: 10-20 min
---

# NOVA Bridge Offline

## Detectie
- Uptime Kuma: NOVA Bridge Heartbeat missed
- N8n workflows falen bij bridge calls

## Stappen

1. **Check bridge container**
   ```bash
   docker ps | grep bridge
   docker logs nova-bridge --tail 30
   ```

2. **Restart bridge**
   ```bash
   docker compose restart bridge
   ```

3. **Als bridge persistent faalt**
   - Check N8n webhook URL configuratie
   - Verify bridge environment variables
   - Check netwerk connectivity tussen containers

## Workaround
- Pipelines kunnen direct agents aanroepen zonder bridge
- N8n workflows met directe HTTP nodes als fallback

## Verificatie
- Bridge heartbeat push resumes in Uptime Kuma
- Test N8n workflow trigger succesvol
