# WSL2 Rollback Runbook

Use this if migration blocks production use.

## Rollback steps
1. Stop all containers started from WSL2 project path.
2. Open Docker Desktop settings.
3. Disable WSL2 backend engine.
4. Re-enable original Windows backend mode.
5. Start stack again from Windows repo path (`L:\!Nova V2\infrastructure`).
6. Restore latest known-good database backup if needed.

## Verification
- `docker info` reflects expected backend mode.
- `nova-ref` health responds.
- `nova-learn` health responds.
- Uptime Kuma UI reachable.
- Bridge notifications functional.

## Recovery notes
- Keep migration dump and rollback timestamps in `infrastructure/docs/migration_log.md`.
- If rollback repeatedly needed, freeze migration and capture a full postmortem before retry.
