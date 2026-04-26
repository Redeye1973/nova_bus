"""
NOVA F-15 v5 — Blue Angels variant met AGGRESSIEVE geel paint scheme.

Verbeteringen vs v4 Blue Angels:
  1. Bbox-relative thresholds in plaats van vaste percentages
  2. Wing-tips: hele leading edge + buitenste 25% van wing
  3. Tail-tops: bovenste 35% van vertical tail height
  4. Canopy-frame: bbox-relative ring rond canopy area
  5. Fuselage-stripe: gele horizontal band op fuselage zijkant
     (iconic Blue Angels marking)
  6. Shade smooth + auto-smooth angle 30° voor vloeiende edges
  7. Subdivision surface modifier voor extra smoothness

Output: F15_OUTPUT_DIR/blue_angels/run_NNN/
"""

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
    r"L:\! 2 Nova v2 OUTPUT !\Ship_F15_v5"
))
STL_PATH = OUTPUT_BASE / "01_freecad" / "f15_v5.stl"

VARIANT_BASE = OUTPUT_BASE / "blue_angels"
VARIANT_BASE.mkdir(parents=True, exist_ok=True)


def next_run_dir(base):
    existing = []
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
print(f"[blue_angels-v5] Run #{RUN_NUM} → {RUN_DIR}")

RENDER_RESOLUTION = 1024


# ============================================================
# COLOR PALETTE
# ============================================================

NAVY_BLUE = (0.05, 0.10, 0.35, 1.0)
NAVY_BLUE_DARKER = (0.03, 0.06, 0.22, 1.0)
ACCENT_YELLOW = (1.00, 0.78, 0.05, 1.0)
CANOPY_DARK = (0.08, 0.08, 0.15, 1.0)


# ============================================================
# SCENE INIT
# ============================================================

def clean_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.meshes):
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in list(bpy.data.materials):
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in list(bpy.data.images):
        if block.users == 0 and block.name not in ('Render Result', 'Viewer Node'):
            bpy.data.images.remove(block)


def import_stl(stl_path):
    if not stl_path.exists():
        raise FileNotFoundError(f"STL not found: {stl_path}")
    try:
        bpy.ops.wm.stl_import(filepath=str(stl_path))
    except AttributeError:
        bpy.ops.import_mesh.stl(filepath=str(stl_path))
    obj = bpy.context.selected_objects[0]
    obj.name = "F15_Body"
    return obj


def cleanup_mesh(obj):
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


def center_and_scale(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    obj.location = (0, 0, 0)
    obj.scale = (0.001, 0.001, 0.001)
    bpy.ops.object.transform_apply(scale=True)


def smooth_shading(obj):
    """Shade smooth + auto-smooth waar beschikbaar (Blender 4.x wisselt API)."""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()
    try:
        obj.data.use_auto_smooth = True
        if hasattr(obj.data, "auto_smooth_angle"):
            obj.data.auto_smooth_angle = math.radians(30)
    except Exception:
        pass
    print("[v5] Shade smooth toegepast (auto-smooth indien ondersteund)")


# ============================================================
# MATERIALS (zelfde als v4)
# ============================================================

def make_navy_blue_paint():
    mat = bpy.data.materials.new(name="BA_Body")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (600, 0)

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    bsdf.inputs["Base Color"].default_value = NAVY_BLUE
    bsdf.inputs["Metallic"].default_value = 0.15
    bsdf.inputs["Roughness"].default_value = 0.35

    geom = nodes.new('ShaderNodeNewGeometry')
    geom.location = (-300, -200)

    edge_ramp = nodes.new('ShaderNodeValToRGB')
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
    mat = bpy.data.materials.new(name="BA_Belly")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = NAVY_BLUE_DARKER
        bsdf.inputs["Metallic"].default_value = 0.10
        bsdf.inputs["Roughness"].default_value = 0.45
    return mat


def make_yellow_accent():
    mat = bpy.data.materials.new(name="BA_Yellow")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = ACCENT_YELLOW
        bsdf.inputs["Metallic"].default_value = 0.10
        bsdf.inputs["Roughness"].default_value = 0.30
    return mat


def make_canopy_dark():
    mat = bpy.data.materials.new(name="BA_Canopy")
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
    mat = bpy.data.materials.new(name="BA_DarkHole")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.02, 0.02, 0.04, 1.0)
        bsdf.inputs["Roughness"].default_value = 1.0
    return mat


