import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def isolate_rate_limit_unit_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep rate limiter tests unit-level by isolating DB/Redis access."""
    from nova_ref.core import rate_limit as rl

    monkeypatch.setattr(rl.CacheStore, "get_rate_limit_override", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(rl.CacheStore, "set_rate_limit_override", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(rl.RateLimiter, "_init_redis", lambda *_args, **_kwargs: None)
