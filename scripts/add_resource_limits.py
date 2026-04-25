"""Add deploy.resources to all services in docker-compose.yml."""
import yaml
from pathlib import Path

COMPOSE = Path(r"L:\!Nova V2\infrastructure\docker-compose.yml")

HEAVY = {
    "agent-22-blender-renderer", "agent-14-blender-baker",
    "agent-33-blender-arch-walkthrough", "agent-23-aseprite-processor",
    "agent-34-unreal-import", "agent-25-pyqt-assembly",
    "agent-21-freecad-parametric",
}

DATABASE = {"postgres-v2"}
SEARCH = {"qdrant-v2"}
INFRA_MEDIUM = {"n8n-v2-main", "minio-v2", "nova-judge"}
INFRA_LIGHT = {"redis-v2", "n8n-v2-worker-1", "n8n-v2-webhook"}

JURY = {
    "sprite-jury-v2", "agent-02-code-jury", "agent-03-audio-jury",
    "agent-04-3d-model-jury", "agent-05-gis-jury", "agent-06-cad-jury",
    "agent-07-narrative-jury", "agent-08-character-art-jury",
    "agent-09-illustration-jury", "agent-10-game-balance-jury",
    "agent-24-aseprite-anim-jury", "agent-30-audio-asset-jury",
}

TINY = {
    "agent-44-secrets-vault", "agent-61-notification-hub",
    "agent-62-service-router",
}

def get_limits(name):
    if name in DATABASE:
        return {"memory": "2G", "cpus": "1.5"}, {"memory": "256M", "cpus": "0.1"}
    if name in SEARCH:
        return {"memory": "1G", "cpus": "0.8"}, {"memory": "128M", "cpus": "0.1"}
    if name in INFRA_MEDIUM:
        return {"memory": "1G", "cpus": "1.0"}, {"memory": "128M", "cpus": "0.1"}
    if name in INFRA_LIGHT:
        return {"memory": "512M", "cpus": "0.5"}, {"memory": "64M", "cpus": "0.1"}
    if name in HEAVY:
        return {"memory": "1G", "cpus": "1.0"}, {"memory": "128M", "cpus": "0.1"}
    if name in JURY or name in TINY:
        return {"memory": "256M", "cpus": "0.3"}, {"memory": "64M", "cpus": "0.05"}
    return {"memory": "512M", "cpus": "0.5"}, {"memory": "64M", "cpus": "0.1"}

with open(COMPOSE) as f:
    data = yaml.safe_load(f)

count = 0
for name, config in data.get("services", {}).items():
    if "deploy" in config:
        continue
    limits, reservations = get_limits(name)
    config["deploy"] = {
        "resources": {
            "limits": limits,
            "reservations": reservations,
        }
    }
    count += 1
    print(f"  {name}: limits={limits}")

with open(COMPOSE, "w") as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f"\nUpdated {count} services with resource limits")