# ============================================================
# AGGRESSIEVE BLUE ANGELS HEURISTICS
# ============================================================

def assign_materials_blue_angels_v5(obj):
    """Aggressievere face-classification voor échte Blue Angels look.

    Strategie:
    - Hele leading edge van wings + outer 30% → geel
    - Bovenste 40% van vertical tails → geel
    - Canopy-frame als ring rond canopy area → geel
    - Fuselage stripe: horizontal band op zijkant → geel
    - Nose-tip → geel (Blue Angels nose accent)
    - Rest body → navy
    - Belly → darker navy
    - Canopy-glass → dark
    - Intakes/outlets → dark
    """
    me = obj.data

    # Bbox bepalen
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    z_min, z_max = min(zs), max(zs)

    x_span = x_max - x_min
    y_span = y_max - y_min
    z_span = z_max - z_min

    print(f"[v5] Mesh bbox: X [{x_min:.2f}, {x_max:.2f}] span {x_span:.2f}")
    print(f"[v5] Mesh bbox: Y [{y_min:.2f}, {y_max:.2f}] span {y_span:.2f}")
    print(f"[v5] Mesh bbox: Z [{z_min:.2f}, {z_max:.2f}] span {z_span:.2f}")

    outlet_x_cut = x_min + x_span * 0.02

    # AGGRESSIEVERE thresholds
    wing_outer_threshold = y_span * 0.30
    tail_top_threshold = z_span * 0.40
    # Wing-leading-edge: voorste 15% van wing (in X)
    # Wings staan rond X=-3 tot X=+2, dus leading = positive X kant
    # Fuselage stripe: midden-band op zijkant
    stripe_z_low = z_min + z_span * 0.45
    stripe_z_high = z_min + z_span * 0.62
    # Nose tip: voorste 5% van X
    nose_threshold = x_max - x_span * 0.05

    mats = {
        "body": make_navy_blue_paint(),
        "belly": make_navy_blue_belly(),
        "yellow": make_yellow_accent(),
        "canopy": make_canopy_dark(),
        "dark": make_intake_dark(),
    }

    obj.data.materials.clear()
    indices = {}
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

        nx, ny, nz = face.normal

        # === CANOPY GLASS (eerst) ===
        if 1.0 < cx < 5.5 and cz > 1.25:
            face.material_index = indices["canopy"]
            canopy_count += 1
            continue

        # === GEEL: NOSE-TIP ===
        if cx > nose_threshold:
            face.material_index = indices["yellow"]
            yellow_count += 1
            continue

        # === GEEL: WING-TIPS (outer 30%) ===
        if (cy < y_min + wing_outer_threshold or cy > y_max - wing_outer_threshold) and 0.45 < cz < 2.1:
            face.material_index = indices["yellow"]
            yellow_count += 1
            continue

        # === GEEL: WING-LEADING-EDGE ===
        if 0 < cx < 2.5 and 0.7 < cz < 1.6 and abs(cy) > 1.0 and nx > 0.3:
            face.material_index = indices["yellow"]
            yellow_count += 1
            continue

        # === GEEL: TAIL-TOPS ===
        if cz > z_max - tail_top_threshold and abs(cy) < 2.0:
            face.material_index = indices["yellow"]
            yellow_count += 1
            continue

        # === GEEL: FUSELAGE-STRIPE ===
        if (
            stripe_z_low < cz < stripe_z_high
            and -7 < cx < 5
            and 0.6 < abs(cy) < 1.3
            and abs(ny) > 0.5
        ):
            face.material_index = indices["yellow"]
            yellow_count += 1
            continue

        # === GEEL: CANOPY-FRAME ===
        if cz > 1.2 and ((0.9 < cx < 1.25) or (5.2 < cx < 5.8)) and abs(cy) < 0.85:
            face.material_index = indices["yellow"]
            yellow_count += 1
            continue

        # === DARK INTAKES ===
        if 0 < cx < 3 and cz < 1.1 and abs(cy) > 0.5:
            face.material_index = indices["dark"]
            dark_count += 1
            continue

        # === DARK ENGINE OUTLETS (smal achter X) ===
        if cx < outlet_x_cut and cz < 1.35:
            face.material_index = indices["dark"]
            dark_count += 1
            continue

        # === BELLY ===
        if nz < -0.3:
            face.material_index = indices["belly"]
            belly_count += 1
            continue

        # === DEFAULT: NAVY BODY ===
        face.material_index = indices["body"]
        body_count += 1

    total = body_count + belly_count + yellow_count + canopy_count + dark_count
    t = max(total, 1)
    print(f"[v5] Material distribution (total {total}):")
    print(f"  body (navy):    {body_count} ({100*body_count/t:.1f}%)")
    print(f"  belly:          {belly_count} ({100*belly_count/t:.1f}%)")
    print(f"  yellow accent:  {yellow_count} ({100*yellow_count/t:.1f}%)")
    print(f"  canopy:         {canopy_count} ({100*canopy_count/t:.1f}%)")
    print(f"  dark:           {dark_count} ({100*dark_count/t:.1f}%)")

    return {
        "body": body_count,
        "belly": belly_count,
        "yellow": yellow_count,
        "canopy": canopy_count,
        "dark": dark_count,
    }


