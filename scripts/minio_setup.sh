#!/bin/bash
set -e

echo "=== Fase 6a: MinIO credential discovery ==="
MINIO_USER=""
MINIO_PASS=""

# Poging 1: Vault
echo "-- Checking Vault for MinIO secrets..."
VAULT_RESULT=$(curl -s "http://localhost:8144/secrets/list" 2>/dev/null || echo '{"error":"vault unreachable"}')
echo "Vault response: $VAULT_RESULT"

if echo "$VAULT_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); assert any('MINIO' in s.get('name','') for s in d.get('secrets',[]))" 2>/dev/null; then
  echo "Found MinIO secrets in Vault"
  MINIO_USER=$(curl -s "http://localhost:8144/secrets/get?name=MINIO_ROOT_USER" | python3 -c "import sys,json; print(json.load(sys.stdin).get('value',''))" 2>/dev/null)
  MINIO_PASS=$(curl -s "http://localhost:8144/secrets/get?name=MINIO_ROOT_PASSWORD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('value',''))" 2>/dev/null)
fi

# Poging 2: .env file
if [ -z "$MINIO_USER" ] || [ -z "$MINIO_PASS" ]; then
  echo "-- Fallback: checking /docker/nova-v2/.env..."
  if [ -f /docker/nova-v2/.env ]; then
    MINIO_USER=$(grep "^MINIO_ROOT_USER=" /docker/nova-v2/.env | cut -d= -f2- 2>/dev/null)
    MINIO_PASS=$(grep "^MINIO_ROOT_PASSWORD=" /docker/nova-v2/.env | cut -d= -f2- 2>/dev/null)
    [ -n "$MINIO_USER" ] && echo "Found in .env" || echo "Not in .env"
  else
    echo ".env file not found"
  fi
fi

# Poging 3: docker inspect
if [ -z "$MINIO_USER" ] || [ -z "$MINIO_PASS" ]; then
  echo "-- Fallback: checking docker inspect minio container..."
  MINIO_USER=$(docker inspect nova-v2-minio 2>/dev/null | python3 -c "
import sys,json
data=json.load(sys.stdin)
for env in data[0].get('Config',{}).get('Env',[]):
  if env.startswith('MINIO_ROOT_USER='):
    print(env.split('=',1)[1])
    break
" 2>/dev/null)
  MINIO_PASS=$(docker inspect nova-v2-minio 2>/dev/null | python3 -c "
import sys,json
data=json.load(sys.stdin)
for env in data[0].get('Config',{}).get('Env',[]):
  if env.startswith('MINIO_ROOT_PASSWORD='):
    print(env.split('=',1)[1])
    break
" 2>/dev/null)
  [ -n "$MINIO_USER" ] && echo "Found via docker inspect" || echo "Not found via docker inspect"
fi

# Final check
if [ -z "$MINIO_USER" ] || [ -z "$MINIO_PASS" ]; then
  echo "SKIP: MinIO credentials niet vindbaar. Geen blocker voor deploy."
  exit 0
fi

echo "MinIO credentials gevonden (user: ${MINIO_USER:0:3}***)"

echo ""
echo "=== Fase 6b: Install mc client ==="
if ! command -v mc &> /dev/null; then
  curl -fsSL https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/local/bin/mc
  chmod +x /usr/local/bin/mc
  echo "mc installed: $(mc --version 2>&1 | head -1)"
else
  echo "mc already installed: $(mc --version 2>&1 | head -1)"
fi

echo ""
echo "=== Fase 6c: Configure mc alias ==="
mc alias set local-minio http://localhost:9000 "$MINIO_USER" "$MINIO_PASS" 2>&1
echo "Buckets:"
mc ls local-minio/ 2>&1

echo ""
echo "=== Fase 6d: Update backup script ==="
cp /root/nova-backup.sh /root/nova-backup.sh.bak

python3 << 'PYTHON'
import re
script_path = "/root/nova-backup.sh"
with open(script_path) as f:
    content = f.read()

minio_block = '''
# MinIO snapshot
echo "-- MinIO snapshot to staging"
if command -v mc &> /dev/null; then
  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  for bucket in $(mc ls local-minio/ 2>/dev/null | awk '{print $5}' | tr -d '/'); do
    if [ -n "$bucket" ]; then
      echo "  Mirroring $bucket..."
      mkdir -p "/tmp/backup-staging/minio-${TIMESTAMP}/$bucket"
      mc mirror --overwrite --quiet "local-minio/$bucket" "/tmp/backup-staging/minio-${TIMESTAMP}/$bucket/" || echo "  WARN: $bucket mirror partial"
    fi
  done
else
  echo "  WARN: mc not installed, skipping MinIO"
fi

'''

if "MinIO snapshot" not in content:
    marker = re.search(r'(# \d+\.\s*Docker configs|# Docker configs)', content)
    if marker:
        pos = marker.start()
        content = content[:pos] + minio_block + content[pos:]
        with open(script_path, 'w') as f:
            f.write(content)
        print("Updated nova-backup.sh with MinIO mirror step")
    else:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'borg create' in line.lower():
                content = '\n'.join(lines[:i]) + '\n' + minio_block + '\n'.join(lines[i:])
                with open(script_path, 'w') as f:
                    f.write(content)
                print("Updated nova-backup.sh with MinIO mirror step (before borg create)")
                break
        else:
            with open(script_path, 'a') as f:
                f.write('\n' + minio_block)
            print("Appended MinIO mirror step to nova-backup.sh")
else:
    print("MinIO step already present, skipping")
PYTHON

bash -n /root/nova-backup.sh && echo "Syntax OK" || echo "SYNTAX ERROR"

echo ""
echo "=== FASE 6 COMPLETE ==="
