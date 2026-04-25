# Sessie D4 + D5 Rapport — External Monitoring + DR Drill

- **Datum:** 2026-04-25
- **Sessie:** Day Build D4 + D5 (gecombineerd)
- **Status:** **SUCCESS**

---

## D4 — Uptime Kuma (self-hosted)

### Deployed
- **Container:** `uptime-kuma` op prod (127.0.0.1:3001, alleen via SSH tunnel)
- **Image:** `louislam/uptime-kuma:1`
- **Compose:** `/docker/uptime-kuma/docker-compose.yml`
- **Data:** `/docker/uptime-kuma/data/`

### Monitors (6 stuks)

| # | Naam | Type | Status |
|---|------|------|--------|
| 1 | NOVA V2 N8n | HTTP(s) :5679 | Online |
| 2 | NOVA Bridge Heartbeat | Push (60s interval) | Online |
| 3 | NOVA Postgres v2 | Docker Container | Online |
| 4 | NOVA Judge | HTTP(s) :11000 | Offline (port niet gemapped — moet Docker Container type worden) |
| 5 | NOVA V1 N8n | HTTP(s) :5678/healthz | Online |
| 6 | NOVA Postgres v1 | Docker Container | Online |

### Bridge Heartbeat Pipeline

```
NOVA_Kuma_Tunnel (NSSM)          NOVA_Heartbeat (NSSM)
   |                                |
   SSH -L 3001:127.0.0.1:3001      elke 60s:
   PC -> prod                      check localhost:8500/health
                                    push -> localhost:3001/api/push/...
                                    (via tunnel naar Kuma)
```

**NSSM services (auto-start, no login required):**

| Service | Status | Function |
|---------|--------|----------|
| NOVA_Kuma_Tunnel | Running | SSH tunnel PC:3001 -> prod:3001 |
| NOVA_Heartbeat | Running | Bridge health -> Kuma push |

**Keys/secrets:**
- SSH key: `L:\tools\nova\secrets\id_ed25519` (kopie, locked ACL: SYSTEM=R, Admin=F)
- Push URL: `L:\tools\nova\secrets\push_url.txt` (zelfde ACL)

### UptimeRobot
Overgeslagen (user request).

---

## D5 — Full DR Drill

### DR Drill uitvoering

| Stap | Tijd | Resultaat |
|------|------|-----------|
| T0: Start | 03:28 | - |
| T1: Borg list archives | 03:28 | 2 archives gevonden |
| T2: Borg extract latest | 03:31 | `nova-2026-04-24_23-16-42` extracted |
| T3: Postgres sandbox start | 03:31 | `postgres:16-alpine` ready |
| T4: V2 restore | 03:31 | rc=0, 79 tables in n8n_v2 |
| T5: V1 restore | 03:31 | rc=0, 110 tables gitea, 4 tables nova |
| T6: Cleanup | 03:31 | sandbox removed |
| **Totaal** | **~3 min** | **PASS** |

### Restore verificatie

| Database | Tabellen | SQL Errors | Verdict |
|----------|----------|------------|---------|
| n8n_v2 | 79 | 1 (DROP postgres role — verwacht bij pg_dumpall) | PASS |
| gitea | 110 | 0 | PASS |
| nova | 4 | 0 | PASS |
| **Totaal** | **193** | **1 (verwacht)** | **PASS** |

### Archive inhoud

```
postgres-v2-2026-04-24_23-16-42.sql   1.2 MB
postgres-v1-2026-04-24_23-16-42.sql   258 KB
n8n-v1-workflows-2026-04-24_23-16-42.json
docker-nova-v2-2026-04-24_23-16-42/   (complete config tree)
.nova_secrets
```

### DR Procedure
Gedocumenteerd in `docs/DR_PROCEDURE.md`:
- Scenario A: Server crash, data intact
- Scenario B: Volledige restore op nieuwe server (10 stappen)
- Scenario C: Standalone DR test (bewezen werkend)

### PC ↔ Storage Box
- PC SSH key geinstalleerd op Storage Box via `install-ssh-key`
- Poort 22 werkt (SFTP), poort 23 geblokkeerd door ISP
- Borg remote access vereist poort 23 → bij echte disaster: andere ISP/VPN of restore via intermediary server

---

## Iteratie-log

| Probleem | Oplossing |
|----------|-----------|
| SSH tunnel service crashte (key permissies te open voor LocalSystem) | Key gekopieerd naar `L:\tools\nova\secrets\` met ICACLs |
| Heartbeat kon secrets niet lezen (LocalSystem ACL) | Push URL apart in `L:\tools\nova\secrets\push_url.txt` met SYSTEM=Read |
| Push URL BOM (PowerShell UTF-8-BOM) | `UTF8Encoding($false)` + heartbeat leest `utf-8-sig` |
| Borg docker image (pschmitt) te oud (1.1.7, geen SSH) | Alpine 3.20 + `apk add borgbackup openssh-client` |
| Docker volume mount 0777 keys | `cp + chmod 600` in container |
| Port 23 geblokkeerd door ISP | Port 22 werkt voor SFTP; borg drill via prod server |

---

## Totaalstatus Day Build

| Sessie | Status | Samenvatting |
|--------|--------|-------------|
| D1 | PASS | Borg backup pipeline naar Hetzner Storage Box |
| D2 | PASS | Monthly automated DR restore test |
| D3 | PASS | Bridge NSSM service + watchdog (192s recovery) |
| D4 | PASS | Uptime Kuma + heartbeat pipeline |
| D5 | PASS | Full DR drill + procedure document |

## Volgende stap

Day Build is feature-complete. Resterende optimalisaties:
- Judge monitor type wijzigen naar Docker Container
- Notification configuratie (Email/Telegram) in Uptime Kuma
- Port 23 access testen via VPN voor directe PC → Storage Box borg
