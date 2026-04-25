#!/bin/bash

echo "=== MinIO credential discovery via docker inspect ==="

for CONTAINER in nova-v2-minio minio; do
  echo "--- Container: $CONTAINER ---"
  USER=$(docker inspect "$CONTAINER" 2>/dev/null | python3 -c "
import sys,json
data=json.load(sys.stdin)
for env in data[0].get('Config',{}).get('Env',[]):
  if env.startswith('MINIO_ROOT_USER='):
    print(env.split('=',1)[1])
    break
" 2>/dev/null)
  PASS=$(docker inspect "$CONTAINER" 2>/dev/null | python3 -c "
import sys,json
data=json.load(sys.stdin)
for env in data[0].get('Config',{}).get('Env',[]):
  if env.startswith('MINIO_ROOT_PASSWORD='):
    print(env.split('=',1)[1])
    break
" 2>/dev/null)
  
  PORT=$(docker port "$CONTAINER" 9000 2>/dev/null | head -1 | cut -d: -f2)
  
  if [ -n "$USER" ] && [ -n "$PASS" ] && [ -n "$PORT" ]; then
    echo "User: ${USER:0:3}*** Port: $PORT"
    ALIAS="minio-${CONTAINER}"
    mc alias set "$ALIAS" "http://localhost:$PORT" "$USER" "$PASS" 2>&1
    if [ $? -eq 0 ]; then
      echo "Alias $ALIAS configured OK"
      echo "Buckets:"
      mc ls "$ALIAS/" 2>&1
    else
      echo "Failed to set alias for $CONTAINER"
    fi
  else
    echo "No credentials found for $CONTAINER"
  fi
  echo ""
done

echo "=== Update backup script ==="
cp /root/nova-backup.sh /root/nova-backup.sh.bak

python3 << 'PYTHON'
script_path = "/root/nova-backup.sh"
with open(script_path) as f:
    content = f.read()

minio_block = '''
# MinIO snapshot
echo "-- MinIO snapshot to staging"
if command -v mc &> /dev/null; then
  MINIO_TS=$(date +%Y%m%d_%H%M%S)
  for ALIAS in minio-nova-v2-minio minio-minio; do
    for bucket in $(mc ls "$ALIAS/" 2>/dev/null | awk '{print $NF}' | tr -d '/'); do
      if [ -n "$bucket" ]; then
        echo "  Mirroring $ALIAS/$bucket..."
        mkdir -p "/tmp/backup-staging/minio-${MINIO_TS}/$bucket"
        mc mirror --overwrite --quiet "$ALIAS/$bucket" "/tmp/backup-staging/minio-${MINIO_TS}/$bucket/" 2>/dev/null || echo "  WARN: $bucket mirror partial"
      fi
    done
  done
else
  echo "  WARN: mc not installed, skipping MinIO"
fi

'''

if "MinIO snapshot" not in content:
    borg_pos = content.find("borg create")
    if borg_pos > 0:
        last_nl = content.rfind('\n', 0, borg_pos)
        content = content[:last_nl+1] + minio_block + content[last_nl+1:]
    else:
        content += '\n' + minio_block
    with open(script_path, 'w') as f:
        f.write(content)
    print("Updated nova-backup.sh with MinIO mirror step")
else:
    print("MinIO step already present, skipping")
PYTHON

bash -n /root/nova-backup.sh && echo "Syntax: OK" || echo "SYNTAX ERROR"

echo ""
echo "=== FASE 6 COMPLETE ==="
