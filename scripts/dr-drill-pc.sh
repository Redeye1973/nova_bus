#!/bin/bash
set -e
echo "=== 4. START POSTGRES SANDBOX ==="
docker stop dr-sandbox 2>/dev/null || true
docker rm dr-sandbox 2>/dev/null || true
docker run -d --name dr-sandbox -e POSTGRES_PASSWORD=test postgres:16-alpine
echo "Waiting for postgres..."
for i in $(seq 1 15); do
  if docker exec dr-sandbox pg_isready -h localhost -U postgres 2>/dev/null; then
    break
  fi
  sleep 2
done

echo "=== 5. RESTORE V2 DUMP ==="
PG_V2=$(find /tmp/dr-drill -name 'postgres-v2-*.sql' | head -1)
if [ -z "$PG_V2" ]; then
  echo "NO V2 DUMP FOUND"
  exit 1
fi
echo "Restoring $PG_V2 ..."
docker exec -i -e PGPASSWORD=test dr-sandbox psql -h localhost -U postgres -v ON_ERROR_STOP=0 < "$PG_V2" > /tmp/dr-restore.log 2>&1
RC=$?
echo "Restore rc=$RC"

echo "=== 6. VERIFY TABLES ==="
DB_LIST=$(docker exec -e PGPASSWORD=test dr-sandbox psql -h localhost -U postgres -tAc \
  "SELECT datname FROM pg_database WHERE datname NOT IN ('postgres','template0','template1')" 2>/dev/null | tr -d '\r')
TOTAL=0
for db in $DB_LIST; do
  [ -z "$db" ] && continue
  N=$(docker exec -e PGPASSWORD=test dr-sandbox psql -h localhost -U postgres -d "$db" -tAc \
    "SELECT count(*) FROM pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema')" 2>/dev/null | tr -d '[:space:]')
  N=${N:-0}
  TOTAL=$((TOTAL + N))
  echo "  db=$db tables=$N"
done
echo "TOTAL_TABLES=$TOTAL"

ERRORS=$(grep -c 'ERROR' /tmp/dr-restore.log 2>/dev/null || echo 0)
echo "SQL_ERRORS=$ERRORS"

echo "=== 7. RESTORE V1 DUMP ==="
PG_V1=$(find /tmp/dr-drill -name 'postgres-v1-*.sql' | head -1)
if [ -n "$PG_V1" ]; then
  echo "Restoring $PG_V1 ..."
  docker exec -i -e PGPASSWORD=test dr-sandbox psql -h localhost -U postgres -v ON_ERROR_STOP=0 < "$PG_V1" > /tmp/dr-restore-v1.log 2>&1
  echo "V1 restore rc=$?"
  DB_LIST_V1=$(docker exec -e PGPASSWORD=test dr-sandbox psql -h localhost -U postgres -tAc \
    "SELECT datname FROM pg_database WHERE datname NOT IN ('postgres','template0','template1')" 2>/dev/null | tr -d '\r')
  for db in $DB_LIST_V1; do
    [ -z "$db" ] && continue
    N=$(docker exec -e PGPASSWORD=test dr-sandbox psql -h localhost -U postgres -d "$db" -tAc \
      "SELECT count(*) FROM pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema')" 2>/dev/null | tr -d '[:space:]')
    echo "  db=$db tables=${N:-0}"
  done
  V1_ERRORS=$(grep -c 'ERROR' /tmp/dr-restore-v1.log 2>/dev/null || echo 0)
  echo "V1_SQL_ERRORS=$V1_ERRORS"
fi

echo "=== 8. CLEANUP ==="
docker stop dr-sandbox && docker rm dr-sandbox
rm -rf /tmp/dr-drill /tmp/dr-restore.log /tmp/dr-restore-v1.log
echo "=== DR DRILL DONE ==="
