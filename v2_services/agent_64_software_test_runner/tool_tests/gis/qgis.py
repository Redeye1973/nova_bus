"""QGIS: qgis_process --version or minimal expression."""
from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
import time

from .._base import TestResult, ToolTest


class QgisTest(ToolTest):
    TOOL_NAME = "qgis"
    CATEGORY = "gis"
    TIER = 3
    TIMEOUT_SECONDS = 120
    EXPECTED_OUTPUT_FILENAME = "qgis_version.txt"

    def _qgis(self) -> Path | None:
        w = shutil.which("qgis_process")
        if w:
            return Path(w)
        for p in (
            Path(r"C:\Program Files\QGIS 3.38.0\bin\qgis_process.exe"),
            Path(r"C:\Program Files\QGIS 3.34.0\bin\qgis_process.exe"),
        ):
            if p.is_file():
                return p
        return None

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        exe = self._qgis()
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        if not exe:
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY, error_message="qgis_process not found",
            )
        proc = await asyncio.create_subprocess_exec(
            str(exe), "--version",
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
        if proc.returncode != 0:
            return TestResult(
                self.TOOL_NAME, "fail", ms, category=self.CATEGORY,
                error_message=f"exit {proc.returncode}",
            )
        ok, reason = self.verify_output(output_dir)
        if not ok:
            return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
        return TestResult(
            self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
            output_path=out, output_size_bytes=out.stat().st_size,
        )
