"""
Vijf vaste spelers-/NPC-schepen: combineert
- `blender modulair ship & pallette.py` (hull-stijlen, cockpit-glas, neon, spiegeling)
- `modulair hardpoint rocket system.py` (raket + railgun op hardpoints)

Multi-wing: meerdere gespiegelde vleugellagen per schip.
Hardpoints: meerdere slots per zijde (raket en/of railgun).

Run in Blender UI of headless:
  blender --background --python "...five_modular_ships_hardpoints.py"

Export naar ``BLENDER_OUTPUT_DIR`` (standaard Nova OUTPUT\\Blender).
Override: omgevingsvariabele ``NOVA_BLENDER_OUTPUT``.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import bpy

BLENDER_OUTPUT_DIR = os.environ.get(
    "NOVA_BLENDER_OUTPUT",
    r"L:\! 2 Nova v2 OUTPUT !\Blender",
)


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
    emission_strength: float = 8.0,
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
        if hasattr(mat, "shadow_method"):
            mat.shadow_method = "HASHED"
    return mat


def _mirror_x(obj: bpy.types.Object) -> None:
    mod = obj.modifiers.new(name="Mirror", type="MIRROR")
    mod.use_axis[0] = True


def _ensure_output_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _export_scene(out_dir: str, stem_name: str) -> tuple[str, str]:
    _ensure_output_dir(out_dir)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    stem = os.path.join(out_dir, f"{stem_name}_{ts}")
    blend_path = stem + ".blend"
    glb_path = stem + ".glb"
    bpy.ops.wm.save_as_mainfile(filepath=blend_path, check_existing=False)
    try:
        bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB", export_apply=True)
    except TypeError:
        bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB")
    latest = os.path.join(out_dir, f"{stem_name}_latest.txt")
    with open(latest, "w", encoding="utf-8") as f:
        f.write(f"blend={blend_path}\nglb={glb_path}\nutc={datetime.now(timezone.utc).isoformat()}\n")
    return blend_path, glb_path


class WeaponFactory:
    """Uit modulair hardpoint rocket system.py — met unieke materiaalnamen per schip."""

    def __init__(self, mat_hull: bpy.types.Material, mat_neon: bpy.types.Material) -> None:
        self.mat_hull = mat_hull
        self.mat_neon = mat_neon

    def create_missile(self, pos: tuple[float, float, float], name_suffix: str) -> bpy.types.Object:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.5, location=pos)
        missile = bpy.context.object
        missile.name = f"Missile_{name_suffix}"
        missile.rotation_euler[0] = 1.57
        missile.active_material = self.mat_hull
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.2, radius2=0.2, depth=0.3, location=(pos[0], pos[1] - 0.6, pos[2]))
        fin = bpy.context.object
        fin.name = f"MissileFin_{name_suffix}"
        fin.parent = missile
        fin.active_material = self.mat_hull
        return missile

    def create_railgun(self, pos: tuple[float, float, float], name_suffix: str) -> bpy.types.Object:
        bpy.ops.mesh.primitive_cube_add(size=0.2, location=pos)
        base = bpy.context.object
        base.name = f"RailBase_{name_suffix}"
        base.scale = (1, 4, 0.5)
        base.active_material = self.mat_hull
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(pos[0], pos[1] + 0.5, pos[2]))
        barrel = bpy.context.object
        barrel.name = f"RailBarrel_{name_suffix}"
        barrel.rotation_euler[0] = 1.57
        barrel.active_material = self.mat_neon
        barrel.parent = base
        return base


def _build_hull(prefix: str, style: int, pos: tuple[float, float, float], mat: bpy.types.Material) -> bpy.types.Object:
    if style == 1:
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.8, radius2=0.1, depth=5, location=pos)
        obj = bpy.context.object
        obj.name = f"{prefix}_Hull"
        obj.rotation_euler[0] = 1.57
    else:
        bpy.ops.mesh.primitive_cube_add(size=1.5, location=pos)
        obj = bpy.context.object
        obj.name = f"{prefix}_Hull"
        obj.scale = (0.85, 1.5, 0.8)
    obj.active_material = mat
    return obj


def _build_cockpit(prefix: str, pos: tuple[float, float, float], rgb: tuple[float, float, float], alpha: float) -> bpy.types.Object:
    loc = (pos[0], pos[1] + 1.0, pos[2] + 0.4)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=loc)
    obj = bpy.context.object
    obj.name = f"{prefix}_Cockpit"
    obj.scale = (0.7, 1.5, 0.4)
    mat = _principled_mat(
        f"{prefix}_Glass",
        (*rgb, 1.0),
        metallic=0.05,
        roughness=0.1,
        alpha=alpha,
        blend=True,
    )
    obj.active_material = mat
    return obj


def _build_wing_layer(
    prefix: str,
    layer_idx: int,
    pos: tuple[float, float, float],
    *,
    kind: str,
    wing_dx: float,
    scale: tuple[float, float, float],
    y_off: float,
    z_off: float,
    mat: bpy.types.Material,
) -> bpy.types.Object:
    base = (pos[0] + wing_dx, pos[1] + y_off, pos[2] + z_off)
    if kind == "delta":
        bpy.ops.mesh.primitive_cylinder_add(vertices=3, radius=1.4, depth=0.12, location=base)
        obj = bpy.context.object
        obj.rotation_euler[2] = 1.57
    else:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=base)
        obj = bpy.context.object
        obj.scale = scale
    obj.name = f"{prefix}_Wing_L{layer_idx}"
    obj.active_material = mat
    _mirror_x(obj)
    return obj


def _place_hardpoints_symmetric(
    wf: WeaponFactory,
    prefix: str,
    base: tuple[float, float, float],
    slots: list[tuple[float, float, float, str]],
) -> None:
    """slots: (x_right, y, z, 'missile'|'rail') — spiegelt naar -x."""
    for i, (xr, y, z, kind) in enumerate(slots):
        pr = (base[0] + xr, base[1] + y, base[2] + z)
        pl = (base[0] - xr, base[1] + y, base[2] + z)
        suf_r = f"{prefix}_hp{i}_R"
        suf_l = f"{prefix}_hp{i}_L"
        if kind == "missile":
            wf.create_missile(pr, suf_r)
            wf.create_missile(pl, suf_l)
        else:
            wf.create_railgun(pr, suf_r)
            wf.create_railgun(pl, suf_l)


def _assemble_ship(x_offset: float, preset: dict) -> None:
    base = (x_offset, 0.0, 0.0)
    pfx = str(preset["id"])
    hull_m = _principled_mat(
        f"{pfx}_HullMat",
        preset["hull_rgba"],
        metallic=preset["hull_metal"],
        roughness=preset["hull_rough"],
    )
    wing_m = _principled_mat(
        f"{pfx}_WingMat",
        preset["wing_rgba"],
        metallic=preset["wing_metal"],
        roughness=preset["wing_rough"],
    )
    wpn_metal = _principled_mat(f"{pfx}_WpnMetal", (0.06, 0.06, 0.07, 1.0), metallic=0.9, roughness=0.2)
    wpn_neon = _principled_mat(
        f"{pfx}_WpnNeon",
        (0.02, 0.02, 0.02, 1.0),
        emission_rgb=tuple(preset["neon_rgb"]),
        emission_strength=float(preset["neon_strength"]),
    )

    _build_hull(pfx, int(preset["hull"]), base, hull_m)
    _build_cockpit(pfx, base, tuple(preset["cockpit_rgb"]), float(preset["cockpit_alpha"]))

    for wi, wdef in enumerate(preset["wings"]):
        _build_wing_layer(
            pfx,
            wi,
            base,
            kind=str(wdef["kind"]),
            wing_dx=float(wdef.get("dx", 1.4)),
            scale=(
                float(wdef.get("sx", 2.0)),
                float(wdef.get("sy", 0.75)),
                float(wdef.get("sz", 0.12)),
            ),
            y_off=float(wdef.get("y", 0.0)),
            z_off=float(wdef.get("z", 0.0)),
            mat=wing_m,
        )

    wf = WeaponFactory(wpn_metal, wpn_neon)
    slots = [(float(s[0]), float(s[1]), float(s[2]), str(s[3])) for s in preset["hardpoints"]]
    _place_hardpoints_symmetric(wf, pfx, base, slots)


# Vijf schepen: verschillende hull, multi-wing, verschillende hardpoint-belasting.
SHIP_PRESETS: list[dict] = [
    {
        "id": "Ship01_Sparrow",
        "hull": 1,
        "hull_rgba": (0.2, 0.45, 0.55, 1.0),
        "wing_rgba": (0.25, 0.55, 0.65, 1.0),
        "hull_metal": 0.82,
        "hull_rough": 0.22,
        "wing_metal": 0.55,
        "wing_rough": 0.32,
        "cockpit_rgb": (0.4, 0.85, 1.0),
        "cockpit_alpha": 0.38,
        "neon_rgb": (0.2, 0.95, 1.0),
        "neon_strength": 11.0,
        "wings": [
            {"kind": "delta", "dx": 1.35, "y": 0.0, "z": 0.0},
            {"kind": "box", "dx": 0.9, "y": 1.1, "z": 0.25, "sx": 1.2, "sy": 0.35, "sz": 0.08},
        ],
        "hardpoints": [
            (1.1, -0.2, -0.35, "missile"),
            (1.9, -0.5, -0.45, "missile"),
        ],
    },
    {
        "id": "Ship02_Bulk",
        "hull": 2,
        "hull_rgba": (0.35, 0.32, 0.28, 1.0),
        "wing_rgba": (0.4, 0.36, 0.3, 1.0),
        "hull_metal": 0.45,
        "hull_rough": 0.55,
        "wing_metal": 0.5,
        "wing_rough": 0.5,
        "cockpit_rgb": (0.5, 0.75, 0.4),
        "cockpit_alpha": 0.42,
        "neon_rgb": (1.0, 0.35, 0.05),
        "neon_strength": 10.0,
        "wings": [
            {"kind": "box", "dx": 1.6, "y": -0.1, "z": 0.0, "sx": 2.4, "sy": 0.9, "sz": 0.14},
            {"kind": "box", "dx": 1.2, "y": 0.4, "z": -0.15, "sx": 1.6, "sy": 0.5, "sz": 0.1},
        ],
        "hardpoints": [
            (1.4, 0.0, -0.4, "missile"),
            (2.2, -0.3, -0.5, "rail"),
            (2.8, -0.6, -0.55, "missile"),
        ],
    },
    {
        "id": "Ship03_Dart",
        "hull": 1,
        "hull_rgba": (0.55, 0.15, 0.18, 1.0),
        "wing_rgba": (0.5, 0.12, 0.16, 1.0),
        "hull_metal": 0.88,
        "hull_rough": 0.18,
        "wing_metal": 0.75,
        "wing_rough": 0.22,
        "cockpit_rgb": (1.0, 0.45, 0.35),
        "cockpit_alpha": 0.4,
        "neon_rgb": (1.0, 0.15, 0.05),
        "neon_strength": 12.0,
        "wings": [
            {"kind": "box", "dx": 1.25, "y": -0.05, "z": 0.1, "sx": 1.8, "sy": 0.45, "sz": 0.09},
            {"kind": "box", "dx": 1.0, "y": 0.35, "z": 0.0, "sx": 1.2, "sy": 0.3, "sz": 0.07},
            {"kind": "delta", "dx": 1.5, "y": -0.4, "z": -0.05},
        ],
        "hardpoints": [
            (1.0, 0.2, -0.25, "rail"),
            (1.7, -0.1, -0.4, "missile"),
        ],
    },
    {
        "id": "Ship04_Spire",
        "hull": 2,
        "hull_rgba": (0.22, 0.2, 0.42, 1.0),
        "wing_rgba": (0.28, 0.22, 0.55, 1.0),
        "hull_metal": 0.7,
        "hull_rough": 0.28,
        "wing_metal": 0.62,
        "wing_rough": 0.3,
        "cockpit_rgb": (0.65, 0.5, 1.0),
        "cockpit_alpha": 0.36,
        "neon_rgb": (0.75, 0.35, 1.0),
        "neon_strength": 9.0,
        "wings": [
            {"kind": "delta", "dx": 1.55, "y": 0.0, "z": 0.05},
            {"kind": "delta", "dx": 1.15, "y": -0.35, "z": -0.12},
            {"kind": "box", "dx": 0.85, "y": 0.9, "z": 0.2, "sx": 1.1, "sy": 0.4, "sz": 0.08},
        ],
        "hardpoints": [
            (1.2, -0.15, -0.38, "missile"),
            (1.9, -0.35, -0.48, "missile"),
            (2.5, -0.55, -0.52, "missile"),
            (3.0, -0.75, -0.55, "missile"),
        ],
    },
    {
        "id": "Ship05_Mule",
        "hull": 2,
        "hull_rgba": (0.28, 0.42, 0.22, 1.0),
        "wing_rgba": (0.32, 0.48, 0.25, 1.0),
        "hull_metal": 0.4,
        "hull_rough": 0.62,
        "wing_metal": 0.42,
        "wing_rough": 0.58,
        "cockpit_rgb": (0.55, 0.9, 0.55),
        "cockpit_alpha": 0.44,
        "neon_rgb": (0.15, 1.0, 0.45),
        "neon_strength": 10.5,
        "wings": [
            {"kind": "box", "dx": 1.75, "y": 0.0, "z": 0.0, "sx": 2.8, "sy": 1.0, "sz": 0.16},
            {"kind": "box", "dx": 1.4, "y": -0.25, "z": -0.12, "sx": 2.0, "sy": 0.65, "sz": 0.12},
            {"kind": "box", "dx": 1.1, "y": 0.55, "z": 0.15, "sx": 1.4, "sy": 0.4, "sz": 0.09},
        ],
        "hardpoints": [
            (1.3, 0.1, -0.42, "rail"),
            (2.0, -0.15, -0.48, "missile"),
            (2.7, -0.35, -0.52, "rail"),
            (3.2, -0.55, -0.55, "missile"),
        ],
    },
]


def main() -> None:
    _clear_scene()
    spacing = 14.0
    for i, preset in enumerate(SHIP_PRESETS):
        _assemble_ship(i * spacing, preset)
    blend_path, glb_path = _export_scene(BLENDER_OUTPUT_DIR, "five_modular_ships")
    print(f"[five_modular_ships] blend -> {blend_path}")
    print(f"[five_modular_ships] glb   -> {glb_path}")


if __name__ == "__main__":
    main()
