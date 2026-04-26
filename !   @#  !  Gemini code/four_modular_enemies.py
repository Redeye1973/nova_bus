"""
Vier vaste enemy-presets: combineert
- `blender modulair pallette.py` (Principled BSDF, cockpit-alpha, thruster-emission)
- `Freecad Modulair systeem enemy.py` (hull/wing/gun types + mirror)

Run in Blender: Scripting workspace → Open → Run Script.
"""
from __future__ import annotations

import bpy


def _clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def _principled_mat(
    name: str,
    base_rgba: tuple[float, float, float, float],
    *,
    metallic: float = 0.65,
    roughness: float = 0.28,
    alpha: float = 1.0,
    blend: bool = False,
    emission_rgb: tuple[float, float, float] | None = None,
    emission_strength: float = 4.0,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = nt.nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_rgba
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Alpha"].default_value = alpha
    if emission_rgb is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission_rgb, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    if blend or alpha < 0.999:
        mat.blend_method = "BLEND"
        mat.shadow_method = "HASHED"
    return mat


def _mirror_x(obj: bpy.types.Object) -> None:
    mod = obj.modifiers.new(name="Mirror", type="MIRROR")
    mod.use_axis[0] = True


class ModularEnemyFactory:
    """Onderdelen uit Freecad-modulair; materialen uit palet-stijl."""

    def __init__(self) -> None:
        self._mats: dict[str, bpy.types.Material] = {}

    def _mat(self, key: str, **kwargs) -> bpy.types.Material:
        if key not in self._mats:
            self._mats[key] = _principled_mat(key, **kwargs)
        return self._mats[key]

    def create_hull(self, hull_type: int, pos: tuple[float, float, float], mat: bpy.types.Material) -> bpy.types.Object:
        if hull_type == 1:
            bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1, depth=4, location=pos)
            obj = bpy.context.object
            obj.rotation_euler[0] = 1.57
        else:
            bpy.ops.mesh.primitive_cube_add(size=2, location=pos)
            obj = bpy.context.object
            obj.scale = (0.8, 2, 0.6)
        obj.active_material = mat
        return obj

    def create_cockpit(self, pos: tuple[float, float, float], mat: bpy.types.Material) -> bpy.types.Object:
        cp_pos = (pos[0], pos[1] + 0.5, pos[2] + 0.6)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=cp_pos)
        obj = bpy.context.object
        obj.scale = (0.7, 1.2, 0.5)
        obj.active_material = mat
        return obj

    def create_wings(self, wing_type: int, pos: tuple[float, float, float], mat: bpy.types.Material) -> bpy.types.Object:
        wing_pos = (pos[0] + 1.5, pos[1], pos[2])
        if wing_type == 1:
            bpy.ops.mesh.primitive_cylinder_add(vertices=3, radius=1.5, depth=0.1, location=wing_pos)
            obj = bpy.context.object
            obj.rotation_euler[2] = 1.57
        else:
            bpy.ops.mesh.primitive_cube_add(size=1, location=wing_pos)
            obj = bpy.context.object
            obj.scale = (2, 0.8, 0.1)
        obj.active_material = mat
        _mirror_x(obj)
        return obj

    def create_guns(self, pos: tuple[float, float, float], mat: bpy.types.Material) -> bpy.types.Object:
        gun_pos = (pos[0] + 2.5, pos[1] + 1, pos[2] - 0.2)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.5, location=gun_pos)
        obj = bpy.context.object
        obj.rotation_euler[0] = 1.57
        obj.active_material = mat
        _mirror_x(obj)
        return obj

    def create_thrusters(self, pos: tuple[float, float, float]) -> bpy.types.Object:
        t_pos = (pos[0] + 0.6, pos[1] - 2, pos[2])
        bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.5, location=t_pos)
        obj = bpy.context.object
        obj.rotation_euler[0] = 1.57
        glow = _principled_mat(
            f"Thruster_{id(obj)}",
            (0.05, 0.05, 0.05, 1.0),
            metallic=0.0,
            roughness=0.35,
            emission_rgb=(1.0, 0.35, 0.05),
            emission_strength=6.0,
        )
        obj.active_material = glow
        _mirror_x(obj)
        return obj

    def assemble_preset(self, x_offset: float, preset: dict) -> None:
        base = (x_offset, 0.0, 0.0)
        hull_t = int(preset["hull"])
        wing_t = int(preset["wing"])
        name = str(preset["name"])

        hull_mat = _principled_mat(f"{name}_Hull", preset["hull_rgba"], metallic=preset["hull_metal"], roughness=preset["hull_rough"])
        wing_mat = _principled_mat(f"{name}_Wing", preset["wing_rgba"], metallic=preset["wing_metal"], roughness=preset["wing_rough"])
        gun_mat = _principled_mat(f"{name}_Gun", preset["gun_rgba"], metallic=0.85, roughness=0.18)
        cockpit_mat = _principled_mat(
            f"{name}_Cockpit",
            (*preset["cockpit_rgb"], 1.0),
            metallic=0.1,
            roughness=0.08,
            alpha=preset["cockpit_alpha"],
            blend=True,
        )

        self.create_hull(hull_t, base, hull_mat)
        self.create_cockpit(base, cockpit_mat)
        self.create_wings(wing_t, base, wing_mat)
        self.create_guns(base, gun_mat)
        if preset.get("thrusters"):
            self.create_thrusters(base)


