from __future__ import annotations

from datetime import UTC, datetime
from fastapi import FastAPI, HTTPException

from .middleware import AlertMessage, should_send_alert
from .models import LifecycleEvent, NotifyRequest
from .notifier import send_discord, send_telegram
from .store import QuietModeStore

app = FastAPI(title="nova-bridge", version="0.2.0")
store = QuietModeStore()


@app.post("/lifecycle")
def lifecycle(event: LifecycleEvent) -> dict:
    try:
        if event.event == "shutdown":
            ttl = 7200
            store.set_quiet_mode(ttl, "shutdown")
        elif event.event == "startup":
            ttl = 300
            store.set_quiet_mode(ttl, "startup")
        else:
            ttl = max((event.duration_minutes or 5) * 60, 60)
            store.set_quiet_mode(ttl, "snooze")

        return {
            "ok": True,
            "event": event.event,
            "host": event.host,
            "quiet_mode_active": True,
            "quiet_mode_ttl": ttl,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"redis unavailable: {exc}") from exc


@app.get("/lifecycle/status")
def lifecycle_status() -> dict:
    try:
        active = store.is_active()
        return {
            "quiet_mode_active": active,
            "remaining_seconds": max(store.ttl(), 0) if active else 0,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"redis unavailable: {exc}") from exc


@app.post("/notify")
def notify(payload: NotifyRequest) -> dict:
    msg = AlertMessage(
        channel=",".join(payload.channels),
        text=f"{payload.title} - {payload.detail}".strip(" -"),
        kind=payload.kind,
    )
    allowed = should_send_alert(msg, store=store)
    if not allowed:
        return {"sent": False, "suppressed": True, "reason": "quiet_mode_active", "remaining_seconds": max(store.ttl(), 0)}

    sent = {}
    text = f"[{payload.severity.upper()}] {payload.title}"
    if payload.detail:
        text += f"\n{payload.detail}"

    if "telegram" in payload.channels:
        sent["telegram"] = send_telegram(text)
    if "discord" in payload.channels:
        sent["discord"] = send_discord(text, severity=payload.severity)

    return {"sent": True, "suppressed": False, "channels": sent}


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "nova-bridge", "version": "0.2.0"}
