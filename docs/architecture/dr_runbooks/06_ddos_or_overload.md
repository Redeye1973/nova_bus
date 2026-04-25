---
title: DR Runbook — DDoS of Server Overload
severity: critical
expected_time: 15-30 min
---

# DDoS of Server Overload

## Detectie
- SSH timeout naar 178.104.207.194
- Uptime Kuma: meerdere monitors DOWN
- Hetzner Cloud Console: server unreachable

## Stappen

1. **Check via Hetzner Console**
   - Login op console.hetzner.cloud
   - Server > Graphs > CPU/Network usage
   - Als CPU >95% sustained: overload
   - Als network spike: mogelijk DDoS

2. **Bij overload (niet DDoS)**
   ```bash
   # Via Hetzner Console terminal (als SSH niet werkt)
   # Stop non-critical containers
   cd /docker/nova-v2
   docker compose stop $(docker compose config --services | grep -E 'jury|processor')
   
   # Check load
   uptime
   top -bn1 | head -20
   ```

3. **Bij DDoS**
   - Hetzner Support ticket: https://console.hetzner.cloud/support
   - Tijdelijk firewall rules via Hetzner Cloud
   - Overweeg Hetzner DDoS protection activeren

4. **Na recovery**
   ```bash
   bash /docker/nova-v2/scripts/staggered_startup.sh docker-compose.yml
   ```

## Preventie
- Resource limits in docker-compose (al actief)
- Staggered startup (al actief)
- Server upgrade bij structurele groei
