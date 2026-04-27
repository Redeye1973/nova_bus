from pydantic import BaseModel, Field


class LifecycleEvent(BaseModel):
    event: str = Field(pattern="^(shutdown|startup|snooze)$")
    host: str
    duration_minutes: int | None = None


class NotifyRequest(BaseModel):
    title: str
    detail: str = ""
    severity: str = Field(default="warning", pattern="^(info|warning|error|critical)$")
    channels: list[str] = Field(default_factory=lambda: ["telegram", "discord"])
    kind: str = Field(default="infrastructure", pattern="^(infrastructure|user_message|critical_alert)$")
    source: str = "unknown"


class TelegramCommandRequest(BaseModel):
    chat_id: str
    text: str
