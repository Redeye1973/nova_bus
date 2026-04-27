from datetime import timedelta

from .base import BaseAdapter
from ..core.timeutils import now_utc
from ..models import Entity, SourceRef


class PDOKBagAdapter(BaseAdapter):
    name = "pdok_bag"
    handles_categories = ["building"]
    license_default = "PDOK-public"

    async def search(self, query: str, hint: dict | None = None) -> list[dict]:
        return [{"source_id": f"bag_{query.strip().lower().replace(' ', '_')}", "name": query.title(), "category": "building"}]

    async def fetch(self, source_id: str) -> dict | None:
        return {"source_id": source_id, "name": source_id.replace("bag_", "").replace("_", " ").title(), "category": "building"}

    def normalize(self, raw: dict) -> Entity:
        now = now_utc()
        slug = str(raw.get("name", "unknown")).strip().lower().replace(" ", "_")
        return Entity(
            id=f"nova_obj_building_{slug}",
            category="building",
            canonical_name=str(raw.get("name", "Unknown building")),
            source_refs=[SourceRef(source=self.name, source_id=str(raw.get("source_id", "")), fetched_at=now)],
            license=self.license_default,
            description="PDOK BAG placeholder adapter result",
            fetched_at=now,
            expires_at=now + timedelta(days=90),
        )

    async def health_check(self) -> bool:
        return True
