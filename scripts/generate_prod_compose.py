"""Generate docker-compose.prod.yml from dev compose — replaces build contexts with GHCR images."""
import yaml
from pathlib import Path

DEV_COMPOSE = Path(r"L:\!Nova V2\infrastructure\docker-compose.yml")
PROD_COMPOSE = Path(r"L:\!Nova V2\infrastructure\docker-compose.prod.yml")

with open(DEV_COMPOSE) as f:
    dev = yaml.safe_load(f)

prod = {"services": {}, "volumes": dev.get("volumes", {}), "networks": dev.get("networks", {})}

for service_name, config in dev["services"].items():
    new_config = {}
    has_build = False
    ghcr_image = None

    for k, v in config.items():
        if k == "build":
            has_build = True
            context = v.get("context", "") if isinstance(v, dict) else v
            agent_dir = Path(context).name
            ghcr_image = f"ghcr.io/redeye1973/nova-{agent_dir}:latest"
            continue
        if k == "image" and has_build:
            continue
        new_config[k] = v

    if has_build and ghcr_image:
        new_config["image"] = ghcr_image
    elif "image" not in new_config:
        new_config["image"] = config.get("image", f"nova-v2-{service_name}:latest")

    prod["services"][service_name] = new_config

with open(PROD_COMPOSE, "w") as f:
    yaml.dump(prod, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

build_count = sum(1 for s in dev["services"].values() if "build" in s)
image_count = sum(1 for s in prod["services"].values() if s.get("image", "").startswith("ghcr.io"))
print(f"Generated {PROD_COMPOSE}")
print(f"  {build_count} build contexts -> {image_count} GHCR images")
print(f"  Total services: {len(prod['services'])}")
