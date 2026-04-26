"""
NOVA F-15 — Blue Angels skin variant.

GEEN tekst-markings (skip text-objects volledig).
Kleurschema: U.S. Navy Blue Angels — donkerblauw met geel accent.

Geel accent automatisch op:
  - Wing-tips (Y-extreme)
  - Tail-tops (Z-extreme van vertical tails)
  - Cockpit-canopy rand
  - Engine outlets

Output naar VERSIONED directory:
  F15_OUTPUT_DIR/blue_angels/run_001/
  F15_OUTPUT_DIR/blue_angels/run_002/
  ...
Auto-detect volgende vrije nummer.
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector


# ============================================================
# VERSIONED OUTPUT DIR
# ============================================================

OUTPUT_BASE = Path(os.environ.get(
    "F15_OUTPUT_DIR",
    r"L:\! 2 Nova v2 OUTPUT !\Ship_F15_v4"
))
STL_PATH = OUTPUT_BASE / "01_freecad" / "f15_v4.stl"

VARIANT_BASE = OUTPUT_BASE / "blue_angels"
VARIANT_BASE.mkdir(parents=True, exist_ok=True)


def next_run_dir(base: Path) -> tuple[Path, int]:
    """Vind volgende run_NNN directory die nog niet bestaat."""
    existing: list[int] = []
    pattern = re.compile(r"^run_(\d{3})$")
    if base.exists():
        for child in base.iterdir():
            if child.is_dir():
                m = pattern.match(child.name)
                if m:
                    existing.append(int(m.group(1)))
    next_num = (max(existing) + 1) if existing else 1
    run_dir = base / f"run_{next_num:03d}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir, next_num


RUN_DIR, RUN_NUM = next_run_dir(VARIANT_BASE)
print(f"[blue_angels] Run #{RUN_NUM} → {RUN_DIR}")

RENDER_RESOLUTION = 1024


# ============================================================
# COLOR PALETTE — Blue Angels
# ============================================================

NAVY_BLUE = (0.05, 0.10, 0.35, 1.0)
NAVY_BLUE_DARKER = (0.03, 0.06, 0.22, 1.0)
ACCENT_YELLOW = (1.00, 0.78, 0.05, 1.0)
CANOPY_DARK = (0.08, 0.08, 0.15, 1.0)


# ============================================================
# SCENE INIT
# ============================================================

def clean_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.meshes):
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in list(bpy.data.materials):
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in list(bpy.data.images):
        if block.users == 0 and block.name not in ("Render Result", "Viewer Node"):
            bpy.data.images.remove(block)


def import_stl(stl_path: Path):
    if not stl_path.is_file():
        raise FileNotFoundError(f"STL not found: {stl_path}")
    try:
        bpy.ops.wm.stl_import(filepath=str(stl_path))
    except AttributeError:
        bpy.ops.import_mesh.stl(filepath=str(stl_path))
    obj = bpy.context.selected_objects[0]
    obj.name = "F15_Body"
    return obj


def cleanup_mesh(obj) -> None:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.delete_loose()
    bmesh.update_edit_mesh(obj.data)
    bm = bmesh.from_edit_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.5)
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def center_and_scale(obj) -> None:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    obj.location = (0, 0, 0)
    obj.scale = (0.001, 0.001, 0.001)
    bpy.ops.object.transform_apply(scale=True)


# ============================================================
# MATERIALS
# ============================================================

def make_navy_blue_paint():
    mat = bpy.data.materials.new(name="BlueAngels_Body")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    bsdf.inputs["Base Color"].default_value = NAVY_BLUE
    bsdf.inputs["Metallic"].default_value = 0.15
    bsdf.inputs["Roughness"].default_value = 0.35

    geom = nodes.new("ShaderNodeNewGeometry")
    geom.location = (-300, -200)

    edge_ramp = nodes.new("ShaderNodeValToRGB")
    edge_ramp.location = (0, -200)
    edge_ramp.color_ramp.elements[0].position = 0.5
    edge_ramp.color_ramp.elements[0].color = NAVY_BLUE
    edge_ramp.color_ramp.elements[1].position = 0.7
    edge_ramp.color_ramp.elements[1].color = (0.10, 0.18, 0.50, 1.0)

    links.new(geom.outputs["Pointiness"], edge_ramp.inputs["Fac"])
    links.new(edge_ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat


def make_navy_blue_belly():
    mat = bpy.data.materials.new(name="BlueAngels_Belly")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = NAVY_BLUE_DARKER
        bsdf.inputs["Metallic"].default_value = 0.10
        bsdf.inputs["Roughness"].default_value = 0.45
    return mat


def make_yellow_accent():
    mat = bpy.data.materials.new(name="BlueAngels_Yellow")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = ACCENT_YELLOW
        bsdf.inputs["Metallic"].default_value = 0.10
        bsdf.inputs["Roughness"].default_value = 0.30
    return mat


def make_canopy_dark():
    mat = bpy.data.materials.new(name="BlueAngels_Canopy")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = CANOPY_DARK
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Roughness"].default_value = 0.05
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 0.2
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = 0.2
    return mat


def make_intake_dark():
    mat = bpy.data.materials.new(name="BlueAngels_DarkHole")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.02, 0.02, 0.04, 1.0)
        bsdf.inputs["Roughness"].default_value = 1.0
    return mat


# ============================================================
# MULTI-MATERIAL ASSIGNMENT
# ============================================================

def assign_materials_blue_angels(obj) -> dict[str, object]:
    """Wijs materialen toe; return face-counts + bbox voor rapport."""
    me = obj.data

    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    z_min, z_max = min(zs), max(zs)

    y_span = y_max - y_min
    z_span = z_max - z_min

    wing_tip_threshold = y_span * 0.06
    tail_top_threshold = z_span * 0.15
    x_span = x_max - x_min
    # Alleen echte uitlaatzone (achterste ~2% X), niet hele staart
    outlet_x_cut = x_min + x_span * 0.02

    mats = {
        "body": make_navy_blue_paint(),
        "belly": make_navy_blue_belly(),
        "yellow": make_yellow_accent(),
        "canopy": make_canopy_dark(),
        "dark": make_intake_dark(),
    }

    obj.data.materials.clear()
    indices: dict[str, int] = {}
    for i, (key, m) in enumerate(mats.items()):
        obj.data.materials.append(m)
        indices[key] = i

    yellow_count = 0
    canopy_count = 0
    dark_count = 0
    belly_count = 0
    body_count = 0

    for face in me.polygons:
        cx = sum(me.vertices[v].co.x for v in face.vertices) / len(face.vertices)
        cy = sum(me.vertices[v].co.y for v in face.vertices) / len(face.vertices)
        cz = sum(me.vertices[v].co.z for v in face.vertices) / len(face.vertices)

        _nx, _ny, nz = face.normal

        # Canopy volume (v4 cockpit ~ +X midden; Z boven romp)
        if 1.0 < cx < 5.5 and cz > 1.25:
            face.material_index = indices["canopy"]
            canopy_count += 1
            continue

        # Wing-tips: extreme Y, romp-/vleugelhoogte (brede Z-band)
        if (cy < y_min + wing_tip_threshold or cy > y_max - wing_tip_threshold) and 0.45 < cz < 2.1:
            face.material_index = indices["yellow"]
            yellow_count += 1
            continue

        # Verticale staarttoppen: hoog Z, relatief smal in Y
        if cz > z_max - tail_top_threshold and abs(cy) < 2.0:
            face.material_index = indices["yellow"]
            yellow_count += 1
            continue

        # Canopy-rand (geel accent net buiten donkere canopy-X-band)
        if cz > 1.2 and ((0.9 < cx < 1.25) or (5.2 < cx < 5.8)) and abs(cy) < 0.85:
            face.material_index = indices["yellow"]
            yellow_count += 1
            continue

        if 0 < cx < 3 and cz < 1.1 and abs(cy) > 0.5:
            face.material_index = indices["dark"]
            dark_count += 1
            continue

        # Uitlaten: achterste stuk X + relatief laag (nacelle)
        if cx < outlet_x_cut and cz < 1.35:
            face.material_index = indices["dark"]
            dark_count += 1
            continue

        if nz < -0.3:
            face.material_index = indices["belly"]
            belly_count += 1
            continue

        face.material_index = indices["body"]
        body_count += 1

    print("[blue_angels] Material distribution:")
    print(f"  body (navy):    {body_count}")
    print(f"  belly:          {belly_count}")
    print(f"  yellow accent:  {yellow_count}")
    print(f"  canopy:         {canopy_count}")
    print(f"  dark:           {dark_count}")

    return {
        "faces_body": body_count,
        "faces_belly": belly_count,
        "faces_yellow": yellow_count,
        "faces_canopy": canopy_count,
        "faces_dark": dark_count,
        "faces_total": len(me.polygons),
        "bbox_x": (round(x_min, 4), round(x_max, 4)),
        "bbox_y": (round(y_min, 4), round(y_max, 4)),
        "bbox_z": (round(z_min, 4), round(z_max, 4)),
    }


def write_run_report(
    run_dir: Path,
    run_num: int,
    face_stats: dict[str, object],
    info: dict[str, object],
    stl_path: Path,
) -> None:
    """Mens-leesbaar rapport in dezelfde map als renders/GLB."""
    lines = [
        "# F-15 — Blue Angels variant (runrapport)\n\n",
        f"- **Run:** `run_{run_num:03d}`\n",
        f"- **Map:** `{run_dir}`\n",
        f"- **Bron-STL:** `{stl_path}`\n",
        f"- **Resolutie renders:** {RENDER_RESOLUTION}² px, Cycles 64 spp, denoise aan\n",
        "- **Tekst-markings:** geen (bewust)\n\n",
        "## Kleurpalet (RGBA)\n\n",
        f"- Navy body: `{NAVY_BLUE}`\n",
        f"- Navy belly: `{NAVY_BLUE_DARKER}`\n",
        f"- Accent geel: `{ACCENT_YELLOW}`\n",
        f"- Canopy donker: `{CANOPY_DARK}`\n\n",
        "## Mesh (na cleanup + schaal 0.001)\n\n",
        f"- Vertices: **{info.get('vertices')}**\n",
        f"- Faces: **{info.get('polygons')}**\n",
        f"- Material slots op mesh: **{info.get('materials')}**\n\n",
        "## Face-verdeling (heuristisch)\n\n",
        "| Slot | Faces | Opmerking |\n",
        "|------|------:|-----------|\n",
        f"| Navy body | {face_stats['faces_body']} | hoofdromp |\n",
        f"| Navy belly | {face_stats['faces_belly']} | nz < -0.3 |\n",
        f"| Geel accent | {face_stats['faces_yellow']} | wing-tips / tail-tops / canopy-rand |\n",
        f"| Canopy | {face_stats['faces_canopy']} | cockpitvolume |\n",
        f"| Dark (intake/outlet) | {face_stats['faces_dark']} | intakes + achterste X-band |\n",
        f"| **Totaal** | **{face_stats['faces_total']}** | |\n\n",
        "## Bounding box (m, na center+scale)\n\n",
        f"- X: {face_stats['bbox_x']}\n",
        f"- Y: {face_stats['bbox_y']}\n",
        f"- Z: {face_stats['bbox_z']}\n\n",
        "## Outputbestanden\n\n",
        "- `f15_blue_angels_topdown.png`\n",
        "- `f15_blue_angels_front.png`\n",
        "- `f15_blue_angels_side.png`\n",
        "- `f15_blue_angels_threequarter.png`\n",
        "- `f15_blue_angels_hero.png`\n",
        "- `f15_blue_angels.glb`\n",
        "- `run_info.json` (machine)\n",
        "- `blue_angels_report.md` (dit bestand)\n\n",
        "## Open punten\n\n",
        "- Geel/canopy zijn positie-gebaseerd; bij mesh-wijziging thresholds evt. tunen.\n",
        "- Geen officiële Blue Angels-markings (nummers); alleen kleur + geometry-accenten.\n",
    ]
    (run_dir / "blue_angels_report.md").write_text("".join(lines), encoding="utf-8")
    print(f"[blue_angels] Report: {run_dir / 'blue_angels_report.md'}")


def write_runs_index(variant_base: Path) -> None:
    """Overzicht van alle run_* onder blue_angels/."""
    rows = ["# Blue Angels — alle runs\n\n", "| Run | Pad |\n|-----|-----|\n"]
    for p in sorted(variant_base.glob("run_*")):
        if p.is_dir():
            rows.append(f"| `{p.name}` | `{p}` |\n")
    rows.append(
        "\nPer run: `blue_angels_report.md`, `run_info.json`, PNG’s, GLB.\n"
    )
    (variant_base / "runs_index.md").write_text("".join(rows), encoding="utf-8")


# ============================================================
# LIGHTING + WORLD
# ============================================================

def setup_lighting() -> None:
    bpy.ops.object.light_add(type="SUN", location=(15, -10, 20))
    key = bpy.context.active_object
    key.data.energy = 4.5
    key.rotation_euler = (math.radians(45), math.radians(20), math.radians(45))

    bpy.ops.object.light_add(type="AREA", location=(-15, 10, 8))
    fill = bpy.context.active_object
    fill.data.energy = 250
    fill.data.size = 12

    bpy.ops.object.light_add(type="AREA", location=(-20, 0, 10))
    rim = bpy.context.active_object
    rim.data.energy = 150
    rim.data.size = 8


def setup_world() -> None:
    world = bpy.context.scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.55, 0.70, 0.88, 1)
    bg.inputs["Strength"].default_value = 0.4


# ============================================================
# RENDER
# ============================================================

def setup_render_settings() -> None:
    scene = bpy.context.scene
    scene.render.resolution_x = RENDER_RESOLUTION
    scene.render.resolution_y = RENDER_RESOLUTION
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False

    try:
        scene.render.engine = "CYCLES"
        scene.cycles.samples = 64
        scene.cycles.use_denoising = True
    except Exception:
        scene.render.engine = "BLENDER_EEVEE_NEXT"


def render_view(
    name: str,
    location: tuple,
    look_at: tuple = (0, 0, 1.5),
    *,
    is_ortho: bool = False,
    ortho_scale: float = 25,
    lens: float = 70,
) -> None:
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.active_object
    if is_ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho_scale
    else:
        cam.data.type = "PERSP"
        cam.data.lens = lens

    direction = Vector(look_at) - Vector(location)
    rot_quat = direction.to_track_quat("-Z", "Y")
    cam.rotation_euler = rot_quat.to_euler()
    cam.data.clip_start = 0.01
    cam.data.clip_end = 500.0
    bpy.context.scene.camera = cam

    output_path = RUN_DIR / f"f15_blue_angels_{name}.png"
    bpy.context.scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)
    print(f"[blue_angels] Rendered {name}: {output_path}")

    bpy.data.objects.remove(cam, do_unlink=True)


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    try:
        print(f"[blue_angels] === RUN #{RUN_NUM} ===")
        print(f"[blue_angels] Output: {RUN_DIR}")

        clean_scene()

        print(f"[blue_angels] Importing STL: {STL_PATH}")
        obj = import_stl(STL_PATH)

        cleanup_mesh(obj)
        center_and_scale(obj)

        print("[blue_angels] Smart UV unwrap...")
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(45), island_margin=0.02)
        bpy.ops.object.mode_set(mode="OBJECT")

        print("[blue_angels] Assigning materials...")
        face_stats = assign_materials_blue_angels(obj)

        setup_lighting()
        setup_world()
        setup_render_settings()

        render_view("topdown", (0, 0, 30), (0, 0, 0), is_ortho=True, ortho_scale=25)
        render_view("front", (30, 0, 1.5), (0, 0, 1.5), is_ortho=True, ortho_scale=18)
        render_view("side", (0, 30, 2), (0, 0, 2), is_ortho=True, ortho_scale=25)
        render_view("threequarter", (20, 18, 14), (0, 0, 1.5), is_ortho=False, lens=85)
        render_view("hero", (15, 10, 6), (0, 0, 2), is_ortho=False, lens=70)

        print("[blue_angels] Exporting GLB...")
        glb_path = RUN_DIR / "f15_blue_angels.glb"
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.export_scene.gltf(
            filepath=str(glb_path),
            export_format="GLB",
            use_selection=True,
            export_apply=True,
            export_yup=True,
        )

        info = {
            "run_number": RUN_NUM,
            "run_dir": str(RUN_DIR),
            "variant": "blue_angels",
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "materials": len(obj.data.materials),
            "face_materials": {k: face_stats[k] for k in face_stats if k.startswith("faces_")},
            "palette": {
                "body": list(NAVY_BLUE),
                "belly": list(NAVY_BLUE_DARKER),
                "accent": list(ACCENT_YELLOW),
                "canopy": list(CANOPY_DARK),
            },
        }
        (RUN_DIR / "run_info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
        write_run_report(RUN_DIR, RUN_NUM, face_stats, info, STL_PATH)
        write_runs_index(VARIANT_BASE)

        print(f"[blue_angels] Run #{RUN_NUM} complete")
        return 0

    except Exception as e:
        print(f"[blue_angels] FAILED: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
