"""Blender: render default cube to PNG (background)."""
from __future__ import annotations

import asyncio
from pathlib import Path
import time

from .._base import TestResult, ToolTest
from .._paths import resolve


class BlenderTest(ToolTest):
    TOOL_NAME = "blender"
    CATEGORY = "three_d"
    TIER = 3
    TIMEOUT_SECONDS = 600
    EXPECTED_OUTPUT_FILENAME = "test_cube.png"
    MIN_OUTPUT_SIZE_BYTES = 500

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        exe = resolve("blender", env_override="BLENDER_PATH")
        if not exe:
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY,
                error_message="Executable niet in tool_paths.yaml of PATH",
            )
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        script = output_dir / "render_cube.py"
        outp = str(out.resolve()).replace("\\", "/")
        script.write_text(
            f"""
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
cam = bpy.data.cameras.new("Cam")
cam_obj = bpy.data.objects.new("Cam", cam)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (6, -6, 5)
cam_obj.rotation_euler = (1.1, 0, 0.9)
bpy.context.scene.camera = cam_obj
for eng in ('BLENDER_WORKBENCH', 'BLENDER_EEVEE', 'CYCLES'):
    try:
        bpy.context.scene.render.engine = eng
        break
    except Exception:
        continue
bpy.context.scene.render.resolution_x = 256
bpy.context.scene.render.resolution_y = 256
bpy.context.scene.render.filepath = r"{outp}"
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
""",
            encoding="utf-8",
        )
        proc = await asyncio.create_subprocess_exec(
            exe, "-b", "--python", str(script),
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
                error_message=f"no render output, exit {proc.returncode}",
            )
        ok, reason = self.verify_output(output_dir)
        if not ok:
            return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
        return TestResult(
            self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
            output_path=out, output_size_bytes=out.stat().st_size,
        )
