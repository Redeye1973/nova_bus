---
title: DR Runbook — MinIO Data Loss
severity: high
expected_time: 15-45 min
---

# MinIO Bucket / Object Loss

## Detectie
- Asset download failures in pipelines
- 404 errors van MinIO API
- `mc ls local-minio/` toont ontbrekende buckets

## Stappen

1. **Check MinIO status**
   ```bash
   docker logs nova-v2-minio --tail 30
   docker exec nova-v2-minio mc admin info local
   ```

2. **Als container down: restart**
   ```bash
   docker compose restart minio
   ```

3. **Als bucket verwijderd: restore van Borg**
   ```bash
   export BORG_REPO='u583230@u583230.your-storagebox.de:nova-v2-backup'
   borg list
   borg extract ::ARCHIVE_NAME minio-export/
   mc cp --recursive minio-export/ local-minio/nova-assets/
   ```

4. **Als volume corrupt**
   ```bash
   docker compose stop minio
   docker volume rm nova-v2-minio-data
   docker compose up -d minio
   # Re-import van backup
   ```

## Verificatie
- `mc ls local-minio/` toont alle verwachte buckets
- Pipeline test run succesvol met asset upload/download

## Impact
- Pipelines pauzeren tot MinIO hersteld
- Geen data loss als Borg backup recent is (dagelijks)
