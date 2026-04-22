# SESSIE D5 — Monitor Agent integratie + DR Drill

**Doel:** Alles samen brengen in Monitor Agent + eerste volledige DR drill
**Tijd:** 45-60 min
**Handwerk:** Geen
**Afhankelijkheid:** D1-D4 + night-sessie 06 (Monitor Agent bestaat)

---

### ===SESSION D5 START===

```
SESSIE D5 — Monitor Agent 11 uitbreiden + volledige DR drill.

Werk autonoom.

## Context

D1-D4 hebben backup + bridge hardening + external monitoring.
Nu: alles aggregeren in Monitor Agent + eerste full DR drill.

## Stap 1: Monitor Agent uitbreiden

Als Monitor Agent (11) nog niet bestaat uit night-sessie 06:
skip deze stap, werk verder met stap 2.

Als wel bestaat: uitbreiden met endpoints:

Add to v2_services/monitor/main.py:

@app.post("/dr_result")
def dr_result(data: dict):
    # Ontvangt DR test resultaten van prod server cron
    cursor.execute("""
        INSERT INTO dr_test_log (timestamp, result, details)
        VALUES (%s, %s, %s)
    """, (data['timestamp'], data['result'], json.dumps(data)))
    return {"status": "logged"}

@app.post("/backup_result")
def backup_result(data: dict):
    # Ontvangt backup run resultaten
    cursor.execute("""
        INSERT INTO backup_log (timestamp, size_gb, archive_name, status)
        VALUES (%s, %s, %s, %s)
    """, (...))
    return {"status": "logged"}

@app.get("/health_summary")
def health_summary():
    # Aggregeert: bridge status, last backup, last DR test, 
    #             V2 container health, UptimeRobot status
    return {
        "bridge_last_heartbeat": ...,
        "last_backup_age_hours": ...,
        "last_dr_test_result": ...,
        "healthy_containers": ...,
        "overall": "green|yellow|red"
    }

Postgres migrations:
CREATE TABLE IF NOT EXISTS dr_test_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  timestamp TIMESTAMP NOT NULL,
  result TEXT NOT NULL,
  details JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS backup_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  timestamp TIMESTAMP NOT NULL,
  size_gb NUMERIC,
  archive_name TEXT,
  status TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

## Stap 2: nova-backup.sh update

Op prod server, update /root/nova-backup.sh einde:

# 8. Report naar Monitor Agent
MONITOR_URL="http://nova-v2-monitor:11000/backup_result"
ARCHIVE_SIZE=$(borg info --rsh "$RSH" "$BORG_REPO::nova-${TIMESTAMP}" | grep "This archive:" | awk '{print $3}')
curl -X POST "$MONITOR_URL" \
  -H "Content-Type: application/json" \
  -d "{\"timestamp\":\"$TIMESTAMP\",\"archive_name\":\"nova-${TIMESTAMP}\",\"status\":\"success\",\"size_gb\":\"$ARCHIVE_SIZE\"}" \
  2>/dev/null || echo "Monitor Agent not reachable"

## Stap 3: status dashboard endpoint

Monitor Agent krijgt publieke (read-only) status:

@app.get("/public_status")
def public_status():
    """Public status voor Uptime Kuma status pages etc."""
    summary = health_summary()
    return {
        "service": "nova-v2",
        "status": summary["overall"],
        "last_check": datetime.utcnow().isoformat(),
        "components": {
            "bridge": summary.get("bridge_last_heartbeat") != "down",
            "backup": summary.get("last_backup_age_hours", 999) < 36,
            "dr_test": summary.get("last_dr_test_result") == "PASS",
        }
    }

Deploy update:
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose build nova-monitor && docker compose up -d nova-monitor"

## Stap 4: FULL DR DRILL (belangrijk)

Dit is de echte test: kun je daadwerkelijk restoren van zero?

Drill scenario: "Hetzner prod server is unreachable. We hebben alleen backup data."

### 4a. Create DR staging server (tijdelijk)

Op je PC, start Docker container die prod server simuleert:

docker run -d --name nova-dr-staging \
  -p 6678:5678 -p 6679:5679 -p 65432:5432 \
  -v nova_dr_data:/var/lib/postgresql \
  postgres:16-alpine

### 4b. Pull laatste archive van Storage Box naar PC

# Install borg op PC (als niet):
# scoop install borg   # Windows via Scoop
# Of via WSL

mkdir L:\!Nova V2\dr-staging
cd L:\!Nova V2\dr-staging

$env:BORG_PASSPHRASE = (Get-Content "L:\!Nova V2\secrets\nova_v2_passwords.txt" |
  Select-String "^BORG_PASSPHRASE=").ToString().Split("=",2)[1]

# Borg extract van Storage Box direct (via SSH)
borg list --rsh "ssh -p 23" <storagebox>:nova-v2-backup
# Latest
$latest = (borg list --rsh "ssh -p 23" --short <storagebox>:nova-v2-backup | Select-Object -Last 1)
borg extract --rsh "ssh -p 23" "<storagebox>:nova-v2-backup::$latest"

### 4c. Restore postgres in staging container

$pgDump = (Get-ChildItem -Recurse -Filter "postgres-v2-*.sql" | Select-Object -First 1).FullName
Get-Content $pgDump | docker exec -i nova-dr-staging psql -U postgres

### 4d. Verify data

docker exec nova-dr-staging psql -U postgres -c "\dt" 
# Should show nova_assets, character_identity etc tables

docker exec nova-dr-staging psql -U postgres -c "SELECT count(*) FROM nova_assets"
# Should show number matching prod

### 4e. Time measurement

Noteer:
- T1: start drill
- T2: archive extract klaar
- T3: postgres restore klaar
- T4: verified

Target: T4 - T1 < 30 min voor 1TB repo.

### 4f. Cleanup

docker stop nova-dr-staging
docker rm nova-dr-staging
docker volume rm nova_dr_data
Remove-Item -Recurse "L:\!Nova V2\dr-staging"

## Stap 5: DR procedure documenteren

File: L:\!Nova V2\docs\DR_PROCEDURE.md

# Disaster Recovery Procedure

## Scenario A: Hetzner prod crash, data intact
1. Hetzner support escalate
2. Wait for recovery
3. Laatste backup = <lokatie>

## Scenario B: Hetzner prod lost, restore op nieuwe server
Step-by-step guide:
1. Order nieuwe Hetzner server
2. Install Docker, Docker Compose
3. Clone nova_bus repo uit GitHub
4. Borg restore van Storage Box naar nieuwe server
5. Restore postgres
6. Start docker compose
7. Verify

Voor elke stap: exact commando + expected output + rollback.

Target RTO (Recovery Time Objective): 4 uur.
Target RPO (Recovery Point Objective): 24 uur (daily backup).

## Stap 6: rapport

File: L:\!Nova V2\docs\session_D5_report.md
# Sessie D5 Rapport
- Timestamp
- Monitor Agent endpoints: /dr_result, /backup_result, /health_summary, /public_status
- Postgres tables: dr_test_log, backup_log
- Backup script reports naar Monitor: active
- Full DR drill: PASS / FAIL
- DR drill time T4-T1: <minutes>
- DR procedure: documented in docs/DR_PROCEDURE.md
- Status: SUCCESS
- Next: niks meer vereist — backup + monitoring compleet

git add v2_services/monitor docs/session_D5_report.md docs/DR_PROCEDURE.md
git commit -m "day session D5: DR drill complete + DR procedure documented"
git push origin main

Tag mijlpaal:
git tag -a v2.0-dr-ready -m "Day build complete: backup + DR tested + monitoring"
git push origin v2.0-dr-ready

Print "DAY BUILD COMPLETE — NOVA v2 has DR + monitoring, ready for production use"

REGELS:
- DR drill is SIMULATIE, raak prod server niet aan
- Als borg extract op PC faalt door Windows path issues: gebruik WSL
- Tijd T4-T1 is belangrijke metric voor DR procedure kwaliteit
- Alles cleanup na drill, geen staging artifacts achterlaten

Ga.
```

