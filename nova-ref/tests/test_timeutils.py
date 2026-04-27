from datetime import timezone

from nova_ref.core.timeutils import now_utc, to_local


def test_now_utc_returns_aware_datetime() -> None:
    now = now_utc()
    assert now.tzinfo is not None
    assert now.tzinfo == timezone.utc


def test_to_local_converts_correctly() -> None:
    # Winter date
    dt_winter = now_utc().replace(year=2026, month=1, day=15, hour=12, minute=0, second=0, microsecond=0)
    local_winter = to_local(dt_winter, "Europe/Amsterdam")
    assert local_winter.hour == 13

    # Summer date
    dt_summer = now_utc().replace(year=2026, month=7, day=15, hour=12, minute=0, second=0, microsecond=0)
    local_summer = to_local(dt_summer, "Europe/Amsterdam")
    assert local_summer.hour == 14
