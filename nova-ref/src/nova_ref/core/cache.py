from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

import psycopg
from psycopg.rows import dict_row

from ..config import settings
from ..models import Entity
from .timeutils import now_utc


class CacheStore:
    def __init__(self) -> None:
        self._dsn = settings.db_dsn

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self._dsn, row_factory=dict_row)

    def lookup_by_query(self, query: str, category_hint: str | None, max_age_days: int) -> Entity | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM cache.entities
                WHERE (%s IS NULL OR category = %s)
                  AND (
                      lower(canonical_name) = lower(%s)
                      OR EXISTS (SELECT 1 FROM unnest(aliases) AS a WHERE lower(a) = lower(%s))
                  )
                  AND expires_at >= NOW() - (%s || ' days')::interval
                ORDER BY fetched_at DESC
                LIMIT 1
                """,
                (category_hint, category_hint, query, query, max_age_days),
            )
            row = cur.fetchone()
            if not row:
                return None
            return Entity.model_validate(self._row_to_entity_payload(row))

    def upsert_entity(self, entity: Entity) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cache.entities (
                  id, category, subcategory, canonical_name, aliases, source_refs, dimensions,
                  materials, era, context, description, license, license_attrib,
                  raw_payload, fetched_at, expires_at, fetch_count
                ) VALUES (
                  %(id)s, %(category)s, %(subcategory)s, %(canonical_name)s, %(aliases)s,
                  %(source_refs)s::jsonb, %(dimensions)s::jsonb, %(materials)s, %(era)s,
                  %(context)s, %(description)s, %(license)s, %(license_attribution)s,
                  %(raw_payload)s::jsonb, %(fetched_at)s, %(expires_at)s, 1
                )
                ON CONFLICT (id) DO UPDATE SET
                  canonical_name = EXCLUDED.canonical_name,
                  aliases = EXCLUDED.aliases,
                  source_refs = EXCLUDED.source_refs,
                  dimensions = EXCLUDED.dimensions,
                  materials = EXCLUDED.materials,
                  era = EXCLUDED.era,
                  context = EXCLUDED.context,
                  description = EXCLUDED.description,
                  license = EXCLUDED.license,
                  license_attrib = EXCLUDED.license_attrib,
                  raw_payload = EXCLUDED.raw_payload,
                  fetched_at = EXCLUDED.fetched_at,
                  expires_at = EXCLUDED.expires_at,
                  fetch_count = cache.entities.fetch_count + 1
                """,
                {
                    **entity.model_dump(),
                    "source_refs": json.dumps([s.model_dump(mode="json") for s in entity.source_refs]),
                    "dimensions": json.dumps(entity.dimensions.model_dump(mode="json") if entity.dimensions else None),
                    "raw_payload": json.dumps(entity.raw_payload or {}),
                },
            )
            conn.commit()

    def log_query(
        self,
        raw_query: str,
        normalized: str,
        category_hint: str | None,
        matched_entity: str | None,
        confidence: float,
        used_adapters: list[str],
        duration_ms: int,
    ) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cache.queries (raw_query, normalized, category_hint, matched_entity, confidence, used_adapters, duration_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (raw_query, normalized, category_hint, matched_entity, confidence, used_adapters, duration_ms),
            )
            conn.commit()

    def insert_build_run(self, payload: dict[str, Any]) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO learn.build_runs (
                  build_name, build_version, request_payload, used_entities, used_adapters,
                  output_artifact, outcome, quality_score, feedback_source, feedback_notes, duration_ms
                ) VALUES (%(build_name)s, %(build_version)s, %(request_payload)s::jsonb,
                          %(used_entities)s, %(used_adapters)s, %(output_artifact)s,
                          %(outcome)s, %(quality_score)s, %(feedback_source)s,
                          %(feedback_notes)s, %(duration_ms)s)
                """,
                {
                    **payload,
                    "request_payload": json.dumps(payload.get("request_payload", {})),
                },
            )
            conn.commit()

    def get_rate_limit_override(self, build_name: str, endpoint: str) -> int | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT limit_per_min
                FROM cache.rate_limits
                WHERE build_name = %s AND endpoint = %s
                """,
                (build_name, endpoint),
            )
            row = cur.fetchone()
            if not row:
                return None
            value = row.get("limit_per_min")
            return int(value) if value is not None else None

    def set_rate_limit_override(self, build_name: str, endpoint: str, limit_per_min: int) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cache.rate_limits (build_name, endpoint, limit_per_min, updated_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (build_name, endpoint)
                DO UPDATE SET limit_per_min = EXCLUDED.limit_per_min, updated_at = NOW()
                """,
                (build_name, endpoint, limit_per_min),
            )
            conn.commit()

    @staticmethod
    def _row_to_entity_payload(row: dict[str, Any]) -> dict[str, Any]:
        result = dict(row)
        for key in ("source_refs", "dimensions", "raw_payload"):
            if isinstance(result.get(key), str):
                result[key] = json.loads(result[key])
        result["license_attribution"] = result.pop("license_attrib", None)
        return result


def compute_expiry(category: str | None, max_age_days: int) -> datetime:
    now = now_utc()
    if category == "fictional":
        return now + timedelta(days=settings.cache_ttl_fictional_days)
    days = max(max_age_days, 1)
    return now + timedelta(days=days)
