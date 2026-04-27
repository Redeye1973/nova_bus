from __future__ import annotations

import asyncio
from dataclasses import dataclass

import asyncpg
import psycopg
from psycopg.rows import dict_row

from ..config import settings

_pool: asyncpg.Pool | None = None
_pool_lock = asyncio.Lock()


@dataclass
class DbPoolStats:
    active: int
    idle: int
    max_size: int

    @property
    def utilization_percent(self) -> float:
        if self.max_size <= 0:
            return 0.0
        return round((self.active / self.max_size) * 100.0, 2)


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is not None:
        return _pool
    async with _pool_lock:
        if _pool is None:
            _pool = await asyncpg.create_pool(
                dsn=(
                    f"postgresql://{settings.nova_ref_db_user}:{settings.nova_ref_db_pass}@"
                    f"{settings.nova_ref_db_host}:{settings.nova_ref_db_port}/{settings.nova_ref_db_name}"
                ),
                min_size=settings.nova_ref_db_pool_min,
                max_size=settings.nova_ref_db_pool_max,
                max_inactive_connection_lifetime=float(settings.nova_ref_db_pool_idle_timeout),
                command_timeout=30.0,
            )
    return _pool


def query_pg_stat_activity() -> DbPoolStats:
    with psycopg.connect(settings.db_dsn, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              COUNT(*) FILTER (WHERE state = 'active') AS active,
              COUNT(*) FILTER (WHERE state = 'idle') AS idle
            FROM pg_stat_activity
            WHERE datname = %s
            """,
            (settings.nova_ref_db_name,),
        )
        row = cur.fetchone() or {"active": 0, "idle": 0}
    active = int(row.get("active") or 0)
    idle = int(row.get("idle") or 0)
    return DbPoolStats(active=active, idle=idle, max_size=settings.nova_ref_db_pool_max)
