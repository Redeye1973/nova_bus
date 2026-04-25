"""NOVA Notification Hub — centralized alert routing to Telegram, Discord, and future channels."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import httpx
import os
import asyncio

app = FastAPI(title="NOVA Notification Hub", version="1.0")

VAULT_URL = os.getenv("VAULT_URL", "http://nova-v2-agent-44-secrets-vault:8144")
VAULT_TOKEN = os.getenv("NOVA_VAULT_TOKEN", "")


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotifyRequest(BaseModel):
    severity: Severity = Severity.INFO
    title: str
    detail: str = ""
    project: Optional[str] = None
    source: Optional[str] = None


_recent_alerts: Dict[str, datetime] = {}
DEDUP_COOLDOWN = timedelta(minutes=15)


def _dedup_key(req: NotifyRequest) -> str:
    return f"{req.severity}:{req.title}:{req.source or ''}"


def _is_duplicate(req: NotifyRequest) -> bool:
    key = _dedup_key(req)
    now = datetime.now()
    if key in _recent_alerts and (now - _recent_alerts[key]) < DEDUP_COOLDOWN:
        return True
    _recent_alerts[key] = now
    return False


_sent_log: List[Dict[str, Any]] = []


async def _get_secret(name: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {VAULT_TOKEN}"} if VAULT_TOKEN else {}
            r = await client.post(f"{VAULT_URL}/secrets/get", json={"name": name}, headers=headers, timeout=5)
            if r.status_code == 200:
                return r.json().get("value")
    except Exception:
        pass
    return os.getenv(name)


async def _send_telegram(title: str, detail: str, severity: str) -> bool:
    token = await _get_secret("TELEGRAM_BOT_TOKEN")
    chat_id = await _get_secret("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False

    icon = {"info": "ℹ️", "warning": "⚠️", "error": "🔴", "critical": "🚨"}.get(severity, "📢")
    text = f"{icon} *{severity.upper()}*: {title}"
    if detail:
        text += f"\n{detail}"

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                timeout=10,
            )
            return r.status_code == 200
    except Exception:
        return False


async def _send_discord(title: str, detail: str, severity: str) -> bool:
    webhook_url = await _get_secret("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return False

    color = {"info": 3447003, "warning": 16776960, "error": 15158332, "critical": 10038562}.get(severity, 0)
    embed = {"title": f"{severity.upper()}: {title}", "description": detail or "No details", "color": color, "timestamp": datetime.utcnow().isoformat()}

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(webhook_url, json={"embeds": [embed], "username": "NOVA Monitor"}, timeout=10)
            return r.status_code in (200, 204)
    except Exception:
        return False


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "channels": ["telegram", "discord"], "sent_total": len(_sent_log)}


@app.get("/health/deep")
async def health_deep() -> Dict[str, Any]:
    import shutil
    telegram_ok = bool(await _get_secret("TELEGRAM_BOT_TOKEN"))
    discord_ok = bool(await _get_secret("DISCORD_WEBHOOK_URL"))
    try:
        usage = shutil.disk_usage("/")
        disk = f"{usage.free / 1e9:.1f}GB free"
    except Exception:
        disk = "unknown"
    checks = {
        "overall": "healthy" if (telegram_ok or discord_ok) else "degraded",
        "service": "ok", "agent": "61_notification_hub", "version": "1.0",
        "channels": {"telegram": telegram_ok, "discord": discord_ok},
        "sent_total": len(_sent_log), "disk_space": disk,
    }
    return checks


@app.post("/notify")
async def notify(body: NotifyRequest) -> Dict[str, Any]:
    if _is_duplicate(body):
        return {"sent": False, "reason": "duplicate_suppressed", "cooldown_minutes": DEDUP_COOLDOWN.seconds // 60}

    results = {}

    if body.severity in (Severity.ERROR, Severity.CRITICAL):
        results["telegram"] = await _send_telegram(body.title, body.detail, body.severity.value)

    if body.severity in (Severity.WARNING, Severity.ERROR, Severity.CRITICAL):
        results["discord"] = await _send_discord(body.title, body.detail, body.severity.value)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "severity": body.severity.value,
        "title": body.title,
        "project": body.project,
        "source": body.source,
        "channels": results,
    }
    _sent_log.append(entry)
    if len(_sent_log) > 500:
        _sent_log.pop(0)

    return {"sent": True, "channels": results}


@app.post("/notify/critical")
async def notify_critical(body: NotifyRequest) -> Dict[str, Any]:
    body.severity = Severity.CRITICAL
    return await notify(body)


@app.get("/channels")
async def list_channels() -> Dict[str, Any]:
    telegram_ok = bool(await _get_secret("TELEGRAM_BOT_TOKEN"))
    discord_ok = bool(await _get_secret("DISCORD_WEBHOOK_URL"))
    return {
        "channels": [
            {"name": "telegram", "configured": telegram_ok},
            {"name": "discord", "configured": discord_ok},
        ]
    }


@app.post("/channels/test")
async def test_channels() -> Dict[str, Any]:
    results = {
        "telegram": await _send_telegram("Channel Test", "Notification Hub connectivity test", "info"),
        "discord": await _send_discord("Channel Test", "Notification Hub connectivity test", "info"),
    }
    return {"results": results}


@app.get("/history")
async def notification_history(limit: int = 50) -> Dict[str, Any]:
    return {"events": _sent_log[-limit:], "total": len(_sent_log)}


@app.post("/invoke")
async def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    action = body.get("action", "")
    if action == "notify":
        return await notify(NotifyRequest(**body))
    elif action == "critical":
        return await notify_critical(NotifyRequest(**body))
    elif action == "channels":
        return await list_channels()
    elif action == "test":
        return await test_channels()
    elif action == "history":
        return await notification_history(body.get("limit", 50))
    else:
        raise HTTPException(400, f"Unknown action: {action}")
