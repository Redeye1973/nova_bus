"""
ShipGeneratorV2 — modulaire romp (bmesh cone) + vleugels met extrude-dikte, parent naar hull, Mirror X.

Export: ``L:\\! 2 Nova v2 OUTPUT !\\Blender`` (blend + glb). Override: ``NOVA_BLENDER_OUTPUT``.

Headless: UI-shading alleen als ``bpy.context.screen`` bestaat.
"""
from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime, timezone

import bmesh
import bpy

BLENDER_OUTPUT_DIR = os.environ.get(
    "NOVA_BLENDER_OUTPUT",
    r"L:\! 2 Nova v2 OUTPUT !\Blender",
)


class ShipGeneratorV2:
    def __init__(self) -> None:
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete(use_global=False)
        self.suffix = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    def create_material(
        self,
        name: str,
        color: tuple[float, ...],
        alpha: float = 1.0,
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
        return mat

    def build_part(
        self,
        name: str,
        mesh_data_func: Callable[[bmesh.types.BMesh], None],
        material: bpy.types.Material,
    ) -> bpy.types.Object:
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)

        bm = bmesh.new()
        mesh_data_func(bm)
        bm.to_mesh(mesh)
        bm.free()

        obj.active_material = material
        return obj

    def assemble_fighter(self) -> tuple[str, str]:
        def hull_geo(bm: bmesh.types.BMesh) -> None:
            bmesh.ops.create_cone(
                bm,
                cap_ends=True,
                segments=12,
                radius1=0.6,
                radius2=0.05,
                depth=7.0,
            )

        hull = self.build_part("Hull_Main", hull_geo, self.create_material("HullMat", (0.1, 0.1, 0.12)))
        hull.rotation_euler[0] = 1.57

        def wing_geo(bm: bmesh.types.BMesh) -> None:
            verts = [(0.5, 1.5, 0), (5, -1, 0), (4.5, -3, 0), (0.5, -2, 0)]
            bm_verts = [bm.verts.new(v) for v in verts]
            bm.verts.ensure_lookup_table()
            face = bm.faces.new(bm_verts)
            bm.faces.ensure_lookup_table()
            res = bmesh.ops.extrude_face_region(bm, geom=[face])
            extruded = [e for e in res["geom"] if isinstance(e, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, verts=extruded, vec=(0.0, 0.0, 0.1))

        wings = self.build_part("Wings", wing_geo, hull.active_material)
        wings.parent = hull

        mirror = wings.modifiers.new(name="Mirror", type="MIRROR")
        mirror.use_axis[0] = True

        bpy.ops.object.select_all(action="DESELECT")
        hull.select_set(True)
        bpy.context.view_layer.objects.active = hull

        # Alleen met interactieve UI (niet in --background)
        screen = getattr(bpy.context, "screen", None)
        if screen is not None:
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    area.spaces.active.shading.type = "MATERIAL"

        print("Schip succesvol geassembleerd en parenting toegepast.")

        return self._export()

    def _export(self) -> tuple[str, str]:
        os.makedirs(BLENDER_OUTPUT_DIR, exist_ok=True)
        stem = os.path.join(BLENDER_OUTPUT_DIR, f"ship_generator_v2_{self.suffix}")
        blend_path = stem + ".blend"
        glb_path = stem + ".glb"
        bpy.ops.wm.save_as_mainfile(filepath=blend_path, check_existing=False)
        try:
            bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB", export_apply=True)
        except TypeError:
            bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB")
        latest = os.path.join(BLENDER_OUTPUT_DIR, "ship_generator_v2_latest.txt")
        with open(latest, "w", encoding="utf-8") as f:
            f.write(f"blend={blend_path}\nglb={glb_path}\nutc={datetime.now(timezone.utc).isoformat()}\n")
        return blend_path, glb_path


def main() -> None:
    gen = ShipGeneratorV2()
    blend, glb = gen.assemble_fighter()
    print(f"[ShipGeneratorV2] blend -> {blend}")
    print(f"[ShipGeneratorV2] glb   -> {glb}")


if __name__ == "__main__":
    main()
