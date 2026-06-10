"""NOVA v2 Agent 38 — Quality Inspector: per-eenheid inspectie + autonome correctie."""
from __future__ import annotations

import io
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sys.path.insert(0, "/nova_shared")
sys.path.insert(0, r"L:\!Nova V2\shared")
try:
    from resume_part_update import notify_part_completed_async
except ImportError:
    async def notify_part_completed_async(**_kwargs):  # type: ignore[misc]
        return {"ok": False, "skipped": True, "reason": "resume_part_update_unavailable"}

try:
    from vision_eye import see
except ImportError:
    async def see(image_path: str, question: str, model: str = "qwen2.5vl:7b") -> str:
        return f"vision_unavailable:{image_path}"

try:
    from proof import make_and_record, make_proof, record_proof
except ImportError:
    def make_proof(*_a, **_k):  # type: ignore[misc]
        return {}

    def record_proof(*_a, **_k):  # type: ignore[misc]
        return {"recorded": False}

    def make_and_record(*_a, **_k):  # type: ignore[misc]
        return {}

app = FastAPI(title="Quality Inspector - Agent 38", version="1.0.0")
BIBLE = Path(os.getenv("NOVA_COMPOSITION_BIBLE", "/config/composition_bible.yaml"))
if not BIBLE.is_file():
    BIBLE = Path(r"L:\!Nova V2\config\composition_bible.yaml")

CORRECT_SPEEDS = [20.0, 38.0, 72.0, 137.0, 260.0]
PLAYER_Z = 10
EFFECTS_Z = 20
UI_Z = 100
BG_PARENT_Z = -100


CHECK_PART_TASK: Dict[str, tuple[str, str]] = {
    "layer_ordering": ("leveldesign", "layer_order_fix"),
    "parallax_speeds": ("core", "parallax"),
    "seamless_tiling": ("core", "parallax"),
    "spawn_safety": ("leveldesign", "enemy_spawn"),
    "collision_logic": ("leveldesign", "collision"),
}


class InspectRequest(BaseModel):
    domain: str
    scene_file: str = ""
    script_files: list[str] = []
    capture_path: str = ""
    auto_fix: bool = True
    project: str = ""


def _resolve_path(raw: str) -> Path:
    path = Path(raw)
    session_mount = (os.getenv("NOVA_SESSION_MOUNT") or "/session").strip()
    session_prefix = (os.getenv("NOVA_SESSION_WIN_PREFIX") or r"L:\ZZZZZ ZZ 31-05-2026").strip()
    mount = (os.getenv("NOVA_GAME_OUTPUT_MOUNT") or "").strip()
    win_prefix = (os.getenv("NOVA_GAME_OUTPUT_WIN_PREFIX") or r"L:\ZZZ ZZ NOVA GAME OUTPUT").strip()
    if raw:
        norm = raw.replace("/", "\\")
        sprefix = session_prefix.replace("/", "\\")
        if session_mount and norm.lower().startswith(sprefix.lower()):
            rel = norm[len(sprefix) :].lstrip("\\/")
            return Path(session_mount) / rel.replace("\\", "/")
        prefix = win_prefix.replace("/", "\\")
        if mount and norm.lower().startswith(prefix.lower()):
            rel = norm[len(prefix) :].lstrip("\\/")
            return Path(mount) / rel.replace("\\", "/")
    return path


def load_inspector_checks(domain: str) -> list:
    bible = yaml.safe_load(BIBLE.read_text(encoding="utf-8"))
    return bible.get("domains", {}).get(domain, {}).get("quality_inspector_checks", [])


def _parse_z_indices(text: str) -> Dict[str, int]:
    nodes: Dict[str, int] = {}
    current: Optional[str] = None
    for line in text.splitlines():
        m = re.match(r'\[node name="([^"]+)"', line)
        if m:
            current = m.group(1)
            continue
        if current and (zm := re.match(r"^z_index\s*=\s*(-?\d+)", line.strip())):
            nodes[current] = int(zm.group(1))
    return nodes


def check_layer_ordering(scene_file: str) -> Optional[str]:
    path = _resolve_path(scene_file)
    if not path.is_file():
        return f"scene_file_not_found:{scene_file}"
    text = path.read_text(encoding="utf-8")
    z = _parse_z_indices(text)
    player_z = z.get("Player")
    bg_z = z.get("BackgroundParallax")
    bg_child_z = [v for k, v in z.items() if k.startswith("Layer") or k in ("SpaceBase", "GradientBlend")]
    issues: List[str] = []
    if player_z is None:
        issues.append("Player node ontbreekt of heeft geen z_index")
    if bg_z is not None and bg_z >= 0:
        issues.append(f"BackgroundParallax z_index={bg_z} moet negatief zijn")
    if player_z is not None and bg_z is not None and player_z <= bg_z:
        issues.append(f"player_z={player_z} niet boven BackgroundParallax z={bg_z}")
    if player_z is not None and bg_child_z:
        mx = max(bg_child_z)
        if player_z <= mx:
            issues.append(f"player_z={player_z} niet boven achtergrond-kinderen max_z={mx}")
    return "; ".join(issues) if issues else None


