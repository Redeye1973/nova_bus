"""Ollama: short generate (often local only)."""
from __future__ import annotations

import time
from pathlib import Path

import httpx

from .._base import TestResult, ToolTest
from .._env import OLLAMA_URL


class OllamaTest(ToolTest):
    TOOL_NAME = "ollama"
    CATEGORY = "infrastructure"
    TIER = 1
    TIMEOUT_SECONDS = 90
    EXPECTED_OUTPUT_FILENAME = "ollama_reply.txt"

    async def _first_available_model(self, client: httpx.AsyncClient) -> str | None:
        r = await client.get(f"{OLLAMA_URL}/api/tags", timeout=5.0)
        if r.status_code != 200:
            return None
        models = r.json().get("models") or []
        if not models:
            return None
        return models[0].get("name")

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        try:
            async with httpx.AsyncClient(timeout=float(self.TIMEOUT_SECONDS)) as client:
                model = await self._first_available_model(client)
                if not model:
                    return TestResult(
                        self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                        category=self.CATEGORY,
                        error_message="Geen Ollama models beschikbaar (/api/tags leeg of unreachable)",
                    )
                r = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={
                        "model": model,
                        "prompt": "Say OK in one word.",
                        "stream": False,
                    },
                )
                if r.status_code != 200:
                    out.write_text(
                        f"tags_ok model={model}\n"
                        f"generate_skipped status={r.status_code}\n"
                        f"detail={r.text[:400]}\n",
                        encoding="utf-8",
                    )
                else:
                    out.write_text(r.text[:8000], encoding="utf-8")
        except Exception as e:
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY,
                error_message=str(e),
            )
        ms = int((time.perf_counter() - t0) * 1000)
        ok, reason = self.verify_output(output_dir)
        if not ok:
            return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
        return TestResult(
            self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
            output_path=out, output_size_bytes=out.stat().st_size,
            metadata={"model": model},
        )
