#!/usr/bin/env python3
"""Quick daily log entry via Memory Curator API."""
import sys
import requests

MEMORY_URL = "http://178.104.207.194:8060"

if len(sys.argv) < 3:
    print("Usage: log.py <project> <message>")
    print("Example: log.py black_ledger 'Started ship component generation'")
    sys.exit(1)

project = sys.argv[1]
message = " ".join(sys.argv[2:])

try:
    response = requests.post(
        f"{MEMORY_URL}/memory/append",
        json={
            "path": f"projects/{project}/progress/daily_log.md",
            "content": message,
        },
    )
    print(response.json())
except requests.ConnectionError:
    print(f"ERROR: Cannot reach Memory Curator at {MEMORY_URL}")
    sys.exit(1)
