# Sessie D1 Rapport — Hetzner Storage Box + Borg backup pipeline

- **Datum:** 2026-04-25
- **Sessie:** Day Build D1
- **Status:** **SUCCESS**

## Storage Box

- Provider: Hetzner BX11
- Locatie: Falkenstein (FSN1-BX1148)
- Username: `u583230`
- Hostname: `u583230.your-storagebox.de`
- Port: `23`
- SSH key auth: actief vanaf prod (`178.104.207.194`) via `prod-to-hetzner-storage-box` (RFC4716 + OpenSSH formaat geinstalleerd via `install-ssh-key`).

## Borg repo

- Repo: `u583230@u583230.your-storagebox.de:nova-v2-backup`
- Encryption: `repokey-blake2`
- Repository ID: `9d4297649c80eea4c317b7e9bf8c6cb07554ccf38addc94bc7bc55abe5480686`
- Borg key geexporteerd naar: `L:\!Nova V2\secrets\borg-key-nova-v2-backup.txt`
- Passphrase opgeslagen in `L:\!Nova V2\secrets\nova_v2_passwords.txt` (sleutel `BORG_PASSPHRASE`).

## Tooling op prod server

- `borg 1.2.8`
- `restic 0.16.4`
- `rclone 1.60.1`
- `sshpass 1.09` (gebruikt voor eenmalige `install-ssh-key`)

## Backup script

- Pad: `/root/nova-backup.sh` (mode `0755`)
- Bron op L:: `L:\!Nova V2\secrets\nova-backup.sh` (master copy, LF endings)
- Logs: `/var/log/nova-backup/<timestamp>.log` + `/var/log/nova-backup/cron.log`
- Staging: `/tmp/nova-backup-staging` (auto-cleanup via trap)

Inhoud per run:

| Bron | Methode | Status |
|------|---------|--------|
| nova-v2 postgres | `docker exec nova-v2-postgres pg_dumpall -U postgres` | OK |
| nova-v1 postgres | `docker exec nova-postgres pg_dumpall -U nova` | OK |
| MinIO | `mc mirror` (only if `mc` aanwezig) | SKIP (mc niet geinstalleerd) |
| Docker compose | `cp -a /docker/nova-v2` | OK |
| n8n V1 workflows | `curl http://localhost:5678/api/v1/workflows` | OK |
| n8n V2 workflows | `curl http://localhost:5679/api/v1/workflows` | OK |
| `/root/.nova_secrets` | direct in archive | OK |
| Logs | direct in archive | OK |

Retention: `--keep-daily 7 --keep-weekly 4 --keep-monthly 6`. Compact na elke prune.

## Secrets file op prod

- Pad: `/root/.nova_secrets` (mode `0600`, owner root)
- Bevat: `BORG_PASSPHRASE`, `N8N_V1_API_KEY`, `N8N_V2_API_KEY`
- Lokale master copy: `L:\!Nova V2\secrets\prod-nova_secrets.env`

## Cron

```cron
0 2 * * * /root/nova-backup.sh >> /var/log/nova-backup/cron.log 2>&1
```

Server tijdzone bepaalt run; default Hetzner Falkenstein = UTC.

## Test resultaten

Twee handmatige runs uitgevoerd:

| Archive | Files | Original | Compressed | Dedup |
|---------|-------|----------|------------|-------|
| `nova-2026-04-24_23-16-05` | 390 | 2.31 MB | 634.59 kB | 606.39 kB |
| `nova-2026-04-24_23-16-42` | 391 | 2.58 MB | 684.52 kB | 204.46 kB |

Cumulatief op Storage Box: `4.89 MB / 1.32 MB / 868.65 kB`.

Verificatie:

```bash
ssh root@178.104.207.194 "BORG_PASSPHRASE='***' \
  borg list --rsh 'ssh -p 23' u583230@u583230.your-storagebox.de:nova-v2-backup"
```

→ 2 archives zichtbaar.

## Known issues / vervolg

- `mc` (MinIO client) niet aanwezig op prod; MinIO objectdata zit nog niet in backup. Op te lossen door `mc` te installeren en aliassen `local-minio` te configureren.
- Eerste handmatige run faalde op v1 dump met user `postgres`; opgelost door script aan te passen naar user `nova`.
- Borg repo bevat `repokey` mode → de key staat in de repo zelf, maar offline copy is veiliggesteld onder `L:\!Nova V2\secrets`.

## Volgende sessie

**D2** — DR restore test automation.
