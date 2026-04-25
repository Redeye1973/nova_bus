"""SoX: WAV → OGG if sox.exe available."""
from __future__ import annotations

import asyncio
import wave
from pathlib import Path
import time

from .._base import TestResult, ToolTest
from .._paths import resolve


class SoxTest(ToolTest):
    TOOL_NAME = "sox"
    CATEGORY = "audio"
    TIER = 2
    TIMEOUT_SECONDS = 60
    EXPECTED_OUTPUT_FILENAME = "converted.ogg"

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        sox = resolve("sox", env_override="SOX_PATH")
        if not sox:
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY,
                error_message="sox.exe niet in tool_paths.yaml of PATH",
            )
        wav = output_dir / "source.wav"
        with wave.open(str(wav), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(8000)
            wf.writeframes(b"\x00\x00" * 1600)
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        proc = await asyncio.create_subprocess_exec(
            sox, str(wav), str(out),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            await asyncio.wait_for(proc.communicate(), self.TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            proc.kill()
            return TestResult(
                self.TOOL_NAME, "fail", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY, error_message="sox timeout",
            )
        ms = int((time.perf_counter() - t0) * 1000)
        if proc.returncode != 0:
            return TestResult(
                self.TOOL_NAME, "fail", ms, category=self.CATEGORY,
                error_message="sox failed",
            )
        ok, reason = self.verify_output(output_dir)
        if not ok:
            return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
        return TestResult(
            self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
            output_path=out, output_size_bytes=out.stat().st_size,
        )
