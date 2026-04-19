"""NOVA v2 Agent 20 — Design Fase (palette, silhouette, consistency POC)."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from palette_manager import generate_master_palette
from palette_validator import validate as validate_palette_fn
from silhouette_checker import check as silhouette_check_fn
from consistency_checker import check as consistency_check_fn

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="NOVA v2 Agent 20 - Design Fase", version="0.1.0")


class PaletteRequest(BaseModel):
    theme: str
    faction_count: int = 6
    restrictions: Dict[str, Any] = Field(default_factory=dict)


class PaletteValidationRequest(BaseModel):
    palette: List[str]
    faction_names: List[str]


class SilhouetteRequest(BaseModel):
    image_base64: str
    target_sizes: List[int] = Field(default_factory=lambda: [32, 64, 128])


class ConsistencyRequest(BaseModel):
    concept_image_base64: str
    faction: str
    reference_faction_assets: Optional[List[str]] = None


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "20_design_fase", "version": "0.1.0"}


@app.post("/palette/create")
def create_palette(req: PaletteRequest) -> Dict[str, Any]:
    return generate_master_palette(req.theme, req.faction_count, req.restrictions)


@app.post("/palette/validate")
def validate_palette(req: PaletteValidationRequest) -> Dict[str, Any]:
    return validate_palette_fn(req.palette, req.faction_names)


@app.post("/silhouette/check")
def check_silhouette(req: SilhouetteRequest) -> Dict[str, Any]:
    return silhouette_check_fn(req.image_base64, req.target_sizes)


@app.post("/consistency/check")
def check_consistency(req: ConsistencyRequest) -> Dict[str, Any]:
    return consistency_check_fn(
        req.concept_image_base64,
        req.faction,
        req.reference_faction_assets,
    )
