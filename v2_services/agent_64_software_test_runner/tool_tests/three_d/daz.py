"""DAZ Studio: resolve uit yaml; smoke (binary aanwezig — geen headless CLI)."""
from __future__ import annotations

import time
from pathlib import Path

from .._base import TestResult, ToolTest
from .._paths import resolve


class DazTest(ToolTest):
    TOOL_NAME = "daz"
    CATEGORY = "three_d"
    TIER = 3
    EXPECTED_OUTPUT_FILENAME = "daz_verified.txt"

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        exe = resolve("daz_studio", env_override="DAZ_PATH")
        if not exe:
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY,
                error_message="DAZ Studio niet in tool_paths.yaml (daz_studio.executable) of DAZ_PATH",
            )
        p = Path(exe)
        if not p.is_file():
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY,
                error_message=f"DAZ-pad ongeldig: {exe}",
            )
        st = p.stat()
        out.write_text(
            f"executable={exe}\n"
            f"size_bytes={st.st_size}\n"
            "note=GUI batch niet headless getest (geen timeout)\n",
            encoding="utf-8",
        )
        ms = int((time.perf_counter() - t0) * 1000)
        ok, reason = self.verify_output(output_dir)
        if not ok:
            return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
        return TestResult(
            self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
            output_path=out, output_size_bytes=out.stat().st_size,
            metadata={"smoke": "executable_only"},
        )
