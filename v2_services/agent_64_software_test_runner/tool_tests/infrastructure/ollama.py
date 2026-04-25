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

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        try:
            async with httpx.AsyncClient(timeout=float(self.TIMEOUT_SECONDS)) as client:
                r = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={
                        "model": "tinyllama",
                        "prompt": "Say OK in one word.",
                        "stream": False,
                    },
                )
                if r.status_code != 200:
                    return TestResult(
                        self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                        category=self.CATEGORY,
                        error_message=f"ollama not reachable or model missing: {r.status_code} {r.text[:200]}",
                    )
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
        )
