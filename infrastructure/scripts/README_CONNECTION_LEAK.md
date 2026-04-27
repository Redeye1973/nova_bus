# Check connection leak diagnostics

```powershell
$env:NOVA_REF_DB_PASS="<db-password>"
powershell -NoProfile -ExecutionPolicy Bypass -File "L:\!Nova V2\infrastructure\scripts\check_connection_leak.ps1"
```

This queries `pg_stat_activity` and prints non-idle sessions ordered by `query_start`.
