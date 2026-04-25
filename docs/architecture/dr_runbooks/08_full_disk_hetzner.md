---
title: DR Runbook — Full Disk Hetzner
severity: high
expected_time: 15-30 min
---

# Full Disk op Hetzner Server

## Detectie
- Agent deep health checks: disk_space_warn = true
- Docker logs: "no space left on device"
- Containers crashen bij write operations

## Stappen

1. **Check disk usage**
   ```bash
   df -h /
   du -sh /docker/* | sort -rh | head -10
   du -sh /var/log/* | sort -rh | head -10
   docker system df
   ```

2. **Quick cleanup — Docker**
   ```bash
   # Verwijder stopped containers
   docker container prune -f
   
   # Verwijder unused images
   docker image prune -a -f
   
   # Verwijder build cache
   docker builder prune -f
   
   # Verwijder unused volumes (VOORZICHTIG)
   # docker volume prune -f  # alleen als je zeker bent
   ```

3. **Quick cleanup — Logs**
   ```bash
   # Truncate grote logs
   find /var/log -name "*.log" -size +100M -exec truncate -s 10M {} \;
   
   # Docker logs per container
   docker ps -q | xargs -I{} sh -c 'echo $(docker inspect --format "{{.Name}}" {}) $(docker inspect --format "{{.LogPath}}" {} | xargs ls -lh | awk "{print \$5}")'
   
   # Truncate Docker container logs
   truncate -s 0 /var/lib/docker/containers/*/*-json.log
   ```

4. **Als meer ruimte nodig**
   - Hetzner Console > Volumes > Add volume
   - Mount als extra storage voor /docker of /data
   - Of: server upgrade naar groter disk plan

## Preventie
- Data retention policies (config/retention_policies.yaml)
- Docker log rotation in daemon.json
- Dagelijkse cleanup cron
