from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def now_utc() -> datetime:
    """Canonical UTC timestamp factory."""
    return datetime.now(timezone.utc)


def to_local(dt: datetime, tz: str = "Europe/Amsterdam") -> datetime:
    """Convert UTC datetime to user-facing local timezone."""
    return dt.astimezone(ZoneInfo(tz))


def format_for_user(dt: datetime, tz: str = "Europe/Amsterdam") -> str:
    """Friendly local datetime formatter for chat messages."""
    return to_local(dt, tz).strftime("%d-%m-%Y %H:%M")