### ===SESSION D5 EINDE===

---

## OUTPUT

- Monitor Agent uitgebreid met dr/backup endpoints
- Postgres tabellen dr_test_log + backup_log
- Backup script rapporteert naar Monitor Agent
- Full DR drill successfully completed
- `docs/DR_PROCEDURE.md`
- Git tag `v2.0-dr-ready`

## WAT JE NU HEBT

- Daily automated backup naar Hetzner Finland
- Monthly automated restore test
- Bridge draait als Windows Service, auto-restart
- Lokale watchdog die bridge restart als 3x fail
- External UptimeRobot heartbeat met email alerts
- Self-hosted Uptime Kuma op Hetzner met status page
- Monitor Agent aggregeert alles
- DR procedure gedocumenteerd + getest
- RTO 4u, RPO 24u

## VERIFIEREN

```bash
# Alle services healthy?
ssh root@178.104.207.194 "docker compose -f /docker/nova-v2/docker-compose.yml ps"

# Monitor status endpoint
curl http://178.104.207.194:11000/public_status

# Git tag aanwezig?
git tag | grep v2.0-dr
```

## KOSTEN OVERZICHT

**Vast maandelijks (nieuw):**
- Hetzner Storage Box BX11 Finland: ~€3-4/mnd

**Gratis (bestaande capaciteit gebruikt):**
- NSSM services (lokaal)
- UptimeRobot free tier
- Uptime Kuma (runs op je bestaande Hetzner server)

**Totaal nieuw:** ~€3-4/maand bovenop bestaande €123/mnd.

Grand total NOVA: ~€127/mnd voor productie-grade infrastructuur.
