"""
NOVA F-15 v4 — Blender headless render script.

Voor execution via nova_host_bridge POST /blender/script,
of direct: blender --background --python f15_v4_blender_render.py

Workflow:
  1. Import f15_v4.stl
  2. Cleanup mesh (delete_loose, recalc normals, merge by distance)
  3. Center op origin, schaal naar Blender-units
  4. Apply matte grey material (geen reflections — silhouette test)
  5. Setup: één sun light van boven (silhouet-test, geen art-direction)
  6. Renders: front, topdown, side (orthographic), threequarter (perspective)
  7. Export GLB voor Godot-import

Output: F15_OUTPUT_DIR/02_blender/
        f15_v4_front.png, _topdown.png, _side.png, _threequarter.png
        f15_v4.glb
"""

import os
import sys
import math
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector


# ============================================================
# CONFIGURATIE
# ============================================================

OUTPUT_DIR = Path(os.environ.get(
    "F15_OUTPUT_DIR",
    r"L:\! 2 Nova v2 OUTPUT !\Ship_F15_v4"
))
STL_PATH = OUTPUT_DIR / "01_freecad" / "f15_v4.stl"
RENDER_DIR = OUTPUT_DIR / "02_blender"
RENDER_DIR.mkdir(parents=True, exist_ok=True)

RENDER_RESOLUTION = 512


# ============================================================
# SCENE SETUP
# ============================================================

