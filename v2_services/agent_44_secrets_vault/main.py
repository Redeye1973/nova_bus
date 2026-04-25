"""NOVA v2 Agent 44 — Secrets Vault.

Centralized secret storage for the NOVA agent ecosystem.
Backing store: AES-256-GCM encrypted SQLite on a Docker volume.

Endpoints:
- GET  /health
- POST /secrets/get        {"name": "KEY_NAME"}
- POST /secrets/set        {"name": "KEY_NAME", "value": "..."}
- POST /secrets/delete     {"name": "KEY_NAME"}
- GET  /secrets/list       returns names only, never values
- POST /secrets/bulk_set   [{"name": "...", "value": "..."}, ...]
- POST /invoke             {"action": "get|set|delete|list"}

Auth: all mutating endpoints require Bearer token (NOVA_VAULT_TOKEN env).
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
import sqlite3
import time
from base64 import b64decode, b64encode
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("secrets_vault")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

VAULT_TOKEN = os.getenv("NOVA_VAULT_TOKEN", "")
DB_PATH = Path(os.getenv("VAULT_DB_PATH", "/data/vault.db"))
VAULT_KEY_HEX = os.getenv("VAULT_ENCRYPTION_KEY", "")

app = FastAPI(title="NOVA v2 Agent 44 - Secrets Vault", version="0.1.0")


def _get_encryption_key() -> bytes:
    if VAULT_KEY_HEX:
        return bytes.fromhex(VAULT_KEY_HEX)
    key_file = DB_PATH.parent / ".vault_key"
    if key_file.exists():
        return bytes.fromhex(key_file.read_text().strip())
    key = AESGCM.generate_key(bit_length=256)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    key_file.write_text(key.hex())
    key_file.chmod(0o600)
    logger.warning("Generated new vault encryption key at %s", key_file)
    return key


ENC_KEY = _get_encryption_key()
AESGCM_INSTANCE = AESGCM(ENC_KEY)


def _encrypt(plaintext: str) -> str:
    nonce = secrets.token_bytes(12)
    ct = AESGCM_INSTANCE.encrypt(nonce, plaintext.encode(), None)
    return b64encode(nonce + ct).decode()


def _decrypt(token: str) -> str:
    raw = b64decode(token)
    nonce, ct = raw[:12], raw[12:]
    return AESGCM_INSTANCE.decrypt(nonce, ct, None).decode()


def _db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS secrets (
            name      TEXT PRIMARY KEY,
            value_enc TEXT NOT NULL,
            updated_at REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            ts         REAL NOT NULL,
            action     TEXT NOT NULL,
            secret_name TEXT NOT NULL,
            caller     TEXT
        )
    """)
    conn.commit()
    return conn


def _audit(conn: sqlite3.Connection, action: str, name: str, caller: str = "api"):
    conn.execute(
        "INSERT INTO audit_log (ts, action, secret_name, caller) VALUES (?, ?, ?, ?)",
        (time.time(), action, name, caller),
    )
    conn.commit()


def _require_token(authorization: Optional[str] = Header(None)):
    if not VAULT_TOKEN:
        raise HTTPException(500, "NOVA_VAULT_TOKEN not configured on server")
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(token, VAULT_TOKEN):
        raise HTTPException(403, "Invalid token")


class SecretGet(BaseModel):
    name: str = Field(..., min_length=1)


class SecretSet(BaseModel):
    name: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)


class SecretBulk(BaseModel):
    secrets: List[SecretSet]


class InvokeBody(BaseModel):
    action: str = "list"
    name: Optional[str] = None
    value: Optional[str] = None
    secrets: Optional[List[Dict[str, str]]] = None


@app.get("/health")
def health() -> Dict[str, Any]:
    db_ok = DB_PATH.exists()
    return {
        "status": "ok",
        "agent": "44_secrets_vault",
        "version": "0.1.0",
        "db_exists": db_ok,
    }


@app.post("/secrets/get")
def secret_get(body: SecretGet, _=Depends(_require_token)) -> Dict[str, Any]:
    conn = _db()
    row = conn.execute("SELECT value_enc FROM secrets WHERE name = ?", (body.name,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, f"Secret '{body.name}' not found")
    return {"name": body.name, "value": _decrypt(row[0])}


@app.post("/secrets/set")
def secret_set(body: SecretSet, _=Depends(_require_token)) -> Dict[str, Any]:
    conn = _db()
    enc = _encrypt(body.value)
    conn.execute(
        "INSERT OR REPLACE INTO secrets (name, value_enc, updated_at) VALUES (?, ?, ?)",
        (body.name, enc, time.time()),
    )
    _audit(conn, "set", body.name)
    conn.close()
    return {"stored": True, "name": body.name}


@app.post("/secrets/delete")
def secret_delete(body: SecretGet, _=Depends(_require_token)) -> Dict[str, Any]:
    conn = _db()
    cur = conn.execute("DELETE FROM secrets WHERE name = ?", (body.name,))
    deleted = cur.rowcount > 0
    if deleted:
        _audit(conn, "delete", body.name)
    conn.close()
    return {"deleted": deleted, "name": body.name}


@app.get("/secrets/list")
def secret_list(_=Depends(_require_token)) -> Dict[str, Any]:
    conn = _db()
    rows = conn.execute("SELECT name, updated_at FROM secrets ORDER BY name").fetchall()
    conn.close()
    return {
        "count": len(rows),
        "secrets": [{"name": r[0], "updated_at": r[1]} for r in rows],
    }


@app.post("/secrets/bulk_set")
def secret_bulk_set(body: SecretBulk, _=Depends(_require_token)) -> Dict[str, Any]:
    conn = _db()
    count = 0
    for s in body.secrets:
        enc = _encrypt(s.value)
        conn.execute(
            "INSERT OR REPLACE INTO secrets (name, value_enc, updated_at) VALUES (?, ?, ?)",
            (s.name, enc, time.time()),
        )
        _audit(conn, "bulk_set", s.name)
        count += 1
    conn.close()
    return {"stored": count}


@app.get("/secrets/audit")
def secret_audit(limit: int = 50, _=Depends(_require_token)) -> Dict[str, Any]:
    conn = _db()
    rows = conn.execute(
        "SELECT ts, action, secret_name, caller FROM audit_log ORDER BY id DESC LIMIT ?",
        (min(limit, 500),),
    ).fetchall()
    conn.close()
    return {
        "count": len(rows),
        "entries": [
            {"ts": r[0], "action": r[1], "secret_name": r[2], "caller": r[3]}
            for r in rows
        ],
    }


@app.post("/invoke")
def invoke(body: InvokeBody, _=Depends(_require_token)) -> Dict[str, Any]:
    action = body.action.lower()
    if action == "list":
        return secret_list()
    if action == "get":
        if not body.name:
            raise HTTPException(400, "name required for get")
        return secret_get(SecretGet(name=body.name))
    if action == "set":
        if not body.name or not body.value:
            raise HTTPException(400, "name and value required for set")
        return secret_set(SecretSet(name=body.name, value=body.value))
    if action == "delete":
        if not body.name:
            raise HTTPException(400, "name required for delete")
        return secret_delete(SecretGet(name=body.name))
    if action == "bulk_set":
        if not body.secrets:
            raise HTTPException(400, "secrets list required for bulk_set")
        items = [SecretSet(name=s["name"], value=s["value"]) for s in body.secrets]
        return secret_bulk_set(SecretBulk(secrets=items))
    return {"error": f"unknown action: {action}", "valid": ["get", "set", "delete", "list", "bulk_set"]}
