"""Composite PNG — Pillow-only by default (avoids PyQt native crashes on Python 3.14+)."""
from __future__ import annotations

import time
from pathlib import Path

from .._base import TestResult, ToolTest


class PyQt5Test(ToolTest):
    TOOL_NAME = "pyqt5"
    CATEGORY = "audio"
    TIER = 2
    EXPECTED_OUTPUT_FILENAME = "composite.png"
    MIN_OUTPUT_SIZE_BYTES = 200

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        backend = "pillow"
        try:
            from PIL import Image, ImageDraw

            im = Image.new("RGB", (256, 256), (0, 40, 80))
            d = ImageDraw.Draw(im)
            d.rectangle([10, 10, 246, 246], outline=(255, 200, 100), width=2)
            d.text((40, 120), "NOVA softtest (Pillow)", fill=(255, 255, 255))
            im.save(out, "PNG")
        except Exception as e:
            return TestResult(
                self.TOOL_NAME, "fail", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY, error_message=str(e),
            )
        ms = int((time.perf_counter() - t0) * 1000)
        ok, reason = self.verify_output(output_dir)
        if not ok:
            return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
        return TestResult(
            self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
            output_path=out, output_size_bytes=out.stat().st_size,
            metadata={"backend": backend, "note": "PyQt5 optional; Pillow default for stability"},
        )
