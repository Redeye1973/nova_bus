"""LDtk: parse minimal project JSON."""
from __future__ import annotations

import json
import time
from pathlib import Path

from .._base import TestResult, ToolTest

_SAMPLE = {
    "jsonVersion": "1.4.1",
    "levels": [{"identifier": "Level_0", "worldX": 0, "worldY": 0, "pxWid": 256, "pxHei": 256}],
}


class LdtkTest(ToolTest):
    TOOL_NAME = "ldtk"
    CATEGORY = "data"
    TIER = 1
    EXPECTED_OUTPUT_FILENAME = "ldtk_parsed.txt"

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        src = output_dir / "sample.ldtk"
        src.write_text(json.dumps(_SAMPLE), encoding="utf-8")
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        try:
            data = json.loads(src.read_text(encoding="utf-8"))
            levels = data.get("levels", [])
            out.write_text(f"levels={len(levels)} first={levels[0].get('identifier')}\n", encoding="utf-8")
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
        )