# ============================================================
# LIGHTING + WORLD
# ============================================================

def setup_lighting():
    bpy.ops.object.light_add(type='SUN', location=(15, -10, 20))
    key = bpy.context.active_object
    key.data.energy = 4.5
    key.rotation_euler = (math.radians(45), math.radians(20), math.radians(45))

    bpy.ops.object.light_add(type='AREA', location=(-15, 10, 8))
    fill = bpy.context.active_object
    fill.data.energy = 250
    fill.data.size = 12

    bpy.ops.object.light_add(type='AREA', location=(-20, 0, 10))
    rim = bpy.context.active_object
    rim.data.energy = 150
    rim.data.size = 8


def setup_world():
    world = bpy.context.scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.55, 0.70, 0.88, 1)
    bg.inputs["Strength"].default_value = 0.4


# ============================================================
# RENDER
# ============================================================

def setup_render_settings():
    scene = bpy.context.scene
    scene.render.resolution_x = RENDER_RESOLUTION
    scene.render.resolution_y = RENDER_RESOLUTION
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.film_transparent = False

    try:
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = 64
        scene.cycles.use_denoising = True
    except:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'


def render_view(name, location, look_at=(0, 0, 1.5), is_ortho=False,
                  ortho_scale=25, lens=70):
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.active_object
    if is_ortho:
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = ortho_scale
    else:
        cam.data.type = 'PERSP'
        cam.data.lens = lens

    direction = Vector(look_at) - Vector(location)
    rot_quat = direction.to_track_quat("-Z", "Y")
    cam.rotation_euler = rot_quat.to_euler()
    cam.data.clip_start = 0.01
    cam.data.clip_end = 500.0
    bpy.context.scene.camera = cam

    output_path = RUN_DIR / f"f15_v5_blue_angels_{name}.png"
    bpy.context.scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)
    print(f"[v5] Rendered {name}")

    bpy.data.objects.remove(cam, do_unlink=True)


