"""
NOVA F-15 v4 — TEXTURED Blender render script.

Versie met procedurele materials, multi-material per body-part,
USAF-style markings als 3D text, en game-ready GLB export.

Strategie:
  1. Import STL als één mesh
  2. Cleanup mesh
  3. Split mesh in face-groups op basis van Z-positie + clustering
     (boven = top paint, onder = belly paint, vooraan-top = canopy)
  4. Per groep eigen material assignen
  5. Procedurele two-tone met edge wear
  6. Canopy glass (transmissive, donker)
  7. Engine intake/outlet zwarte holes
  8. 3D text-objects voor "USAF" + tail number
  9. Render 4 angles, export GLB

Output: F15_OUTPUT_DIR/02_blender_textured/
        renders + f15_v4_textured.glb
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
RENDER_DIR = OUTPUT_DIR / "02_blender_textured"
RENDER_DIR.mkdir(parents=True, exist_ok=True)

RENDER_RESOLUTION = 1024  # hoger dan silhouette-test, voor materials zichtbaar


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
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.delete_loose()
    bmesh.update_edit_mesh(obj.data)
    bm = bmesh.from_edit_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.5)
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')


def center_and_scale(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    obj.location = (0, 0, 0)
    obj.scale = (0.001, 0.001, 0.001)
    bpy.ops.object.transform_apply(scale=True)


# ============================================================
# MATERIAL FACTORIES
# ============================================================

def make_top_paint_material(name="F15_Top_Paint"):
    """Donkergrijs voor bovenzijde. F-15 standaard: FS36251 (medium grey).
    Met edge wear via Geometry > Pointiness."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Output
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (600, 0)

    # Principled BSDF
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    bsdf.inputs["Base Color"].default_value = (0.32, 0.34, 0.37, 1.0)  # bluegrey
    bsdf.inputs["Metallic"].default_value = 0.1
    bsdf.inputs["Roughness"].default_value = 0.6

    # Geometry voor edge wear
    geom = nodes.new('ShaderNodeNewGeometry')
    geom.location = (-300, -200)

    # Color ramp voor pointiness → wear amount
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (0, -200)
    ramp.color_ramp.elements[0].position = 0.4
    ramp.color_ramp.elements[0].color = (0.32, 0.34, 0.37, 1.0)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (0.55, 0.55, 0.55, 1.0)  # lichter op edges

    links.new(geom.outputs["Pointiness"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat


def make_belly_paint_material(name="F15_Belly_Paint"):
    """Lichtgrijs voor onderzijde. F-15: FS36375 (light gull grey)."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.55, 0.57, 0.60, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.05
        bsdf.inputs["Roughness"].default_value = 0.65
    return mat


def make_canopy_glass_material(name="F15_Canopy_Glass"):
    """Donker glanzend canopy."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.05, 0.08, 0.12, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Roughness"].default_value = 0.05
        # Transmission voor glass-effect (in Blender 4.x heet dit "Transmission Weight")
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 0.3
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = 0.3
    return mat


def make_radome_material(name="F15_Radome"):
    """Donkere radome voor neuspunt."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.18, 0.18, 0.20, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Roughness"].default_value = 0.7
    return mat


def make_intake_dark_material(name="F15_Intake_Dark"):
    """Zwart voor air intake en engine outlet 'gat'."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Roughness"].default_value = 1.0
    return mat


