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
        echo "SSH attempt $attempt/$max_attempts failed, waiting 30s..."
        sleep 30
        attempt=$((attempt + 1))
    done

    echo "SSH failed after $max_attempts attempts"
    return 1
}

echo "=== NOVA Pull-Only Deploy ==="
echo "Server doet GEEN builds — alleen pull + restart"

echo "--- Upload prod compose ---"
scp -o ConnectTimeout=10 infrastructure/docker-compose.prod.yml root@178.104.207.194:/docker/nova-v2/docker-compose.prod.yml

echo "--- Login GHCR op server ---"
ssh_with_retry 'cd /docker/nova-v2 && TOKEN=$(curl -s -X POST http://localhost:8144/secrets/get -H "Content-Type: application/json" -H "Authorization: Bearer $(grep NOVA_VAULT_TOKEN .env | cut -d= -f2)" -d "{\"name\":\"GITHUB_GHCR_TOKEN\"}" | python3 -c "import sys,json; print(json.load(sys.stdin).get(\"value\",\"\"))") && echo "$TOKEN" | docker login ghcr.io -u Redeye1973 --password-stdin'

echo "--- Pull all images (network only, no CPU load) ---"
ssh_with_retry "cd /docker/nova-v2 && docker compose -f docker-compose.prod.yml pull 2>&1 | tail -20"

echo "--- Rolling restart ---"
ssh_with_retry 'cd /docker/nova-v2 && for service in $(docker compose -f docker-compose.prod.yml config --services); do echo "Starting $service..."; docker compose -f docker-compose.prod.yml up -d --no-deps "$service" 2>&1 | tail -1; sleep 3; done'

echo "--- Health summary ---"
sleep 10
ssh_with_retry "docker ps --filter name=nova-v2 --format '{{.Names}}\t{{.Status}}' | sort"

echo "=== Pull-Only Deploy Complete ==="
