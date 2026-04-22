#!/usr/bin/env python3
"""Session 08 — run pipeline steps over HTTP, log latency/verdicts, write artifacts.

Dry-run (default): writes artifacts/pipeline_validation_latest.json with step plan only.

Execute on published Compose ports (same host):
  set PIPELINE_USE_PUBLISHED_PORTS=1
  python scripts/run_pipeline_validation.py --pipeline all

Requires each agent port published to 127.0.0.1 (same as internal port). If not
published, steps will fail with connection errors (mark FAILED after retries).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
ART.mkdir(parents=True, exist_ok=True)
OUT_JSON = ART / "pipeline_validation_latest.json"

# Internal Compose DNS → same port on localhost when published.
SERVICE_PORTS: Dict[str, int] = {
    "agent-20-design-fase": 8120,
    "agent-21-freecad-parametric": 8121,
    "agent-22-blender-renderer": 8122,
    "agent-23-aseprite-processor": 8123,
    "agent-24-aseprite-anim-jury": 8124,
    "agent-25-pyqt-assembly": 8125,
    "sprite-jury-v2": 8101,
    "agent-26-godot-import": 8126,
    "agent-13-pdok-downloader": 8113,
    "agent-15-qgis-processor": 8115,
    "agent-31-qgis-analysis": 8131,
    "agent-32-grass-gis": 8132,
    "agent-14-blender-baker": 8114,
    "agent-04-3d-model-jury": 8104,
    "agent-05-gis-jury": 8105,
    "agent-19-distribution": 8119,
    "agent-28-story-integration": 8128,
    "agent-07-narrative-jury": 8107,
    "agent-27-storyboard": 8127,
    "agent-08-character-art-jury": 8108,
    "agent-09-illustration-jury": 8109,
    "agent-29-elevenlabs": 8129,
    "agent-30-audio-asset-jury": 8130,
    "agent-11-monitor": 8111,
}

_TINY_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _localize_url(url: str) -> str:
    if os.environ.get("PIPELINE_USE_PUBLISHED_PORTS", "").strip() != "1":
        return url
    m = re.match(r"http://([^:]+):(\d+)(/.*)$", url)
    if not m:
        return url
    host, _port, path = m.group(1), m.group(2), m.group(3)
    p = SERVICE_PORTS.get(host)
    if p is None:
        return url
    return f"http://127.0.0.1:{p}{path}"


def _http_json(method: str, url: str, body: Optional[Dict[str, Any]], timeout: float) -> tuple[int, str, Any]:
    u = _localize_url(url)
    data = None
    headers = {"Content-Type": "application/json"}
    if body is not None and method.upper() != "GET":
        data = json.dumps(body).encode("utf-8")
    req = Request(u, data=data, headers=headers, method=method.upper())
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            code = resp.getcode() or 200
            try:
                return code, raw, json.loads(raw) if raw.strip() else {}
            except json.JSONDecodeError:
                return code, raw, {"_raw": raw[:2000]}
    except HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        try:
            parsed = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            parsed = {"_raw": raw[:2000]}
        return int(e.code), raw, parsed
    except URLError as e:
        return 0, str(e.reason), {"error": str(e)}


def _pending_bridge(code: int, parsed: Any) -> bool:
    if code == 503:
        return True
    if isinstance(parsed, dict):
        st = str(parsed.get("status", "") or "").lower()
        if st == "pending_full_bridge" or "pending_full_bridge" in st:
            return True
        if parsed.get("mode") == "stub":
            return True
        det = parsed.get("detail")
        if det == "Bridge not fully wired. See session 08+.":
            return True
        if isinstance(det, str) and "pending_full_bridge" in det.lower():
            return True
    return False


def _verdict_from(parsed: Any) -> str:
    if not isinstance(parsed, dict):
        return "skip"
    if "verdict" in parsed:
        return str(parsed.get("verdict"))
    if parsed.get("status") == "dry_run" or parsed.get("status") == "dry_run_no_flux_credentials":
        return "accept"
    if parsed.get("metrics"):
        return "accept"
    return "skip"


@dataclass
class Step:
    order: int
    agent: str
    method: str
    url: str
    body: Optional[Dict[str, Any]] = None
    timeout: float = 120.0


def shmup_steps() -> List[Step]:
    return [
        Step(1, "agent_20", "POST", "http://agent-20-design-fase:8120/palette/create", {"theme": "retro pulp", "faction_count": 4, "restrictions": {"ship": "red fighter"}}),
        Step(2, "agent_21", "POST", "http://agent-21-freecad-parametric:8121/model/build-base", {"category": "fighter", "dimensions": {"length": 10, "radius": 1.2}}),
        Step(3, "agent_22", "POST", "http://agent-22-blender-renderer:8122/render", {}),
        Step(4, "agent_23", "POST", "http://agent-23-aseprite-processor:8123/process", {}),
        Step(5, "agent_24", "POST", "http://agent-24-aseprite-anim-jury:8124/animate/review", {"frames_b64": [_TINY_PNG, _TINY_PNG], "fps_hint": 12.0}),
        Step(6, "agent_25", "POST", "http://agent-25-pyqt-assembly:8125/assemble", {}),
        Step(7, "agent_01_sprite", "POST", "http://sprite-jury-v2:8101/v1/verdict", {"pixel_integrity": 8.0, "jury_scores": [7.5, 8.0]}),
        Step(8, "agent_26", "POST", "http://agent-26-godot-import:8126/import", {"assets": [], "type": "sprite"}),
    ]


def bake_steps() -> List[Step]:
    return [
        Step(1, "agent_13", "POST", "http://agent-13-pdok-downloader:8113/download", {"postcode": "7901", "layers": ["buildings", "roads"]}),
        Step(2, "agent_15", "POST", "http://agent-15-qgis-processor:8115/process", {"operation": "buffer"}),
        Step(3, "agent_31", "POST", "http://agent-31-qgis-analysis:8131/analyze", {}),
        Step(4, "agent_32", "POST", "http://agent-32-grass-gis:8132/analyze", {}),
        Step(5, "agent_14", "POST", "http://agent-14-blender-baker:8114/bake", {"region": "Hoogeveen centrum"}),
        Step(6, "agent_04", "POST", "http://agent-04-3d-model-jury:8104/review", {"job_id": "bake", "artifact": {"mesh_format": "gltf", "vertices": 1200}, "context": {}}),
        Step(7, "agent_05", "POST", "http://agent-05-gis-jury:8105/review", {"job_id": "bake", "artifact": {"crs": "EPSG:28992", "layer_count": 2}, "context": {}}),
        Step(8, "agent_19", "POST", "http://agent-19-distribution:8119/invoke", {"asset_id": "bake-demo", "consumer_id": "nova", "consumer_key": "pipeline-dev-key"}),
    ]


def story_steps() -> List[Step]:
    return [
        Step(1, "agent_28", "POST", "http://agent-28-story-integration:8128/canon/search", {"query": "Cathleen Thael Geode surilians"}),
        Step(2, "agent_07", "POST", "http://agent-07-narrative-jury:8107/invoke", {"job_id": "story", "text": "Cathleen ontmoet Thael in Geode lab", "canon_hits": 2, "voice_profile_matched": True}),
        Step(3, "agent_27", "POST", "http://agent-27-storyboard:8127/storyboard/generate", {"scene_description": "Cathleen ontmoet Thael in Geode lab", "style_bible": "first contact, tentative", "panel_count": 2}),
        Step(4, "agent_08", "POST", "http://agent-08-character-art-jury:8108/review", {"job_id": "story", "artifact": {"image_base64": _TINY_PNG}, "context": {"characters": ["cathleen", "thael"]}}),
        Step(5, "agent_09", "POST", "http://agent-09-illustration-jury:8109/review", {"job_id": "story", "artifact": {"image_base64": _TINY_PNG}, "context": {}}),
        Step(6, "agent_29_reg", "POST", "http://agent-29-elevenlabs:8129/voices/register", {"voice_id": "v_story", "label": "Pipeline", "character_id": "x"}),
        Step(7, "agent_29_tts", "POST", "http://agent-29-elevenlabs:8129/invoke", {"action": "tts", "voice_id": "v_story", "text": "Pipeline validation line."}),
        Step(8, "agent_30", "GET", "http://agent-30-audio-asset-jury:8130/health", None),
        Step(9, "agent_11", "POST", "http://agent-11-monitor:8111/feedback", {"message": "story pipeline validation", "source": "session08"}),
    ]


def run_pipeline(name: str, dry_run: bool, max_retries: int = 2) -> Dict[str, Any]:
    planners = {"shmup": shmup_steps, "bake": bake_steps, "story": story_steps}
    steps = planners[name]()
    run_id = str(uuid.uuid4())
    rec: Dict[str, Any] = {
        "run_id": run_id,
        "pipeline_name": name,
        "dry_run": dry_run,
        "steps": [],
        "totals": {"pending_bridge": 0, "failed": 0, "ok": 0, "latency_ms": 0},
    }
    for st in steps:
        entry: Dict[str, Any] = {
            "step": st.order,
            "agent": st.agent,
            "url": st.url,
            "method": st.method,
        }
        if dry_run:
            entry.update({"skipped": True, "latency_ms": 0, "code": 0, "verdict": "dry_run", "pending_bridge": False})
            rec["steps"].append(entry)
            continue
        attempt = 0
        while attempt <= max_retries:
            attempt += 1
            t0 = time.perf_counter()
            code, raw, parsed = _http_json(st.method, st.url, st.body, st.timeout)
            lat = int((time.perf_counter() - t0) * 1000)
            pb = _pending_bridge(code, parsed)
            fail = code >= 400 and not pb and code != 0
            entry.update(
                {
                    "latency_ms": lat,
                    "code": code,
                    "pending_bridge": pb,
                    "verdict": _verdict_from(parsed),
                    "excerpt": raw[:400] if isinstance(raw, str) else str(raw)[:400],
                    "attempt": attempt,
                }
            )
            if not fail or attempt > max_retries:
                break
        rec["totals"]["latency_ms"] += int(entry.get("latency_ms") or 0)
        if entry.get("pending_bridge"):
            rec["totals"]["pending_bridge"] += 1
        elif int(entry.get("code") or 0) >= 400 or int(entry.get("code") or 0) == 0:
            rec["totals"]["failed"] += 1
        else:
            rec["totals"]["ok"] += 1
        rec["steps"].append(entry)
    # final verdict (live only; dry-run never claims SUCCESS)
    if dry_run:
        rec["final_verdict"] = "DRY_RUN"
    elif rec["totals"]["failed"] > 0:
        rec["final_verdict"] = "FAILED"
    elif rec["totals"]["pending_bridge"] > 0:
        rec["final_verdict"] = "PARTIAL"
    else:
        rec["final_verdict"] = "SUCCESS"
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pipeline", choices=["shmup", "bake", "story", "all"], default="all")
    ap.add_argument("--execute", action="store_true", help="Run HTTP steps (needs reachable URLs or PIPELINE_USE_PUBLISHED_PORTS=1)")
    args = ap.parse_args()
    dry = not args.execute
    names = ["shmup", "bake", "story"] if args.pipeline == "all" else [args.pipeline]
    bundle = {"generated_at": time.time(), "pipelines": {}}
    for n in names:
        bundle["pipelines"][n] = run_pipeline(n, dry_run=dry)
    OUT_JSON.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print("wrote", OUT_JSON.relative_to(ROOT))


if __name__ == "__main__":
    main()
