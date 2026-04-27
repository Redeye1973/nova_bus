from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from .timeutils import now_utc


@dataclass
class WeeklyMetrics:
    lookup_count: int
    prev_lookup_count: int
    cache_hit_rate: float
    prev_cache_hit_rate: float
    adapter_avg_latency: dict[str, float]
    prev_adapter_avg_latency: dict[str, float]
    top_builds: list[tuple[str, int, float]]
    sample_entities: list[tuple[str, str, str, str]]
    ingest_count: int
    top_actor: str
    postgres_size_gb: float
    postgres_growth_gb: float
    backup_count: int
    backup_oldest_days: int
    disk_l_percent: int
    todo_count: int


def detect_anomalies(metrics: WeeklyMetrics) -> list[str]:
    anomalies: list[str] = []
    for adapter, latency in metrics.adapter_avg_latency.items():
        prev = metrics.prev_adapter_avg_latency.get(adapter, 0.0)
        if prev > 0 and latency > (2 * prev):
            anomalies.append(f"Adapter {adapter} latency spike: {latency:.1f}ms vs {prev:.1f}ms vorige week")
    if metrics.prev_cache_hit_rate > 0 and (metrics.prev_cache_hit_rate - metrics.cache_hit_rate) > 10:
        anomalies.append(f"Cache hit rate drop: {metrics.cache_hit_rate:.1f}% vs {metrics.prev_cache_hit_rate:.1f}%")
    if metrics.prev_lookup_count > 0 and metrics.lookup_count < (metrics.prev_lookup_count * 0.5):
        anomalies.append(f"Build volume drop >50%: {metrics.lookup_count} vs {metrics.prev_lookup_count}")
    if metrics.postgres_growth_gb > 1.0:
        anomalies.append(f"Postgres groei hoog: +{metrics.postgres_growth_gb:.2f}GB in 1 week")
    for entity_id, canonical_name, category, age in metrics.sample_entities:
        if category != "fictional":
            try:
                days = int(age.split()[0])
                if days > 60:
                    anomalies.append(f"Oude non-fictional entity: {entity_id} ({canonical_name}) fetched {age} geleden")
            except Exception:
                continue
    return anomalies


def build_weekly_markdown(metrics: WeeklyMetrics, week_iso: str) -> str:
    anomalies = detect_anomalies(metrics)
    top_lines = "\n".join(
        f"{idx + 1}. {build}: {count} lookups, {success:.1f}% success"
        for idx, (build, count, success) in enumerate(metrics.top_builds[:5])
    ) or "- weinig activiteit"
    adapter_rows = "\n".join(
        f"| {name} | n/a | n/a | {lat:.1f}ms |" for name, lat in metrics.adapter_avg_latency.items()
    ) or "| n/a | n/a | n/a | n/a |"
    entities = "\n".join(
        f"- {eid}: {name} ({cat}, fetched {age} ago)"
        for eid, name, cat, age in metrics.sample_entities
    ) or "- geen entities beschikbaar"
    anomalies_block = "\n".join(f"- {line}" for line in anomalies) or "- geen opvallende afwijkingen"

    return (
        f"## Nova Weekrapport — {week_iso}\n"
        f"Periode: {(now_utc() - timedelta(days=7)).date()} t/m {now_utc().date()}\n\n"
        "### Volume\n"
        f"- Lookups deze week: {metrics.lookup_count}\n"
        f"- Cache hit rate: {metrics.cache_hit_rate:.1f}% (target: >70%)\n"
        f"- Top builds:\n{top_lines}\n\n"
        "### Adapters\n"
        "| Adapter | Calls | Success | Avg latency |\n"
        "|---------|-------|---------|-------------|\n"
        f"{adapter_rows}\n\n"
        "### Drie willekeurige entities (visuele check)\n"
        f"{entities}\n\n"
        "### Audit\n"
        f"- Nieuwe entries via /ingest: {metrics.ingest_count}\n"
        f"- Top actor: {metrics.top_actor}\n\n"
        "### Disk & resources\n"
        f"- Postgres data: {metrics.postgres_size_gb:.2f}GB ({metrics.postgres_growth_gb:+.2f}GB growth)\n"
        f"- Backups: {metrics.backup_count} (oudste {metrics.backup_oldest_days} dagen)\n"
        f"- Disk L:: {metrics.disk_l_percent}% used\n\n"
        "### Open TODOs\n"
        f"- {metrics.todo_count} TODO/FIXME in codebase\n\n"
        "### Aandachtspunten\n"
        f"{anomalies_block}\n"
    )


def chunk_markdown(text: str, max_chars: int = 4000) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    cursor = 0
    while cursor < len(text):
        chunks.append(text[cursor : cursor + max_chars])
        cursor += max_chars
    total = len(chunks)
    return [f"{chunk}\n\n({i + 1}/{total})" for i, chunk in enumerate(chunks)]


def sample_entities(entities: list[tuple[str, str, str, str]], count: int = 3) -> list[tuple[str, str, str, str]]:
    if len(entities) <= count:
        return entities
    return random.sample(entities, count)


def save_report(markdown: str, week_iso: str) -> Path:
    out_dir = Path("C:/nova/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{week_iso}.md"
    out.write_text(markdown, encoding="utf-8")
    return out
