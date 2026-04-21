"""PyQt5 adapter voor nova_host_bridge.

In tegenstelling tot CLI tools: PyQt5 is een Python library.
Adapter roept Python subprocess aan met specifieke scripts die PyQt5 gebruiken.
"""
import logging
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_config

router = APIRouter(prefix="/pyqt", tags=["pyqt"])
logger = logging.getLogger(__name__)

CONFIG = get_config()
PYTHON_PATH = CONFIG.get("python_path") or sys.executable
DEFAULT_TIMEOUT = 60


class StatusResponse(BaseModel):
    tool: str = "pyqt"
    available: bool
    version: Optional[str] = None
    python_path: Optional[str] = None
    error: Optional[str] = None


class SpriteLayer(BaseModel):
    image_path: str
    x: int = 0
    y: int = 0
    opacity: float = Field(1.0, ge=0, le=1)


class SpriteAssemblyRequest(BaseModel):
    layers: List[SpriteLayer] = Field(..., min_length=1)
    output_path: str
    canvas_width: int = Field(..., gt=0, le=8192)
    canvas_height: int = Field(..., gt=0, le=8192)
    background: Optional[str] = Field(None, description="Hex color zoals #000000")


class ImageComposeRequest(BaseModel):
    input_images: List[str]
    output_path: str
    layout: str = Field("grid", description="grid | horizontal | vertical")
    spacing: int = 0
    columns: Optional[int] = None


class MetadataSheetRequest(BaseModel):
    sprite_sheet_path: str
    sprite_width: int
    sprite_height: int
    output_json: str
    metadata: dict = Field(default_factory=dict, description="Extra metadata per sprite")


# Embedded Python scripts voor PyQt operations

SPRITE_ASSEMBLY_SCRIPT = '''
import json
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPainter, QColor, QPixmap

def main():
    with open(sys.argv[1]) as f:
        config = json.load(f)
    
    # Create canvas
    canvas = QImage(config["canvas_width"], config["canvas_height"], QImage.Format_ARGB32)
    
    if config.get("background"):
        bg_color = QColor(config["background"])
    else:
        bg_color = QColor(0, 0, 0, 0)  # transparent
    canvas.fill(bg_color)
    
    painter = QPainter(canvas)
    
    for layer in config["layers"]:
        layer_img = QImage(layer["image_path"])
        if layer_img.isNull():
            print(f"ERROR: Kan niet laden: {layer[\\'image_path\\']}")
            sys.exit(1)
        
        painter.setOpacity(layer["opacity"])
        painter.drawImage(layer["x"], layer["y"], layer_img)
    
    painter.end()
    
    if not canvas.save(config["output_path"]):
        print(f"ERROR: Kan niet opslaan: {config[\\'output_path\\']}")
        sys.exit(1)
    
    print("SUCCESS")

if __name__ == "__main__":
    main()
'''

IMAGE_COMPOSE_SCRIPT = '''
import json
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPainter, QColor

def main():
    with open(sys.argv[1]) as f:
        config = json.load(f)
    
    images = []
    for img_path in config["input_images"]:
        img = QImage(img_path)
        if img.isNull():
            print(f"ERROR: Kan niet laden: {img_path}")
            sys.exit(1)
        images.append(img)
    
    spacing = config["spacing"]
    layout = config["layout"]
    
    if layout == "horizontal":
        total_width = sum(img.width() for img in images) + spacing * (len(images) - 1)
        max_height = max(img.height() for img in images)
        canvas = QImage(total_width, max_height, QImage.Format_ARGB32)
        canvas.fill(QColor(0, 0, 0, 0))
        
        painter = QPainter(canvas)
        x = 0
        for img in images:
            painter.drawImage(x, 0, img)
            x += img.width() + spacing
        painter.end()
    
    elif layout == "vertical":
        max_width = max(img.width() for img in images)
        total_height = sum(img.height() for img in images) + spacing * (len(images) - 1)
        canvas = QImage(max_width, total_height, QImage.Format_ARGB32)
        canvas.fill(QColor(0, 0, 0, 0))
        
        painter = QPainter(canvas)
        y = 0
        for img in images:
            painter.drawImage(0, y, img)
            y += img.height() + spacing
        painter.end()
    
    else:  # grid
        cols = config.get("columns") or int(len(images) ** 0.5) + 1
        rows = (len(images) + cols - 1) // cols
        
        max_w = max(img.width() for img in images)
        max_h = max(img.height() for img in images)
        
        canvas_w = max_w * cols + spacing * (cols - 1)
        canvas_h = max_h * rows + spacing * (rows - 1)
        canvas = QImage(canvas_w, canvas_h, QImage.Format_ARGB32)
        canvas.fill(QColor(0, 0, 0, 0))
        
        painter = QPainter(canvas)
        for i, img in enumerate(images):
            col = i % cols
            row = i // cols
            x = col * (max_w + spacing)
            y = row * (max_h + spacing)
            painter.drawImage(x, y, img)
        painter.end()
    
    if not canvas.save(config["output_path"]):
        print(f"ERROR: Kan niet opslaan")
        sys.exit(1)
    
    print(f"SUCCESS layout={layout} dimensions={canvas.width()}x{canvas.height()}")

if __name__ == "__main__":
    main()
'''


