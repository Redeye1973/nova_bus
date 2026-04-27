from __future__ import annotations

import os
from typing import Protocol


class RedisLike(Protocol):
    def set(self, key: str, value: str, ex: int) -> object: ...
    def delete(self, key: str) -> object: ...
    def ttl(self, key: str) -> int: ...
    def exists(self, key: str) -> int: ...


class InMemoryRedis:
    def __init__(self) -> None:
        self._exists = False
        self._ttl = -2

    def set(self, key: str, value: str, ex: int) -> object:
        self._exists = True
        self._ttl = ex
        return True

    def delete(self, key: str) -> object:
        self._exists = False
        self._ttl = -2
        return True

    def ttl(self, key: str) -> int:
        return self._ttl

    def exists(self, key: str) -> int:
        return 1 if self._exists and self._ttl > 0 else 0


class QuietModeStore:
    def __init__(self, redis_client: RedisLike | None = None) -> None:
        self._key = "nova:quiet_mode"
        self.redis = redis_client or self._build_client()

    def _build_client(self) -> RedisLike:
        try:
            from redis import Redis  # type: ignore
            return Redis.from_url(os.getenv("NOVA_BRIDGE_REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
        except Exception:
            return InMemoryRedis()

    def set_quiet_mode(self, seconds: int, reason: str) -> None:
        self.redis.set(self._key, reason, ex=max(seconds, 1))

    def clear_quiet_mode(self) -> None:
        self.redis.delete(self._key)

    def ttl(self) -> int:
        return int(self.redis.ttl(self._key))

    def is_active(self) -> bool:
        return self.redis.exists(self._key) == 1
