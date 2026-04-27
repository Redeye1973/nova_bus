from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_local(dt: datetime, tz: str = "Europe/Amsterdam") -> datetime:
    return dt.astimezone(ZoneInfo(tz))


def format_for_user(dt: datetime, tz: str = "Europe/Amsterdam") -> str:
    return to_local(dt, tz).strftime("%d-%m-%Y %H:%M")
