#!/usr/bin/env python3
"""Emit Markdown summary from artifacts/pipeline_validation_latest.json (session 08)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "artifacts" / "pipeline_validation_latest.json"


def main() -> None:
    if not SRC.is_file():
        print("# Pipeline validation\n\n(no artifacts yet — run `python scripts/run_pipeline_validation.py`)", file=sys.stderr)
        sys.exit(1)
    data = json.loads(SRC.read_text(encoding="utf-8"))
    lines = ["# Pipeline validation snapshot\n"]
    for name, pl in sorted(data.get("pipelines", {}).items()):
        lines.append(f"## {name}\n")
        lines.append(f"- **final_verdict:** {pl.get('final_verdict')}")
        lines.append(f"- **dry_run:** {pl.get('dry_run')}")
        t = pl.get("totals") or {}
        lines.append(f"- **totals:** pending_bridge={t.get('pending_bridge')}, failed={t.get('failed')}, ok={t.get('ok')}, latency_ms={t.get('latency_ms')}")
        lines.append("\n| step | agent | code | ms | pending_bridge | verdict |\n|---|---|---:|---:|---|---|")
        for s in pl.get("steps", []):
            lines.append(
                "| {step} | {agent} | {code} | {lat} | {pb} | {verdict} |".format(
                    step=s.get("step"),
                    agent=s.get("agent"),
                    code=s.get("code", ""),
                    lat=s.get("latency_ms", ""),
                    pb=s.get("pending_bridge", ""),
                    verdict=s.get("verdict", ""),
                )
            )
        lines.append("")
    text = "\n".join(lines)
    print(text)


if __name__ == "__main__":
    main()
