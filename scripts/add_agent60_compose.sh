#!/bin/bash
cd /docker/nova-v2

if grep -q "agent-60-memory-curator" docker-compose.yml; then
  echo "Agent 60 already in docker-compose.yml"
else
  cp docker-compose.yml docker-compose.yml.bak.agent60

  python3 << 'PYTHON'
with open("/docker/nova-v2/docker-compose.yml") as f:
    content = f.read()

agent60_block = """
  agent-60-memory-curator:
    build:
      context: ./services/agent_60_memory_curator
    image: nova-v2-agent-60-memory-curator:poc
    container_name: nova-v2-memory-curator
    restart: unless-stopped
    ports:
      - "8060:8060"
    volumes:
      - /docker/nova-v2/docs:/docs:rw
    networks:
      - nova-v2-network
    environment:
      - DOCS_ROOT=/docs
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres-v2:5432/${POSTGRES_DB}
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8060/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
"""

# Insert before volumes: section
if "volumes:" in content:
    content = content.replace("\nvolumes:", agent60_block + "\nvolumes:", 1)
    with open("/docker/nova-v2/docker-compose.yml", "w") as f:
        f.write(content)
    print("Added agent-60-memory-curator to docker-compose.yml")
else:
    print("ERROR: could not find volumes: section")
PYTHON
fi

# Sync docs folder to server
mkdir -p /docker/nova-v2/docs

echo "Building agent 60..."
docker compose build agent-60-memory-curator 2>&1 | tail -10

echo "Starting agent 60..."
docker compose up -d agent-60-memory-curator 2>&1

sleep 15
docker ps --filter name=memory-curator --format "{{.Names}} {{.Status}}"