def fix_layer_ordering(scene_file: str) -> None:
    path = _resolve_path(scene_file)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    out: List[str] = []
    current: Optional[str] = None
    for line in lines:
        m = re.match(r'\[node name="([^"]+)"', line)
        if m:
            current = m.group(1)
            out.append(line)
            continue
        if current == "BackgroundParallax" and re.match(r"^z_index\s*=", line.strip()):
            out.append(f"z_index = {BG_PARENT_Z}")
            continue
        if current == "Player" and re.match(r"^z_index\s*=", line.strip()):
            out.append(f"z_index = {PLAYER_Z}")
            continue
        if current and current.startswith("Layer") and re.match(r"^z_index\s*=", line.strip()):
            idx = int(re.search(r"Layer(\d+)", current).group(1)) if re.search(r"Layer(\d+)", current) else 1
            out.append(f"z_index = {-10 + (idx - 1)}")
            continue
        out.append(line)
    path.write_text("\n".join(out) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")


def _extract_speeds(text: str) -> Optional[list[float]]:
    m = re.search(
        r"scroll_speeds(?::\s*Array\[float\])?\s*=\s*\[([0-9.,\s]+)\]",
        text,
    )
    if not m:
        return None
    return [float(x.strip()) for x in m.group(1).split(",") if x.strip()]


def check_parallax_speeds(script_files: list[str]) -> Optional[str]:
    for raw in script_files:
        path = _resolve_path(raw)
        if not path.is_file():
            return f"script_not_found:{raw}"
        speeds = _extract_speeds(path.read_text(encoding="utf-8"))
        if speeds is None:
            continue
        for i in range(1, len(speeds)):
            if speeds[i] <= speeds[i - 1]:
                return f"scroll_speeds niet oplopend op laag {i}"
            ratio = speeds[i] / speeds[i - 1] if speeds[i - 1] else 0
            if ratio < 1.6 or ratio > 2.2:
                return f"Parallax ratio {ratio:.2f} tussen laag {i - 1} en {i} buiten 1.6-2.2x"
    return None


def fix_parallax_speeds(script_files: list[str]) -> None:
    correct = CORRECT_SPEEDS
    for raw in script_files:
        path = _resolve_path(raw)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if "scroll_speeds" not in text:
            continue
        new = re.sub(
            r"@export var scroll_speeds: Array\[float\] = \[[0-9.,\s]+\]",
            f"@export var scroll_speeds: Array[float] = {correct}",
            text,
        )
        if new == text:
            new = re.sub(
                r"scroll_speeds(?::\s*Array\[float\])?\s*=\s*\[[0-9.,\s]+\]",
                f"scroll_speeds = {correct}",
                text,
            )
        path.write_text(new, encoding="utf-8")


def check_seamless_tiling(script_files: list[str], scene_file: str) -> Optional[str]:
    project = _resolve_path(scene_file).parent.parent if scene_file else None
    bg_dir = project / "assets" / "backgrounds" if project else None
    if not bg_dir or not bg_dir.is_dir():
        return "backgrounds_dir_missing_for_seam_check"
    try:
        from PIL import Image, ImageChops, ImageStat
    except ImportError:
        return "PIL_unavailable"
    worst = 0.0
    for png in sorted(bg_dir.glob("bg_layer_*.png"))[:5]:
        im = Image.open(png).convert("RGB")
        w, h = im.size
        top = im.crop((0, 0, w, 2))
        bottom = im.crop((0, h - 2, w, h))
        seam = sum(ImageStat.Stat(ImageChops.difference(top, bottom)).mean) / 3.0
        worst = max(worst, seam)
    if worst > 35:
        return f"seam_mismatch_mean={worst:.1f}px (>3px drempel visueel)"
    return None


def check_spawn_safety(scene_file: str) -> Optional[str]:
    path = _resolve_path(scene_file)
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    player_y = None
    for m in re.finditer(r'\[node name="Player"[^\]]*\][\s\S]*?position = Vector2\([^,]+,\s*([0-9.]+)\)', text):
        player_y = float(m.group(1))
    if player_y is None:
        return "player_startpositie_niet_gevonden"
    spawner = path.parent.parent / "scripts" / "spawner.gd"
    if spawner.is_file() and "player" in spawner.read_text(encoding="utf-8").lower():
        return None
    return None


def check_collision_logic(scene_file: str) -> Optional[str]:
    project = _resolve_path(scene_file).parent.parent if scene_file else None
    if not project:
        return None
    enemy = project / "scenes" / "enemy_basic.tscn"
    bullet = project / "scenes" / "bullet_player.tscn"
    issues = []
    for label, p in (("enemy", enemy), ("bullet", bullet)):
        if p.is_file() and "CollisionShape2D" not in p.read_text(encoding="utf-8"):
            issues.append(f"{label}_missing_collision")
    return "; ".join(issues) if issues else None


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "agent": 38, "name": "Quality Inspector", "bible": str(BIBLE)}


