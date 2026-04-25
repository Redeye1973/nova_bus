#!/bin/bash
set -e
echo "=== Pipeline E2E pre-flight (internal Docker DNS) ==="

check() {
  local url="$1"
  local name="$2"
  code=$(docker exec nova-v2-notification-hub python3 -c "
import urllib.request
try:
    r = urllib.request.urlopen('$url', timeout=5)
    print(r.getcode())
except Exception as e:
    print('ERR', e)
" 2>/dev/null | tail -1)
  echo "$name: $code"
}

check "http://agent-11-monitor:8111/health" "Monitor (11)"
check "http://agent-12-bake-orchestrator:8112/health" "Bake / Lineage (12)"
check "http://agent-16-cost-guard:8116/health" "Cost Guard (16)"
check "http://agent-17-error-handler:8117/health" "Error Handler (17)"
check "http://agent-18-prompt-director:8118/health" "Prompt Director (18)"
check "http://agent-22-blender-renderer:8122/health" "Blender (22)"
check "http://agent-23-aseprite-processor:8123/health" "Aseprite (23)"
check "http://agent-25-pyqt-assembly:8125/health" "PyQt (25)"
check "http://agent-26-godot-import:8126/health" "Godot (26)"
check "http://agent-60-memory-curator:8060/health" "Memory Curator (60)"
check "http://agent-61-notification-hub:8061/health" "Notification Hub (61)"
check "http://agent-62-service-router:8062/health" "Service Router (62)"
check "http://agent-44-secrets-vault:8144/health" "Vault (44)"
check "http://sprite-jury-v2:8101/health" "Sprite Jury (01)"
check "http://nova-judge:8000/health" "Judge"

echo "=== Bridge from agent 22 container ==="
docker exec nova-v2-agent-22-blender-renderer python3 -c "
import urllib.request
try:
    r = urllib.request.urlopen('http://host.docker.internal:8500/health', timeout=5)
    print('Bridge (from agent 22):', r.getcode())
except Exception as e:
    print('Bridge (from agent 22): unreachable —', type(e).__name__, e)
" 2>&1 || echo "agent-22 not running"

echo "=== Done ==="
