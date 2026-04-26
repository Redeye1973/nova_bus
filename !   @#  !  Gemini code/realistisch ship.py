"""
Realistische shmup-fighter (F-15-achtige romp, delta-vleugels, tandem-cockpit,
stabilisatoren, raketten, neon-motoren).

Run in Blender of headless:
  blender --background --python "...realistisch ship.py"

Export: ``BLENDER_OUTPUT_DIR`` (default ``L:\\! 2 Nova v2 OUTPUT !\\Blender``).
Override: ``NOVA_BLENDER_OUTPUT``.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import bmesh
import bpy
from mathutils import Vector

BLENDER_OUTPUT_DIR = os.environ.get(
    "NOVA_BLENDER_OUTPUT",
    r"L:\! 2 Nova v2 OUTPUT !\Blender",
)


def _clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def _ensure_output_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _export_scene(out_dir: str, stem: str) -> tuple[str, str]:
    _ensure_output_dir(out_dir)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base = os.path.join(out_dir, f"{stem}_{ts}")
    blend_path = base + ".blend"
    glb_path = base + ".glb"
    bpy.ops.wm.save_as_mainfile(filepath=blend_path, check_existing=False)
    try:
        bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB", export_apply=True)
    except TypeError:
        bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB")
    latest = os.path.join(out_dir, f"{stem}_latest.txt")
    with open(latest, "w", encoding="utf-8") as f:
        f.write(f"blend={blend_path}\nglb={glb_path}\nutc={datetime.now(timezone.utc).isoformat()}\n")
    return blend_path, glb_path


