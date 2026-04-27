from __future__ import annotations

from fastapi.testclient import TestClient

from nova_bridge import alert_suppressor as svc
from nova_bridge.middleware import AlertMessage, should_send_alert


class FakeRedis:
    def __init__(self) -> None:
        self._value = None
        self._ttl = -2

    def set(self, key, value, ex):
        self._value = value
        self._ttl = ex

    def delete(self, key):
        self._value = None
        self._ttl = -2

    def ttl(self, key):
        return self._ttl

    def exists(self, key):
        return 1 if self._value is not None and self._ttl > 0 else 0


class RaisingRedis(FakeRedis):
    def set(self, key, value, ex):
        raise RuntimeError("redis down")

    def exists(self, key):
        raise RuntimeError("redis down")


def _set_fake_store(fake_redis: FakeRedis):
    svc.store.redis = fake_redis


def test_shutdown_event_sets_quiet_mode_2h():
    fake = FakeRedis()
    _set_fake_store(fake)
    client = TestClient(svc.app)
    r = client.post("/lifecycle", json={"event": "shutdown", "host": "nova-desktop"})
    assert r.status_code == 200
    status = client.get("/lifecycle/status").json()
    assert status["quiet_mode_active"] is True
    assert 7100 <= status["remaining_seconds"] <= 7200


def test_startup_event_sets_quiet_mode_5min():
    fake = FakeRedis()
    _set_fake_store(fake)
    client = TestClient(svc.app)
    r = client.post("/lifecycle", json={"event": "startup", "host": "nova-desktop"})
    assert r.status_code == 200
    status = client.get("/lifecycle/status").json()
    assert status["quiet_mode_active"] is True
    assert 280 <= status["remaining_seconds"] <= 300


def test_alert_during_quiet_mode_logged_not_sent(monkeypatch):
    fake = FakeRedis()
    fake.set("nova:quiet_mode", "startup", ex=300)

    writes = []

    def _fake_log(channel, text, reason, ttl):
        writes.append((channel, text, reason, ttl))

    monkeypatch.setattr("nova_bridge.middleware.log_suppressed_alert", _fake_log)

    msg = AlertMessage(channel="telegram", text="infra down", kind="infrastructure")
    sent = should_send_alert(msg, store=svc.store.__class__(redis_client=fake))
    assert sent is False
    assert len(writes) == 1


def test_alert_outside_quiet_mode_sent_normally(monkeypatch):
    fake = FakeRedis()

    writes = []

    def _fake_log(channel, text, reason, ttl):
        writes.append((channel, text, reason, ttl))

    monkeypatch.setattr("nova_bridge.middleware.log_suppressed_alert", _fake_log)

    msg = AlertMessage(channel="discord", text="infra down", kind="infrastructure")
    sent = should_send_alert(msg, store=svc.store.__class__(redis_client=fake))
    assert sent is True
    assert writes == []


def test_user_messages_bypass_filter(monkeypatch):
    fake = FakeRedis()
    fake.set("nova:quiet_mode", "startup", ex=300)
    writes = []
    monkeypatch.setattr("nova_bridge.middleware.log_suppressed_alert", lambda *a, **k: writes.append(1))

    msg = AlertMessage(channel="telegram", text="hello alex", kind="user_message")
    sent = should_send_alert(msg, store=svc.store.__class__(redis_client=fake))
    assert sent is True
    assert writes == []


def test_notify_infrastructure_suppressed_during_quiet_mode(monkeypatch):
    fake = FakeRedis()
    fake.set("nova:quiet_mode", "startup", ex=300)
    _set_fake_store(fake)

    monkeypatch.setattr("nova_bridge.alert_suppressor.send_telegram", lambda text: True)
    monkeypatch.setattr("nova_bridge.alert_suppressor.send_discord", lambda text, severity='warning': True)

    client = TestClient(svc.app)
    r = client.post(
        "/notify",
        json={"title": "Nova down", "detail": "bridge not reachable", "severity": "warning", "kind": "infrastructure"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["suppressed"] is True


def test_notify_user_message_bypasses_quiet_mode(monkeypatch):
    fake = FakeRedis()
    fake.set("nova:quiet_mode", "startup", ex=300)
    _set_fake_store(fake)

    monkeypatch.setattr("nova_bridge.alert_suppressor.send_telegram", lambda text: True)
    monkeypatch.setattr("nova_bridge.alert_suppressor.send_discord", lambda text, severity='warning': True)

    client = TestClient(svc.app)
    r = client.post(
        "/notify",
        json={"title": "Alex message", "detail": "manual note", "severity": "info", "kind": "user_message", "channels": ["telegram"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["suppressed"] is False
    assert body["channels"]["telegram"] is True


def test_lifecycle_endpoint_returns_503_if_redis_down():
    svc.store.redis = RaisingRedis()
    client = TestClient(svc.app)
    r = client.post("/lifecycle", json={"event": "shutdown", "host": "nova-desktop"})
    assert r.status_code == 503
