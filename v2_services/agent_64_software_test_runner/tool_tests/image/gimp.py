"""GIMP batch (heavy): simple PNG via Script-Fu if gimp console exists."""
from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
import time

from .._base import TestResult, ToolTest


class GimpTest(ToolTest):
    TOOL_NAME = "gimp"
    CATEGORY = "image"
    TIER = 3
    TIMEOUT_SECONDS = 300
    EXPECTED_OUTPUT_FILENAME = "gimp_out.png"
    MIN_OUTPUT_SIZE_BYTES = 50

    def _gimp(self) -> Path | None:
        for p in (
            Path(r"C:\Program Files\GIMP 2\bin\gimp-console-2.10.exe"),
            Path(r"C:\Program Files\GIMP 3\bin\gimp-console.exe"),
        ):
            if p.is_file():
                return p
        w = shutil.which("gimp-console")
        return Path(w) if w else None

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        gimp = self._gimp()
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        if not gimp:
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY, error_message="gimp-console not found",
            )
        # Batch: create image and save — minimal Python-fu via gimp -i -b
        batch = (
            f'(let* ((img (car (gimp-image-new 64 64 RGB)))'
            f' (drw (car (gimp-layer-new img 64 64 RGBA "L" 100 NORMAL))))'
            f' (gimp-image-insert-layer img drw 0 0)'
            f' (file-png-save RUN-NONINTERACTIVE img drw "{out.as_posix()}" "{out.name}" 0 9 0 0 0 0 0)'
            f' (gimp-image-delete img))'
        )
        proc = await asyncio.create_subprocess_exec(
            str(gimp), "-i", "-b", batch, "-b", "(gimp-quit 0)",
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
        if not out.exists():
            return TestResult(
                self.TOOL_NAME, "fail", ms, category=self.CATEGORY,
                error_message=f"gimp exit {proc.returncode}, no output",
            )
        ok, reason = self.verify_output(output_dir)
        if not ok:
            return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
        return TestResult(
            self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
            output_path=out, output_size_bytes=out.stat().st_size,
        )
