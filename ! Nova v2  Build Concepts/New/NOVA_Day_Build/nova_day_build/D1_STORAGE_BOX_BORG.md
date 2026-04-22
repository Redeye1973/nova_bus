# SESSIE D1 — Hetzner Storage Box + Borg Backup Pipeline

**Doel:** Externe backup opslag + automated daily backup
**Tijd:** 60-90 min
**Handwerk:** Storage Box bestellen + SSH key registreren

---

## HANDWERK VOORAF (5-10 min)

1. Open https://console.hetzner.com
2. Login met je Hetzner account
3. Linker menu → **Storage Boxes** → **Order**
4. Kies **BX11** (1 TB, goedkoopste)
5. Location: **Helsinki, Finland** (andere DC dan je prod server)
6. Payment: zelfde als prod server
7. Confirm order
8. Wacht 1-5 minuten tot provisioning klaar is
9. Noteer de username (begint met `u`, bijv. `u123456`) en hostname (bijv. `u123456.your-storagebox.de`)

**SSH key uploaden:**
10. Klik op je nieuwe Storage Box → Settings
11. Tab "SSH Keys"
12. Upload je publieke SSH key (zelfde key als Hetzner prod server gebruikt)
13. Of genereer nieuwe op prod server: `ssh-keygen -t ed25519 -f ~/.ssh/storagebox_key`

**Test verbinding vanaf je prod Hetzner server (niet PC):**
```bash
ssh root@178.104.207.194
ssh -p 23 u123456@u123456.your-storagebox.de "echo OK"
```

Als "OK" verschijnt: klaar voor Cursor sessie.

---

### ===SESSION D1 START===

