"""GIMP: console binary uit yaml + snelle --version smoke (batch PNG hangt op sommige GIMP 3 builds)."""
from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path
import time

from .._base import TestResult, ToolTest
from .._paths import resolve_any


class GimpTest(ToolTest):
    TOOL_NAME = "gimp"
    CATEGORY = "image"
    TIER = 3
    TIMEOUT_SECONDS = 60
    EXPECTED_OUTPUT_FILENAME = "gimp_version.txt"
    MIN_OUTPUT_SIZE_BYTES = 16

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        gimp = resolve_any(
            "gimp",
            ["cli_executable", "executable"],
            env_override="GIMP_CLI_PATH",
        )
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        if not gimp:
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY,
                error_message="gimp cli_executable niet in yaml of PATH",
            )
        kwargs: dict = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        proc = await asyncio.create_subprocess_exec(
            gimp, "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **kwargs,
        )
        try:
            so, se = await asyncio.wait_for(proc.communicate(), self.TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            proc.kill()
            return TestResult(
                self.TOOL_NAME, "fail", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY, error_message="gimp --version timeout",
            )
        text = (so or b"").decode(errors="replace") + (se or b"").decode(errors="replace")
        out.write_text(text.strip()[:4000] or f"exit={proc.returncode}\n", encoding="utf-8")
        ms = int((time.perf_counter() - t0) * 1000)
        if proc.returncode != 0:
            return TestResult(
                self.TOOL_NAME, "fail", ms, category=self.CATEGORY,
                error_message=f"gimp --version exit {proc.returncode}",
            )
        ok, reason = self.verify_output(output_dir)
        if not ok:
            return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
        return TestResult(
            self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
            output_path=out, output_size_bytes=out.stat().st_size,
        )