def clean_scene():
    """Verwijder default cube, light, camera."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # Ook verwees materials / meshes opruimen
    for block in list(bpy.data.meshes):
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in list(bpy.data.materials):
        if block.users == 0:
            bpy.data.materials.remove(block)


def import_stl(stl_path):
    """Import STL — Blender 4.3 gebruikt bpy.ops.wm.stl_import."""
    if not stl_path.exists():
        raise FileNotFoundError(f"STL not found: {stl_path}")

    # Blender 4.3 syntax
    try:
        bpy.ops.wm.stl_import(filepath=str(stl_path))
    except AttributeError:
        # Fallback older Blender
        bpy.ops.import_mesh.stl(filepath=str(stl_path))

    # Get geïmporteerde object
    obj = bpy.context.selected_objects[0]
    obj.name = "F15_Body"
    return obj


def cleanup_mesh(obj):
    """Mesh hygiene: delete loose, recalc normals, merge by distance."""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')

    bpy.ops.mesh.select_all(action='SELECT')

    # Verwijder floating fragments
    bpy.ops.mesh.delete_loose()
    bmesh.update_edit_mesh(obj.data)

    # Merge duplicates (remove_doubles ontbreekt in Blender 4.3+)
    bm = bmesh.from_edit_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.5)
    bmesh.update_edit_mesh(obj.data)

    # Recalculate normals outside
    bpy.ops.mesh.normals_make_consistent(inside=False)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Print stats
    me = obj.data
    print(f"[F15] Mesh: {len(me.vertices)} verts, {len(me.polygons)} faces")


def center_and_scale(obj):
    """Center op wereld-origin en schaal naar zinnige units."""
    # Origin to geometry
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # Move to world origin
    obj.location = (0, 0, 0)

    # Schaal: FreeCAD output in mm, Blender wil meters voor render
    # F-15 echt = 19m, model = 19000mm = 19 Blender-units met scale 0.001
    obj.scale = (0.001, 0.001, 0.001)
    bpy.ops.object.transform_apply(scale=True)


def apply_matte_material(obj):
    """Matte grey, geen reflectie. Voor silhouette-test."""
    mat = bpy.data.materials.new(name="F15_Matte")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.65, 0.65, 0.65, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Roughness"].default_value = 1.0

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def setup_lighting():
    """Single sun light van boven — voor sterk silhouet."""
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 50))
    sun = bpy.context.active_object
    sun.data.energy = 3.0
    sun.rotation_euler = (0, 0, 0)  # straight down


def setup_world_background():
    """Zwarte achtergrond voor sprite-style transparant render."""
    world = bpy.context.scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0, 0, 0, 1)


# ============================================================
# CAMERAS PER ANGLE
# ============================================================

def render_orthographic(name, location, look_at=(0, 0, 0),
                          ortho_scale=25, output_path=None):
    """Render één orthographic view."""
    # Camera
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.active_object
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = ortho_scale

    # Aim at look_at
    direction = Vector(look_at) - Vector(location)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam.rotation_euler = rot_quat.to_euler()

    # Set as active camera
    bpy.context.scene.camera = cam

    # Render settings
    scene = bpy.context.scene
    scene.render.resolution_x = RENDER_RESOLUTION
    scene.render.resolution_y = RENDER_RESOLUTION
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'

    # Engine: Cycles voor beste resultaat, fallback Eevee
    try:
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = 32  # snel
    except:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'

    if output_path:
        scene.render.filepath = str(output_path)
        bpy.ops.render.render(write_still=True)
        print(f"[F15] Rendered {name}: {output_path}")

    # Cleanup camera
    bpy.data.objects.remove(cam, do_unlink=True)


def render_perspective(name, location, look_at=(0, 0, 0),
                         output_path=None):
    """Render perspective view."""
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.active_object
    cam.data.type = 'PERSP'
    cam.data.lens = 50

    direction = Vector(look_at) - Vector(location)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam.rotation_euler = rot_quat.to_euler()

    bpy.context.scene.camera = cam

    scene = bpy.context.scene
    scene.render.resolution_x = RENDER_RESOLUTION
    scene.render.resolution_y = RENDER_RESOLUTION
    scene.render.film_transparent = True

    if output_path:
        scene.render.filepath = str(output_path)
        bpy.ops.render.render(write_still=True)
        print(f"[F15] Rendered {name}: {output_path}")

    bpy.data.objects.remove(cam, do_unlink=True)


# ============================================================
# MAIN
# ============================================================

def main():
    try:
        print("[F15] Cleaning scene...")
        clean_scene()

        print(f"[F15] Importing STL: {STL_PATH}")
        obj = import_stl(STL_PATH)

        print("[F15] Cleaning mesh...")
        cleanup_mesh(obj)

        print("[F15] Centering and scaling...")
        center_and_scale(obj)

        print("[F15] Applying material...")
        apply_matte_material(obj)

        print("[F15] Setting up lighting...")
        setup_lighting()
        setup_world_background()

        # 4 renders
        # F-15 ligt in XY-plane met +X = neus richting

        print("[F15] Rendering topdown...")
        # Camera van boven, kijkt naar -Z
        render_orthographic(
            "topdown",
            location=(0, 0, 30),
            look_at=(0, 0, 0),
            ortho_scale=25,
            output_path=RENDER_DIR / "f15_v4_topdown.png"
        )

        print("[F15] Rendering front...")
        # Camera vóór de neus, kijkt naar -X
        render_orthographic(
            "front",
            location=(30, 0, 1),
            look_at=(0, 0, 1),
            ortho_scale=18,
            output_path=RENDER_DIR / "f15_v4_front.png"
        )

        print("[F15] Rendering side...")
        # Camera aan zijkant, kijkt naar -Y
        render_orthographic(
            "side",
            location=(0, 30, 1),
            look_at=(0, 0, 1),
            ortho_scale=25,
            output_path=RENDER_DIR / "f15_v4_side.png"
        )

        print("[F15] Rendering threequarter...")
        # Iso-achtige hoek
        render_perspective(
            "threequarter",
            location=(20, 20, 15),
            look_at=(0, 0, 1),
            output_path=RENDER_DIR / "f15_v4_threequarter.png"
        )

        # Export GLB voor Godot-mogelijkheid
        print("[F15] Exporting GLB...")
        glb_path = RENDER_DIR / "f15_v4.glb"
        # Selecteer alleen ship object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        bpy.ops.export_scene.gltf(
            filepath=str(glb_path),
            export_format='GLB',
            use_selection=True,
            export_apply=True,
            export_yup=True,  # Godot Y-up convention
        )
        print(f"[F15] GLB saved: {glb_path}")

        # Print mesh stats voor mesh jury
        me = obj.data
        stats = {
            "vertices": len(me.vertices),
            "polygons": len(me.polygons),
            "materials": len(obj.data.materials),
            "bounds_x": (
                min(v.co.x for v in me.vertices),
                max(v.co.x for v in me.vertices)
            ),
            "bounds_y": (
                min(v.co.y for v in me.vertices),
                max(v.co.y for v in me.vertices)
            ),
            "bounds_z": (
                min(v.co.z for v in me.vertices),
                max(v.co.z for v in me.vertices)
            ),
        }
        print(f"[F15] Mesh stats: {stats}")

        # Schrijf stats naar JSON
        import json
        stats_path = RENDER_DIR / "mesh_stats.json"
        # Convert tuples voor JSON
        json_stats = {
            "vertices": stats["vertices"],
            "polygons": stats["polygons"],
            "materials": stats["materials"],
            "bounds_x": list(stats["bounds_x"]),
            "bounds_y": list(stats["bounds_y"]),
            "bounds_z": list(stats["bounds_z"]),
        }
        stats_path.write_text(json.dumps(json_stats, indent=2))

        print("[F15] Render pipeline complete")
        return 0

    except Exception as e:
        print(f"[F15] FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