```
SESSIE D1 — Hetzner Storage Box backup pipeline setup.

Werk autonoom. Geen check-ins.

## Context

Alex heeft Hetzner Storage Box BX11 besteld in Finland. SSH key is al
geregistreerd. Storage Box hostname en username hebben we nodig als input.

## Stap 1: vraag Storage Box credentials

Stel Alex ÉÉN vraag:
"Plak Storage Box username en hostname (format: u123456@u123456.your-storagebox.de)"

Wacht op antwoord. Parse username en host.

## Stap 2: opslaan in secrets

Voeg toe aan L:\!Nova V2\secrets\nova_v2_passwords.txt:
STORAGEBOX_USER=<user>
STORAGEBOX_HOST=<host>
STORAGEBOX_PORT=23

Genereer Borg passphrase (32 chars random):
$passphrase = -join ((33..126) | Get-Random -Count 32 | % {[char]$_})

Voeg toe aan secrets:
BORG_PASSPHRASE=<passphrase>

Commit niet deze file naar git.

## Stap 3: Borg installeren op prod server

ssh root@178.104.207.194 << 'EOF'
apt update -qq
apt install -y borgbackup restic python3-pip rclone
borg --version
restic version
EOF

## Stap 4: Borg repo initialiseren op Storage Box

Via SSH tunnel door prod server:

ssh root@178.104.207.194 "
export BORG_PASSPHRASE='<passphrase_from_secrets>'
borg init --encryption=repokey-blake2 \
  --rsh 'ssh -p 23' \
  '<storagebox_user>@<storagebox_host>:nova-v2-backup'
"

Verify: borg info commando.

## Stap 5: backup script schrijven

Op prod server, file /root/nova-backup.sh:

#!/bin/bash
set -euo pipefail

export BORG_PASSPHRASE='<passphrase>'
BORG_REPO='<storagebox_user>@<storagebox_host>:nova-v2-backup'
RSH='ssh -p 23'

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
LOG=/var/log/nova-backup/${TIMESTAMP}.log
mkdir -p /var/log/nova-backup
exec > >(tee -a $LOG) 2>&1

echo "=== Backup start $TIMESTAMP ==="

# 1. Postgres dumps
echo "-- Postgres dumps"
mkdir -p /tmp/backup-staging
docker exec nova-v2-postgres pg_dumpall -U postgres \
  > /tmp/backup-staging/postgres-v2-${TIMESTAMP}.sql
docker exec nova-v1-postgres pg_dumpall -U postgres \
  > /tmp/backup-staging/postgres-v1-${TIMESTAMP}.sql 2>/dev/null || echo "V1 postgres skip"

# 2. MinIO data snapshot (via mc client)
echo "-- MinIO snapshot to staging"
# Alleen als mc geinstalleerd
if command -v mc &> /dev/null; then
  mc mirror --overwrite local-minio/nova /tmp/backup-staging/minio-${TIMESTAMP}/ || true
fi

# 3. Docker configs
echo "-- Docker compose files"
cp -r /docker/nova-v2 /tmp/backup-staging/docker-nova-v2-${TIMESTAMP}/ 2>/dev/null || true

# 4. N8n workflow exports via API
echo "-- N8n workflows"
V1_KEY=$(grep "^N8N_V1_API_KEY=" /root/.nova_secrets 2>/dev/null | cut -d= -f2)
if [ -n "$V1_KEY" ]; then
  curl -s -H "X-N8N-API-KEY: $V1_KEY" \
    http://localhost:5678/api/v1/workflows \
    > /tmp/backup-staging/n8n-v1-workflows-${TIMESTAMP}.json || true
fi

# 5. Borg create
echo "-- Creating borg archive"
borg create \
  --rsh "$RSH" \
  --compression lz4 \
  --stats \
  "$BORG_REPO::nova-${TIMESTAMP}" \
  /tmp/backup-staging \
  /root/.nova_secrets \
  /var/log/nova-backup \
  --exclude '*.tmp' \
  --exclude '__pycache__'

# 6. Prune old archives
echo "-- Pruning old archives"
borg prune \
  --rsh "$RSH" \
  --keep-daily 7 \
  --keep-weekly 4 \
  --keep-monthly 6 \
  "$BORG_REPO"

# 7. Cleanup staging
rm -rf /tmp/backup-staging

echo "=== Backup complete ==="

Chmod +x en test run.

## Stap 6: secrets file op server

Copy alleen de secrets die backup nodig heeft naar /root/.nova_secrets:
BORG_PASSPHRASE=<phrase>
N8N_V1_API_KEY=<key if available>

chmod 600 /root/.nova_secrets

## Stap 7: cron schedule

crontab -e toevoegen:

0 2 * * * /root/nova-backup.sh >> /var/log/nova-backup/cron.log 2>&1

Dagelijks 02:00 Hetzner lokale tijd.

## Stap 8: eerste run testen

ssh root@178.104.207.194 "/root/nova-backup.sh"

Verwacht: exit code 0, archive op Storage Box.

Verify archive:
ssh root@178.104.207.194 "
export BORG_PASSPHRASE='<phrase>'
borg list --rsh 'ssh -p 23' <storagebox>:nova-v2-backup
"

Moet 1 archive tonen.

## Stap 9: rapport

File: L:\!Nova V2\docs\session_D1_report.md
# Sessie D1 Rapport
- Timestamp
- Storage Box: BX11 Finland
- Hostname: <host>
- SSH test: OK
- Borg repo: geinitialiseerd
- Backup script: /root/nova-backup.sh
- Cron: 02:00 daily
- Eerste backup: geslaagd, <size> GB
- Archive count op Storage Box: 1
- Status: SUCCESS / PARTIAL / FAILED
- Next: sessie D2 (restore test automation)

git add docs/session_D1_report.md
git commit -m "day session D1: Hetzner Storage Box backup pipeline"
git push origin main

Print "SESSION D1 COMPLETE — next: sessie D2 restore test"

REGELS:
- BORG_PASSPHRASE nooit in chat/logs/commits
- Als Borg init faalt: check SSH -p 23 handmatig, retry max 2x
- Als backup > 30 min duurt: break, log, rapporteer (normaal <5 min voor fresh)

Ga.
```

### ===SESSION D1 EINDE===

---

## OUTPUT

- Hetzner Storage Box BX11 actief in Finland
- Borg repo initialiseerd met encryption
- `/root/nova-backup.sh` op prod server
- Cron daily 02:00
- Eerste backup archive aanwezig
- `docs/session_D1_report.md`

## VERIFIEREN

```bash
ssh root@178.104.207.194 "cat /var/log/nova-backup/*.log | tail -20"
ssh root@178.104.207.194 "export BORG_PASSPHRASE='...'; borg list --rsh 'ssh -p 23' user@host:nova-v2-backup"
```

Minstens 1 archive met timestamp vandaag.
