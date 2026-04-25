"""FreeCAD: parametric box → STL via Part export."""
from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
import time

from .._base import TestResult, ToolTest


class FreecadTest(ToolTest):
    TOOL_NAME = "freecad"
    CATEGORY = "three_d"
    TIER = 3
    TIMEOUT_SECONDS = 300
    EXPECTED_OUTPUT_FILENAME = "box.stl"

    def _cmd(self) -> Path | None:
        for p in (
            Path(r"C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe"),
            Path(r"C:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe"),
        ):
            if p.is_file():
                return p
        w = shutil.which("FreeCADCmd")
        return Path(w) if w else None

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        exe = self._cmd()
        if not exe:
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY, error_message="FreeCADCmd not found",
            )
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        outp = str(out.resolve()).replace("\\", "/")
        script = output_dir / "box.py"
        script.write_text(
            f"""
import Part
shape = Part.makeBox(10, 10, 10)
try:
    shape.exportStl("{outp}")
except Exception:
    # Older builds
    import Mesh
    mesh = Mesh.Mesh()
    mesh.addMesh(Mesh.MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.5))
    mesh.write("{outp}")
""",
            encoding="utf-8",
        )
        proc = await asyncio.create_subprocess_exec(
            str(exe), str(script),
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
        ms = int((time.perf_counter() - t0) * 1000)
        if not out.exists():
            err = (se or b"").decode(errors="replace")[-800:]
            return TestResult(
                self.TOOL_NAME, "fail", ms, category=self.CATEGORY,
                error_message=f"no stl, exit {proc.returncode}: {err}",
            )
        ok, reason = self.verify_output(output_dir)
        if not ok:
            return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
        return TestResult(
            self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
            output_path=out, output_size_bytes=out.stat().st_size,
        )
