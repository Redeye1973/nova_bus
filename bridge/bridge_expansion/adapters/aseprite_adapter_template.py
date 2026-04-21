"""Aseprite adapter voor nova_host_bridge.

Aseprite CLI voor pixel art batch operations.
"""
import logging
import subprocess
from pathlib import Path
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_config

router = APIRouter(prefix="/aseprite", tags=["aseprite"])
logger = logging.getLogger(__name__)

CONFIG = get_config()
ASEPRITE_PATH = CONFIG.get("aseprite_path") or "aseprite"
DEFAULT_TIMEOUT = 120


class StatusResponse(BaseModel):
    tool: str = "aseprite"
    available: bool
    version: Optional[str] = None
    path: Optional[str] = None
    error: Optional[str] = None


class BatchExportRequest(BaseModel):
    input_files: List[str] = Field(..., description="Lijst .ase/.aseprite files")
    output_dir: str
    sheet_format: Literal["png", "gif"] = "png"
    include_json: bool = True


class ConvertRequest(BaseModel):
    input_path: str
    output_path: str
    scale: float = Field(1.0, gt=0, le=16)


class PaletteApplyRequest(BaseModel):
    input_path: str
    output_path: str
    palette_path: str = Field(..., description="Path naar .gpl/.ase palette")


class AnimationExportRequest(BaseModel):
    input_path: str
    output_dir: str
    separate_frames: bool = True
    frame_format: str = "frame-{frame0001}.png"


def _run_aseprite(args: list, timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str, str]:
    """Run aseprite subprocess batch mode."""
    full_cmd = [ASEPRITE_PATH, "--batch"] + args
    logger.info(f"Aseprite cmd: {' '.join(full_cmd)}")
    
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
        raise HTTPException(status_code=504, detail=f"Aseprite timeout na {timeout}s")
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail=f"Aseprite binary niet gevonden: {ASEPRITE_PATH}")


def status() -> dict:
    try:
        result = subprocess.run(
            [ASEPRITE_PATH, "--version"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            return StatusResponse(
                available=True,
                version=version,
                path=ASEPRITE_PATH,
            ).model_dump()
    except Exception as e:
        logger.warning(f"Aseprite status check failed: {e}")
    
    return StatusResponse(
        available=False,
        error="Aseprite niet beschikbaar (paid tool, check installatie)",
    ).model_dump()


@router.get("/status")
def get_status():
    return status()


@router.post("/batch_export")
def batch_export(request: BatchExportRequest):
    """Export meerdere .ase files naar sprite sheets."""
    # Validate inputs
    missing = [f for f in request.input_files if not Path(f).exists()]
    if missing:
        raise HTTPException(status_code=404, detail=f"Files niet gevonden: {missing}")
    
    Path(request.output_dir).mkdir(parents=True, exist_ok=True)
    
    results = []
    for input_file in request.input_files:
        base_name = Path(input_file).stem
        sheet_path = f"{request.output_dir}/{base_name}.{request.sheet_format}"
        json_path = f"{request.output_dir}/{base_name}.json" if request.include_json else None
        
        args = [input_file, "--sheet", sheet_path]
        if json_path:
            args.extend(["--data", json_path])
        args.extend(["--sheet-pack"])
        
        code, stdout, stderr = _run_aseprite(args)
        results.append({
            "input": input_file,
            "sheet": sheet_path if code == 0 else None,
            "json": json_path if code == 0 else None,
            "success": code == 0,
            "error": stderr[-200:] if code != 0 else None,
        })
    
    success_count = sum(1 for r in results if r["success"])
    return {
        "total": len(results),
        "success": success_count,
        "failed": len(results) - success_count,
        "results": results,
    }


@router.post("/convert")
def convert(request: ConvertRequest):
    """Convert tussen formats (PNG ↔ ASE) met optionele scaling."""
    if not Path(request.input_path).exists():
        raise HTTPException(status_code=404, detail="Input niet gevonden")
    
    Path(request.output_path).parent.mkdir(parents=True, exist_ok=True)
    
    args = [
        request.input_path,
        "--scale", str(request.scale),
        "--save-as", request.output_path,
    ]
    
    code, stdout, stderr = _run_aseprite(args)
    
    if code != 0:
        raise HTTPException(status_code=500, detail=f"Convert failed: {stderr[-300:]}")
    
    return {
        "success": True,
        "input": request.input_path,
        "output": request.output_path,
        "scale": request.scale,
    }


@router.post("/palette_apply")
def palette_apply(request: PaletteApplyRequest):
    """Pas palette toe op sprite."""
    for p in [request.input_path, request.palette_path]:
        if not Path(p).exists():
            raise HTTPException(status_code=404, detail=f"Niet gevonden: {p}")
    
    Path(request.output_path).parent.mkdir(parents=True, exist_ok=True)
    
    args = [
        request.input_path,
        "--palette", request.palette_path,
        "--save-as", request.output_path,
    ]
    
    code, stdout, stderr = _run_aseprite(args)
    
    if code != 0:
        raise HTTPException(status_code=500, detail=f"Palette apply failed: {stderr[-300:]}")
    
    return {
        "success": True,
        "output": request.output_path,
    }


@router.post("/animation_export")
def animation_export(request: AnimationExportRequest):
    """Export animatie frames individueel."""
    if not Path(request.input_path).exists():
        raise HTTPException(status_code=404, detail="Input niet gevonden")
    
    Path(request.output_dir).mkdir(parents=True, exist_ok=True)
    
    output_pattern = f"{request.output_dir}/{request.frame_format}"
    
    args = [
        request.input_path,
        "--save-as", output_pattern,
    ]
    
    code, stdout, stderr = _run_aseprite(args)
    
    if code != 0:
        raise HTTPException(status_code=500, detail=f"Animation export failed: {stderr[-300:]}")
    
    # Count exported frames
    frame_count = len(list(Path(request.output_dir).glob("frame-*")))
    
    return {
        "success": True,
        "frames_exported": frame_count,
        "output_dir": request.output_dir,
    }
