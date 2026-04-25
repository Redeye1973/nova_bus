#!/bin/bash
set -e

ssh_with_retry() {
    local cmd="$1"
    local max_attempts=5
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if ssh -o ConnectTimeout=10 -o ServerAliveInterval=5 root@178.104.207.194 "$cmd"; then
            return 0
        fi
        echo "SSH attempt $attempt failed, waiting 30s..."
        sleep 30
        attempt=$((attempt + 1))
    done

    echo "SSH failed after $max_attempts attempts"
    return 1
}

echo "=== NOVA Deploy (serial builds, SSH retry) ==="

echo "--- SCP files ---"
scp -o ConnectTimeout=10 infrastructure/docker-compose.yml root@178.104.207.194:/docker/nova-v2/docker-compose.yml

echo "--- Serial build on server ---"
ssh_with_retry "cd /docker/nova-v2 && for service in \$(docker compose config --services); do echo \"Building \$service...\"; docker compose build \"\$service\" 2>&1 | tail -2; sleep 3; done"

echo "--- Rolling restart ---"
ssh_with_retry "cd /docker/nova-v2 && docker compose up -d 2>&1"

echo "--- Health check ---"
sleep 10
ssh_with_retry "docker ps --filter name=nova-v2 --format '{{.Names}}\t{{.Status}}' | head -20"

echo "=== Deploy complete ==="
