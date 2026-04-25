import json, urllib.request, sys

TOKEN = "th4-qgRrl7eH9_GHgnga9FncjRKFXVb50xCEBVmvwig3ypTz"
ENV_FILE = "/tmp/prod.env"

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

print(f"Found {len(secrets)} secrets")
body = json.dumps({"secrets": secrets}).encode()
req = urllib.request.Request(
    "http://localhost:8144/secrets/bulk_set",
    data=body,
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
)
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())
print(f"Stored: {result['stored']}")

req2 = urllib.request.Request(
    "http://localhost:8144/secrets/list",
    headers={"Authorization": f"Bearer {TOKEN}"},
)
resp2 = urllib.request.urlopen(req2)
vault = json.loads(resp2.read())
print(f"Vault total: {vault['count']} secrets")
for s in vault["secrets"]:
    print(f"  {s['name']}")
print("MIGRATION COMPLETE")
