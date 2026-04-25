"""Compare current run directory to baseline."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def compare_runs(current_dir: Path, baseline_dir: Path) -> List[Dict[str, Any]]:
    diffs: List[Dict[str, Any]] = []
    if not baseline_dir.is_dir():
        return diffs

    for current_tool_dir in sorted(current_dir.iterdir()):
        if not current_tool_dir.is_dir() or current_tool_dir.name.startswith("_"):
            continue
        baseline_tool_dir = baseline_dir / current_tool_dir.name
        if not baseline_tool_dir.exists():
            continue
        for current_file in current_tool_dir.iterdir():
            if current_file.is_dir() or current_file.name.startswith("_"):
                continue
            baseline_file = baseline_tool_dir / current_file.name
            if not baseline_file.exists():
                diffs.append({"tool": current_tool_dir.name, "file": current_file.name, "type": "new_in_current"})
                continue
            curr_size = current_file.stat().st_size
            base_size = baseline_file.stat().st_size
            if base_size > 0:
                size_pct = abs(curr_size - base_size) / base_size * 100
                if size_pct > 50:
                    diffs.append({
                        "tool": current_tool_dir.name,
                        "type": "size_change",
                        "value": size_pct,
                        "threshold": 50,
                    })
            if current_file.suffix.lower() in (".png", ".jpg", ".jpeg"):
                try:
                    from PIL import Image
                    import imagehash

                    curr_hash = imagehash.phash(Image.open(current_file))
                    base_hash = imagehash.phash(Image.open(baseline_file))
                    score = curr_hash - base_hash
                    if score > 10:
                        diffs.append({"tool": current_tool_dir.name, "type": "visual_drift", "value": score})
                except Exception:
                    pass
    return diffs
