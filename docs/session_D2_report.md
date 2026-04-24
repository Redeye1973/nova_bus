# Sessie D2 Rapport — DR Restore Test Automation

- **Datum:** 2026-04-25
- **Sessie:** Day Build D2
- **Status:** **SUCCESS**
- **Afhankelijkheid:** D1 (Borg pipeline + minstens 1 archive op Storage Box).

## Tooling toegevoegd op prod

- `jq 1.7`
- `postgresql-client 16.13` (psql/pg_isready voor sandbox tests)

## Scripts geinstalleerd

| Pad | Doel | Master copy |
|-----|------|-------------|
| `/root/nova-dr-test.sh` | Maandelijkse DR restore test (Agent 45) | `L:\!Nova V2\secrets\nova-dr-test.sh` |
| `/root/nova-dr-report.sh` | Resultaat naar Monitor Agent webhook | `L:\!Nova V2\secrets\nova-dr-report.sh` |
| `/root/nova-prod-health.sh` | 15-min health probe over docker compose | `L:\!Nova V2\secrets\nova-prod-health.sh` |

## DR test pipeline (`nova-dr-test.sh`)

1. Pak laatste archive uit `nova-v2-backup` op Storage Box.
2. `borg extract` naar tijdelijke `/tmp/nova-dr-test-<epoch>/`.
3. Integriteits-checks:
   - Postgres v2 dump: groottecontrole + header `PostgreSQL database cluster dump`.
   - Postgres v1 dump: aanwezig + groottecontrole.
   - Docker compose tree aanwezig.
   - n8n V1 + V2 workflows JSON parseable.
4. Sandbox: `docker run -d --rm postgres:16-alpine` + `pg_isready -h localhost` loop tot 60s.
5. `docker exec -i sandbox psql` herstelt `pg_dumpall`-output via TCP (Unix socket pad verschilt op Alpine).
6. Telt tables in alle herstelde databases (pg_dumpall plaatst in `n8n_v2`, niet in `postgres`).
7. Trap cleanup: container `dr-test-pg-<ts>` wordt altijd verwijderd, ook bij crash.
8. Exit 0 op PASS, 1 op FAIL.

## Cron schedule

```cron
0 2 * * * /root/nova-backup.sh >> /var/log/nova-backup/cron.log 2>&1
0 3 1 * * /root/nova-dr-test.sh >> /var/log/nova-dr-test/cron.log 2>&1
5 3 1 * * /root/nova-dr-report.sh >> /var/log/nova-dr-test/report.log 2>&1
*/15 * * * * /root/nova-prod-health.sh
```

DR test draait elke 1e van de maand 03:00 UTC, 5 minuten later report-push.

## Eerste handmatige run (na 3 fix-iteraties)

```
=== DR TEST START 2026-04-24_23-23-49 ===
Testing archive: nova-2026-04-24_23-16-42
OK: postgres v2 dump valid (1168050 bytes)
OK: postgres v1 dump present (263368 bytes)
OK: docker configs present
OK: n8n v1 workflows JSON valid (68 workflows)
OK: n8n v2 workflows JSON valid (9 workflows)
-- Testing postgres restore into sandbox dr-test-pg-2026-04-24_23-23-49
  db=n8n_v2 tables=79
OK: postgres v2 restored (79 tables, psql rc=0, 1 sql errors)
=== DR TEST RESULT ===
PASS (0 errors)
```

Tabel-restore: **79 tables** in database `n8n_v2`. Eén benigne SQL-error (typische `DROP ROLE postgres` constructie van pg_dumpall) — handmatig geverifieerd dat schema en data correct hersteld zijn.

## Health probe sample

```
2026-04-24T23:24:05+00:00 total=41 running=41 healthy=41 unhealthy=0
```

Alle 41 V2 containers draaien healthy.

## Iteraties tot werkende test (debug log voor toekomst)

| Poging | Probleem | Fix |
|--------|----------|-----|
| 1 | psql via `127.0.0.1:55432` kreeg `server closed the connection unexpectedly` (pg_dumpall stuurt `DROP ROLE postgres`, dat killt de actieve sessie) | Restore via `docker exec -i` (TCP loopback binnen container) i.p.v. host port mapping |
| 2 | `psql: socket "/var/run/postgresql/.s.PGSQL.5432" failed: No such file` | Toegevoegd `-h localhost` zodat psql niet over Unix socket gaat |
| 3 | Restore liep door (`psql rc=0`) maar `TABLE_COUNT=0` | `pg_dumpall` plaatst tables in `n8n_v2`, niet in `postgres`. Count-query nu over alle databases |
| 4 | PASS (79 tables in n8n_v2) | — |

## Volgende sessie

**D3** — Bridge NSSM Service + lokale watchdog (45-60 min, wel 1× handwerk: NSSM download).
