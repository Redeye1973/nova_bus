"""Generic adapter template voor Fase 4 tools (GRASS, GIMP, Krita, Inkscape).

Cursor past dit template aan per tool. Structuur blijft consistent.
"""
import logging
import subprocess
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_config

# Replace <TOOL> met tool naam (grass/gimp/krita/inkscape)
TOOL_NAME = "<TOOL>"
router = APIRouter(prefix=f"/{TOOL_NAME}", tags=[TOOL_NAME])
logger = logging.getLogger(__name__)

CONFIG = get_config()
TOOL_PATH = CONFIG.get(f"{TOOL_NAME}_path") or TOOL_NAME
DEFAULT_TIMEOUT = 120


class StatusResponse(BaseModel):
    tool: str = TOOL_NAME
    available: bool
    version: Optional[str] = None
    path: Optional[str] = None
    error: Optional[str] = None


# === TOOL-SPECIFIC MODELS ===
# Cursor: definieer Pydantic models per operation hier

class ExampleRequest(BaseModel):
    input_path: str
    output_path: str
    # ... tool-specific params


def _run_tool(args: list, timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str, str]:
    """Generic subprocess runner."""
    full_cmd = [TOOL_PATH] + args
    logger.info(f"{TOOL_NAME} cmd: {' '.join(full_cmd)}")
    
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
        raise HTTPException(status_code=504, detail=f"{TOOL_NAME} timeout na {timeout}s")
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail=f"{TOOL_NAME} niet gevonden")


def status() -> dict:
    """Universal status check. Cursor past --version flag aan indien nodig."""
    try:
        result = subprocess.run(
            [TOOL_PATH, "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version = (result.stdout or result.stderr).strip().split("\n")[0]
            return StatusResponse(
                available=True,
                version=version,
                path=TOOL_PATH,
            ).model_dump()
    except Exception as e:
        logger.warning(f"{TOOL_NAME} status check failed: {e}")
    
    return StatusResponse(
        available=False,
        error=f"{TOOL_NAME} niet beschikbaar",
    ).model_dump()


@router.get("/status")
def get_status():
    return status()


# === TOOL-SPECIFIC ENDPOINTS ===
# Cursor: implementeer endpoints per tool

@router.post("/example")
def example_operation(request: ExampleRequest):
    """Placeholder - vervang met echte operation."""
    raise HTTPException(status_code=501, detail="Not implemented - Cursor moet dit vullen")


# ============================================================
# TOOL-SPECIFIEKE NOTES VOOR CURSOR
# ============================================================
#
# GRASS GIS:
# - Vereist location + mapset setup
# - CLI: grass <location/mapset> --exec g.proj -p
# - Modules via: grass location/mapset --exec <module> <args>
# - Status check: grass --version
#
# GIMP:
# - Batch via Script-Fu: gimp -i -b "(script)" -b "(gimp-quit 0)"
# - Python-Fu alternatief: gimp -i --batch-interpreter=python-fu-eval
# - Status check: gimp --version
#
# Krita:
# - Batch: krita --batch --script <script.py>
# - Python API binnen Krita scripting
# - Status check: krita --version
#
# Inkscape 1.3+:
# - Actions-based CLI: inkscape --actions="select-all;export-type:png;export-do" file.svg
# - --export-filename voor output
# - Status check: inkscape --version
#
# ============================================================
