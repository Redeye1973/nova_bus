"""Run summaries and timing artifacts."""
from __future__ import annotations

import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, List

if TYPE_CHECKING:
    from .tool_tests._base import TestResult


def write_run_info(run_dir: Path, run_id: str, results: List[Any], started_at: str) -> None:
    passed = sum(1 for r in results if r.status == "pass")
    failed = sum(1 for r in results if r.status == "fail")
    skipped = sum(1 for r in results if r.status == "skip")
    lines = [
        "# Software Test Run",
        "",
        f"- Run ID: {run_id}",
        f"- Started: {started_at}",
        f"- Finished: {datetime.now().isoformat()}",
        f"- Output: {run_dir}",
        "",
        "## Resultaten",
        f"- Total: {len(results)}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        f"- Skipped: {skipped}",
        "",
        "## Per tool",
        "",
    ]
    for r in results:
        sym = {"pass": "[OK]", "fail": "[FAIL]", "skip": "[SKIP]"}.get(r.status, "[?]")
        line = f"- {sym} **{r.tool_name}** ({r.duration_ms}ms)"
        if r.error_message:
            line += f" — {r.error_message}"
        lines.append(line)
    (run_dir / "_RUN_INFO.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_timing_csv(run_dir: Path, results: List[Any]) -> None:
    with (run_dir / "_TIMING.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tool", "category", "status", "duration_ms", "output_size", "output_hash"])
        for r in results:
            w.writerow([
                r.tool_name,
                getattr(r, "category", "") or "",
                r.status,
                r.duration_ms,
                r.output_size_bytes or 0,
                r.output_hash or "",
            ])


def write_inventory(run_dir: Path, results: List[Any]) -> None:
    parts = ["# Outputs Inventory", ""]
    for r in results:
        if r.status == "pass" and r.output_path:
            p = Path(r.output_path)
            try:
                rel = p.relative_to(run_dir)
            except ValueError:
                rel = p
            parts.append(f"- `{rel}` ({r.output_size_bytes} bytes)")
    (run_dir / "_OUTPUTS_INVENTORY.md").write_text("\n".join(parts) + "\n", encoding="utf-8")


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()