def write_v5_run_report(run_dir: Path, run_num: int, face_dist: dict, info: dict) -> None:
    fd = face_dist
    lines = [
        "# F-15 v5 — Blue Angels (runrapport)\n\n",
        f"- **Run:** `run_{run_num:03d}`\n",
        f"- **Map:** `{run_dir}`\n",
        f"- **STL:** `{STL_PATH}`\n",
        f"- **Resolutie:** {RENDER_RESOLUTION}², Cycles 64 spp\n\n",
        "## Face-verdeling\n\n",
        "| Slot | Faces |\n|------|------:|\n",
        f"| body | {fd.get('body', 0)} |\n",
        f"| belly | {fd.get('belly', 0)} |\n",
        f"| yellow | {fd.get('yellow', 0)} |\n",
        f"| canopy | {fd.get('canopy', 0)} |\n",
        f"| dark | {fd.get('dark', 0)} |\n\n",
        "## Mesh\n\n",
        f"- Vertices: **{info.get('vertices')}**\n",
        f"- Polygons: **{info.get('polygons')}**\n\n",
        "## Bestanden\n\n",
        "- `f15_v5_blue_angels_*.png` (5 views)\n",
        "- `f15_v5_blue_angels.glb`\n",
        "- `run_info.json`\n",
        "- `blue_angels_report.md` (dit bestand)\n",
    ]
    (run_dir / "blue_angels_report.md").write_text("".join(lines), encoding="utf-8")
    print(f"[v5] Report: {run_dir / 'blue_angels_report.md'}")


def write_runs_index(variant_base: Path) -> None:
    rows = ["# Blue Angels v5 — runs\n\n", "| Run | Pad |\n|-----|-----|\n"]
    for p in sorted(variant_base.glob("run_*")):
        if p.is_dir():
            rows.append(f"| `{p.name}` | `{p}` |\n")
    rows.append("\nZie per run `blue_angels_report.md` en `run_info.json`.\n")
    (variant_base / "runs_index.md").write_text("".join(rows), encoding="utf-8")


# ============================================================
# MAIN
# ============================================================

def main():
    try:
        print(f"[v5] === RUN #{RUN_NUM} ===")
        clean_scene()

        print(f"[v5] Importing STL: {STL_PATH}")
        obj = import_stl(STL_PATH)

        cleanup_mesh(obj)
        center_and_scale(obj)

        print("[v5] Smart UV unwrap...")
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(45),
                                   island_margin=0.02)
        bpy.ops.object.mode_set(mode='OBJECT')

        print("[v5] Smooth shading...")
        smooth_shading(obj)

        print("[v5] Aggressieve material assignment...")
        face_dist = assign_materials_blue_angels_v5(obj)

        setup_lighting()
        setup_world()
        setup_render_settings()

        render_view("topdown", (0, 0, 30), (0, 0, 0),
                     is_ortho=True, ortho_scale=25)
        render_view("front", (30, 0, 1.5), (0, 0, 1.5),
                     is_ortho=True, ortho_scale=18)
        render_view("side", (0, 30, 2), (0, 0, 2),
                     is_ortho=True, ortho_scale=25)
        render_view("threequarter", (20, 18, 14), (0, 0, 1.5),
                     is_ortho=False, lens=85)
        render_view("hero", (15, 10, 6), (0, 0, 2),
                     is_ortho=False, lens=70)

        print("[v5] Exporting GLB...")
        glb_path = RUN_DIR / "f15_v5_blue_angels.glb"
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.export_scene.gltf(
            filepath=str(glb_path),
            export_format='GLB',
            use_selection=True,
            export_apply=True,
            export_yup=True,
        )

        info = {
            "run_number": RUN_NUM,
            "run_dir": str(RUN_DIR),
            "model_version": "v5",
            "variant": "blue_angels",
            "improvements_vs_v4": [
                "smoother fuselage (14 sections)",
                "finer tessellation (0.1mm)",
                "shade smooth + auto-smooth 30 deg",
                "aggressive yellow heuristics",
                "fuselage stripe added",
                "nose-tip yellow accent added",
            ],
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "materials": len(obj.data.materials),
            "face_distribution": face_dist,
            "palette": {
                "body": list(NAVY_BLUE),
                "belly": list(NAVY_BLUE_DARKER),
                "accent": list(ACCENT_YELLOW),
                "canopy": list(CANOPY_DARK),
            },
        }
        (RUN_DIR / "run_info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
        write_v5_run_report(RUN_DIR, RUN_NUM, face_dist, info)
        write_runs_index(VARIANT_BASE)

        print(f"[v5] Run #{RUN_NUM} complete")
        return 0

    except Exception as e:
        print(f"[v5] FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
