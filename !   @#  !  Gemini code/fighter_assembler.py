"""
FighterAssembler — modulaire romp als parent voor vleugels, cockpit en bewapening.

Export: standaard ``L:\\! 2 Nova v2 OUTPUT !\\Blender`` (blend + glb + *_latest.txt).
Override: ``NOVA_BLENDER_OUTPUT``.

Run: Blender → Run Script, of ``blender --background --python ...fighter_assembler.py``.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import bmesh
import bpy

BLENDER_OUTPUT_DIR = os.environ.get(
    "NOVA_BLENDER_OUTPUT",
    r"L:\! 2 Nova v2 OUTPUT !\Blender",
)


class FighterAssembler:
    """Voegt modulaire onderdelen samen; romp is parent voor manipulatie."""

    def __init__(self) -> None:
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete(use_global=False)
        self.suffix = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.parts: list[bpy.types.Object] = []

    def create_material(
        self,
        name: str,
        color: tuple[float, ...],
        alpha: float = 1.0,
        is_glow: bool = False,
    ) -> bpy.types.Material:
        mat = bpy.data.materials.new(f"{name}_{self.suffix}")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is None:
            bsdf = mat.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
        r, g, b = float(color[0]), float(color[1]), float(color[2])
        bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)

        if alpha < 1.0:
            bsdf.inputs["Alpha"].default_value = alpha
            mat.blend_method = "BLEND"
            if hasattr(mat, "shadow_method"):
                mat.shadow_method = "HASHED"

        if is_glow:
            bsdf.inputs["Emission Color"].default_value = (r, g, b, 1.0)
            bsdf.inputs["Emission Strength"].default_value = 15.0

        return mat

    def build_hull(self) -> bpy.types.Object:
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.7, depth=8)
        hull = bpy.context.object
        hull.name = "Hull_Main"
        hull.rotation_euler[0] = 1.57
        hull.scale = (1, 1, 0.6)
        hull.active_material = self.create_material("Hull", (0.05, 0.05, 0.07))
        return hull

    def build_wings(self, parent: bpy.types.Object) -> bpy.types.Object:
        mesh = bpy.data.meshes.new("Wings")
        obj = bpy.data.objects.new("Wings", mesh)
        bpy.context.collection.objects.link(obj)

        bm = bmesh.new()
        verts = [(0.6, 2, 0), (5.5, -2, 0), (5, -4.5, 0), (0.6, -3, 0)]
        bm_verts = [bm.verts.new(v) for v in verts]
        bm.verts.ensure_lookup_table()
        face = bm.faces.new(bm_verts)
        bm.faces.ensure_lookup_table()

        res = bmesh.ops.extrude_face_region(bm, geom=[face])
        verts_to_move = [e for e in res["geom"] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=verts_to_move, vec=(0.0, 0.0, 0.15))

        bm.to_mesh(mesh)
        bm.free()

        obj.active_material = parent.active_material
        obj.parent = parent

        mod = obj.modifiers.new(name="Mirror", type="MIRROR")
        mod.use_axis[0] = True
        return obj

    def build_cockpit(self, parent: bpy.types.Object) -> bpy.types.Object:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.45, location=(0, 1.8, 0.5))
        cp = bpy.context.object
        cp.name = "Cockpit_Glass"
        cp.scale = (0.7, 3.5, 0.45)
        cp.active_material = self.create_material("Glass", (0, 0.5, 1), alpha=0.4)
        cp.parent = parent
        return cp

    def build_weaponry(self, parent: bpy.types.Object) -> None:
        for side in (-1, 1):
            for dist in (2.2, 4.0):
                pos = (side * dist, -0.5, -0.3)
                bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=2.5, location=pos)
                missile = bpy.context.object
                missile.name = f"Missile_{'L' if side < 0 else 'R'}_{dist}"
                missile.rotation_euler[0] = 1.57
                missile.active_material = parent.active_material
                missile.parent = parent

                bpy.ops.mesh.primitive_cone_add(
                    vertices=6,
                    radius1=0.3,
                    radius2=0.12,
                    depth=0.5,
                    location=(pos[0], pos[1] - 1.0, pos[2]),
                )
                fin = bpy.context.object
                fin.name = f"MissileFin_{missile.name}"
                fin.active_material = parent.active_material
                fin.parent = missile

    def _export(self) -> tuple[str, str]:
        os.makedirs(BLENDER_OUTPUT_DIR, exist_ok=True)
        stem = os.path.join(BLENDER_OUTPUT_DIR, f"assembled_fighter_{self.suffix}")
        blend_path = stem + ".blend"
        glb_path = stem + ".glb"
        bpy.ops.wm.save_as_mainfile(filepath=blend_path, check_existing=False)
        try:
            bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB", export_apply=True)
        except TypeError:
            bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB")
        latest = os.path.join(BLENDER_OUTPUT_DIR, "assembled_fighter_latest.txt")
        with open(latest, "w", encoding="utf-8") as f:
            f.write(f"blend={blend_path}\nglb={glb_path}\nutc={datetime.now(timezone.utc).isoformat()}\n")
        return blend_path, glb_path

    def assemble(self) -> None:
        hull = self.build_hull()
        self.parts.append(hull)
        self.parts.append(self.build_wings(hull))
        self.parts.append(self.build_cockpit(hull))
        self.build_weaponry(hull)
        blend, glb = self._export()
        print(f"[FighterAssembler] blend -> {blend}")
        print(f"[FighterAssembler] glb   -> {glb}")


def main() -> None:
    assembler = FighterAssembler()
    assembler.assemble()


if __name__ == "__main__":
    main()
