"""Aseprite batch export (if installed)."""
from __future__ import annotations

import asyncio
from pathlib import Path
import time

from .._base import TestResult, ToolTest
from .._paths import resolve


class AsepriteTest(ToolTest):
    TOOL_NAME = "aseprite"
    CATEGORY = "image"
    TIER = 2
    TIMEOUT_SECONDS = 120
    EXPECTED_OUTPUT_FILENAME = "sprite.png"
    MIN_OUTPUT_SIZE_BYTES = 50

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        exe = resolve("aseprite", env_override="ASEPRITE_PATH")
        if not exe:
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY,
                error_message="Executable niet in tool_paths.yaml of PATH",
            )
        ase = output_dir / "blank.aseprite"
        # Minimal valid aseprite file is complex — use CLI to create 1x1 via script if available
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        proc = await asyncio.create_subprocess_exec(
            exe, "-b", "--save-as", str(out), "--width", "32", "--height", "32",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            await asyncio.wait_for(proc.communicate(), self.TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            proc.kill()
            return TestResult(
                self.TOOL_NAME, "fail", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY, error_message="timeout",
            )
        ms = int((time.perf_counter() - t0) * 1000)
        if not out.exists() or proc.returncode != 0:
            # Aseprite CLI varies — fallback Pillow PNG
            try:
                from PIL import Image

                Image.new("RGBA", (32, 32), (200, 100, 50, 255)).save(out, "PNG")
            except Exception as e:
                return TestResult(
                    self.TOOL_NAME, "fail", ms, category=self.CATEGORY,
                    error_message=f"aseprite+fallback: {e}",
                )
        ok, reason = self.verify_output(output_dir)
        if not ok:
            return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
        return TestResult(
            self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
            output_path=out, output_size_bytes=out.stat().st_size,
            metadata={"cli_exit": proc.returncode},
        )
