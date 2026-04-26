"""
NOVA F-15 v5 — smoother model.

Verbeteringen ten opzichte van v4:
  1. 14 fuselage cross-sections in plaats van 10 → smoother taper
  2. Extra sections in nose-to-body transition zone
  3. Finer tessellation: 0.1mm linear deflection (was 0.5)
     → veel meer mesh-vertices, vloeiende edges in render
  4. Wing root meer geïntegreerd (kleinere offset van fuselage)
  5. Canopy met fijnere profile-points voor smooth bubble

Output: L:\\! 2 Nova v2 OUTPUT !\\Ship_F15_v5\\01_freecad\\
"""

import os
import sys
import math
from pathlib import Path

import FreeCAD as App
import Part
from FreeCAD import Vector, Rotation, Placement


OUTPUT_DIR = Path(os.environ.get(
    "F15_OUTPUT_DIR",
    r"L:\! 2 Nova v2 OUTPUT !\Ship_F15_v5\01_freecad"
))

DOC_NAME = "F15_v5"


# ============================================================
# PROFILE BUILDERS (zelfde als v4)
# ============================================================

def ellipse_profile(x_pos, half_width, half_height, z_offset=900):
    center = Vector(x_pos, 0, z_offset)
    s1 = Vector(x_pos, half_width, z_offset)
    s2 = Vector(x_pos, 0, z_offset + half_height)
    ellipse = Part.Ellipse(s1, s2, center)
    edge = ellipse.toShape()
    return Part.Wire([edge])


def airfoil_profile(chord, thickness, x_pos, y_pos, z_pos, sweep_offset=0):
    leading_edge = Vector(x_pos, y_pos, z_pos)
    trailing_edge = Vector(x_pos - chord + sweep_offset, y_pos, z_pos)
    max_t_x = x_pos - chord * 0.3
    top_max = Vector(max_t_x, y_pos, z_pos + thickness * 0.5)
    bot_max = Vector(max_t_x, y_pos, z_pos - thickness * 0.5)
    near_trail_x = x_pos - chord * 0.95
    near_trail_top = Vector(near_trail_x, y_pos, z_pos + thickness * 0.1)
    near_trail_bot = Vector(near_trail_x, y_pos, z_pos - thickness * 0.1)

    upper_pts = [leading_edge, top_max, near_trail_top, trailing_edge]
    lower_pts = [trailing_edge, near_trail_bot, bot_max, leading_edge]

    upper_spline = Part.BSplineCurve()
    upper_spline.interpolate(upper_pts)
    lower_spline = Part.BSplineCurve()
    lower_spline.interpolate(lower_pts)

    return Part.Wire([upper_spline.toShape(), lower_spline.toShape()])


# ============================================================
# COMPONENT BUILDERS
# ============================================================

def build_fuselage():
    """Hoofdrompf via Loft tussen 14 cross-section profielen.
    Meer sections = vloeiendere taper, geen knik bij nose-body
    overgang."""

    sections = [
        # (x_pos, half_width, half_height, z_offset)
        (9300, 60,  60,  1100),    # neus tip — extra klein
        (8800, 150, 130, 1100),    # neus 2
        (8200, 280, 240, 1100),    # neus 3
        (7500, 430, 360, 1100),    # nose taper begin
        (6800, 580, 460, 1100),    # NIEUW v5: extra section
        (6000, 730, 540, 1100),    # cockpit-area onder
        (5000, 850, 600, 1100),    # main fuselage voor
        (3500, 950, 650, 1100),    # NIEUW v5: extra section
        (2000, 1020, 700, 1100),   # widest point
        (-500, 1080, 700, 1100),   # NIEUW v5: extra section
        (-3000, 1100, 680, 1100),  # achter cockpit
        (-6000, 1280, 620, 1100),  # voor engines
        (-8500, 1480, 560, 1100),  # tail bay
        (-9800, 1300, 500, 1100),  # achter end
    ]

    profiles = []
    for x_pos, hw, hh, z in sections:
        profiles.append(ellipse_profile(x_pos, hw, hh, z))

    fuselage = Part.makeLoft(profiles, True, False, False)
    App.Console.PrintMessage(f"[F15-v5] Fuselage loft: {len(profiles)} sections (smoother)\n")
    return fuselage


