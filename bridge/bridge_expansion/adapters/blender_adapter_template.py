"""Blender adapter voor nova_host_bridge.

Exposeert Blender headless operations aan Hetzner agents.
Belangrijk: Blender draait als subprocess, elke operatie is stateless.
"""
import asyncio
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_config

router = APIRouter(prefix="/blender", tags=["blender"])
logger = logging.getLogger(__name__)

# Config
CONFIG = get_config()
BLENDER_PATH = CONFIG.get("blender_path") or "blender"
DEFAULT_TIMEOUT = 300  # 5 min default, lange renders overriden


class StatusResponse(BaseModel):
    tool: str = "blender"
    available: bool
    version: Optional[str] = None
    path: Optional[str] = None
    error: Optional[str] = None


class RenderRequest(BaseModel):
    scene_path: str = Field(..., description="Absolute path naar .blend file")
    output_path: str = Field(..., description="Output image path (full path incl extension)")
    format: Literal["PNG", "JPEG", "EXR", "TIFF"] = "PNG"
    resolution_x: int = Field(1920, ge=16, le=16384)
    resolution_y: int = Field(1080, ge=16, le=16384)
    samples: int = Field(128, ge=1, le=10000, description="Cycles samples, 128 default")
    frame: int = Field(1, description="Frame nummer, 1 voor single frame")
    engine: Literal["CYCLES", "BLENDER_EEVEE_NEXT"] = "BLENDER_EEVEE_NEXT"
    timeout_seconds: int = Field(DEFAULT_TIMEOUT, ge=10, le=3600)


class ExportRequest(BaseModel):
    scene_path: str
    output_path: str
    format: Literal["GLB", "FBX", "OBJ", "USD"] = "GLB"
    apply_modifiers: bool = True
    export_animations: bool = False
    timeout_seconds: int = 120


class ScriptRequest(BaseModel):
    script: str = Field(..., description="Python script als string")
    scene_path: Optional[str] = None
    script_args: dict = Field(default_factory=dict)
    timeout_seconds: int = 120


def _run_blender(args: list, timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str, str]:
    """Run blender subprocess. Returns (exit_code, stdout, stderr)."""
    full_cmd = [BLENDER_PATH, "--background"] + args
    logger.info(f"Blender cmd: {' '.join(full_cmd)}")
    
    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail=f"Blender timeout na {timeout}s")
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail=f"Blender binary niet gevonden: {BLENDER_PATH}")


def status() -> dict:
    """Return adapter status."""
    try:
        result = subprocess.run(
            [BLENDER_PATH, "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            # Parse version
            version_line = result.stdout.split("\n")[0]
            return StatusResponse(
                available=True,
                version=version_line.strip(),
                path=BLENDER_PATH,
            ).model_dump()
    except Exception as e:
        logger.warning(f"Blender status check failed: {e}")
    
    return StatusResponse(
        available=False,
        error="Blender niet beschikbaar",
    ).model_dump()


@router.get("/status")
def get_status():
    return status()


@router.post("/render")
def render_scene(request: RenderRequest):
    """Render scene naar afbeelding via Cycles of Eevee."""
    # Validate scene exists
    if not Path(request.scene_path).exists():
        raise HTTPException(status_code=404, detail=f"Scene niet gevonden: {request.scene_path}")
    
    # Ensure output dir exists
    output_parent = Path(request.output_path).parent
    output_parent.mkdir(parents=True, exist_ok=True)
    
    # Build render script
    render_script = f'''
import bpy
scene = bpy.context.scene
scene.render.engine = "{request.engine}"
scene.render.resolution_x = {request.resolution_x}
scene.render.resolution_y = {request.resolution_y}
scene.render.image_settings.file_format = "{request.format}"
scene.cycles.samples = {request.samples} if scene.render.engine == "CYCLES" else scene.cycles.samples
scene.frame_set({request.frame})
scene.render.filepath = r"{request.output_path}"
bpy.ops.render.render(write_still=True)
print("NOVA_RENDER_COMPLETE")
'''
    
    # Write script to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
        tmp.write(render_script)
        script_path = tmp.name
    
    try:
        code, stdout, stderr = _run_blender(
            [request.scene_path, "--python", script_path],
            timeout=request.timeout_seconds
        )
        
        if code != 0 or "NOVA_RENDER_COMPLETE" not in stdout:
            raise HTTPException(
                status_code=500,
                detail=f"Render failed. stderr: {stderr[-500:]}"
            )
        
        return {
            "success": True,
            "output_path": request.output_path,
            "engine_used": request.engine,
            "resolution": f"{request.resolution_x}x{request.resolution_y}",
        }
    finally:
        os.unlink(script_path)


@router.post("/export")
def export_scene(request: ExportRequest):
    """Export scene naar 3D format."""
    if not Path(request.scene_path).exists():
        raise HTTPException(status_code=404, detail=f"Scene niet gevonden: {request.scene_path}")
    
    Path(request.output_path).parent.mkdir(parents=True, exist_ok=True)
    
    export_scripts = {
        "GLB": f'bpy.ops.export_scene.gltf(filepath=r"{request.output_path}", export_format="GLB", export_apply={request.apply_modifiers}, export_animations={request.export_animations})',
        "FBX": f'bpy.ops.export_scene.fbx(filepath=r"{request.output_path}", use_mesh_modifiers={request.apply_modifiers}, bake_anim={request.export_animations})',
        "OBJ": f'bpy.ops.wm.obj_export(filepath=r"{request.output_path}", apply_modifiers={request.apply_modifiers})',
        "USD": f'bpy.ops.wm.usd_export(filepath=r"{request.output_path}", export_animation={request.export_animations})',
    }
    
    script = f'''
import bpy
{export_scripts[request.format]}
print("NOVA_EXPORT_COMPLETE")
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
        tmp.write(script)
        script_path = tmp.name
    
    try:
        code, stdout, stderr = _run_blender(
            [request.scene_path, "--python", script_path],
            timeout=request.timeout_seconds
        )
        
        if code != 0 or "NOVA_EXPORT_COMPLETE" not in stdout:
            raise HTTPException(
                status_code=500,
                detail=f"Export failed. stderr: {stderr[-500:]}"
            )
        
        file_size = Path(request.output_path).stat().st_size if Path(request.output_path).exists() else 0
        
        return {
            "success": True,
            "output_path": request.output_path,
            "format": request.format,
            "file_size_bytes": file_size,
        }
    finally:
        os.unlink(script_path)


@router.post("/script")
def execute_script(request: ScriptRequest):
    """Run arbitrair Python script in Blender context."""
    # Safety: log script (eerste 200 chars) voor audit
    logger.info(f"Blender script execute: {request.script[:200]}...")
    
    # Inject args als module-level variables
    args_code = "\n".join([f'{k} = {repr(v)}' for k, v in request.script_args.items()])
    full_script = f"{args_code}\n\n{request.script}"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
        tmp.write(full_script)
        script_path = tmp.name
    
    cmd_args = ["--python", script_path]
    if request.scene_path:
        if not Path(request.scene_path).exists():
            raise HTTPException(status_code=404, detail=f"Scene niet gevonden: {request.scene_path}")
        cmd_args = [request.scene_path] + cmd_args
    
    try:
        code, stdout, stderr = _run_blender(cmd_args, timeout=request.timeout_seconds)
        
        return {
            "success": code == 0,
            "exit_code": code,
            "stdout": stdout[-2000:] if stdout else "",
            "stderr": stderr[-1000:] if stderr else "",
        }
    finally:
        os.unlink(script_path)
