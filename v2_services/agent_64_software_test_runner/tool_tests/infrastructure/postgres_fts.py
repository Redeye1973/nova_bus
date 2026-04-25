"""Postgres full-text sanity (session-local temp table)."""
from __future__ import annotations

import os
import time
from pathlib import Path

from .._base import TestResult, ToolTest


class PostgresFtsTest(ToolTest):
    TOOL_NAME = "postgres_fts"
    CATEGORY = "infrastructure"
    TIER = 1
    TIMEOUT_SECONDS = 30
    EXPECTED_OUTPUT_FILENAME = "fts_probe.txt"

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        dsn = os.getenv("DATABASE_URL")
        if not dsn:
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY,
                error_message="DATABASE_URL not set",
            )
        try:
            import psycopg2

            conn = psycopg2.connect(dsn, connect_timeout=10)
            conn.autocommit = False
            cur = conn.cursor()
            cur.execute("DROP TABLE IF EXISTS software_test_fts_probe")
            cur.execute(
                """
                CREATE TEMP TABLE software_test_fts_probe (
                    id serial PRIMARY KEY,
                    body text
                ) ON COMMIT DROP
                """
            )
            cur.execute(
                "INSERT INTO software_test_fts_probe(body) VALUES (%s)",
                ("hello nova software test",),
            )
            cur.execute(
                """
                SELECT count(*) FROM software_test_fts_probe
                WHERE to_tsvector('english', body) @@ plainto_tsquery('english', 'nova')
                """
            )
            n = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            out.write_text(f"fts_hits={n}\n", encoding="utf-8")
            ms = int((time.perf_counter() - t0) * 1000)
            ok, reason = self.verify_output(output_dir)
            if not ok or n < 1:
                return TestResult(
                    self.TOOL_NAME, "fail", ms, category=self.CATEGORY,
                    error_message=reason if not ok else "FTS expected >=1 hit",
                )
            return TestResult(
                self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
                output_path=out, output_size_bytes=out.stat().st_size,
                metadata={"hits": n},
            )
        except Exception as e:
            return TestResult(
                self.TOOL_NAME, "fail", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY, error_message=str(e),
            )
