from nova_ref.core.rate_limit import RateLimiter


def _new_limiter_without_redis() -> RateLimiter:
    limiter = RateLimiter()
    limiter._redis = None  # noqa: SLF001
    return limiter


def test_rate_limit_allows_under_threshold() -> None:
    limiter = _new_limiter_without_redis()
    for i in range(50):
        result = limiter.check("build_a", "/lookup")
        assert result.allowed, f"unexpected block at {i}"


def test_rate_limit_blocks_at_threshold() -> None:
    limiter = _new_limiter_without_redis()
    for _ in range(60):
        assert limiter.check("build_a", "/lookup").allowed
    blocked = limiter.check("build_a", "/lookup")
    assert not blocked.allowed
    assert blocked.limit == 60


def test_429_retry_after_positive() -> None:
    limiter = _new_limiter_without_redis()
    for _ in range(61):
        result = limiter.check("build_a", "/lookup")
    assert not result.allowed
    assert result.retry_after > 0


def test_per_build_isolation() -> None:
    limiter = _new_limiter_without_redis()
    for _ in range(61):
        limiter.check("build_a", "/lookup")
    assert not limiter.check("build_a", "/lookup").allowed
    assert limiter.check("build_b", "/lookup").allowed


def test_admin_override_increases_limit(monkeypatch) -> None:
    limiter = _new_limiter_without_redis()

    monkeypatch.setattr(limiter._cache, "set_rate_limit_override", lambda *_args, **_kwargs: None)  # noqa: SLF001
    monkeypatch.setattr(limiter._cache, "get_rate_limit_override", lambda *_args, **_kwargs: None)  # noqa: SLF001

    limiter.set_override("build_a", "/lookup", 120)
    for _ in range(90):
        assert limiter.check("build_a", "/lookup").allowed