class RealisticShipBuilder:
    def __init__(self) -> None:
        _clear_scene()
        self._suffix = datetime.now(timezone.utc).strftime("%H%M%S")
        self.materials = self._create_materials()

    def _mat_name(self, base: str) -> str:
        return f"{base}_{self._suffix}"

    def _create_materials(self) -> dict[str, bpy.types.Material]:
        mats: dict[str, bpy.types.Material] = {}

        mats["hull"] = bpy.data.materials.new(self._mat_name("HullMat"))
        mats["hull"].use_nodes = True
        bsdf = mats["hull"].node_tree.nodes.get("Principled BSDF")
        assert bsdf is not None
        bsdf.inputs["Base Color"].default_value = (0.08, 0.1, 0.12, 1)
        bsdf.inputs["Metallic"].default_value = 0.7
        bsdf.inputs["Roughness"].default_value = 0.3

        mats["cockpit"] = bpy.data.materials.new(self._mat_name("CockpitMat"))
        mats["cockpit"].use_nodes = True
        cp_bsdf = mats["cockpit"].node_tree.nodes.get("Principled BSDF")
        assert cp_bsdf is not None
        cp_bsdf.inputs["Base Color"].default_value = (0.0, 0.4, 0.8, 1)
        cp_bsdf.inputs["Alpha"].default_value = 0.4
        mats["cockpit"].blend_method = "BLEND"
        if hasattr(mats["cockpit"], "shadow_method"):
            mats["cockpit"].shadow_method = "HASHED"

        mats["neon"] = bpy.data.materials.new(self._mat_name("NeonMat"))
        mats["neon"].use_nodes = True
        neon_bsdf = mats["neon"].node_tree.nodes.get("Principled BSDF")
        assert neon_bsdf is not None
        neon_bsdf.inputs["Base Color"].default_value = (0.0, 0.15, 0.2, 1.0)
        neon_bsdf.inputs["Emission Color"].default_value = (0, 0.8, 1, 1)
        neon_bsdf.inputs["Emission Strength"].default_value = 15.0

        return mats

    def add_mirror(self, obj: bpy.types.Object) -> None:
        mod = obj.modifiers.new(name="Mirror", type="MIRROR")
        mod.use_axis[0] = True

    def build_hull(self) -> bpy.types.Object:
        mesh = bpy.data.meshes.new("Hull")
        obj = bpy.data.objects.new("Hull", mesh)
        bpy.context.collection.objects.link(obj)

        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.y *= 6.0
            v.co.x *= 0.9
            v.co.z *= 0.4
            if v.co.y > 0:
                v.co.x *= 0.1
                v.co.z *= 0.1
                v.co.y += 2.0

        bm.to_mesh(mesh)
        bm.free()
        obj.active_material = self.materials["hull"]
        return obj

    def build_wings(self) -> bpy.types.Object:
        mesh = bpy.data.meshes.new("Wings")
        obj = bpy.data.objects.new("Wings", mesh)
        bpy.context.collection.objects.link(obj)

        bm = bmesh.new()
        verts = [
            (0.5, 1.5, 0),
            (4.5, -1.0, 0),
            (4.0, -3.5, 0),
            (0.5, -2.5, 0),
        ]
        for co in verts:
            bm.verts.new(co)
        bm.verts.ensure_lookup_table()
        f = bm.faces.new(bm.verts)
        bm.faces.ensure_lookup_table()

        ext = bmesh.ops.extrude_face_region(bm, geom=[f])
        extruded_verts = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=extruded_verts, vec=Vector((0.0, 0.0, 0.12)))

        bm.to_mesh(mesh)
        bm.free()

        obj.active_material = self.materials["hull"]
        self.add_mirror(obj)
        return obj

    def build_cockpit(self) -> bpy.types.Object:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=(0, 1.8, 0.45))
        cp = bpy.context.object
        cp.name = "Cockpit"
        cp.scale = (0.7, 3.5, 0.5)
        cp.active_material = self.materials["cockpit"]
        return cp

    def build_stabilizers(self) -> bpy.types.Object:
        mesh = bpy.data.meshes.new("Fins")
        obj = bpy.data.objects.new("Fins", mesh)
        bpy.context.collection.objects.link(obj)

        bm = bmesh.new()
        for co in [(0.8, -3, 0), (0.8, -5.5, 0), (1.5, -6, 2.5), (1.5, -4, 2.5)]:
            bm.verts.new(co)
        bm.verts.ensure_lookup_table()
        bm.faces.new(bm.verts)

        bm.to_mesh(mesh)
        bm.free()
        obj.active_material = self.materials["hull"]
        self.add_mirror(obj)
        return obj

    def build_weaponry(self) -> None:
        for side in (-1, 1):
            for dist in (1.8, 3.2):
                pos = (side * dist, -1, -0.3)
                bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=2.0, location=pos)
                missile = bpy.context.object
                missile.name = f"Missile_{'L' if side < 0 else 'R'}_{dist}"
                missile.rotation_euler[0] = 1.57
                missile.active_material = self.materials["hull"]

                bpy.ops.mesh.primitive_cone_add(
                    vertices=6,
                    radius1=0.25,
                    radius2=0.1,
                    depth=0.4,
                    location=(pos[0], pos[1] - 0.8, pos[2]),
                )
                fin = bpy.context.object
                fin.name = f"MissileFin_{missile.name}"
                fin.active_material = self.materials["hull"]
                fin.parent = missile

    def build_engines(self) -> None:
        for side in (-1, 1):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=1.2, location=(side * 0.6, -5.5, 0))
            eng = bpy.context.object
            eng.name = f"Engine_{'L' if side < 0 else 'R'}"
            eng.rotation_euler[0] = 1.57
            eng.active_material = self.materials["neon"]

    def assemble(self) -> None:
        self.build_hull()
        self.build_wings()
        self.build_cockpit()
        self.build_stabilizers()
        self.build_weaponry()
        self.build_engines()


def main() -> None:
    builder = RealisticShipBuilder()
    builder.assemble()
    blend, glb = _export_scene(BLENDER_OUTPUT_DIR, "realistisch_ship")
    print(f"[realistisch_ship] blend -> {blend}")
    print(f"[realistisch_ship] glb   -> {glb}")


if __name__ == "__main__":
    main()
