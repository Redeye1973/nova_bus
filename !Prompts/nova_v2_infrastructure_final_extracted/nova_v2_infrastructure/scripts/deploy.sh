#!/bin/bash
# NOVA v2 Infrastructure Deploy Script
# Voor Hetzner server: 178.104.207.194
# Draai dit vanaf Hetzner server zelf (SSH erop eerst)

set -e

NOVA_V2_DIR="/docker/nova-v2"
COMPOSE_FILE="${NOVA_V2_DIR}/docker-compose.yml"
ENV_FILE="${NOVA_V2_DIR}/.env"

echo "=========================================="
echo "NOVA v2 Infrastructure Deployment"
echo "=========================================="

# Check Docker installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not installed. Install first: https://docs.docker.com/engine/install/"
    exit 1
fi

# Check docker compose
if ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose v2 not installed."
    exit 1
fi

# Create directory structure
echo ""
echo "Step 1: Creating directory structure..."
sudo mkdir -p "${NOVA_V2_DIR}"
sudo mkdir -p "${NOVA_V2_DIR}/scripts"
sudo mkdir -p "${NOVA_V2_DIR}/config/n8n-custom"
sudo mkdir -p "${NOVA_V2_DIR}/logs"
sudo chown -R $USER:$USER "${NOVA_V2_DIR}"

# Check env file
echo ""
echo "Step 2: Checking configuration..."
if [ ! -f "${ENV_FILE}" ]; then
    echo "ERROR: .env file not found at ${ENV_FILE}"
    echo ""
    echo "Copy .env.template and fill in passwords:"
    echo "  cp ${NOVA_V2_DIR}/.env.template ${ENV_FILE}"
    echo "  nano ${ENV_FILE}"
    echo ""
    echo "Generate strong passwords with:"
    echo "  openssl rand -base64 32"
    echo "  openssl rand -hex 32  # voor N8N_ENCRYPTION_KEY"
    exit 1
fi

# Check env has been filled in (no CHANGE_ME left)
if grep -q "CHANGE_ME" "${ENV_FILE}"; then
    echo "ERROR: .env still contains CHANGE_ME placeholders. Fill in actual passwords first."
    exit 1
fi

# Check firewall ports (informational)
echo ""
echo "Step 3: Checking ports..."
PORTS=(5679 5680 9000 9001 6333 6334)
for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "WARNING: Port $port already in use. Stop conflicting service first."
    else
        echo "  Port $port: available"
    fi
done

# Pull latest images
echo ""
echo "Step 4: Pulling latest Docker images..."
cd "${NOVA_V2_DIR}"
docker compose pull

# Start services
echo ""
echo "Step 5: Starting NOVA v2 services..."
docker compose up -d

# Wait for health checks
echo ""
echo "Step 6: Waiting for services to be healthy..."
sleep 10

# Check health
echo ""
echo "Step 7: Health check..."
docker compose ps

# Verify N8n is responding
echo ""
echo "Step 8: Verifying N8n main instance..."
for i in {1..30}; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5679 | grep -q "200\|401"; then
        echo "  N8n main responds on port 5679"
        break
    fi
    echo "  Waiting for N8n main... ($i/30)"
    sleep 2
done

# Verify webhook
echo ""
echo "Step 9: Verifying N8n webhook instance..."
for i in {1..30}; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5680 | grep -q "200\|404"; then
        echo "  N8n webhook responds on port 5680"
        break
    fi
    echo "  Waiting for N8n webhook... ($i/30)"
    sleep 2
done

# Verify MinIO
echo ""
echo "Step 10: Verifying MinIO..."
if curl -s http://localhost:9000/minio/health/live | head -n 1; then
    echo "  MinIO responds"
fi

# Verify Qdrant
echo ""
echo "Step 11: Verifying Qdrant..."
if curl -s http://localhost:6333/ | grep -q "qdrant"; then
    echo "  Qdrant responds"
fi

echo ""
echo "=========================================="
echo "NOVA v2 Deployment Complete!"
echo "=========================================="
echo ""
echo "Access URLs (vanaf Hetzner IP 178.104.207.194):"
echo "  N8n UI:          http://178.104.207.194:5679"
echo "  N8n webhooks:    http://178.104.207.194:5680"
echo "  MinIO console:   http://178.104.207.194:9001"
echo "  Qdrant API:      http://178.104.207.194:6333"
echo ""
echo "Volgende stappen:"
echo "  1. Open N8n UI en maak admin account"
echo "  2. Bewaar N8n API key in Key Backup folder"
echo "  3. Test webhook met curl naar :5680/webhook/test"
echo "  4. Configure MinIO buckets: nova-assets, nova-cache"
echo "  5. Configure Qdrant collections: surilians_bible, sprite_library"
echo ""
echo "Logs bekijken:"
echo "  docker compose logs -f n8n-v2-main"
echo ""
echo "Stop/start/restart:"
echo "  docker compose stop"
echo "  docker compose start"
echo "  docker compose restart"
echo ""
echo "BELANGRIJK: v1 (poort 5678) draait ongewijzigd door!"
