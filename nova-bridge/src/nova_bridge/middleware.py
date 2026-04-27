from __future__ import annotations

from dataclasses import dataclass
from .db import log_suppressed_alert
from .store import QuietModeStore


@dataclass
class AlertMessage:
    channel: str
    text: str
    kind: str  # infrastructure | user_message | critical_alert


def should_send_alert(message: AlertMessage, store: QuietModeStore) -> bool:
    if message.kind == "user_message":
        return True
    if message.kind == "critical_alert":
        return True
    if not store.is_active():
        return True
    ttl = store.ttl()
    log_suppressed_alert(message.channel, message.text, "quiet_mode_active", ttl)
    return False