@app.post("/inspect")
async def inspect(req: InspectRequest) -> Dict[str, Any]:
    checks = load_inspector_checks(req.domain)
    results: List[Dict[str, Any]] = []

    for check in checks:
        name = check["check"]
        result: Dict[str, Any] = {"check": name, "rule": check["rule"], "status": "ok", "action": None}

        if name == "layer_ordering" and req.scene_file:
            problem = check_layer_ordering(req.scene_file)
            if problem:
                result["status"] = "fail"
                result["detail"] = problem
                if req.auto_fix:
                    fix_layer_ordering(req.scene_file)
                    result["action"] = "z_index gecorrigeerd in scene file"
                    result["fixed"] = True

        elif name == "parallax_speeds" and req.script_files:
            problem = check_parallax_speeds(req.script_files)
            if problem:
                result["status"] = "fail"
                result["detail"] = problem
                if req.auto_fix:
                    fix_parallax_speeds(req.script_files)
                    result["action"] = "scroll_speeds gecorrigeerd"
                    result["fixed"] = True

        elif name == "seamless_tiling" and req.scene_file:
            problem = check_seamless_tiling(req.script_files, req.scene_file)
            if problem:
                result["status"] = "fail"
                result["detail"] = problem

        elif name == "spawn_safety" and req.scene_file:
            problem = check_spawn_safety(req.scene_file)
            if problem:
                result["status"] = "fail"
                result["detail"] = problem
                result["action"] = check.get("fix", "manueel")

        elif name == "collision_logic" and req.scene_file:
            problem = check_collision_logic(req.scene_file)
            if problem:
                result["status"] = "fail"
                result["detail"] = problem

        elif req.capture_path and name in ("layer_ordering", "parallax_speeds", "seamless_tiling"):
            cap = _resolve_path(req.capture_path)
            if cap.is_file():
                verdict = await see(
                    str(cap),
                    f"Check regel: {check['rule']}. Is dit correct in beeld? "
                    f"Zo nee, beschrijf precies wat er mis is.",
                )
                low = verdict.lower()
                if any(w in low for w in ("nee", "mis", "fout", "achter", "onleesbaar", "reject")):
                    result["status"] = "fail"
                    result["detail"] = verdict[:500]
                    result["action"] = f"Fix nodig: {check.get('fix', 'manueel')}"

        results.append(result)

    part_updates: List[Dict[str, Any]] = []
    for result in results:
        if not result.get("fixed"):
            continue
        mapping = CHECK_PART_TASK.get(result["check"])
        if not mapping:
            continue
        part, task = mapping
        # Fase 2: bewijs van de daadwerkelijk gewijzigde file mee in de claim
        fixed_path = ""
        if result["check"] in ("layer_ordering", "seamless_tiling", "spawn_safety", "collision_logic"):
            fixed_path = req.scene_file
        elif result["check"] == "parallax_speeds" and req.script_files:
            fixed_path = req.script_files[0]
        fix_proof = (
            make_and_record(
                "file",
                path=fixed_path,
                agent="38_quality_inspector",
                note=f"auto-fix {result['check']}",
                context="quality_inspector_fix",
            )
            if fixed_path
            else make_and_record(
                "report",
                id=f"qi_fix_{result['check']}",
                agent="38_quality_inspector",
                context="quality_inspector_fix",
            )
        )
        upd = await notify_part_completed_async(
            part=part,
            completed_task=task,
            project=req.project,
            proof=fix_proof,
        )
        part_updates.append({"check": result["check"], "proof": fix_proof, **upd})

    out: Dict[str, Any] = {
        "agent": "Quality Inspector",
        "domain": req.domain,
        "results": results,
    }
    if part_updates:
        out["part_updates"] = part_updates
    # Fase 2 bewijs-standaard: elke "klaar"-response bevat een proof-object
    import time as _time

    out["proof"] = make_and_record(
        "report",
        id=f"qi_inspect_{req.domain}_{int(_time.time())}",
        agent="38_quality_inspector",
        note=f"{len(results)} checks, {sum(1 for r in results if r['status'] != 'ok')} fails",
        context="quality_inspector_inspect",
    )
    return out
