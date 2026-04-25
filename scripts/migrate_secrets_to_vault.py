"""Migrate plaintext secrets from nova_v2_passwords.txt into Agent 44 vault.

Usage:
    python migrate_secrets_to_vault.py [--vault-url URL] [--token TOKEN] [--dry-run]

Reads L:\!Nova V2\secrets\nova_v2_passwords.txt, parses KEY=VALUE lines,
and bulk-uploads them to the Secrets Vault agent.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

SECRETS_FILE = Path(r"L:\!Nova V2\secrets\nova_v2_passwords.txt")
DEFAULT_VAULT_URL = "http://agent-44-secrets-vault:8144"


def parse_secrets(path: Path) -> list[dict[str, str]]:
    items = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            continue
        items.append({"name": key, "value": value})
    return items


def upload(vault_url: str, token: str, secrets: list[dict[str, str]], dry_run: bool) -> None:
    print(f"Found {len(secrets)} secrets to migrate")
    if dry_run:
        for s in secrets:
            print(f"  [DRY RUN] {s['name']} = {s['value'][:8]}...")
        return

    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(
        f"{vault_url}/secrets/bulk_set",
        json={"secrets": secrets},
        headers=headers,
        timeout=30,
    )
    if r.status_code == 200:
        print(f"OK: {r.json()['stored']} secrets stored in vault")
    else:
        print(f"FAIL: http {r.status_code} — {r.text}", file=sys.stderr)
        sys.exit(1)

    print("\nVerifying...")
    r = requests.get(f"{vault_url}/secrets/list", headers=headers, timeout=10)
    if r.status_code == 200:
        vault_names = {s["name"] for s in r.json()["secrets"]}
        local_names = {s["name"] for s in secrets}
        missing = local_names - vault_names
        if missing:
            print(f"WARNING: {len(missing)} secrets not found in vault: {missing}")
        else:
            print(f"All {len(local_names)} secrets verified in vault")
    else:
        print(f"Could not verify: {r.status_code}")


def write_mapping(secrets: list[dict[str, str]]) -> None:
    mapping_path = SECRETS_FILE.parent / "vault_mapping.yaml"
    lines = ["# Vault secret name mapping (no values, safe to commit)", "secrets:"]
    for s in sorted(secrets, key=lambda x: x["name"]):
        lines.append(f"  - {s['name']}")
    mapping_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Mapping written to {mapping_path}")


def main():
    parser = argparse.ArgumentParser(description="Migrate secrets to vault")
    parser.add_argument("--vault-url", default=DEFAULT_VAULT_URL)
    parser.add_argument("--token", default="", help="NOVA_VAULT_TOKEN")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not SECRETS_FILE.exists():
        print(f"Secrets file not found: {SECRETS_FILE}", file=sys.stderr)
        sys.exit(1)

    secrets = parse_secrets(SECRETS_FILE)
    if not secrets:
        print("No secrets found to migrate")
        sys.exit(0)

    write_mapping(secrets)

    if args.dry_run:
        upload(args.vault_url, args.token, secrets, dry_run=True)
    else:
        if not args.token:
            print("ERROR: --token required (or set NOVA_VAULT_TOKEN)", file=sys.stderr)
            sys.exit(1)
        upload(args.vault_url, args.token, secrets, dry_run=False)


if __name__ == "__main__":
    main()
