from nova_bridge.weekly_report import WeeklyMetrics, build_weekly_markdown, chunk_markdown, detect_anomalies


def _metrics() -> WeeklyMetrics:
    return WeeklyMetrics(
        lookup_count=100,
        prev_lookup_count=120,
        cache_hit_rate=72.5,
        prev_cache_hit_rate=74.0,
        adapter_avg_latency={"wikidata": 180.0},
        prev_adapter_avg_latency={"wikidata": 120.0},
        top_builds=[("build_a", 55, 98.1), ("build_b", 30, 95.0)],
        sample_entities=[
            ("ent-1", "Alpha", "building", "12 days"),
            ("ent-2", "Beta", "vehicle", "4 days"),
            ("ent-3", "Gamma", "fictional", "120 days"),
        ],
        ingest_count=5,
        top_actor="agent:sprite_pipeline",
        postgres_size_gb=2.4,
        postgres_growth_gb=0.2,
        backup_count=6,
        backup_oldest_days=12,
        disk_l_percent=67,
        todo_count=14,
    )


def test_report_generation_with_data() -> None:
    md = build_weekly_markdown(_metrics(), week_iso="2026-W17")
    assert "Nova Weekrapport — 2026-W17" in md
    assert "Lookups deze week: 100" in md
    assert "Top builds" in md


def test_anomaly_detection_latency_spike() -> None:
    metrics = _metrics()
    metrics.adapter_avg_latency["wikidata"] = 300.0
    metrics.prev_adapter_avg_latency["wikidata"] = 100.0
    anomalies = detect_anomalies(metrics)
    assert any("latency spike" in a for a in anomalies)


def test_telegram_chunking() -> None:
    text = "x" * 6000
    chunks = chunk_markdown(text, max_chars=4000)
    assert len(chunks) == 2
    assert "(1/2)" in chunks[0]
    assert "(2/2)" in chunks[1]


def test_empty_week_no_crash() -> None:
    metrics = WeeklyMetrics(
        lookup_count=0,
        prev_lookup_count=0,
        cache_hit_rate=0.0,
        prev_cache_hit_rate=0.0,
        adapter_avg_latency={},
        prev_adapter_avg_latency={},
        top_builds=[],
        sample_entities=[],
        ingest_count=0,
        top_actor="unknown",
        postgres_size_gb=0.0,
        postgres_growth_gb=0.0,
        backup_count=0,
        backup_oldest_days=0,
        disk_l_percent=0,
        todo_count=0,
    )
    md = build_weekly_markdown(metrics, week_iso="2026-W17")
    assert "weinig activiteit" in md
