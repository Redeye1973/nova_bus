from __future__ import annotations

import threading
from collections import defaultdict, deque
from dataclasses import dataclass
from time import time

import httpx
try:
    import redis
except ModuleNotFoundError:  # pragma: no cover
    redis = None  # type: ignore[assignment]
import structlog
from prometheus_client import Counter, Gauge

from ..config import settings
try:
    from .cache import CacheStore
except ModuleNotFoundError:  # pragma: no cover
    class CacheStore:  # type: ignore[override]
        def get_rate_limit_override(self, _build_name: str, _endpoint: str) -> int | None:
            return None

        def set_rate_limit_override(self, _build_name: str, _endpoint: str, _limit_per_min: int) -> None:
            return None

LOGGER = structlog.get_logger(__name__)

RATE_LIMIT_HITS = Counter(
    "nova_ref_rate_limit_hits_total",
    "Rate limit hits per build and endpoint",
    ["build", "endpoint"],
)
RATE_LIMIT_ACTIVE_KEYS = Gauge(
    "nova_ref_rate_limit_active_keys",
    "Active rate limit key count",
)
RATE_LIMIT_OVERRIDES = Counter(
    "nova_ref_rate_limit_overrides_total",
    "Rate limit override writes",
    ["endpoint"],
)


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    current: int
    retry_after: int


class RateLimiter:
    _defaults = {
        "/lookup": settings.rate_limit_lookup_per_min,
        "/search": settings.rate_limit_search_per_min,
        "/ingest": settings.rate_limit_ingest_per_min,
        "/feedback": settings.rate_limit_feedback_per_min,
    }

    def __init__(self) -> None:
        self._cache = CacheStore()
        self._override_cache: dict[tuple[str, str], tuple[int, float]] = {}
        self._inmem: dict[str, deque[float]] = defaultdict(deque)
        self._runaway: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._redis = self._init_redis()

    def _init_redis(self) -> redis.Redis | None:
        if redis is None:
            return None
        try:
            return redis.Redis.from_url(
                settings.redis_url,
                password=settings.redis_password or None,
                decode_responses=True,
                socket_timeout=2,
            )
        except Exception as exc:
            LOGGER.warning("rate_limit.redis_init_failed", error=str(exc))
            return None

    def get_limit(self, build_name: str, endpoint: str) -> int:
        key = (build_name, endpoint)
        now = time()
        cached = self._override_cache.get(key)
        if cached and cached[1] > now:
            return cached[0]
        override = self._cache.get_rate_limit_override(build_name, endpoint)
        if override is not None:
            self._override_cache[key] = (override, now + settings.rate_limit_override_cache_seconds)
            return override
        return self._defaults.get(endpoint, 60)

    def set_override(self, build_name: str, endpoint: str, limit_per_min: int) -> None:
        self._cache.set_rate_limit_override(build_name, endpoint, limit_per_min)
        self._override_cache[(build_name, endpoint)] = (limit_per_min, time() + settings.rate_limit_override_cache_seconds)
        RATE_LIMIT_OVERRIDES.labels(endpoint=endpoint).inc()

    def check(self, build_name: str, endpoint: str) -> RateLimitResult:
        limit = max(self.get_limit(build_name, endpoint), 1)
        now = int(time())
        window = now // 60
        redis_key = f"ratelimit:{build_name}:{endpoint}:{window}"
        retry_after = 60 - (now % 60)

        if self._redis is not None:
            try:
                current = int(self._redis.incr(redis_key))
                if current == 1:
                    self._redis.expire(redis_key, retry_after)
                RATE_LIMIT_ACTIVE_KEYS.set(float(len(self._redis.keys("ratelimit:*"))))
                allowed = current <= limit
                return self._result(build_name, endpoint, allowed, limit, current, retry_after)
            except Exception as exc:
                LOGGER.warning("rate_limit.redis_runtime_failed", error=str(exc))

        with self._lock:
            bucket = self._inmem[redis_key]
            cutoff = time() - 60.0
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            bucket.append(time())
            current = len(bucket)
            allowed = current <= limit
            RATE_LIMIT_ACTIVE_KEYS.set(float(len(self._inmem)))
            return self._result(build_name, endpoint, allowed, limit, current, retry_after)

    def _result(
        self,
        build_name: str,
        endpoint: str,
        allowed: bool,
        limit: int,
        current: int,
        retry_after: int,
    ) -> RateLimitResult:
        if not allowed:
            RATE_LIMIT_HITS.labels(build=build_name, endpoint=endpoint).inc()
            self._register_runaway(build_name, endpoint)
            LOGGER.warning(
                "rate_limit.exceeded",
                build_name=build_name,
                endpoint=endpoint,
                current_rate=current,
                limit=limit,
            )
        return RateLimitResult(allowed=allowed, limit=limit, current=current, retry_after=retry_after)

    def _register_runaway(self, build_name: str, endpoint: str) -> None:
        key = (build_name, endpoint)
        q = self._runaway[key]
        now = time()
        q.append(now)
        cutoff = now - 300
        while q and q[0] < cutoff:
            q.popleft()
        if len(q) >= 5:
            LOGGER.error("rate_limit.runaway_suspected", build_name=build_name, endpoint=endpoint, hits_5min=len(q))
            self._send_runaway_alert(build_name, endpoint)
            q.clear()

    def _send_runaway_alert(self, build_name: str, endpoint: str) -> None:
        try:
            httpx.post(
                settings.bridge_notify_url,
                json={
                    "kind": "infrastructure",
                    "severity": "warning",
                    "title": "Nova Ref runaway suspected",
                    "detail": f"build={build_name} endpoint={endpoint} hit rate-limit 5x in 5 minutes",
                    "channels": ["telegram"],
                },
                timeout=5,
            )
        except Exception as exc:
            LOGGER.warning("rate_limit.runaway_alert_failed", error=str(exc))
