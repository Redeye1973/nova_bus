#!/bin/bash
set -e

COMPOSE_FILE="${1:-docker-compose.yml}"
TIERS_CONFIG="${2:-infrastructure/startup_tiers.yaml}"
LOG="/var/log/nova-startup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"
}

wait_healthy() {
    local services="$1"
    local timeout="${2:-120}"
    local elapsed=0

    while [ $elapsed -lt $timeout ]; do
        local all_ok=true
        for svc in $services; do
            local cid
            cid=$(docker compose -f "$COMPOSE_FILE" ps -q "$svc" 2>/dev/null)
            if [ -z "$cid" ]; then
                all_ok=false
                break
            fi
            local status
            status=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}running{{end}}' "$cid" 2>/dev/null || echo "missing")
            if [ "$status" = "unhealthy" ] || [ "$status" = "missing" ]; then
                all_ok=false
                break
            fi
            if [ "$status" != "healthy" ] && [ "$status" != "running" ]; then
                all_ok=false
                break
            fi
        done
        if [ "$all_ok" = true ]; then
            return 0
        fi
        sleep 5
        elapsed=$((elapsed + 5))
    done
    log "  WARNING: not all healthy after ${timeout}s"
    return 1
}

start_tier() {
    local tier_name="$1"
    shift
    local wait_after="$1"
    shift
    local services="$*"

    log "=== Tier: $tier_name ==="
    for svc in $services; do
        log "  up: $svc"
        docker compose -f "$COMPOSE_FILE" up -d --no-deps "$svc" 2>/dev/null || true
        sleep 2
    done

    log "  waiting for healthy (max 120s)..."
    wait_healthy "$services" 120 || true

    if [ "$wait_after" -gt 0 ]; then
        log "  cooldown ${wait_after}s"
        sleep "$wait_after"
    fi
}

main() {
    cd /docker/nova-v2
    log "===== NOVA Staggered Startup ====="
    log "Compose: $COMPOSE_FILE"
    log "Load: $(uptime | awk -F'load average:' '{print $2}')"

    start_tier "0 Foundation" 30 \
        postgres-v2 redis-v2 minio-v2 qdrant-v2

    start_tier "1 Core" 20 \
        agent-44-secrets-vault n8n-v2-main n8n-v2-worker-1 n8n-v2-webhook \
        agent-11-monitor agent-60-memory-curator

    start_tier "2 Critical" 15 \
        nova-judge agent-16-cost-guard agent-17-error-handler \
        agent-18-prompt-director agent-12-bake-orchestrator \
        agent-61-notification-hub agent-62-service-router

    start_tier "3 Processors" 10 \
        agent-20-design-fase agent-22-blender-renderer agent-23-aseprite-processor \
        agent-25-pyqt-assembly agent-26-godot-import agent-21-freecad-parametric \
        agent-14-blender-baker agent-13-pdok-downloader agent-15-qgis-processor \
        agent-27-storyboard agent-28-story-integration agent-29-elevenlabs \
        agent-31-qgis-analysis agent-32-grass-gis agent-33-blender-arch-walkthrough \
        agent-34-unreal-import agent-35-raster-2d agent-19-distribution

    start_tier "4 Juries" 5 \
        sprite-jury-v2 agent-02-code-jury agent-03-audio-jury \
        agent-04-3d-model-jury agent-05-gis-jury agent-06-cad-jury \
        agent-07-narrative-jury agent-08-character-art-jury \
        agent-09-illustration-jury agent-10-game-balance-jury \
        agent-24-aseprite-anim-jury agent-30-audio-asset-jury

    log "=== Starting remaining services ==="
    docker compose -f "$COMPOSE_FILE" up -d 2>/dev/null || true

    TOTAL=$(docker ps -q | wc -l)
    HEALTHY=$(docker ps --filter "health=healthy" -q | wc -l)
    log "===== Startup complete: $TOTAL running, $HEALTHY healthy ====="
    log "Load: $(uptime | awk -F'load average:' '{print $2}')"
}

main "$@"
