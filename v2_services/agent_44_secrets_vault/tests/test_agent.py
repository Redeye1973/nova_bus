"""Tests for Agent 44 — Secrets Vault."""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

os.environ["NOVA_VAULT_TOKEN"] = "test-token-12345"
os.environ["VAULT_DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test_vault.db")

from main import app  # noqa: E402

client = TestClient(app)
AUTH = {"Authorization": "Bearer test-token-12345"}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["agent"] == "44_secrets_vault"


def test_set_and_get():
    r = client.post("/secrets/set", json={"name": "TEST_KEY", "value": "hello"}, headers=AUTH)
    assert r.status_code == 200
    assert r.json()["stored"] is True

    r = client.post("/secrets/get", json={"name": "TEST_KEY"}, headers=AUTH)
    assert r.status_code == 200
    assert r.json()["value"] == "hello"


def test_get_missing_returns_404():
    r = client.post("/secrets/get", json={"name": "NONEXISTENT"}, headers=AUTH)
    assert r.status_code == 404


def test_delete():
    client.post("/secrets/set", json={"name": "DEL_ME", "value": "x"}, headers=AUTH)
    r = client.post("/secrets/delete", json={"name": "DEL_ME"}, headers=AUTH)
    assert r.status_code == 200
    assert r.json()["deleted"] is True

    r = client.post("/secrets/get", json={"name": "DEL_ME"}, headers=AUTH)
    assert r.status_code == 404


def test_list():
    client.post("/secrets/set", json={"name": "A_KEY", "value": "1"}, headers=AUTH)
    client.post("/secrets/set", json={"name": "B_KEY", "value": "2"}, headers=AUTH)
    r = client.get("/secrets/list", headers=AUTH)
    assert r.status_code == 200
    names = [s["name"] for s in r.json()["secrets"]]
    assert "A_KEY" in names
    assert "B_KEY" in names


def test_bulk_set():
    r = client.post(
        "/secrets/bulk_set",
        json={"secrets": [{"name": "BULK_1", "value": "v1"}, {"name": "BULK_2", "value": "v2"}]},
        headers=AUTH,
    )
    assert r.status_code == 200
    assert r.json()["stored"] == 2


def test_audit_log():
    client.post("/secrets/set", json={"name": "AUDIT_TEST", "value": "x"}, headers=AUTH)
    r = client.get("/secrets/audit", headers=AUTH)
    assert r.status_code == 200
    assert r.json()["count"] > 0
    assert any(e["secret_name"] == "AUDIT_TEST" for e in r.json()["entries"])


def test_no_auth_returns_401():
    r = client.post("/secrets/get", json={"name": "X"})
    assert r.status_code == 401


def test_bad_token_returns_403():
    r = client.post("/secrets/get", json={"name": "X"}, headers={"Authorization": "Bearer wrong"})
    assert r.status_code == 403


def test_overwrite_secret():
    client.post("/secrets/set", json={"name": "OW_KEY", "value": "old"}, headers=AUTH)
    client.post("/secrets/set", json={"name": "OW_KEY", "value": "new"}, headers=AUTH)
    r = client.post("/secrets/get", json={"name": "OW_KEY"}, headers=AUTH)
    assert r.json()["value"] == "new"