def _run_pyqt_script(script: str, config: dict, timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str, str]:
    """Run inline Python script met PyQt5, config als JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as script_tmp:
        script_tmp.write(script)
        script_path = script_tmp.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as config_tmp:
        json.dump(config, config_tmp)
        config_path = config_tmp.name
    
    try:
        result = subprocess.run(
            [PYTHON_PATH, script_path, config_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail=f"PyQt timeout na {timeout}s")
    finally:
        Path(script_path).unlink(missing_ok=True)
        Path(config_path).unlink(missing_ok=True)


def status() -> dict:
    """Check PyQt5 availability."""
    try:
        result = subprocess.run(
            [PYTHON_PATH, "-c", "from PyQt5 import QtCore; print(QtCore.PYQT_VERSION_STR)"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return StatusResponse(
                available=True,
                version=result.stdout.strip(),
                python_path=PYTHON_PATH,
            ).model_dump()
    except Exception as e:
        logger.warning(f"PyQt status failed: {e}")
    
    return StatusResponse(
        available=False,
        error="PyQt5 niet geïnstalleerd",
    ).model_dump()


@router.get("/status")
def get_status():
    return status()


@router.post("/sprite_assembly")
def sprite_assembly(request: SpriteAssemblyRequest):
    """Combineer meerdere sprites tot één canvas."""
    # Validate layer files
    for layer in request.layers:
        if not Path(layer.image_path).exists():
            raise HTTPException(status_code=404, detail=f"Layer niet gevonden: {layer.image_path}")
    
    Path(request.output_path).parent.mkdir(parents=True, exist_ok=True)
    
    config = request.model_dump()
    code, stdout, stderr = _run_pyqt_script(SPRITE_ASSEMBLY_SCRIPT, config)
    
    if code != 0 or "SUCCESS" not in stdout:
        raise HTTPException(
            status_code=500,
            detail=f"Assembly failed. stdout: {stdout} stderr: {stderr}"
        )
    
    return {
        "success": True,
        "output_path": request.output_path,
        "canvas_size": f"{request.canvas_width}x{request.canvas_height}",
        "layers_composed": len(request.layers),
    }


@router.post("/image_compose")
def image_compose(request: ImageComposeRequest):
    """Compose images in grid/horizontal/vertical layout."""
    missing = [p for p in request.input_images if not Path(p).exists()]
    if missing:
        raise HTTPException(status_code=404, detail=f"Images niet gevonden: {missing}")
    
    Path(request.output_path).parent.mkdir(parents=True, exist_ok=True)
    
    config = request.model_dump()
    code, stdout, stderr = _run_pyqt_script(IMAGE_COMPOSE_SCRIPT, config)
    
    if code != 0 or "SUCCESS" not in stdout:
        raise HTTPException(
            status_code=500,
            detail=f"Compose failed. stdout: {stdout} stderr: {stderr}"
        )
    
    return {
        "success": True,
        "output_path": request.output_path,
        "layout": request.layout,
        "images_composed": len(request.input_images),
    }


@router.post("/metadata_sheet")
def metadata_sheet(request: MetadataSheetRequest):
    """Genereer sprite sheet metadata JSON (positie per frame)."""
    if not Path(request.sprite_sheet_path).exists():
        raise HTTPException(status_code=404, detail="Sprite sheet niet gevonden")
    
    # Read sheet dimensions
    check_script = f'''
import sys
from PyQt5.QtGui import QImage
img = QImage(r"{request.sprite_sheet_path}")
if img.isNull():
    sys.exit(1)
print(f"{{img.width()}},{{img.height()}}")
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
        tmp.write(check_script)
        tmp_path = tmp.name
    
    try:
        result = subprocess.run([PYTHON_PATH, tmp_path], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail="Kan sheet dimensions niet bepalen")
        
        width, height = map(int, result.stdout.strip().split(","))
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    
    # Calculate frames
    cols = width // request.sprite_width
    rows = height // request.sprite_height
    total_frames = cols * rows
    
    frames = []
    for i in range(total_frames):
        col = i % cols
        row = i // cols
        frames.append({
            "frame_index": i,
            "x": col * request.sprite_width,
            "y": row * request.sprite_height,
            "width": request.sprite_width,
            "height": request.sprite_height,
        })
    
    metadata = {
        "sheet_path": request.sprite_sheet_path,
        "sheet_dimensions": [width, height],
        "sprite_dimensions": [request.sprite_width, request.sprite_height],
        "grid": [cols, rows],
        "total_frames": total_frames,
        "frames": frames,
        **request.metadata,
    }
    
    Path(request.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(request.output_json).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    
    return {
        "success": True,
        "metadata_path": request.output_json,
        "total_frames": total_frames,
        "grid": f"{cols}x{rows}",
    }
