"""Inkscape CLI: SVG → PNG."""
from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
import time

from .._base import TestResult, ToolTest


class InkscapeTest(ToolTest):
    TOOL_NAME = "inkscape"
    CATEGORY = "image"
    TIER = 2
    TIMEOUT_SECONDS = 120
    EXPECTED_OUTPUT_FILENAME = "export.png"
    MIN_OUTPUT_SIZE_BYTES = 80

    def _ink(self) -> Path | None:
        for p in (
            Path(r"C:\Program Files\Inkscape\bin\inkscape.exe"),
            Path(r"C:\Program Files\Inkscape\inkscape.exe"),
        ):
            if p.is_file():
                return p
        w = shutil.which("inkscape")
        return Path(w) if w else None

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        ink = self._ink()
        if not ink:
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY, error_message="inkscape not found",
            )
        svg = output_dir / "test.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="80">'
            '<rect width="120" height="80" fill="#224466"/>'
            '<text x="10" y="45" fill="white" font-size="14">NOVA</text></svg>',
            encoding="utf-8",
        )
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        proc = await asyncio.create_subprocess_exec(
            str(ink), str(svg), "--export-type=png", f"--export-filename={out}",
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
        if proc.returncode != 0:
            return TestResult(
                self.TOOL_NAME, "fail", ms, category=self.CATEGORY,
                error_message=f"inkscape exit {proc.returncode}",
            )
        ok, reason = self.verify_output(output_dir)
        if not ok:
            return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
        return TestResult(
            self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
            output_path=out, output_size_bytes=out.stat().st_size,
        )
