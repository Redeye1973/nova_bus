from __future__ import annotations

import os
from datetime import UTC, datetime

import httpx


def send_telegram(text: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return False
    try:
        r = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        return r.status_code == 200
    except Exception:
        return False


def send_discord(text: str, severity: str = "info") -> bool:
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")
    if not webhook_url:
        return False
    color = {"info": 3447003, "warning": 16776960, "error": 15158332, "critical": 10038562}.get(severity, 0)
    payload = {
        "username": "NOVA Bridge",
        "embeds": [
            {
                "title": f"NOVA {severity.upper()}",
                "description": text,
                "color": color,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        ],
    }
    try:
        r = httpx.post(webhook_url, json=payload, timeout=10)
        return r.status_code in (200, 204)
    except Exception:
        return False
