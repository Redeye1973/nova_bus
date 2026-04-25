#!/usr/bin/env python3
"""Benchmark Postgres query performance."""
import time
import json
import os

DB_URL = os.getenv("DATABASE_URL", "")


def benchmark_db():
    if not DB_URL:
        return [{"test": "skip", "reason": "no DATABASE_URL"}]

    import psycopg2
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    results = []

    start = time.perf_counter()
    cur.execute("SELECT 1")
    cur.fetchone()
    results.append({"test": "simple_select", "ms": round((time.perf_counter() - start) * 1000, 2)})

    start = time.perf_counter()
    cur.execute("SELECT COUNT(*) FROM pipeline_checkpoints")
    count = cur.fetchone()[0]
    results.append({"test": "count_checkpoints", "ms": round((time.perf_counter() - start) * 1000, 2), "rows": count})

    start = time.perf_counter()
    cur.execute("SELECT COUNT(*) FROM audit_log")
    count = cur.fetchone()[0]
    results.append({"test": "count_audit", "ms": round((time.perf_counter() - start) * 1000, 2), "rows": count})

    try:
        start = time.perf_counter()
        cur.execute("SELECT COUNT(*) FROM memory_index")
        count = cur.fetchone()[0]
        results.append({"test": "count_memory_index", "ms": round((time.perf_counter() - start) * 1000, 2), "rows": count})

        start = time.perf_counter()
        cur.execute("SELECT * FROM memory_index WHERE search_vector @@ to_tsquery('english', 'nova') LIMIT 5")
        rows = cur.fetchall()
        results.append({"test": "fts_search", "ms": round((time.perf_counter() - start) * 1000, 2), "results": len(rows)})
    except Exception:
        pass

    for r in results:
        try:
            cur.execute(
                """INSERT INTO benchmark_results (benchmark_name, metric_name, value, unit, metadata)
                   VALUES (%s, %s, %s, %s, %s)""",
                ("db_performance", r["test"], r["ms"], "ms", json.dumps(r)),
            )
        except Exception:
            pass
    conn.commit()
    conn.close()
    return results


if __name__ == "__main__":
    results = benchmark_db()
    print(json.dumps(results, indent=2))
