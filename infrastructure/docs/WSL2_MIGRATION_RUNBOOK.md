# WSL2 Migration Runbook

## Scope
Migrate Nova from native Windows Docker backend to Docker Desktop WSL2 backend.

## Pre-flight (must be green)
- Stop active build/processing workloads.
- Create backup at `C:\nova\backups\pre_wsl2_migration.dump`.
- Confirm >=50GB free on target disk.
- Confirm Docker Desktop and Windows version support WSL2.

## Step A — Install/prepare WSL2
1. Install Ubuntu 22.04 with WSL2.
2. Initialize Linux user.
3. Update packages (`apt update && apt upgrade -y`).

## Step B — Enable Docker WSL2 engine
1. Docker Desktop -> General -> enable WSL2 engine.
2. Docker Desktop -> Resources -> WSL Integration -> enable Ubuntu 22.04.
3. Apply and restart Docker Desktop.
4. Verify `docker info` returns `OSType: linux`.

## Step C — Migrate project to Linux filesystem
1. Stop Nova containers.
2. Create dump from `postgres-ref` and validate dump list.
3. Copy project from Windows path to `~/projects/nova` inside WSL.
4. Run compose from Linux filesystem path (not `/mnt/l/...`).

## Step D — Start and validate
1. Start stack from WSL project path.
2. Restore DB dump.
3. Validate health endpoints and Uptime Kuma.
4. Run pgbench baseline and post-migration checks; log in `infrastructure/docs/migration_log.md`.

## Notes
- Keep named volumes for stateful services where possible.
- Do not run mixed filesystem setup (Linux + `/mnt/*`) for active services.
