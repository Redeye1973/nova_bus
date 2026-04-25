"""DAZ Studio — not CLI-automated in this stack."""
from __future__ import annotations

import time
from pathlib import Path

from .._base import TestResult, ToolTest


class DazTest(ToolTest):
    TOOL_NAME = "daz"
    CATEGORY = "three_d"
    TIER = 3
    EXPECTED_OUTPUT_FILENAME = "daz_skip.txt"

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        return TestResult(
            self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
            category=self.CATEGORY,
            error_message="DAZ Studio batch not wired (manual / future)",
        )
