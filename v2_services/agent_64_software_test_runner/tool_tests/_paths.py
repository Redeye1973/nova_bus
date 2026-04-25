"""Resolve tool executables from config/tool_paths.yaml with PATH fallback."""
from __future__ import annotations

import os
import shutil
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# tool_tests/_paths.py -> parents[3] = repo root (!Nova V2)
REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = REPO_ROOT / "config" / "tool_paths.yaml"

_SECTIONS = ("tools", "audio")


@lru_cache(maxsize=1)
def _load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {}


def get_tool_entry(tool_key: str) -> Optional[Dict[str, Any]]:
    cfg = _load_config()
    for sec in _SECTIONS:
        block = cfg.get(sec)
        if not isinstance(block, dict):
            continue
        if tool_key in block and isinstance(block[tool_key], dict):
            return block[tool_key]
    return None


def resolve(
    tool_key: str,
    executable_key: str = "executable",
    env_override: Optional[str] = None,
) -> Optional[str]:
    if env_override:
        env_value = os.getenv(env_override)
        if env_value:
            p = Path(env_value).expanduser()
            if p.is_file():
                return str(p.resolve())

    entry = get_tool_entry(tool_key)
    if entry:
        exe = entry.get(executable_key)
        if exe and isinstance(exe, str):
            p = Path(exe)
            if p.is_file():
                return str(p.resolve())

    # PATH: try tool_key and common exe names
    for candidate in (tool_key, tool_key.replace("_", "-")):
        w = shutil.which(candidate)
        if w:
            return w
    return None


def resolve_any(tool_key: str, keys: List[str], env_override: Optional[str] = None) -> Optional[str]:
    if env_override:
        env_value = os.getenv(env_override)
        if env_value:
            p = Path(env_value).expanduser()
            if p.is_file():
                return str(p.resolve())
    entry = get_tool_entry(tool_key)
    if entry:
        for k in keys:
            exe = entry.get(k)
            if exe and isinstance(exe, str):
                p = Path(exe)
                if p.is_file():
                    return str(p.resolve())
    return None


def qgis_install_root() -> Optional[Path]:
    entry = get_tool_entry("qgis")
    if not entry:
        return None
    root = entry.get("install_root")
    if root and isinstance(root, str):
        p = Path(root)
        if p.is_dir():
            return p
    return None


def grass_bundled_browser_exe() -> Optional[Path]:
    """GRASS UI helper shipped with QGIS LTR (smoke: binary exists)."""
    root = qgis_install_root()
    if not root:
        return None
    candidates = [
        root / "apps" / "qgis-ltr" / "grass" / "bin" / "qgis.g.browser8.exe",
        root / "apps" / "qgis" / "grass" / "bin" / "qgis.g.browser8.exe",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None