def make_text_material(name="F15_Marking_Text"):
    """Zwarte tekst voor markings."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.05, 0.05, 0.05, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Roughness"].default_value = 0.8
    return mat


# ============================================================
# MULTI-MATERIAL ASSIGNMENT VIA FACE-GROUPS
# ============================================================

def assign_materials_by_geometry(obj):
    """Verdeel mesh-faces over materialen op basis van positie.

    Strategie:
    - Faces met normal-Z > 0.3 (boven-georiënteerd) → top paint
    - Faces met normal-Z < -0.3 (onder-georiënteerd) → belly paint
    - Faces in canopy-region (X tussen 1.5 en 4.5, Z > 1.7) → canopy glass
    - Faces in nose-tip (X > 8) → radome
    - Faces in intake-region (X 0 tot 3, Z < 1, naast fuselage) → intake dark
    - Rest → top paint default
    """
    me = obj.data

    # Materialen toevoegen aan object
    materials = {
        "top": make_top_paint_material(),
        "belly": make_belly_paint_material(),
        "canopy": make_canopy_glass_material(),
        "radome": make_radome_material(),
        "intake": make_intake_dark_material(),
    }

    # Clear existing materials op object
    obj.data.materials.clear()

    # Voeg materials toe in vaste volgorde — index matters voor face.material_index
    mat_indices = {}
    for idx, (key, mat) in enumerate(materials.items()):
        obj.data.materials.append(mat)
        mat_indices[key] = idx

    # Per face: bepaal material op basis van positie + normal
    for face in me.polygons:
        # Bereken centroid
        cx = sum(me.vertices[v].co.x for v in face.vertices) / len(face.vertices)
        cy = sum(me.vertices[v].co.y for v in face.vertices) / len(face.vertices)
        cz = sum(me.vertices[v].co.z for v in face.vertices) / len(face.vertices)

        # Normal (al genormaliseerd door Blender)
        nx, ny, nz = face.normal

        # Beslissingsboom (in Blender-units, na 0.001 schaal: F-15 is ~19 wide)

        # Canopy: voor cockpit, bovenkant, X tussen 1.5 en 4.5, Z hoog
        if 1.5 < cx < 4.7 and cz > 1.7:
            face.material_index = mat_indices["canopy"]
            continue

        # Radome (neuspunt)
        if cx > 8.5:
            face.material_index = mat_indices["radome"]
            continue

        # Intake region (onder cockpit, naast fuselage)
        if 0 < cx < 3 and cz < 1.1 and abs(cy) > 0.5:
            face.material_index = mat_indices["intake"]
            continue

        # Bottom-facing faces → belly
        if nz < -0.3:
            face.material_index = mat_indices["belly"]
            continue

        # Default → top paint
        face.material_index = mat_indices["top"]


# ============================================================
# 3D TEXT MARKINGS
# ============================================================

def add_text_marking(text, location, rotation=(0, 0, 0), size=0.5,
                       extrude=0.02, name=None):
    """Voeg 3D text toe als marking. Default: zwart, plat extrude."""
    bpy.ops.object.text_add(location=location, rotation=rotation)
    text_obj = bpy.context.active_object
    if name:
        text_obj.name = name
    text_obj.data.body = text
    text_obj.data.size = size
    text_obj.data.extrude = extrude
    text_obj.data.align_x = 'CENTER'
    text_obj.data.align_y = 'CENTER'

    # Material
    mat = make_text_material(name=f"Text_{name or text}_Mat")
    text_obj.data.materials.append(mat)

    return text_obj


def add_f15_markings():
    """Voeg USAF-style markings toe aan model.

    Coordinaten zijn in Blender-units (na 0.001 schaal).
    F-15 ligt nu langs X-as, span ~13 in Y, lengte ~19 in X.
    """
    markings = []

    # Tail nummer "AF 90-255" op rechter vertical tail
    # Right tail zit rond Y=+0.9, X=-7.5, Z=2.7
    markings.append(add_text_marking(
        "AF 90-255",
        location=(-7.8, 0.96, 3.2),
        rotation=(math.radians(90), 0, math.radians(90)),
        size=0.25,
        name="TailNumber_Right"
    ))

    # Idem op linker tail
    markings.append(add_text_marking(
        "AF 90-255",
        location=(-7.8, -0.96, 3.2),
        rotation=(math.radians(90), 0, math.radians(-90)),
        size=0.25,
        name="TailNumber_Left"
    ))

    # "USAF" op fuselage zijkant
    markings.append(add_text_marking(
        "U.S. AIR FORCE",
        location=(-3.0, 1.05, 1.5),
        rotation=(math.radians(90), 0, math.radians(90)),
        size=0.35,
        name="USAF_Right"
    ))

    markings.append(add_text_marking(
        "U.S. AIR FORCE",
        location=(-3.0, -1.05, 1.5),
        rotation=(math.radians(90), 0, math.radians(-90)),
        size=0.35,
        name="USAF_Left"
    ))

    # "MO" base code op tail
    markings.append(add_text_marking(
        "MO",
        location=(-7.5, 0.96, 4.0),
        rotation=(math.radians(90), 0, math.radians(90)),
        size=0.6,
        name="Base_MO_Right"
    ))

    markings.append(add_text_marking(
        "MO",
        location=(-7.5, -0.96, 4.0),
        rotation=(math.radians(90), 0, math.radians(-90)),
        size=0.6,
        name="Base_MO_Left"
    ))

    return markings


# ============================================================
# LIGHTING + WORLD
# ============================================================

def setup_lighting():
    """3-point lighting voor product-shot kwaliteit."""
    # Key light (sun, van rechtsboven)
    bpy.ops.object.light_add(type='SUN', location=(15, -10, 20))
    key = bpy.context.active_object
    key.name = "KeyLight"
    key.data.energy = 4.0
    key.rotation_euler = (math.radians(45), math.radians(20), math.radians(45))

    # Fill light (zwakker, van linkeronderkant)
    bpy.ops.object.light_add(type='AREA', location=(-15, 10, 8))
    fill = bpy.context.active_object
    fill.name = "FillLight"
    fill.data.energy = 200
    fill.data.size = 10

    # Rim light (voor edge highlight)
    bpy.ops.object.light_add(type='AREA', location=(-20, 0, 10))
    rim = bpy.context.active_object
    rim.name = "RimLight"
    rim.data.energy = 100
    rim.data.size = 8


def setup_world():
    """Lichte hemel-achtergrond voor non-silhouette renders."""
    world = bpy.context.scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.85, 0.87, 0.92, 1)  # licht blauw-grijs
    bg.inputs["Strength"].default_value = 0.3


# ============================================================
# RENDER
# ============================================================

def setup_render_settings():
    scene = bpy.context.scene
    scene.render.resolution_x = RENDER_RESOLUTION
    scene.render.resolution_y = RENDER_RESOLUTION
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.film_transparent = False  # nu mét achtergrond

    # Cycles voor beste kwaliteit
    try:
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = 64
        scene.cycles.use_denoising = True
    except:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'


def render_view(name, location, look_at=(0, 0, 1), is_ortho=False,
                  ortho_scale=25, lens=50):
    """Render één view, save naar RENDER_DIR."""
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.active_object
    if is_ortho:
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = ortho_scale
    else:
        cam.data.type = 'PERSP'
        cam.data.lens = lens

    direction = Vector(look_at) - Vector(location)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam.rotation_euler = rot_quat.to_euler()
    cam.data.clip_start = 0.01
    cam.data.clip_end = 500.0
    bpy.context.scene.camera = cam

    output_path = RENDER_DIR / f"f15_v4_textured_{name}.png"
    bpy.context.scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)
    print(f"[F15-tex] Rendered {name}: {output_path}")

    bpy.data.objects.remove(cam, do_unlink=True)


# ============================================================
# MAIN
# ============================================================

def main():
    try:
        print("[F15-tex] Cleaning scene...")
        clean_scene()

        print(f"[F15-tex] Importing STL: {STL_PATH}")
        obj = import_stl(STL_PATH)

        print("[F15-tex] Cleaning mesh...")
        cleanup_mesh(obj)

        print("[F15-tex] Centering and scaling...")
        center_and_scale(obj)

        print("[F15-tex] Smart UV unwrap...")
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66))
        bpy.ops.object.mode_set(mode='OBJECT')

        print("[F15-tex] Assigning materials by geometry...")
        assign_materials_by_geometry(obj)

        print("[F15-tex] Adding text markings...")
        markings = add_f15_markings()
        print(f"[F15-tex] Added {len(markings)} markings")

        print("[F15-tex] Setting up lighting...")
        setup_lighting()
        setup_world()

        print("[F15-tex] Render settings...")
        setup_render_settings()

        # Renders
        print("[F15-tex] Rendering topdown ortho...")
        render_view("topdown",
                     location=(0, 0, 30), look_at=(0, 0, 0),
                     is_ortho=True, ortho_scale=25)

        print("[F15-tex] Rendering front ortho...")
        render_view("front",
                     location=(30, 0, 1.5), look_at=(0, 0, 1.5),
                     is_ortho=True, ortho_scale=18)

        print("[F15-tex] Rendering side ortho...")
        render_view("side",
                     location=(0, 30, 2), look_at=(0, 0, 2),
                     is_ortho=True, ortho_scale=25)

        print("[F15-tex] Rendering threequarter perspective...")
        render_view("threequarter",
                     location=(20, 18, 14), look_at=(0, 0, 1.5),
                     is_ortho=False, lens=85)

        print("[F15-tex] Rendering hero shot...")
        # Hero perspective dichtbij voor product-shot
        render_view("hero",
                     location=(15, 10, 6), look_at=(0, 0, 2),
                     is_ortho=False, lens=70)

        # Font → mesh voor stabiele glTF-export
        print("[F15-tex] Converting text markings to mesh...")
        bpy.ops.object.select_all(action='DESELECT')
        for m in markings:
            bpy.context.view_layer.objects.active = m
            m.select_set(True)
            bpy.ops.object.convert(target="MESH")
            m.select_set(False)

        # Export GLB voor Godot
        print("[F15-tex] Exporting GLB...")
        glb_path = RENDER_DIR / "f15_v4_textured.glb"
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        for m in markings:
            m.select_set(True)
        bpy.context.view_layer.objects.active = obj

        bpy.ops.export_scene.gltf(
            filepath=str(glb_path),
            export_format='GLB',
            use_selection=True,
            export_apply=True,
            export_yup=True,
        )
        print(f"[F15-tex] GLB saved: {glb_path}")

        # Stats
        me = obj.data
        stats = {
            "vertices": len(me.vertices),
            "polygons": len(me.polygons),
            "materials": len(obj.data.materials),
            "markings": len(markings),
        }

        import json
        stats_path = RENDER_DIR / "render_stats.json"
        stats_path.write_text(json.dumps(stats, indent=2))
        print(f"[F15-tex] Stats: {stats}")

        print("[F15-tex] Textured render complete")
        return 0

    except Exception as e:
        print(f"[F15-tex] FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
