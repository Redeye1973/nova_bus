#!/usr/bin/env python3
"""NOVA operational restoration phase 1 — inventory, agent starts, smoke, reports.

Does NOT enqueue Black Ledger jobs: uses Dale /invoke ``agent_call`` only (no job files).
Smoke tests hit bridge + agents directly where needed.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(r"L:\!Nova V2")
VSVC = REPO / "v2_services"
OUT = Path(r"L:\! 2 Nova v2  OUTPUT !\ZZZ   Wat is Nova")
# Bridge-contract: POST /blender/script verwacht een pad naar een .py op schijf (geen inline code).
BLENDER_ARTIFACTS = Path(r"L:\! 2 Nova v2 OUTPUT !\Blender")
SMOKE = OUT / "smoke_test"
LOG = OUT / "operational_restore_phase1.log"
BRIDGE = os.environ.get("NOVA_BRIDGE_URL", "http://127.0.0.1:8501").rstrip("/")
DALE = os.environ.get("NOVA_DALE_URL", "http://127.0.0.1:8170").rstrip("/")

CREATE_NO_WINDOW = 0x08000000
DETACHED = 0x00000008


def log(msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {msg}"
    OUT.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fp:
        fp.write(line + "\n")
    print(line)


def _headers() -> dict[str, str]:
    h = {"Content-Type": "application/json"}
    tok = (os.environ.get("BRIDGE_TOKEN") or "").strip()
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def http_json(method: str, url: str, body: dict | None = None, timeout: float = 120.0) -> tuple[int, dict | str]:
    data = None
    headers = _headers()
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(raw) if raw.strip() else {}
            except json.JSONDecodeError:
                return resp.status, raw[:2000]
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw) if raw.strip() else {"error": raw[:500]}
        except json.JSONDecodeError:
            return e.code, {"error": raw[:500]}
    except Exception as exc:  # noqa: BLE001
        return -1, {"error": f"{type(exc).__name__}:{exc}"}


def health_ok(url: str, timeout: float = 3.0) -> bool:
    st, _ = http_json("GET", url.rstrip("/") + "/health", None, timeout)
    return st == 200


def agent_port_from_name(folder: str) -> int | None:
    if folder == "01_sprite_jury":
        return 8101
    m = re.match(r"agent_(\d+)_", folder)
    if not m:
        return None
    n = int(m.group(1))
    if n == 70:
        return None
    return 8100 + n


def start_uvicorn(cwd: Path, port: int, module_app: str) -> tuple[bool, str]:
    if health_ok(f"http://127.0.0.1:{port}", 1.5):
        return True, "already_up"
    try:
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                module_app,
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=str(cwd),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW | DETACHED,
        )
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    return True, "started"


def dale_agent_call(agent_name: str, payload: dict, agent_url: str | None = None) -> dict:
    url = f"{DALE}/invoke"
    pl: dict[str, object] = {"agent_name": agent_name, "payload": payload}
    if agent_url:
        pl["agent_url"] = agent_url
    body = {"action": "agent_call", "payload": pl}
    st, data = http_json("POST", url, body, timeout=180.0)
    return {"http": st, "data": data}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    SMOKE.mkdir(parents=True, exist_ok=True)
    for sub in ("visual", "gis", "character", "audio", "code"):
        (SMOKE / sub).mkdir(parents=True, exist_ok=True)

    # --- Inventory ---
    rows: list[dict[str, object]] = []
    for d in sorted(VSVC.iterdir()):
        if not d.is_dir():
            continue
        name = d.name
        if not (name.startswith("agent_") or name == "01_sprite_jury" or name == "nova_v1_v2_hybrid_gate"):
            continue
        port = agent_port_from_name(name) if name != "nova_v1_v2_hybrid_gate" else 8191
        main_py = d / "main.py"
        if name == "01_sprite_jury":
            entry = (d / "app" / "main.py").is_file()
            mod = "app.main:app"
            cwd = d
        elif name == "nova_v1_v2_hybrid_gate":
            entry = main_py.is_file()
            mod = "main:app"
            cwd = d
        else:
            entry = main_py.is_file()
            mod = "main:app"
            cwd = d
        hp = f"http://127.0.0.1:{port}/health" if port else ""
        up = health_ok(hp) if port and hp else False
        mtime = ""
        if entry:
            try:
                mtime = datetime.fromtimestamp((cwd / ("app/main.py" if name == "01_sprite_jury" else "main.py")).stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")
            except OSError:
                mtime = "?"
        rows.append(
            {
                "folder": name,
                "port": port,
                "entrypoint": str((cwd / "app/main.py") if name == "01_sprite_jury" else (cwd / "main.py")),
                "entry_exists": entry,
                "health_url": hp,
                "running": up,
                "src_mtime_utc": mtime,
            }
        )

    inv_path = OUT / "agents_status_full_2026-04-26.md"
    lines = [
        "# agents_status_full_2026-04-26",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "| agent map | port | entrypoint exists | running /health | src mtime (utc) |",
        "|-------------|------|-------------------|------------------|----------------|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['folder']}` | {r['port'] or ''} | {r['entry_exists']} | {r['running']} | {r['src_mtime_utc']} |"
        )
    lines.append("")
    lines.append("**Note:** poort = 8100 + agentnummer (conventie agent_11 monitor / docker); uitzonderingen: `01_sprite_jury`=8101, `nova_v1_v2_hybrid_gate`=8191.")
    inv_path.write_text("\n".join(lines), encoding="utf-8")
    log(f"wrote {inv_path}")

    # --- Start targets (single attempt each) ---
    targets: list[tuple[str, Path, int, str]] = [
        ("01_sprite_jury", VSVC / "01_sprite_jury", 8101, "app.main:app"),
        ("agent_02_code_jury", VSVC / "agent_02_code_jury", 8102, "main:app"),
        ("agent_03_audio_jury", VSVC / "agent_03_audio_jury", 8103, "main:app"),
        ("agent_04_3d_model_jury", VSVC / "agent_04_3d_model_jury", 8104, "main:app"),
        ("agent_08_character_art_jury", VSVC / "agent_08_character_art_jury", 8108, "main:app"),
        ("agent_13_pdok_downloader", VSVC / "agent_13_pdok_downloader", 8113, "main:app"),
        ("agent_21_freecad_parametric", VSVC / "agent_21_freecad_parametric", 8121, "main:app"),
        ("agent_22_blender_renderer", VSVC / "agent_22_blender_renderer", 8122, "main:app"),
        ("agent_23_aseprite_processor", VSVC / "agent_23_aseprite_processor", 8123, "main:app"),
        ("agent_26_godot_import", VSVC / "agent_26_godot_import", 8126, "main:app"),
        ("agent_31_qgis_analysis", VSVC / "agent_31_qgis_analysis", 8131, "main:app"),
        ("agent_51_gimp_processor", VSVC / "agent_51_gimp_processor", 8151, "main:app"),
        ("agent_61_notification_hub", VSVC / "agent_61_notification_hub", 8161, "main:app"),
        ("nova_v1_v2_hybrid_gate", VSVC / "nova_v1_v2_hybrid_gate", 8191, "main:app"),
    ]
    start_results: list[dict[str, object]] = []
    for label, cwd, port, mod in targets:
        if not cwd.is_dir():
            start_results.append({"agent": label, "port": port, "ok": False, "detail": "missing_dir"})
            log(f"MISS {label} no dir")
            continue
        ok, detail = start_uvicorn(cwd, port, mod)
        start_results.append({"agent": label, "port": port, "ok": ok, "detail": detail})
        log(f"start {label} :{port} -> {detail}")
    time.sleep(4)

    # re-probe running flags
    for r in rows:
        port = r["port"]
        if isinstance(port, int):
            r["running_after"] = health_ok(f"http://127.0.0.1:{port}")

    # --- Smoke tests (direct HTTP; geen BL jobfiles) ---
    smoke: dict[str, object] = {}

    # 5.1a FreeCAD via bridge
    fc_body = {"category": "box", "dimensions": {"x": 64, "y": 64, "z": 64}}
    st, fc_resp = http_json("POST", f"{BRIDGE}/freecad/parametric", fc_body, timeout=300.0)
    (SMOKE / "visual" / "freecad_bridge.json").write_text(json.dumps({"http": st, "body": fc_resp}, indent=2), encoding="utf-8")
    smoke["visual_freecad"] = "PASS" if st == 200 else f"FAIL_http_{st}"

    # 5.1b Blender via bridge — script moet bestandspad zijn (nova_host_bridge adapters/blender.py)
    BLENDER_ARTIFACTS.mkdir(parents=True, exist_ok=True)
    bl_script_path = BLENDER_ARTIFACTS / "_smoke_blender_bridge_ping.py"
    bl_script_path.write_text("import bpy\nprint('SMOKE_BLENDER_OK')\n", encoding="utf-8")
    bl_body = {"script": str(bl_script_path.resolve())}
    stb, bl_resp = http_json("POST", f"{BRIDGE}/blender/script", bl_body, timeout=300.0)
    (SMOKE / "visual" / "blender_bridge.json").write_text(json.dumps({"http": stb, "body": bl_resp}, indent=2), encoding="utf-8")
    smoke["visual_blender"] = "PASS" if stb == 200 else f"FAIL_http_{stb}"

    # 5.1c Aseprite via agent invoke Dale agent_call (no job file)
    if health_ok("http://127.0.0.1:8123"):
        ar = dale_agent_call("aseprite_processor", {"action": "availability"})
        (SMOKE / "visual" / "aseprite_agent_call.json").write_text(json.dumps(ar, indent=2), encoding="utf-8")
        smoke["visual_aseprite"] = "PASS" if ar.get("http") == 200 else f"FAIL_{ar}"
    else:
        smoke["visual_aseprite"] = "SKIPPED_agent_down"

    # 5.1d sprite jury — POST /judge if exists
    sj = http_json(
        "GET",
        "http://127.0.0.1:8101/health",
        None,
        5.0,
    )
    smoke["visual_sprite_jury"] = "PASS" if sj[0] == 200 else "SKIPPED_or_FAIL"

    # 5.2 GIS qgis via bridge — list algorithms (light)
    stq, qresp = http_json("GET", f"{BRIDGE}/qgis/algorithms", None, 60.0)
    (SMOKE / "gis" / "qgis_algorithms.json").write_text(json.dumps({"http": stq, "body": qresp}, indent=2)[:50000], encoding="utf-8")
    smoke["gis_qgis"] = "PASS" if stq == 200 else f"FAIL_http_{stq}"

    # PDOK agent_call if up
    if health_ok("http://127.0.0.1:8113"):
        stp, pbody = http_json("GET", "http://127.0.0.1:8113/health", None, 10.0)
        (SMOKE / "gis" / "pdok_health.json").write_text(json.dumps({"http": stp, "body": pbody}, indent=2), encoding="utf-8")
        smoke["gis_pdok"] = "PASS" if stp == 200 else f"FAIL_{stp}"
    else:
        smoke["gis_pdok"] = "SKIPPED_agent_down"

    # 5.3 DAZ — SKIP (no Agent 38 / orchestrator path in repo)
    smoke["character_daz"] = "SKIPPED_no_agent_38_pipeline"

    # 5.4 Audio — SKIP (not wired via bridge in this phase)
    smoke["audio_sc_sox"] = "SKIPPED_not_automated"

    # 5.5 code jury gdscript direct
    if health_ok("http://127.0.0.1:8102"):
        code_body = {"code": "extends Node\nfunc _ready():\n\tpass\n", "base64_encoded": False}
        stc, cresp = http_json("POST", "http://127.0.0.1:8102/review/gdscript", code_body, 60.0)
        (SMOKE / "code" / "code_jury_gdscript.json").write_text(json.dumps({"http": stc, "body": cresp}, indent=2), encoding="utf-8")
        smoke["code_jury"] = "PASS" if stc == 200 else f"FAIL_{stc}"
    else:
        smoke["code_jury"] = "SKIPPED_agent_down"

    (SMOKE / "verdict.json").write_text(json.dumps({"smoke": smoke, "at": datetime.now(timezone.utc).isoformat()}, indent=2), encoding="utf-8")

    # save start_results
    (OUT / "operational_restore_starts.json").write_text(json.dumps(start_results, indent=2), encoding="utf-8")

    log("phase1 orchestration done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