# Vier bewust verschillende combinaties (hull × wing × kleur × thruster).
ENEMY_PRESETS: list[dict] = [
    {
        "name": "Enemy01_Stinger",
        "hull": 1,
        "wing": 1,
        "hull_rgba": (0.15, 0.55, 0.62, 1.0),
        "wing_rgba": (0.2, 0.65, 0.72, 1.0),
        "gun_rgba": (0.08, 0.08, 0.1, 1.0),
        "cockpit_rgb": (0.5, 0.85, 1.0),
        "cockpit_alpha": 0.38,
        "hull_metal": 0.78,
        "hull_rough": 0.22,
        "wing_metal": 0.55,
        "wing_rough": 0.3,
        "thrusters": True,
    },
    {
        "name": "Enemy02_Brick",
        "hull": 2,
        "wing": 2,
        "hull_rgba": (0.22, 0.28, 0.12, 1.0),
        "wing_rgba": (0.18, 0.24, 0.1, 1.0),
        "gun_rgba": (0.12, 0.12, 0.12, 1.0),
        "cockpit_rgb": (0.35, 0.55, 0.25),
        "cockpit_alpha": 0.45,
        "hull_metal": 0.35,
        "hull_rough": 0.72,
        "wing_metal": 0.4,
        "wing_rough": 0.65,
        "thrusters": False,
    },
    {
        "name": "Enemy03_Razor",
        "hull": 1,
        "wing": 2,
        "hull_rgba": (0.55, 0.06, 0.08, 1.0),
        "wing_rgba": (0.45, 0.05, 0.07, 1.0),
        "gun_rgba": (0.2, 0.2, 0.22, 1.0),
        "cockpit_rgb": (0.9, 0.25, 0.2),
        "cockpit_alpha": 0.42,
        "hull_metal": 0.9,
        "hull_rough": 0.18,
        "wing_metal": 0.88,
        "wing_rough": 0.2,
        "thrusters": True,
    },
    {
        "name": "Enemy04_Maul",
        "hull": 2,
        "wing": 1,
        "hull_rgba": (0.32, 0.12, 0.45, 1.0),
        "wing_rgba": (0.38, 0.14, 0.52, 1.0),
        "gun_rgba": (0.85, 0.7, 0.25, 1.0),
        "cockpit_rgb": (0.65, 0.45, 0.95),
        "cockpit_alpha": 0.36,
        "hull_metal": 0.72,
        "hull_rough": 0.26,
        "wing_metal": 0.68,
        "wing_rough": 0.28,
        "thrusters": True,
    },
]


def main() -> None:
    _clear_scene()
    factory = ModularEnemyFactory()
    spacing = 6.0
    for i, preset in enumerate(ENEMY_PRESETS):
        factory.assemble_preset(i * spacing, preset)


if __name__ == "__main__":
    main()
