"""Load Art Direction Bible YAML for NOVA generate + jury pipelines."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

DEFAULT_BIBLE_PATH = Path(r"L:\ZZZZZ ZZ 31-05-2026\agents\art_direction_bible.yaml")
_ENV_PATH = "NOVA_ART_DIRECTION_BIBLE"


def resolve_bible_path() -> Path:
    env = os.getenv(_ENV_PATH, "").strip()
    if env:
        return Path(env)
    return DEFAULT_BIBLE_PATH


def load_art_direction_bible() -> Dict[str, Any]:
    path = resolve_bible_path()
    if not path.is_file():
        return {}
    if yaml is None:
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError:
        return {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def bible_section(name: str) -> Dict[str, Any]:
    bible = load_art_direction_bible()
    sec = bible.get(name)
    return sec if isinstance(sec, dict) else {}


def jury_metrics(section: str) -> List[Dict[str, Any]]:
    bible = load_art_direction_bible()
    jm = bible.get("jury_metrics")
    if not isinstance(jm, dict):
        return []
    rows = jm.get(section)
    if not isinstance(rows, list):
        return []
    return [r for r in rows if isinstance(r, dict)]


def _rules_lines(*sections: str) -> List[str]:
    lines: List[str] = []
    for sec_name in sections:
        sec = bible_section(sec_name)
        rules = sec.get("rules")
        if isinstance(rules, list):
            for r in rules:
                if isinstance(r, str) and r.strip():
                    lines.append(r.strip())
    return lines


def prompt_prefix_for_asset(asset_category: str = "", asset_subdir: str = "") -> str:
    """Prepend Raptor/Tyrian rules to PixelLab prompts."""
    cat = (asset_category or "").lower()
    sub = (asset_subdir or "").lower()
    is_bg = sub == "backgrounds" or cat.startswith("bg_layer") or "parallax" in cat or "background" in cat
    if is_bg:
        sections = ("parallax", "palette")
        label = "Raptor/Tyrian parallax+palette"
    else:
        sections = ("sprites", "palette")
        label = "Raptor/Tyrian sprite+palette"
    rules = _rules_lines(*sections)
    if not rules:
        return ""
    joined = "; ".join(rules[:8])
    return f"{label}: {joined}. "


def learned_rules() -> List[Dict[str, Any]]:
    """Geleerde regels (fase 3, via /feedback op agent 41)."""
    rows = load_art_direction_bible().get("geleerde_regels")
    if not isinstance(rows, list):
        return []
    return [r for r in rows if isinstance(r, dict) and r.get("regel")]


def excerpt_for_pipeline(kind: str) -> Dict[str, Any]:
    """Compact dict for Dale/jury payloads (parallax | sprites | full)."""
    bible = load_art_direction_bible()
    extra = {"geleerde_regels": learned_rules()} if learned_rules() else {}
    if kind == "parallax":
        return {
            "version": bible.get("version"),
            "parallax": bible.get("parallax"),
            "palette": bible.get("palette"),
            "jury_metrics": {"parallax_jury": jury_metrics("parallax_jury")},
            **extra,
        }
    if kind == "sprites":
        return {
            "version": bible.get("version"),
            "sprites": bible.get("sprites"),
            "palette": bible.get("palette"),
            "jury_metrics": {"sprite_jury": jury_metrics("sprite_jury")},
            **extra,
        }
    return bible


def bible_meta() -> Dict[str, Any]:
    path = resolve_bible_path()
    bible = load_art_direction_bible()
    return {
        "bible_path": str(path),
        "bible_loaded": bool(bible),
        "version": bible.get("version"),
        "domain": bible.get("domain"),
    }
