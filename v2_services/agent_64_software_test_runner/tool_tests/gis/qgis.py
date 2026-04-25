"""QGIS: qgis_process --version or minimal expression."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
import time

from .._base import TestResult, ToolTest
from .._paths import qgis_install_root, resolve_any


class QgisTest(ToolTest):
    TOOL_NAME = "qgis"
    CATEGORY = "gis"
    TIER = 3
    TIMEOUT_SECONDS = 120
    EXPECTED_OUTPUT_FILENAME = "qgis_version.txt"

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        exe = resolve_any(
            "qgis",
            ["cli_executable", "executable"],
            env_override="QGIS_PROCESS_PATH",
        )
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        if not exe:
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY,
                error_message="qgis_process niet in tool_paths.yaml of PATH",
            )
        exe_path = Path(exe)
        env = os.environ.copy()
        path_bits: list[str] = [str(exe_path.parent)]
        root = qgis_install_root()
        if root:
            for sub in (
                "bin",
                r"apps\qgis-ltr\bin",
                r"apps\qgis\bin",
                r"apps\Qt5\bin",
            ):
                p = root / sub
                if p.is_dir():
                    path_bits.append(str(p))
            for py_dlls in root.glob(r"apps\Python*\DLLs"):
                if py_dlls.is_dir():
                    path_bits.append(str(py_dlls))
                    break
        env["PATH"] = os.pathsep.join(path_bits) + os.pathsep + env.get("PATH", "")
        proc = await asyncio.create_subprocess_exec(
            exe, "--version",
            cwd=str(exe_path.parent),
            env=env,
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
