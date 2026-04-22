#!/usr/bin/env bash
# NOVA V2 — Hetzner backup cron templates (session 09).
# Do NOT run this whole file as-is: copy the cron blocks into `crontab -e` on the
# server after filling secrets paths and MinIO/S3 endpoints.
#
# Prerequisites on server:
# - docker CLI, access to postgres-v2 + minio containers (or host pg_dump + mc)
# - `mc` (MinIO client) configured: `mc alias set local http://127.0.0.1:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"`
# - Optional: rclone or mc mirror to Hetzner Object Storage / Storage Box S3 API
#
# shellcheck disable=SC2034,SC2086

set -euo pipefail

echo "=== Reference variables (export in /root/.nova_backup_env or similar) ==="
cat <<'VARS'
export POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-postgres-v2}"
export POSTGRES_DB="${POSTGRES_DB:-nova_v2}"
export POSTGRES_USER="${POSTGRES_USER:-nova}"
export BACKUP_BUCKET="${BACKUP_BUCKET:-nova-backups}"
export MINIO_ALIAS="${MINIO_ALIAS:-local}"
export REMOTE_MIRROR_ALIAS="${REMOTE_MIRROR_ALIAS:-hetzner-s3}"   # mc alias for external bucket
export CONFIG_TARBALL="/root/nova-v2-config-$(date +%F).tar.gz"
VARS

echo ""
echo "=== 1) Daily 02:00 — pg_dump → MinIO /backups/ ==="
cat <<'CRON1'
0 2 * * * docker exec "$POSTGRES_CONTAINER" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > /var/log/nova-backup/pg-$(date +\%F).dump 2>>/var/log/nova-backup/cron.log && \
  mc cp /var/log/nova-backup/pg-$(date +\%F).dump "$MINIO_ALIAS/$BACKUP_BUCKET/postgres/" >>/var/log/nova-backup/cron.log 2>&1
CRON1

echo ""
echo "=== 2) Daily 03:00 — mirror MinIO bucket to external S3-compatible target ==="
cat <<'CRON2'
0 3 * * * mc mirror --overwrite --remove "$MINIO_ALIAS/$BACKUP_BUCKET" "$REMOTE_MIRROR_ALIAS/nova-v2-mirror" >>/var/log/nova-backup/mirror.log 2>&1
CRON2

echo ""
echo "=== 3) Weekly Sunday 04:00 — tarball .env + compose + selected secrets (NO private keys in git) ==="
cat <<'CRON3'
0 4 * * 0 tar czf "$CONFIG_TARBALL" -C /docker/nova-v2 docker-compose.yml .env 2>/dev/null; \
  mc cp "$CONFIG_TARBALL" "$MINIO_ALIAS/$BACKUP_BUCKET/config/" >>/var/log/nova-backup/config.log 2>&1 || true
CRON3

echo ""
echo "=== Setup once on server ==="
cat <<'SETUP'
sudo mkdir -p /var/log/nova-backup && sudo chmod 700 /var/log/nova-backup
# Install mc, configure aliases, test: mc ls local/
SETUP
