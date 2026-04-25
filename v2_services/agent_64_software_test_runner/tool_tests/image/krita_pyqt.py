"""Krita replacement: Pillow canvas (same as PyQt fallback pattern)."""
from __future__ import annotations

import time
from pathlib import Path

from .._base import TestResult, ToolTest


class KritaPyQtTest(ToolTest):
    TOOL_NAME = "krita_pyqt"
    CATEGORY = "image"
    TIER = 2
    EXPECTED_OUTPUT_FILENAME = "krita_like.png"
    MIN_OUTPUT_SIZE_BYTES = 100

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        try:
            from PIL import Image, ImageDraw

            im = Image.new("RGBA", (200, 200), (30, 30, 40, 255))
            d = ImageDraw.Draw(im)
            d.rectangle([20, 20, 180, 180], outline=(255, 200, 100), width=3)
            d.text((40, 90), "Krita-class PyQt canvas", fill=(255, 255, 255))
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
            metadata={"note": "Pillow stand-in for Krita CLI"},
        )
