#!/bin/bash
echo "=== Container health ==="
TOTAL=$(docker ps -q | wc -l)
HEALTHY=$(docker ps --filter "health=healthy" -q | wc -l)
UNHEALTHY=$(docker ps --filter "health=unhealthy" -q | wc -l)
STARTING=$(docker ps --filter "health=starting" -q | wc -l)
echo "Total: $TOTAL | Healthy: $HEALTHY | Unhealthy: $UNHEALTHY | Starting: $STARTING"

echo ""
echo "=== Critical endpoints ==="
curl -s -o /dev/null -w "Vault (8144): %{http_code}\n" http://localhost:8144/health
curl -s -o /dev/null -w "N8n V1 (5678): %{http_code}\n" http://localhost:5678/healthz
curl -s -o /dev/null -w "N8n V2 (5679): %{http_code}\n" http://localhost:5679/healthz
curl -s -o /dev/null -w "Judge (8000): %{http_code}\n" http://localhost:8000/health
curl -s -o /dev/null -w "Monitor (11000): %{http_code}\n" http://localhost:11000/health

echo ""
echo "=== All agents ping ==="
for port in 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010 11000 12000 13000 14000 15000 16000 17000 18000 19000 22000 23000 25000 26000 31000 32000 33000 35000; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://localhost:$port/health 2>/dev/null)
  echo "Port $port: $STATUS"
done

echo ""
echo "=== Unhealthy containers ==="
docker ps --filter "health=unhealthy" --format "{{.Names}}\t{{.Status}}" 2>/dev/null || echo "none"
