# WSL2 Migration Log

## Baseline
- Date:
- Operator:
- Docker backend before migration:
- Current repo path:

## Pre-flight checklist
- [ ] No active long-running Nova workloads
- [ ] Fresh pg_dump created and validated
- [ ] At least 50GB free on target disk
- [ ] Windows build supports WSL2
- [ ] Docker Desktop installed and healthy

## Migration execution notes
- WSL install status:
- Docker WSL2 engine enabled:
- Project copied to Linux filesystem:
- Compose started from WSL path:
- Restore completed:

## Validation
- `docker info` OSType:
- `nova-ref /health`:
- `nova-learn /health`:
- `Uptime Kuma`:
- `pgbench` result baseline:
- `pgbench` result post-migration:

## Issues and fixes
- Issue:
- Fix:

## Final sign-off
- Migration complete: [ ]
- Rollback needed: [ ]
- Notes:
