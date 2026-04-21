"""Godot adapter voor nova_host_bridge.

Godot headless operations voor asset import testing, project validatie, exports.
"""
import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_config

router = APIRouter(prefix="/godot", tags=["godot"])
logger = logging.getLogger(__name__)

CONFIG = get_config()
GODOT_PATH = CONFIG.get("godot_path") or "godot"
DEFAULT_TIMEOUT = 60


class StatusResponse(BaseModel):
    tool: str = "godot"
    available: bool
    version: Optional[str] = None
    path: Optional[str] = None
    error: Optional[str] = None


class ImportTestRequest(BaseModel):
    asset_path: str
    asset_type: Literal["sprite", "mesh", "audio", "scene", "shader", "font"]
    project_path: str = Field(..., description="Godot project waar import in getest wordt")


class ProjectValidateRequest(BaseModel):
    project_path: str
    check_scripts: bool = True
    check_scenes: bool = True
    check_resources: bool = True


class HeadlessTestRequest(BaseModel):
    project_path: str
    test_scene: str = Field(..., description="Relative path in project, bv 'tests/unit_test.tscn'")
    timeout_seconds: int = Field(60, ge=5, le=600)


class ExportBuildRequest(BaseModel):
    project_path: str
    preset: str = Field(..., description="Export preset name, bv 'Windows Desktop'")
    output_path: str
    debug: bool = False
    timeout_seconds: int = Field(300, ge=10, le=3600)


class ScriptExecuteRequest(BaseModel):
    script_path: str = Field(..., description="Path naar .gd bestand")
    project_path: Optional[str] = None
    timeout_seconds: int = 60


def _run_godot(args: list, timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str, str]:
    """Run godot subprocess headless."""
    full_cmd = [GODOT_PATH, "--headless"] + args
    logger.info(f"Godot cmd: {' '.join(full_cmd)}")
    
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
        raise HTTPException(status_code=504, detail=f"Godot timeout na {timeout}s")
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail=f"Godot binary niet gevonden: {GODOT_PATH}")


def status() -> dict:
    try:
        result = subprocess.run(
            [GODOT_PATH, "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return StatusResponse(
                available=True,
                version=version,
                path=GODOT_PATH,
            ).model_dump()
    except Exception as e:
        logger.warning(f"Godot status failed: {e}")
    
    return StatusResponse(
        available=False,
        error="Godot niet beschikbaar",
    ).model_dump()


@router.get("/status")
def get_status():
    return status()


@router.post("/import_test")
def import_test(request: ImportTestRequest):
    """Test of asset correct importeert in Godot project."""
    if not Path(request.asset_path).exists():
        raise HTTPException(status_code=404, detail="Asset niet gevonden")
    
    project_godot = Path(request.project_path) / "project.godot"
    if not project_godot.exists():
        raise HTTPException(status_code=404, detail=f"Geen Godot project in {request.project_path}")
    
    # Copy asset to project temp location
    test_dir = Path(request.project_path) / "_nova_import_test"
    test_dir.mkdir(exist_ok=True)
    asset_name = Path(request.asset_path).name
    target_asset = test_dir / asset_name
    
    try:
        shutil.copy2(request.asset_path, target_asset)
        
        # Run import
        code, stdout, stderr = _run_godot(
            ["--path", request.project_path, "--import"],
            timeout=60
        )
        
        # Check for .import file (Godot maakt deze bij succesvolle import)
        import_file = target_asset.with_suffix(target_asset.suffix + ".import")
        import_succeeded = import_file.exists()
        
        # Parse errors uit output
        errors = [line for line in stderr.split("\n") if "ERROR" in line or "error" in line.lower()]
        warnings = [line for line in stderr.split("\n") if "WARNING" in line]
        
        return {
            "success": code == 0 and import_succeeded,
            "asset_type": request.asset_type,
            "asset_name": asset_name,
            "import_file_created": import_succeeded,
            "errors": errors[:10],
            "warnings": warnings[:10],
            "exit_code": code,
        }
    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir, ignore_errors=True)


@router.post("/project_validate")
def project_validate(request: ProjectValidateRequest):
    """Valideer heel Godot project."""
    project_path = Path(request.project_path)
    project_godot = project_path / "project.godot"
    
    if not project_godot.exists():
        raise HTTPException(status_code=404, detail="Geen project.godot")
    
    report = {
        "project": str(project_path),
        "project_godot_valid": True,
        "scripts": {"total": 0, "valid": 0, "errors": []},
        "scenes": {"total": 0, "found": 0},
        "resources": {"total": 0, "found": 0},
    }
    
    # Script validation
    if request.check_scripts:
        gd_files = list(project_path.rglob("*.gd"))
        report["scripts"]["total"] = len(gd_files)
        
        for gd_file in gd_files:
            code, stdout, stderr = _run_godot(
                ["--path", str(project_path), "--check-only", "--script", str(gd_file)],
                timeout=10
            )
            if code == 0:
                report["scripts"]["valid"] += 1
            else:
                report["scripts"]["errors"].append({
                    "file": str(gd_file.relative_to(project_path)),
                    "error": stderr[-300:] if stderr else "unknown",
                })
    
    # Scene files found (geen runtime check, alleen bestaan)
    if request.check_scenes:
        tscn_files = list(project_path.rglob("*.tscn"))
        report["scenes"]["total"] = len(tscn_files)
        report["scenes"]["found"] = len(tscn_files)  # Basic check
    
    # Resource files
    if request.check_resources:
        tres_files = list(project_path.rglob("*.tres"))
        report["resources"]["total"] = len(tres_files)
        report["resources"]["found"] = len(tres_files)
    
    report["overall_valid"] = (
        report["project_godot_valid"]
        and report["scripts"]["valid"] == report["scripts"]["total"]
    )
    
    return report


@router.post("/headless_test")
def headless_test(request: HeadlessTestRequest):
    """Run Godot test scene headless."""
    project_godot = Path(request.project_path) / "project.godot"
    if not project_godot.exists():
        raise HTTPException(status_code=404, detail="Geen Godot project")
    
    test_scene_full = Path(request.project_path) / request.test_scene
    if not test_scene_full.exists():
        raise HTTPException(status_code=404, detail=f"Test scene niet gevonden: {request.test_scene}")
    
    code, stdout, stderr = _run_godot(
        ["--path", request.project_path, request.test_scene, "--quit-after", "300"],
        timeout=request.timeout_seconds
    )
    
    # Detect assertions/failures in stdout
    assertion_failures = [line for line in stdout.split("\n") if "FAIL" in line.upper()]
    test_outputs = [line for line in stdout.split("\n") if "TEST" in line.upper()]
    
    return {
        "success": code == 0 and len(assertion_failures) == 0,
        "exit_code": code,
        "test_outputs": test_outputs,
        "failures": assertion_failures,
        "stdout_tail": stdout[-2000:],
        "stderr_tail": stderr[-1000:] if stderr else "",
    }


@router.post("/export_build")
def export_build(request: ExportBuildRequest):
    """Export Godot project naar binary."""
    project_godot = Path(request.project_path) / "project.godot"
    export_presets = Path(request.project_path) / "export_presets.cfg"
    
    if not project_godot.exists():
        raise HTTPException(status_code=404, detail="Geen Godot project")
    if not export_presets.exists():
        raise HTTPException(status_code=400, detail="Geen export_presets.cfg - maak preset in Godot eerst")
    
    Path(request.output_path).parent.mkdir(parents=True, exist_ok=True)
    
    flag = "--export-debug" if request.debug else "--export-release"
    
    code, stdout, stderr = _run_godot(
        ["--path", request.project_path, flag, request.preset, request.output_path],
        timeout=request.timeout_seconds
    )
    
    output_exists = Path(request.output_path).exists()
    file_size = Path(request.output_path).stat().st_size if output_exists else 0
    
    return {
        "success": code == 0 and output_exists,
        "output_path": request.output_path,
        "file_size_bytes": file_size,
        "preset": request.preset,
        "build_type": "debug" if request.debug else "release",
        "errors": [line for line in stderr.split("\n") if "ERROR" in line][-10:],
    }


@router.post("/script_execute")
def script_execute(request: ScriptExecuteRequest):
    """Run GDScript headless (bijv. unit test of utility)."""
    if not Path(request.script_path).exists():
        raise HTTPException(status_code=404, detail="Script niet gevonden")
    
    args = ["--script", request.script_path]
    if request.project_path:
        args = ["--path", request.project_path] + args
    
    code, stdout, stderr = _run_godot(args, timeout=request.timeout_seconds)
    
    return {
        "success": code == 0,
        "exit_code": code,
        "stdout": stdout[-2000:],
        "stderr": stderr[-1000:] if stderr else "",
    }