def build_wing(side="left"):
    """Wing met root meer geïntegreerd in fuselage."""
    sign = -1 if side == "left" else 1

    # Root iets dieper in fuselage voor smoothere aansluiting
    root_x = 1500
    root_y = sign * 700        # was 900 — nu dichter op fuselage
    root_z = 1300
    root_chord = 5500
    root_thickness = 400

    span = 6700               # iets meer span
    sweep_x_offset = 4500
    tip_x = root_x - sweep_x_offset
    tip_y = sign * (700 + span)
    tip_z = root_z - 100
    tip_chord = 1800
    tip_thickness = 150

    root_wire = airfoil_profile(root_chord, root_thickness,
                                  root_x, root_y, root_z)
    tip_wire = airfoil_profile(tip_chord, tip_thickness,
                                 tip_x, tip_y, tip_z)

    wing = Part.makeLoft([root_wire, tip_wire], True, False, False)
    App.Console.PrintMessage(f"[F15-v5] Wing {side} built\n")
    return wing


def build_vertical_tail(side="left"):
    sign = -1 if side == "left" else 1

    base_x = -7500
    base_y = sign * 1100
    base_z = 1700

    length = 2400
    width = 100
    height = 2600

    box = Part.makeBox(length, width, height)
    placement = Placement()
    placement.Base = Vector(base_x - length/2, base_y - width/2, base_z)
    cant_angle = sign * -10
    rotation = Rotation(Vector(1, 0, 0), cant_angle)
    placement.Rotation = rotation
    box.Placement = placement

    cut_block = Part.makeBox(1500, 200, 1500)
    cut_placement = Placement()
    cut_placement.Base = Vector(base_x + 800, base_y - 100, base_z + 1500)
    cut_placement.Rotation = Rotation(Vector(0, 1, 0), 30)
    cut_block.Placement = cut_placement

    tapered = box.cut(cut_block)
    App.Console.PrintMessage(f"[F15-v5] Vertical tail {side} built\n")
    return tapered


def build_horizontal_stabilizer(side="left"):
    sign = -1 if side == "left" else 1

    root_x = -8000
    root_y = sign * 1300
    root_z = 1200

    span = 2500
    sweep_offset = 1500
    tip_x = root_x - sweep_offset
    tip_y = sign * (1300 + span)
    tip_z = 1200
    root_chord = 2000
    tip_chord = 700
    thickness = 100

    root_wire = airfoil_profile(root_chord, thickness,
                                  root_x, root_y, root_z)
    tip_wire = airfoil_profile(tip_chord, thickness * 0.5,
                                 tip_x, tip_y, tip_z)
    stab = Part.makeLoft([root_wire, tip_wire], True, False, False)
    App.Console.PrintMessage(f"[F15-v5] Horizontal stab {side} built\n")
    return stab


def build_engine_nacelle(side="left"):
    sign = -1 if side == "left" else 1

    radius = 700
    length = 6500
    x_start = -10500
    y_pos = sign * 950
    z_pos = 850

    cyl = Part.makeCylinder(radius, length, Vector(x_start, y_pos, z_pos),
                              Vector(1, 0, 0))
    App.Console.PrintMessage(f"[F15-v5] Engine nacelle {side} built\n")
    return cyl


def build_engine_outlet(side="left"):
    sign = -1 if side == "left" else 1

    radius = 600
    length = 400
    x_start = -10800
    y_pos = sign * 950
    z_pos = 850

    outlet = Part.makeCylinder(radius, length, Vector(x_start, y_pos, z_pos),
                                 Vector(1, 0, 0))
    App.Console.PrintMessage(f"[F15-v5] Engine outlet {side} built\n")
    return outlet


