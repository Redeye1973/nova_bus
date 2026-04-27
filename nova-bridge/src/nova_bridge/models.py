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


class WeeklyReportRequest(BaseModel):
    week_iso: str
    lookup_count: int = 0
    prev_lookup_count: int = 0
    cache_hit_rate: float = 0.0
    prev_cache_hit_rate: float = 0.0
    adapter_avg_latency: dict[str, float] = Field(default_factory=dict)
    prev_adapter_avg_latency: dict[str, float] = Field(default_factory=dict)
    top_builds: list[tuple[str, int, float]] = Field(default_factory=list)
    sample_entities: list[tuple[str, str, str, str]] = Field(default_factory=list)
    ingest_count: int = 0
    top_actor: str = "unknown"
    postgres_size_gb: float = 0.0
    postgres_growth_gb: float = 0.0
    backup_count: int = 0
    backup_oldest_days: int = 0
    disk_l_percent: int = 0
    todo_count: int = 0
