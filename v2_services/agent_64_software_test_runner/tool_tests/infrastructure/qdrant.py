"""Qdrant: create ephemeral collection, upsert, search, delete."""
from __future__ import annotations

import time
import uuid
from pathlib import Path

import httpx

from .._base import TestResult, ToolTest
from .._env import QDRANT_URL


class QdrantTest(ToolTest):
    TOOL_NAME = "qdrant"
    CATEGORY = "infrastructure"
    TIER = 1
    EXPECTED_OUTPUT_FILENAME = "qdrant_search.json"

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        col = f"softtest_{uuid.uuid4().hex[:10]}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.put(
                    f"{QDRANT_URL}/collections/{col}",
                    json={"vectors": {"size": 4, "distance": "Cosine"}},
                )
                if r.status_code not in (200, 201):
                    return TestResult(
                        self.TOOL_NAME, "fail", int((time.perf_counter() - t0) * 1000),
                        category=self.CATEGORY,
                        error_message=f"create collection: {r.status_code} {r.text[:200]}",
                    )
                point_id = 1
                r2 = await client.put(
                    f"{QDRANT_URL}/collections/{col}/points",
                    json={
                        "points": [
                            {"id": point_id, "vector": [0.1, 0.2, 0.3, 0.4], "payload": {"t": "softtest"}}
                        ]
                    },
                )
                if r2.status_code not in (200, 201):
                    await client.delete(f"{QDRANT_URL}/collections/{col}")
                    return TestResult(
                        self.TOOL_NAME, "fail", int((time.perf_counter() - t0) * 1000),
                        category=self.CATEGORY,
                        error_message=f"upsert: {r2.status_code}",
                    )
                r3 = await client.post(
                    f"{QDRANT_URL}/collections/{col}/points/search",
                    json={"vector": [0.1, 0.2, 0.3, 0.4], "limit": 2},
                )
                await client.delete(f"{QDRANT_URL}/collections/{col}")
                if r3.status_code != 200:
                    return TestResult(
                        self.TOOL_NAME, "fail", int((time.perf_counter() - t0) * 1000),
                        category=self.CATEGORY,
                        error_message=f"search: {r3.status_code}",
                    )
                out.write_text(r3.text[:4000], encoding="utf-8")
            ms = int((time.perf_counter() - t0) * 1000)
            ok, reason = self.verify_output(output_dir)
            if not ok:
                return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
            return TestResult(
                self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
                output_path=out, output_size_bytes=out.stat().st_size,
                metadata={"collection": col},
            )
        except Exception as e:
            return TestResult(
                self.TOOL_NAME, "fail", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY, error_message=str(e),
            )
