"""Migrate secrets from /docker/nova-v2/.env into Agent 44 vault (runs on prod)."""
from __future__ import annotations
import json, sys, urllib.request

VAULT_URL = "http://nova-v2-agent-44-secrets-vault:8144"
TOKEN = sys.argv[1] if len(sys.argv) > 1 else ""
ENV_FILE = "/docker/nova-v2/.env"

if not TOKEN:
    print("Usage: python migrate_prod_env_to_vault.py <VAULT_TOKEN>", file=sys.stderr)
    sys.exit(1)

secrets = []
with open(ENV_FILE) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key, val = key.strip(), val.strip()
        if key and val:
            secrets.append({"name": key, "value": val})

print(f"Found {len(secrets)} secrets in {ENV_FILE}")
for s in secrets:
    print(f"  {s['name']} = {s['value'][:8]}...")

body = json.dumps({"secrets": secrets}).encode()
req = urllib.request.Request(
    f"{VAULT_URL}/secrets/bulk_set",
    data=body,
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
)
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())
print(f"\nStored: {result['stored']} secrets")

req2 = urllib.request.Request(
    f"{VAULT_URL}/secrets/list",
    headers={"Authorization": f"Bearer {TOKEN}"},
)
resp2 = urllib.request.urlopen(req2)
vault = json.loads(resp2.read())
print(f"Vault now has {vault['count']} secrets")
print("MIGRATION COMPLETE")
