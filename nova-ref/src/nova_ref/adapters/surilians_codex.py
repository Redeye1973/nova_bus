from datetime import timedelta
from pathlib import Path

from .base import BaseAdapter
from ..config import settings
from ..core.timeutils import now_utc
from ..models import Entity, SourceRef


class SuriliansCodexAdapter(BaseAdapter):
    name = "surilians_codex"
    handles_categories = ["fictional"]
    license_default = "proprietary"

    async def search(self, query: str, hint: dict | None = None) -> list[dict]:
        root = Path(settings.surilians_codex_path)
        if not root.exists():
            return []
        results: list[dict] = []
        needle = query.strip().lower()
        for md in root.glob("*.md"):
            if needle in md.stem.lower():
                results.append({"source_id": md.name, "name": md.stem, "path": str(md), "category": "fictional"})
        return results

    async def fetch(self, source_id: str) -> dict | None:
        path = Path(settings.surilians_codex_path) / source_id
        if not path.exists():
            return None
        return {"source_id": source_id, "name": path.stem, "category": "fictional", "content": path.read_text(encoding="utf-8")}

    def normalize(self, raw: dict) -> Entity:
        now = now_utc()
        slug = str(raw.get("name", "unknown")).strip().lower().replace(" ", "_")
        return Entity(
            id=f"nova_obj_fictional_{slug}",
            category="fictional",
            canonical_name=str(raw.get("name", "Unknown fictional")),
            source_refs=[SourceRef(source=self.name, source_id=str(raw.get("source_id", "")), fetched_at=now)],
            license=self.license_default,
            description=(raw.get("content") or "")[:2000],
            raw_payload=raw,
            fetched_at=now,
            expires_at=now + timedelta(days=settings.cache_ttl_fictional_days),
        )

    async def health_check(self) -> bool:
        return Path(settings.surilians_codex_path).exists()
