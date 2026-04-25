#!/usr/bin/env python3
"""Benchmark end-to-end pipeline simulation times."""
import httpx
import time
import json
import os

MONITOR_URL = os.getenv("MONITOR_URL", "http://nova-v2-agent-11-monitor:8111")
DB_URL = os.getenv("DATABASE_URL", "")


def benchmark_pipeline_flow():
    client = httpx.Client(timeout=30)
    results = []

    start = time.perf_counter()
    r = client.post(f"{MONITOR_URL}/pipeline/start", json={
        "name": "benchmark_pipeline", "triggered_by": "benchmark"
    })
    pid = r.json().get("pipeline_id", "unknown")
    start_ms = (time.perf_counter() - start) * 1000
    results.append({"step": "pipeline_start", "ms": round(start_ms, 2)})

    for i, stage in enumerate(["init", "generate", "evaluate", "finalize"]):
        start = time.perf_counter()
        client.post(f"{MONITOR_URL}/pipeline/stage", json={
            "pipeline_id": pid, "stage": stage, "status": "completed"
        })
        elapsed = (time.perf_counter() - start) * 1000
        results.append({"step": f"stage_{stage}", "ms": round(elapsed, 2)})

    start = time.perf_counter()
    client.post(f"{MONITOR_URL}/pipeline/{pid}/checkpoint", json={
        "stage_name": "benchmark_final", "stage_index": 4,
        "stage_state": {"benchmark": True}
    })
    cp_ms = (time.perf_counter() - start) * 1000
    results.append({"step": "checkpoint_save", "ms": round(cp_ms, 2)})

    start = time.perf_counter()
    client.post(f"{MONITOR_URL}/pipeline/finish", json={
        "pipeline_id": pid, "status": "success"
    })
    finish_ms = (time.perf_counter() - start) * 1000
    results.append({"step": "pipeline_finish", "ms": round(finish_ms, 2)})

    total_ms = sum(r["ms"] for r in results)
    results.append({"step": "total", "ms": round(total_ms, 2)})

    if DB_URL:
        try:
            import psycopg2
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            for r in results:
                cur.execute(
                    """INSERT INTO benchmark_results (benchmark_name, metric_name, value, unit, metadata)
                       VALUES (%s, %s, %s, %s, %s)""",
                    ("pipeline_flow", r["step"], r["ms"], "ms", json.dumps({"pipeline_id": pid})),
                )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB save failed: {e}")

    return results


if __name__ == "__main__":
    results = benchmark_pipeline_flow()
    print(json.dumps(results, indent=2))
