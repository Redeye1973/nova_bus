"""GRASS GIS: grass --version if available; else QGIS-bundled GRASS smoke."""
from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
import time

from .._base import TestResult, ToolTest
from .._paths import grass_bundled_browser_exe


class GrassTest(ToolTest):
    TOOL_NAME = "grass"
    CATEGORY = "gis"
    TIER = 3
    TIMEOUT_SECONDS = 60
    EXPECTED_OUTPUT_FILENAME = "grass_version.txt"

    def _path_grass(self) -> str | None:
        for name in ("grass", "grass84", "grass78"):
            w = shutil.which(name)
            if w:
                return w
        return None

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        exe = self._path_grass()
        if exe:
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

        bundled = grass_bundled_browser_exe()
        if bundled:
            msg = f"bundled_grass_component={bundled}\n(standalone grass niet op PATH; QGIS bundle aanwezig)\n"
            out.write_text(msg, encoding="utf-8")
            ms = int((time.perf_counter() - t0) * 1000)
            ok, reason = self.verify_output(output_dir)
            if not ok:
                return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
            return TestResult(
                self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
                output_path=out, output_size_bytes=out.stat().st_size,
                metadata={"bundled": str(bundled)},
            )

        return TestResult(
            self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
            category=self.CATEGORY,
            error_message="tool not installed (geen grass op PATH, geen QGIS-bundelde component)",
        )
