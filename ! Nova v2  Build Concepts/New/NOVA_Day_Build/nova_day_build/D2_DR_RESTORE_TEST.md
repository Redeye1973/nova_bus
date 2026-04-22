# SESSIE D2 — DR Restore Test Automation

**Doel:** Maandelijkse automated restore test zodat je weet dat backup werkt
**Tijd:** 45-60 min
**Handwerk:** Nee
**Afhankelijkheid:** D1 compleet (Borg repo met minstens 1 archive)

---

"Een backup die nooit getest wordt is geen backup" — DR agent principe.

Deze sessie bouwt Agent 45 DR Agent (uit Fase I gaps-analyse) als concrete implementatie.

---

### ===SESSION D2 START===

```
SESSIE D2 — DR restore test automation (Agent 45).

Werk autonoom.

## Context

D1 heeft Borg backup pipeline opgezet. Nu: automated monthly restore test
die data integrity verifieert.

## Stap 1: restore test script

Op prod server, file /root/nova-dr-test.sh:

#!/bin/bash
set -euo pipefail

export BORG_PASSPHRASE=$(grep "^BORG_PASSPHRASE=" /root/.nova_secrets | cut -d= -f2)
BORG_REPO='<from_secrets>'
RSH='ssh -p 23'
TEST_DIR=/tmp/nova-dr-test-$(date +%s)

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
LOG=/var/log/nova-dr-test/${TIMESTAMP}.log
mkdir -p /var/log/nova-dr-test
exec > >(tee -a $LOG) 2>&1

echo "=== DR TEST START $TIMESTAMP ==="

# 1. List archives, pick latest
LATEST=$(borg list --rsh "$RSH" --short "$BORG_REPO" | tail -1)
echo "Testing archive: $LATEST"

if [ -z "$LATEST" ]; then
  echo "FAIL: geen archives gevonden"
  exit 1
fi

# 2. Extract to test dir
mkdir -p $TEST_DIR
cd $TEST_DIR
echo "-- Extracting to $TEST_DIR"
borg extract --rsh "$RSH" "$BORG_REPO::$LATEST"

# 3. Integriteit checks
echo "-- Running integrity checks"

ERRORS=0

# Postgres dump check
PG_DUMP=$(find $TEST_DIR -name "postgres-v2-*.sql" | head -1)
if [ -f "$PG_DUMP" ]; then
  SIZE=$(stat -c%s "$PG_DUMP")
  if [ "$SIZE" -lt 1024 ]; then
    echo "FAIL: postgres dump too small ($SIZE bytes)"
    ERRORS=$((ERRORS+1))
  else
    # Check SQL header
    if head -5 "$PG_DUMP" | grep -q "PostgreSQL database cluster dump"; then
      echo "OK: postgres dump valid ($SIZE bytes)"
    else
      echo "FAIL: postgres dump header invalid"
      ERRORS=$((ERRORS+1))
    fi
  fi
else
  echo "WARN: no postgres dump in archive"
fi

# Docker compose check
if [ -d "$(find $TEST_DIR -type d -name 'docker-nova-v2-*' | head -1)" ]; then
  echo "OK: docker configs present"
else
  echo "WARN: docker configs missing from archive"
fi

# N8n workflow check
N8N_JSON=$(find $TEST_DIR -name "n8n-v1-workflows-*.json" | head -1)
if [ -f "$N8N_JSON" ]; then
  if python3 -c "import json; json.load(open('$N8N_JSON'))" 2>/dev/null; then
    COUNT=$(python3 -c "import json; print(len(json.load(open('$N8N_JSON')).get('data', [])))")
    echo "OK: n8n workflows JSON valid ($COUNT workflows)"
  else
    echo "FAIL: n8n workflows JSON invalid"
    ERRORS=$((ERRORS+1))
  fi
fi

# 4. Test restore naar test Postgres
echo "-- Testing postgres restore into sandbox"
docker run --rm -d --name dr-test-pg \
  -e POSTGRES_PASSWORD=test \
  -p 55432:5432 \
  postgres:16-alpine

sleep 10

if [ -f "$PG_DUMP" ]; then
  if PGPASSWORD=test psql -h localhost -p 55432 -U postgres -f "$PG_DUMP" > /tmp/restore.log 2>&1; then
    # Count tables restored
    TABLES=$(PGPASSWORD=test psql -h localhost -p 55432 -U postgres -tAc \
      "SELECT count(*) FROM pg_tables WHERE schemaname='public'")
    echo "OK: postgres restored successfully ($TABLES tables)"
  else
    echo "FAIL: postgres restore errors"
    tail -20 /tmp/restore.log
    ERRORS=$((ERRORS+1))
  fi
fi

docker stop dr-test-pg || true

# 5. Cleanup
rm -rf $TEST_DIR

# 6. Report
echo ""
echo "=== DR TEST RESULT ==="
if [ $ERRORS -eq 0 ]; then
  echo "PASS (0 errors)"
  exit 0
else
  echo "FAIL ($ERRORS errors)"
  exit 1
fi

Chmod +x.

## Stap 2: monthly cron

Cron entry (1e van de maand 03:00):
0 3 1 * * /root/nova-dr-test.sh >> /var/log/nova-dr-test/cron.log 2>&1

## Stap 3: report generator

File /root/nova-dr-report.sh:

#!/bin/bash
# Verzamelt DR test result en stuurt naar Monitor Agent webhook (of echo)
LATEST_LOG=$(ls -t /var/log/nova-dr-test/*.log 2>/dev/null | grep -v cron | head -1)
if [ -f "$LATEST_LOG" ]; then
  RESULT=$(tail -3 "$LATEST_LOG" | head -1)
  TIMESTAMP=$(basename "$LATEST_LOG" .log)
  
  # POST naar Monitor Agent als die draait
  MONITOR_URL="http://localhost:11000/dr_result"
  if curl -s -o /dev/null -w "%{http_code}" "$MONITOR_URL" | grep -q "200\|404"; then
    curl -X POST "$MONITOR_URL" \
      -H "Content-Type: application/json" \
      -d "{\"timestamp\":\"$TIMESTAMP\",\"result\":\"$RESULT\"}" 2>/dev/null || true
  fi
  
  echo "$TIMESTAMP: $RESULT"
fi

Chmod +x, cron entry:
5 3 1 * * /root/nova-dr-report.sh

## Stap 4: eerste test runnen

ssh root@178.104.207.194 "/root/nova-dr-test.sh"

Verwacht: exit 0, "PASS" in output. Als FAIL: log lezen, fix issue, retry.

Max 2 retries. Als nog steeds FAIL na 2 pogingen: log als known issue
in rapport en door (backup zelf werkt nog, alleen restore-path heeft issue).

## Stap 5: Docker healthcheck monitoring

Ook monthly check: zijn alle V2 containers nog healthy die gebacked worden?

File /root/nova-prod-health.sh:

#!/bin/bash
cd /docker/nova-v2
UNHEALTHY=$(docker compose ps --format json | jq -r '.[] | select(.Health != "healthy") | .Name' | wc -l)
TOTAL=$(docker compose ps --format json | jq -r '.[] | .Name' | wc -l)
echo "$(date -Iseconds) healthy=$(($TOTAL-$UNHEALTHY))/$TOTAL"

Simpele health log, Monitor Agent leest dit later uit.

Cron elke 15 min:
*/15 * * * * /root/nova-prod-health.sh >> /var/log/nova-health/health.log

## Stap 6: rapport

File: L:\!Nova V2\docs\session_D2_report.md
# Sessie D2 Rapport
- Timestamp
- DR test script: /root/nova-dr-test.sh
- Monthly cron: 1e 03:00
- First test run: PASS / FAIL
- Archives getest: <archive_name>
- Tables restored: <count>
- Workflows in archive: <count>
- Health monitoring: cron 15min active
- Status: SUCCESS / PARTIAL / FAILED
- Next: sessie D3 (bridge NSSM service)

git add docs/session_D2_report.md
git commit -m "day session D2: DR restore test automation"
git push origin main

Print "SESSION D2 COMPLETE — backup+restore verified"

REGELS:
- Als restore test FAIL bij eerste run: log details maar markeer niet als
  halt. Backup pipeline zelf werkt, alleen restore-path behoeft fix.
- Postgres sandbox container (dr-test-pg) altijd cleanup, ook bij crash
- jq moet geïnstalleerd zijn: apt install -y jq

Ga.
```

### ===SESSION D2 EINDE===

---

## OUTPUT

- `/root/nova-dr-test.sh` monthly restore test
- `/root/nova-dr-report.sh` report generator
- `/root/nova-prod-health.sh` 15-min health probe
- Cron entries voor alle drie
- First DR test: PASS verwacht
- `docs/session_D2_report.md`

## VERIFIEREN

```bash
ssh root@178.104.207.194 "cat /var/log/nova-dr-test/*.log | tail -30"
ssh root@178.104.207.194 "crontab -l | grep nova"
```

Moet minstens 3 cron regels tonen.
