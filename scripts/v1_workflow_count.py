"""Print V1 n8n workflow count (never echoes the API key). Exit 2 if key line missing."""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

p = Path(r"L:/!Nova V2/secrets/nova_v2_passwords.txt")
text = p.read_text(encoding="utf-8", errors="ignore")
m = re.search(r"^N8N_V1_API_KEY=(.+)$", text, re.MULTILINE)
if not m:
    print("RESULT:MISSING_KEY_LINE")
    sys.exit(2)
key = m.group(1).strip().strip('"').strip("'")
req = urllib.request.Request(
    "http://178.104.207.194:5678/api/v1/workflows?limit=100",
    headers={"X-N8N-API-KEY": key},
)
try:
    with urllib.request.urlopen(req, timeout=45) as r:
        body = json.load(r)
except urllib.error.HTTPError as e:
    print("RESULT:HTTP", e.code)
    sys.exit(1)
except OSError as e:
    print("RESULT:ERROR", type(e).__name__)
    sys.exit(1)
n = len(body.get("data") or [])
print("RESULT:OK")
print("V1_workflows_count:", n)
print("meets_50:", n >= 50)