def build_canopy():
    """Bubble canopy met meer profile-points voor smooth shape."""
    # Meer punten = vloeiendere bubble
    pts = [
        Vector(4500, 0, 1700),    # voor onderkant
        Vector(4450, 0, 1850),    # NIEUW v5: smoother nose
        Vector(4350, 0, 2050),    # NIEUW v5
        Vector(4150, 0, 2200),    # NIEUW v5
        Vector(3700, 0, 2300),    # hoogste punt
        Vector(3000, 0, 2300),    # NIEUW v5: plateau top
        Vector(2300, 0, 2200),    # NIEUW v5
        Vector(1700, 0, 2000),    # achterkant taper begin
        Vector(1500, 0, 1850),    # NIEUW v5
        Vector(1500, 0, 1700),    # achter onderkant
        Vector(4500, 0, 1700),    # gesloten
    ]

    edges = []
    for i in range(len(pts) - 1):
        line = Part.LineSegment(pts[i], pts[i+1])
        edges.append(line.toShape())
    wire = Part.Wire(edges)
    face = Part.Face(wire)

    canopy = face.revolve(Vector(0, 0, 1700), Vector(1, 0, 0), 180)
    App.Console.PrintMessage(f"[F15-v5] Canopy built (smoother profile)\n")
    return canopy


def build_air_intake(side="left"):
    sign = -1 if side == "left" else 1

    length = 2800
    width = 700
    height = 800

    x_start = 2800
    y_pos = sign * (900 + 50)
    z_pos = 600

    if side == "left":
        x_corner = x_start - length
        y_corner = y_pos - width
    else:
        x_corner = x_start - length
        y_corner = y_pos

    intake = Part.makeBox(length, width, height,
                            Vector(x_corner, y_corner, z_pos))
    App.Console.PrintMessage(f"[F15-v5] Air intake {side} built\n")
    return intake


def build_pylon(side="left"):
    sign = -1 if side == "left" else 1

    radius = 150
    length = 2500
    x_start = -1000
    y_pos = sign * 3500
    z_pos = 1000

    pylon = Part.makeCylinder(radius, length,
                                Vector(x_start, y_pos, z_pos),
                                Vector(1, 0, 0))
    App.Console.PrintMessage(f"[F15-v5] Pylon {side} built\n")
    return pylon


# ============================================================
# MAIN ASSEMBLY
# ============================================================

