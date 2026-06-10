"""NOVA v2 Agent 40 — Juice Inspector (game feel + GDScript snippets)."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml
from fastapi import FastAPI
from pydantic import BaseModel

sys.path.insert(0, "/nova_shared")
sys.path.insert(0, r"L:\!Nova V2\shared")
try:
    from resume_part_update import notify_part_completed
except ImportError:
    def notify_part_completed(**_kwargs):  # type: ignore[misc]
        return {"ok": False, "skipped": True, "reason": "resume_part_update_unavailable"}

try:
    from proof import make_and_record
except ImportError:
    def make_and_record(*_a, **_k):  # type: ignore[misc]
        return {}

EFFECT_TO_TASK = {
    "screen_shake": "screen_shake",
    "hit_flash": "hit_flash",
    "knockback": "knockback",
    "explosion_particles": "particles",
    "hit_stop": "hit_stop",
    "muzzle_flash": "muzzle_flash",
    "pickup_pop": "pickup_pop",
    "weapon_weight": "shooting",
}

app = FastAPI(title="Juice Inspector - Agent 40", version="1.0.0")

AGENT_ID = 40
BIBLE = Path(os.getenv("NOVA_JUICE_BIBLE", "/config/juice_bible.yaml"))
if not BIBLE.is_file():
    BIBLE = Path(r"L:\!Nova V2\config\juice_bible.yaml")


class JuiceRequest(BaseModel):
    domain: str = "shmup"
    project_dir: str = ""
    scripts: list[str] = []
    auto_inject: bool = False
    project: str = ""


def load_juice(domain: str) -> dict:
    bible = yaml.safe_load(BIBLE.read_text(encoding="utf-8"))
    return bible.get("domains", {}).get(domain, {})


def generate_snippet(effect_name: str) -> str:
    snippets = {
        "screen_shake": """
# Voeg toe aan een Camera2D node of autoload
var shake_amount = 0.0
func _process(delta):
    if shake_amount > 0:
        offset = Vector2(randf_range(-shake_amount,shake_amount), randf_range(-shake_amount,shake_amount))
        shake_amount = max(shake_amount - delta * 40, 0)
func shake(amount): shake_amount = amount  # roep aan bij explosie: camera.shake(8)
""",
        "hit_flash": """
# Voeg toe aan enemy/player script
func flash():
    modulate = Color(4,4,4)  # fel wit
    var t = create_tween()
    t.tween_property(self, "modulate", Color(1,1,1), 0.1)
""",
        "knockback": """
func apply_knockback(dir: Vector2, force: float = 20.0):
    position += dir.normalized() * force
""",
        "explosion_particles": """
# Maak een Explosion.tscn met GPUParticles2D (one_shot=true)
const EXPLOSION = preload("res://scenes/explosion.tscn")
func spawn_explosion(pos):
    var e = EXPLOSION.instantiate()
    e.position = pos
    get_tree().current_scene.add_child(e)
    e.emitting = true
""",
        "hit_stop": """
func hit_stop(duration: float = 0.05):
    Engine.time_scale = 0.05
    await get_tree().create_timer(duration * 0.05).timeout
    Engine.time_scale = 1.0
""",
        "muzzle_flash": """
# Korte flits bij schietpunt
func muzzle_flash(pos):
    var flash = Sprite2D.new()
    # ... set texture, add_child, tween modulate alpha naar 0 in 0.05s
""",
        "pickup_pop": """
func pickup_pop():
    var t = create_tween()
    scale = Vector2(1.4,1.4)
    t.tween_property(self,"scale",Vector2(1,1),0.15)
""",
        "weapon_weight": """
# Camera kick tegengesteld aan schietrichting
func weapon_kick(camera, dir): camera.offset -= dir.normalized() * 3
""",
    }
    return snippets.get(effect_name, "# TODO")


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "agent": AGENT_ID,
        "name": "Juice Inspector",
        "port": 8140,
        "bible": str(BIBLE),
    }


@app.post("/inspect")
def inspect(req: JuiceRequest) -> Dict[str, Any]:
    juice = load_juice(req.domain)
    required = juice.get("required_juice", [])
    findings: List[Dict[str, Any]] = []

    all_code = ""
    for script_path in req.scripts:
        path = Path(script_path)
        if path.is_file():
            all_code += path.read_text(encoding="utf-8").lower()

    for effect in required:
        name = effect["effect"]
        present = name.replace("_", " ") in all_code or name in all_code
        keyword = name.split("_")[0]
        present = present or keyword in all_code
        if not present:
            findings.append(
                {
                    "missing": name,
                    "trigger": effect["trigger"],
                    "rule": effect["rule"],
                    "godot_impl": effect["godot_impl"],
                    "snippet": generate_snippet(name),
                }
            )

    import time as _time

    return {
        "agent": "Juice Inspector",
        "agent_id": AGENT_ID,
        "domain": req.domain,
        "missing_count": len(findings),
        "findings": findings,
        "director_checks": juice.get("director_checks", []),
        "proof": make_and_record(
            "report",
            id=f"juice_inspect_{req.domain}_{int(_time.time())}",
            agent="40_juice_inspector",
            note=f"{len(findings)} ontbrekende juice-effecten",
            context="juice_inspector_inspect",
        ),
    }


@app.post("/inject")
def inject(req: JuiceRequest) -> Dict[str, Any]:
    """Schrijf snippets als commentaarblok onderaan scripts (geen blind overschrijven)."""
    result = inspect(req)
    injected: list[str] = []
    if req.auto_inject:
        for script_path in req.scripts:
            path = Path(script_path)
            if path.is_file():
                block = "\n\n# ===== JUICE INSPECTOR — ontbrekende effecten =====\n"
                for finding in result["findings"]:
                    effect = finding["missing"]
                    block += f"# --- {effect} ({finding['trigger']}) ---\n"
                    block += "".join("# " + line + "\n" for line in finding["snippet"].splitlines())
                    injected.append(effect)
                if block.strip():
                    path.write_text(path.read_text(encoding="utf-8") + block, encoding="utf-8")
    part_updates: list[Dict[str, Any]] = []
    for effect in injected:
        task = EFFECT_TO_TASK.get(effect)
        if not task:
            continue
        # Fase 2: bewijs van het daadwerkelijk gewijzigde script
        inject_proof = (
            make_and_record(
                "file",
                path=req.scripts[0],
                agent="40_juice_inspector",
                note=f"juice inject {effect}",
                context="juice_inspector_inject",
            )
            if req.scripts
            else make_and_record(
                "report",
                id=f"juice_inject_{effect}",
                agent="40_juice_inspector",
                context="juice_inspector_inject",
            )
        )
        part_updates.append(
            {
                "effect": effect,
                "proof": inject_proof,
                **notify_part_completed(
                    part="juice",
                    completed_task=task,
                    project=req.project,
                    proof=inject_proof,
                ),
            }
        )
    if part_updates:
        result["part_updates"] = part_updates
        result["injected_effects"] = injected
    return result
