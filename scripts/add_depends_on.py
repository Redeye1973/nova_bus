"""Add tier-based depends_on to docker-compose.yml for staggered startup."""
import yaml
from pathlib import Path

COMPOSE = Path(r"L:\!Nova V2\infrastructure\docker-compose.yml")
TIERS = Path(r"L:\!Nova V2\infrastructure\startup_tiers.yaml")

with open(COMPOSE) as f:
    data = yaml.safe_load(f)

with open(TIERS) as f:
    tiers = yaml.safe_load(f)

tier_0 = set(tiers["tiers"]["0_foundation"]["services"])
tier_1 = set(tiers["tiers"]["1_core"]["services"])
tier_2 = set(tiers["tiers"]["2_critical"]["services"])
tier_3 = set(tiers["tiers"]["3_processors"]["services"])
tier_4 = set(tiers["tiers"]["4_juries"]["services"])

FOUNDATION_DEPS = {
    "postgres-v2": {"condition": "service_healthy"},
    "redis-v2": {"condition": "service_healthy"},
}

CORE_DEPS = {
    "postgres-v2": {"condition": "service_healthy"},
    "agent-44-secrets-vault": {"condition": "service_healthy"},
}

JUDGE_DEP = {
    "nova-judge": {"condition": "service_healthy"},
}

count = 0
for name, config in data.get("services", {}).items():
    if name in tier_0:
        continue

    if name in tier_1:
        deps = {"postgres-v2": {"condition": "service_healthy"}}
        if name not in ("n8n-v2-main",):
            pass
    elif name in tier_2:
        deps = dict(CORE_DEPS)
    elif name in tier_3:
        deps = {"agent-44-secrets-vault": {"condition": "service_healthy"}}
    elif name in tier_4:
        deps = {
            "agent-44-secrets-vault": {"condition": "service_healthy"},
            "nova-judge": {"condition": "service_healthy"},
        }
    else:
        continue

    existing = config.get("depends_on", {})
    if isinstance(existing, list):
        existing = {s: {"condition": "service_started"} for s in existing}
    elif isinstance(existing, dict):
        pass
    else:
        existing = {}

    merged = {**existing, **deps}
    config["depends_on"] = merged
    count += 1
    print(f"  {name}: depends_on {list(merged.keys())}")

for name, config in data.get("services", {}).items():
    hc = config.get("healthcheck", {})
    if hc:
        if "start_period" not in hc:
            hc["start_period"] = "30s"
            config["healthcheck"] = hc

with open(COMPOSE, "w") as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f"\nUpdated {count} services with depends_on")
