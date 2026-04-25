#!/usr/bin/env python3
"""Benchmark agent response times and availability."""
import httpx
import time
import json
import sys
import os

AGENTS = [
    ("agent_11_monitor", "http://nova-v2-agent-11-monitor:8111/health"),
    ("agent_16_cost_guard", "http://nova-v2-agent-16-cost-guard:8116/health"),
    ("agent_17_error_handler", "http://nova-v2-agent-17-error-handler:8117/health"),
    ("agent_18_prompt_director", "http://nova-v2-agent-18-prompt-director:8118/health"),
    ("agent_44_secrets_vault", "http://nova-v2-agent-44-secrets-vault:8144/health"),
    ("agent_60_memory_curator", "http://nova-v2-memory-curator:8060/health"),
    ("agent_61_notification_hub", "http://nova-v2-notification-hub:8061/health"),
]

DB_URL = os.getenv("DATABASE_URL", "")


def benchmark_agents():
    results = []
    client = httpx.Client(timeout=10)
    for name, url in AGENTS:
        timings = []
        for _ in range(3):
            start = time.perf_counter()
            try:
                r = client.get(url)
                elapsed = (time.perf_counter() - start) * 1000
                timings.append({"ms": round(elapsed, 2), "status": r.status_code})
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                timings.append({"ms": round(elapsed, 2), "error": str(e)})

        avg_ms = sum(t["ms"] for t in timings) / len(timings)
        ok_count = sum(1 for t in timings if t.get("status") == 200)
        results.append({
            "agent": name,
            "avg_ms": round(avg_ms, 2),
            "availability": f"{ok_count}/{len(timings)}",
            "runs": timings,
        })

    if DB_URL:
        try:
            import psycopg2
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS benchmark_results (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                benchmark_name TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value DECIMAL,
                unit TEXT,
                timestamp TIMESTAMP DEFAULT NOW(),
                metadata JSONB DEFAULT '{}'
            )""")
            for r in results:
                cur.execute(
                    "INSERT INTO benchmark_results (benchmark_name, metric_name, value, unit, metadata) VALUES (%s, %s, %s, %s, %s)",
                    ("agent_health", r["agent"], r["avg_ms"], "ms", json.dumps(r)),
                )
            conn.commit()
            conn.close()
            print("Results saved to Postgres")
        except Exception as e:
            print(f"DB save failed: {e}")

    return results


if __name__ == "__main__":
    results = benchmark_agents()
    print(json.dumps(results, indent=2))
