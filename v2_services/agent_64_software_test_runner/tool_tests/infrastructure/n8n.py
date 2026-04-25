"""n8n: health endpoint."""
from __future__ import annotations

import time
from pathlib import Path

import httpx

from .._base import TestResult, ToolTest
from .._env import N8N_URL


class N8nTest(ToolTest):
    TOOL_NAME = "n8n"
    CATEGORY = "infrastructure"
    TIER = 1
    EXPECTED_OUTPUT_FILENAME = "n8n_health.txt"

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                for path in ("/healthz", "/health", "/"):
                    try:
                        r = await client.get(f"{N8N_URL}{path}")
                        if r.status_code < 500:
                            out.write_text(f"path={path} status={r.status_code}\n{r.text[:1500]}", encoding="utf-8")
                            break
                    except Exception:
                        continue
                else:
                    return TestResult(
                        self.TOOL_NAME, "fail", int((time.perf_counter() - t0) * 1000),
                        category=self.CATEGORY, error_message="no healthy n8n path",
                    )
            ms = int((time.perf_counter() - t0) * 1000)
            ok, reason = self.verify_output(output_dir)
            if not ok:
                return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
            return TestResult(
                self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
                output_path=out, output_size_bytes=out.stat().st_size,
            )
        except Exception as e:
            return TestResult(
                self.TOOL_NAME, "fail", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY, error_message=str(e),
            )
