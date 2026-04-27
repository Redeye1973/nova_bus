from __future__ import annotations

import os
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from shutil import disk_usage

import httpx
from fastapi import FastAPI, HTTPException

from .middleware import AlertMessage, should_send_alert
from .models import LifecycleEvent, NotifyRequest, TelegramCommandRequest
from .notifier import send_discord, send_telegram
from .store import QuietModeStore
from .timeutils import format_for_user, now_utc, to_local

app = FastAPI(title="nova-bridge", version="0.2.0")
store = QuietModeStore()
SERVICE_ENDPOINTS = {
    "nova-ref": os.getenv("NOVA_REF_HEALTH_URL", "http://127.0.0.1:8400/health"),
    "nova-learn": os.getenv("NOVA_LEARN_HEALTH_URL", "http://127.0.0.1:8401/health"),
    "bridge": os.getenv("NOVA_BRIDGE_HEALTH_URL", "http://127.0.0.1:8088/health"),
}


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


def _admin_chatids() -> set[str]:
    raw = os.getenv("NOVA_TELEGRAM_ADMIN_CHATIDS", "")
    return {v.strip() for v in raw.split(",") if v.strip()}


def _parse_duration_to_seconds(token: str) -> int | None:
    token = token.strip().lower()
    if token == "night":
        now_local = to_local(now_utc())
        target = now_local.replace(hour=8, minute=0, second=0, microsecond=0)
        if target <= now_local:
            target = target + timedelta(days=1)
        seconds = int((target - now_local).total_seconds())
        return max(60, min(seconds, 12 * 3600))

    match = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?", token)
    if not match:
        return None
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    seconds = h * 3600 + m * 60
    if seconds <= 0:
        return None
    return max(60, min(seconds, 12 * 3600))


def _service_state() -> tuple[list[str], list[str]]:
    up: list[str] = []
    down: list[str] = []
    for name, url in SERVICE_ENDPOINTS.items():
        try:
            r = httpx.get(url, timeout=2)
            if r.status_code == 200:
                up.append(name)
            else:
                down.append(name)
        except Exception:
            down.append(name)
    return up, down


def _disk_usage_percent(path: str = "L:/") -> int:
    try:
        total, used, _ = disk_usage(path)
        if total <= 0:
            return 0
        return int((used / total) * 100)
    except Exception:
        return -1


def _last_backup_hint() -> str:
    root = Path("C:/nova/backups")
    if not root.exists():
        return "unknown"
    files = [p for p in root.glob("*") if p.is_file()]
    if not files:
        return "none"
    newest = max(files, key=lambda p: p.stat().st_mtime)
    dt = datetime.fromtimestamp(newest.stat().st_mtime, tz=UTC)
    return f"{newest.name} ({format_for_user(dt)})"


@app.post("/telegram/command")
def telegram_command(payload: TelegramCommandRequest) -> dict:
    chat_id = payload.chat_id.strip()
    text = payload.text.strip()
    admins = _admin_chatids()
    if chat_id not in admins:
        return {"ok": True, "handled": False}

    lowered = text.lower()
    if lowered.startswith("/nova snooze"):
        tokens = text.split()
        if len(tokens) < 3:
            return {"ok": True, "handled": True, "reply": "Usage: /nova snooze 4h | 30m | night"}
        seconds = _parse_duration_to_seconds(tokens[2])
        if seconds is None:
            return {"ok": True, "handled": True, "reply": "Usage: /nova snooze 4h | 30m | night"}
        store.set_quiet_mode(seconds, "snooze")
        end_time = now_utc() + timedelta(seconds=seconds)
        return {"ok": True, "handled": True, "reply": f"🌙 Snooze actief tot {format_for_user(end_time)}"}

    if lowered.startswith("/nova wake"):
        store.clear_quiet_mode()
        return {"ok": True, "handled": True, "reply": "👁️ Monitoring weer actief"}

    if lowered.startswith("/nova status"):
        active = store.is_active()
        ttl = max(store.ttl(), 0) if active else 0
        up, down = _service_state()
        disk = _disk_usage_percent("L:/")
        status_line = f"snoozed (nog {ttl // 3600}h {(ttl % 3600) // 60}m)" if active else "actief"
        reply = (
            "Nova-status:\n"
            f"- Monitoring: {status_line}\n"
            f"- Services up: {', '.join(up) if up else '(geen)'}\n"
            f"- Services down: {', '.join(down) if down else '(geen)'}\n"
            f"- Disk usage L:: {disk if disk >= 0 else 'unknown'}%\n"
            f"- Last backup: {_last_backup_hint()}"
        )
        return {"ok": True, "handled": True, "reply": reply}

    if lowered in {"/help", "/start"}:
        return {"ok": True, "handled": True, "reply": "/nova snooze 4h | 30m | night\n/nova wake\n/nova status"}

    return {"ok": True, "handled": False}
