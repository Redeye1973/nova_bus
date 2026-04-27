from datetime import timedelta

from .base import BaseAdapter
from ..core.timeutils import now_utc
from ..models import Entity, SourceRef


class WikidataAdapter(BaseAdapter):
    name = "wikidata"
    handles_categories = ["aircraft", "building", "vehicle", "spacecraft", "historical_object"]
    license_default = "CC0"

    async def search(self, query: str, hint: dict | None = None) -> list[dict]:
        slug = query.strip().lower().replace(" ", "_")
        return [{"source_id": f"Q_{slug}", "name": query.title(), "category": (hint or {}).get("category_hint") or "general"}]

    async def fetch(self, source_id: str) -> dict | None:
        return {"source_id": source_id, "name": source_id.replace("Q_", "").replace("_", " ").title()}

    def normalize(self, raw: dict) -> Entity:
        now = now_utc()
        slug = str(raw.get("name", "unknown")).strip().lower().replace(" ", "_")
        return Entity(
            id=f"nova_obj_wikidata_{slug}",
            category=raw.get("category") or "general",
            canonical_name=str(raw.get("name", "Unknown")),
            source_refs=[SourceRef(source=self.name, source_id=str(raw.get("source_id", "")), fetched_at=now)],
            license=self.license_default,
            description="Wikidata placeholder adapter result",
            fetched_at=now,
            expires_at=now + timedelta(days=30),
        )

    async def health_check(self) -> bool:
        return True
