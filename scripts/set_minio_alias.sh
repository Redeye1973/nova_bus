#!/bin/bash
USER=$(docker inspect minio 2>/dev/null | python3 -c "
import sys,json
data=json.load(sys.stdin)
for env in data[0]['Config']['Env']:
  if env.startswith('MINIO_ROOT_USER='):
    print(env.split('=',1)[1])
    break
")
PASS=$(docker inspect minio 2>/dev/null | python3 -c "
import sys,json
data=json.load(sys.stdin)
for env in data[0]['Config']['Env']:
  if env.startswith('MINIO_ROOT_PASSWORD='):
    print(env.split('=',1)[1])
    break
")
mc alias set local-minio "http://localhost:9000" "$USER" "$PASS"
echo "Alias local-minio set for port 9000"
mc ls local-minio/ 2>&1
echo "mc version: $(mc --version 2>&1 | head -1)"
