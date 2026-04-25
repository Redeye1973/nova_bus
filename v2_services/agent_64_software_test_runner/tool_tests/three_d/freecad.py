"""FreeCAD: parametric box → STL via Mesh / Part.export."""
from __future__ import annotations

import asyncio
from pathlib import Path
import time

from .._base import TestResult, ToolTest
from .._paths import resolve_any


class FreecadTest(ToolTest):
    TOOL_NAME = "freecad"
    CATEGORY = "three_d"
    TIER = 3
    TIMEOUT_SECONDS = 300
    EXPECTED_OUTPUT_FILENAME = "box.stl"

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        exe = resolve_any(
            "freecad",
            ["cli_executable", "executable"],
            env_override="FREECAD_CMD_PATH",
        )
        if not exe:
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY,
                error_message="FreeCADCmd niet in tool_paths.yaml of PATH",
            )
        stl_path = output_dir / self.EXPECTED_OUTPUT_FILENAME
        fcstd_path = output_dir / "box.FCStd"
        script_path = output_dir / "box_export.py"
        script = f"""
import FreeCAD
import Part
import Mesh

doc = FreeCAD.newDocument("test")
box = doc.addObject("Part::Box", "Box")
box.Length = 10
box.Width = 10
box.Height = 10
doc.recompute()
shape = box.Shape

try:
    mesh = Mesh.Mesh()
    mesh.addFacets(shape.tessellate(0.1)[1])
    mesh.write(r"{stl_path.as_posix()}")
    print("STL written via Mesh")
except Exception as e:
    print("Mesh method failed:", e)
    try:
        Part.export([box], r"{stl_path.as_posix()}")
        print("STL written via Part.export")
    except Exception as e2:
        print("Part.export failed:", e2)

doc.saveAs(r"{fcstd_path.as_posix()}")
print("FCStd saved")
"""
        script_path.write_text(script, encoding="utf-8")
        proc = await asyncio.create_subprocess_exec(
            exe,
            str(script_path),
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
        log = (output_dir / "command.log")
        log.write_text(
            f"STDOUT:\n{(so or b'').decode(errors='replace')}\n\n"
            f"STDERR:\n{(se or b'').decode(errors='replace')}\n",
            encoding="utf-8",
        )
        if not stl_path.exists():
            head = (so or b"").decode(errors="replace")[:200]
            return TestResult(
                self.TOOL_NAME, "fail", ms, category=self.CATEGORY,
                error_message=f"STL not produced. exit={proc.returncode} stdout[:200]={head!r}",
            )
        ok, reason = self.verify_output(output_dir)
        if not ok:
            return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
        return TestResult(
            self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
            output_path=stl_path, output_size_bytes=stl_path.stat().st_size,
        )
