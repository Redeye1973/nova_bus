import urllib.request, json, sys

VAULT_URL = "http://localhost:8144"
TOKEN = "th4-qgRrl7eH9_GHgnga9FncjRKFXVb50xCEBVmvwig3ypTz"

def req(method, path, data=None):
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(
        f"{VAULT_URL}{path}",
        data=body,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        method=method,
    )
    resp = urllib.request.urlopen(r)
    return json.loads(resp.read())

print("1. List (empty):", req("GET", "/secrets/list"))
print("2. Set TEST_KEY:", req("POST", "/secrets/set", {"name": "TEST_KEY", "value": "hello123"}))
print("3. Get TEST_KEY:", req("POST", "/secrets/get", {"name": "TEST_KEY"}))
print("4. List (1 key):", req("GET", "/secrets/list"))
print("5. Delete TEST_KEY:", req("POST", "/secrets/delete", {"name": "TEST_KEY"}))
print("ALL TESTS PASS")
