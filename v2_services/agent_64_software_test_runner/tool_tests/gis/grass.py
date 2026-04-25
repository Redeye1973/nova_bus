"""GRASS GIS: grass --version if available."""
from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
import time

from .._base import TestResult, ToolTest


class GrassTest(ToolTest):
    TOOL_NAME = "grass"
    CATEGORY = "gis"
    TIER = 3
    TIMEOUT_SECONDS = 60
    EXPECTED_OUTPUT_FILENAME = "grass_version.txt"

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        exe = shutil.which("grass") or shutil.which("grass84")
        if not exe:
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY, error_message="grass not in PATH",
            )
        proc = await asyncio.create_subprocess_exec(
            exe, "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            so, se = await asyncio.wait_for(proc.communicate(), self.TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            proc.kill()
            return TestResult(
                self.TOOL_NAME, "fail", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY, error_message="timeout",
            )
        text = (so or b"").decode(errors="replace") + (se or b"").decode(errors="replace")
        out.write_text(text[:4000], encoding="utf-8")
        ms = int((time.perf_counter() - t0) * 1000)
        ok, reason = self.verify_output(output_dir)
        if not ok:
            return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
        return TestResult(
            self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
            output_path=out, output_size_bytes=out.stat().st_size,
        )