def build_f15():
    components = {}

    try:
        components["fuselage"] = build_fuselage()
    except Exception as e:
        App.Console.PrintError(f"[F15-v5] Fuselage failed: {e}\n")
        raise

    try:
        components["wing_left"] = build_wing("left")
        components["wing_right"] = build_wing("right")
    except Exception as e:
        App.Console.PrintError(f"[F15-v5] Wings failed: {e}\n")
        raise

    try:
        components["v_tail_left"] = build_vertical_tail("left")
        components["v_tail_right"] = build_vertical_tail("right")
    except Exception as e:
        App.Console.PrintError(f"[F15-v5] Vertical tails failed: {e}\n")

    try:
        components["h_stab_left"] = build_horizontal_stabilizer("left")
        components["h_stab_right"] = build_horizontal_stabilizer("right")
    except Exception as e:
        App.Console.PrintError(f"[F15-v5] Horizontal stabs failed: {e}\n")

    try:
        components["engine_left"] = build_engine_nacelle("left")
        components["engine_right"] = build_engine_nacelle("right")
        components["outlet_left"] = build_engine_outlet("left")
        components["outlet_right"] = build_engine_outlet("right")
    except Exception as e:
        App.Console.PrintError(f"[F15-v5] Engines failed: {e}\n")

    try:
        components["canopy"] = build_canopy()
    except Exception as e:
        App.Console.PrintError(f"[F15-v5] Canopy failed: {e}\n")

    try:
        components["intake_left"] = build_air_intake("left")
        components["intake_right"] = build_air_intake("right")
    except Exception as e:
        App.Console.PrintError(f"[F15-v5] Intakes failed: {e}\n")

    try:
        components["pylon_left"] = build_pylon("left")
        components["pylon_right"] = build_pylon("right")
    except Exception as e:
        App.Console.PrintError(f"[F15-v5] Pylons failed: {e}\n")

    if not components:
        raise RuntimeError("Geen componenten succesvol gebouwd")

    base = components.pop("fuselage")
    others = list(components.values())

    if others:
        ship = base.fuse(others)
        App.Console.PrintMessage(f"[F15-v5] Fused {len(others)} components\n")
    else:
        ship = base

    return ship, components


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    doc = App.newDocument(DOC_NAME)
    try:
        App.Console.PrintMessage(f"[F15-v5] Building smoother model...\n")
        ship, parts = build_f15()

        feature = doc.addObject("Part::Feature", "F15_v5_Body")
        feature.Shape = ship
        doc.recompute()

        # Export STEP
        step_path = str(OUTPUT_DIR / "f15_v5.step")
        Part.export([feature], step_path)
        App.Console.PrintMessage(f"[F15-v5] STEP saved: {step_path}\n")

        # Export STL met FINER tessellation
        # 0.1mm in plaats van 0.5mm = 5x meer vertices = smoother
        stl_path = str(OUTPUT_DIR / "f15_v5.stl")
        import Mesh
        mesh = Mesh.Mesh(ship.tessellate(0.1))  # FINER!
        mesh.write(stl_path)
        App.Console.PrintMessage(f"[F15-v5] STL saved (fine tessellation): {stl_path}\n")

        fcstd_path = str(OUTPUT_DIR / "f15_v5.FCStd")
        doc.saveAs(fcstd_path)

        # Inventory met v5 stats
        inventory_path = OUTPUT_DIR / "parts_inventory.md"
        with open(inventory_path, "w") as f:
            f.write("# F-15 v5 Parts Inventory\n\n")
            f.write("Verbeteringen vs v4:\n")
            f.write("- 14 fuselage cross-sections (was 10)\n")
            f.write("- Extra nose-to-body transition profiles\n")
            f.write("- Wing root dichter op fuselage\n")
            f.write("- Canopy met 11 profile points (was 7)\n")
            f.write("- Tessellation 0.1mm (was 0.5mm)\n\n")
            f.write(f"Successfully built: fuselage + {len(parts)} components\n\n")
            f.write("| Component | Status |\n|---|---|\n")
            f.write("| fuselage | OK (14 sections) |\n")
            for name in parts.keys():
                f.write(f"| {name} | OK |\n")
            f.write("\n## Bounding Box\n\n")
            bb = ship.BoundBox
            f.write(f"- X (length): {bb.XMin:.0f} to {bb.XMax:.0f}, span {bb.XLength:.0f}\n")
            f.write(f"- Y (width):  {bb.YMin:.0f} to {bb.YMax:.0f}, span {bb.YLength:.0f}\n")
            f.write(f"- Z (height): {bb.ZMin:.0f} to {bb.ZMax:.0f}, span {bb.ZLength:.0f}\n")

        App.Console.PrintMessage("[F15-v5] Build complete\n")
        return 0

    except Exception as e:
        App.Console.PrintError(f"[F15-v5] Build failed: {e}\n")
        import traceback
        App.Console.PrintError(traceback.format_exc() + "\n")
        return 1

    finally:
        App.closeDocument(doc.Name)


# freecadcmd laadt als module; altijd main.
try:
    sys.exit(main())
except SystemExit:
    raise
except Exception as _e:  # noqa: BLE001
    try:
        App.Console.PrintError(f"f15_v5_freecad failed: {_e}\n")
    except Exception:
        print(f"f15_v5_freecad failed: {_e}", file=sys.stderr)
    sys.exit(1)
