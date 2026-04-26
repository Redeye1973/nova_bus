"""
NOVA F-15 Eagle parametric model — v4.

Pure FreeCAD Python script voor headless execution via
FreeCADCmd.exe (door nova_host_bridge /freecad/script endpoint).

Verschil met v1-v3 (primitive fuse via JSON-spec):
  - Fuselage via Loft tussen cross-section profielen (smooth taper)
  - Wings via Loft tussen root + tip airfoil (echte sweep + taper)
  - Canopy via Revolve (echte bubble shape)
  - Volledige FreeCAD Part API beschikbaar — niet beperkt tot
    Box/Cylinder/Cone/Cut

Conventie (zie FreeCAD_API_Referentie.md):
  X-as = Length  (neus → staart richting, neus = +X)
  Y-as = Width   (vleugel-spanning, links = -Y)
  Z-as = Height  (omhoog = +Z)

Origin op zwaartepunt onder fuselage. Schaal: mm waar 1 mm = 1 meter
voor proportie. F-15 echte: 19m × 13m × 5.6m → 19000 × 13000 × 5600.

Output: STEP + STL in F15_OUTPUT_DIR (env) of default
        L:\\! 2 Nova v2 OUTPUT !\\Ship_F15_v4\\01_freecad\\
"""

import os
import sys
import math
from pathlib import Path

import FreeCAD as App
import Part
from FreeCAD import Vector, Rotation, Placement


# ============================================================
# CONFIGURATIE
# ============================================================

OUTPUT_DIR = Path(os.environ.get(
    "F15_OUTPUT_DIR",
    r"L:\! 2 Nova v2 OUTPUT !\Ship_F15_v4\01_freecad"
))

DOC_NAME = "F15_v4"


# ============================================================
# HELPERS — profile builders
# ============================================================

def circle_profile(x_pos, radius, y_offset=0, z_offset=900):
    """Cirkelvormig profiel in YZ-plane op gegeven X-positie.
    Returns een gesloten Wire."""
    center = Vector(x_pos, y_offset, z_offset)
    normal = Vector(1, 0, 0)
    circle = Part.Circle(center, normal, radius)
    edge = circle.toShape()
    return Part.Wire([edge])


def ellipse_profile(x_pos, half_width, half_height, z_offset=900):
    """Elliptisch profiel in YZ-plane.
    half_width = halve Y-as, half_height = halve Z-as."""
    center = Vector(x_pos, 0, z_offset)
    # Part.Ellipse(s1, s2, center) waar s1 op major en s2 op minor as
    s1 = Vector(x_pos, half_width, z_offset)
    s2 = Vector(x_pos, 0, z_offset + half_height)
    ellipse = Part.Ellipse(s1, s2, center)
    edge = ellipse.toShape()
    return Part.Wire([edge])


def rounded_rect_profile(x_pos, half_width, half_height, z_offset=900,
                          fillet_radius=150):
    """Rechthoek met afgeronde hoeken in YZ-plane.
    Voor fuselage cross-section met platte onderkant en bolle bovenkant
    gebruiken we ellipse boven en flat onder. Voor eenvoud nu: pure
    ellipse die goed approximeert."""
    return ellipse_profile(x_pos, half_width, half_height, z_offset)


def airfoil_profile(chord, thickness, x_pos, y_pos, z_pos, sweep_offset=0):
    """Vereenvoudigd airfoil-profiel — symmetrisch, dik in midden.

    Bouwt op via 4-punts NACA-achtige outline:
    - leading edge punt (voorkant)
    - max thickness punt (boven en onder, op 30% chord)
    - trailing edge punt (achterkant)

    chord = lengte voorkant-achterkant (langs X)
    thickness = max dikte (langs Z)
    x_pos, y_pos, z_pos = positie van leading edge
    sweep_offset = X-offset voor trailing edge (voor swept wings)
    """
    # 8-punts approximation, mirrored bovenkant
    leading_edge = Vector(x_pos, y_pos, z_pos)
    trailing_edge = Vector(x_pos - chord + sweep_offset, y_pos, z_pos)

    # Bovenste curve: leading → max-thickness-top → trailing
    max_t_x = x_pos - chord * 0.3
    top_max = Vector(max_t_x, y_pos, z_pos + thickness * 0.5)
    bot_max = Vector(max_t_x, y_pos, z_pos - thickness * 0.5)

    # 5% chord vóór trailing voor smooth closing
    near_trail_x = x_pos - chord * 0.95
    near_trail_top = Vector(near_trail_x, y_pos, z_pos + thickness * 0.1)
    near_trail_bot = Vector(near_trail_x, y_pos, z_pos - thickness * 0.1)

    # Bouw via BSpline voor smooth shape
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
    """Hoofdrompf via Loft tussen 8 cross-section profielen.
    Profielen lopen van neus (+X) naar staart (-X)."""

    sections = [
        # (x_pos, half_width, half_height, z_offset)
        # NEUS — klein cirkelvormig
        (9300, 80,  80,  1100),    # neuspunt
        (8500, 200, 200, 1100),    # voor radar dome
        (7000, 400, 350, 1100),    # nose taper
        (5500, 700, 500, 1100),    # cockpit area onder
        (3500, 900, 600, 1100),    # main fuselage voor
        (1000, 1000, 700, 1100),   # widest point
        (-2500, 1100, 700, 1100),  # achter cockpit
        (-6000, 1300, 600, 1100),  # voor engines, breder
        (-8500, 1500, 550, 1100),  # tail bay
        (-9800, 1300, 500, 1100),  # achter end voor outlets
    ]

    profiles = []
    for x_pos, hw, hh, z in sections:
        profiles.append(ellipse_profile(x_pos, hw, hh, z))

    # Loft maakt smooth surface tussen profielen
    fuselage = Part.makeLoft(profiles, True, False, False)
    App.Console.PrintMessage(f"[F15] Fuselage loft: {len(profiles)} sections\n")
    return fuselage


def build_wing(side="left"):
    """Wing via Loft tussen root airfoil en tip airfoil.
    Sweep + taper ingebouwd in tip positie + chord verschil.

    F-15 echte data:
      Wing root chord: ~5500mm
      Wing tip chord:  ~1800mm
      Wing span (één kant): ~6500mm
      Sweep angle leading edge: 38°
      Dihedral: -1° (anhedral, lichte negatieve dihedral)
    """
    sign = -1 if side == "left" else 1

    # Root airfoil — bij fuselage zijkant
    root_x = 1500          # voor de cockpit, achter het midden
    root_y = sign * 900    # op fuselage zijkant
    root_z = 1300          # mid-fuselage hoogte
    root_chord = 5500
    root_thickness = 400

    # Tip airfoil — sweep naar achteren + outboard + lichte anhedral
    span = 6500
    sweep_x_offset = 4500  # 38° sweep ≈ tan(38°) × 6500 ≈ 5078, iets minder
    tip_x = root_x - sweep_x_offset
    tip_y = sign * (900 + span)
    tip_z = root_z - 100   # licht omlaag = -1° anhedral
    tip_chord = 1800
    tip_thickness = 150

    # Bouw twee airfoils
    root_wire = airfoil_profile(root_chord, root_thickness,
                                  root_x, root_y, root_z)
    tip_wire = airfoil_profile(tip_chord, tip_thickness,
                                 tip_x, tip_y, tip_z)

    # Loft tussen beide
    wing = Part.makeLoft([root_wire, tip_wire], True, False, False)
    App.Console.PrintMessage(f"[F15] Wing {side} built\n")
    return wing


def build_vertical_tail(side="left"):
    """Verticale staart — gecanteerd 10° naar buiten.
    F-15 heeft TWEE verticale tails op de engine-nacelles."""
    sign = -1 if side == "left" else 1

    # Tail base profiel (rechthoekig met afgeronde top)
    # Plaats op engine nacelle achterkant
    base_x = -7500
    base_y = sign * 1100
    base_z = 1700  # op fuselage tail

    # Maak via Box + rotation, eenvoudige verticale stab
    length = 2400  # langs X (chord)
    width = 100    # dik (langs Y)
    height = 2600  # omhoog (langs Z)

    box = Part.makeBox(length, width, height)
    # Position: center op base_x, base_y, vanaf Z=base_z
    placement = Placement()
    placement.Base = Vector(base_x - length/2, base_y - width/2, base_z)

    # Rotation: 10° canted buitenwaarts (om X-as)
    cant_angle = sign * -10  # left=-10, right=+10 in onze conventie
    rotation = Rotation(Vector(1, 0, 0), cant_angle)
    placement.Rotation = rotation

    box.Placement = placement

    # Taper de leading edge: cut diagonal
    cut_block = Part.makeBox(1500, 200, 1500)
    cut_placement = Placement()
    cut_placement.Base = Vector(base_x + 800, base_y - 100, base_z + 1500)
    cut_placement.Rotation = Rotation(Vector(0, 1, 0), 30)
    cut_block.Placement = cut_placement

    tapered = box.cut(cut_block)
    App.Console.PrintMessage(f"[F15] Vertical tail {side} built\n")
    return tapered


def build_horizontal_stabilizer(side="left"):
    """Horizontale stabilizer — getapered, gesweept.
    F-15 heeft die op de tail-section, OUTSIDE de vertical tails."""
    sign = -1 if side == "left" else 1

    # Tapered swept stabilizer via Loft van root naar tip
    root_x = -8000
    root_y = sign * 1300  # buiten fuselage
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
    App.Console.PrintMessage(f"[F15] Horizontal stab {side} built\n")
    return stab


def build_engine_nacelle(side="left"):
    """Engine nacelle — cilinder onder fuselage tail-section.
    F-15 heeft twee parallelle engines, zichtbaar achter de wings."""
    sign = -1 if side == "left" else 1

    radius = 700
    length = 6500
    x_start = -10500   # achter end (uitlaat)
    y_pos = sign * 950 # naast fuselage centerline
    z_pos = 850        # iets onder fuselage center

    cyl = Part.makeCylinder(radius, length, Vector(x_start, y_pos, z_pos),
                              Vector(1, 0, 0))
    App.Console.PrintMessage(f"[F15] Engine nacelle {side} built\n")
    return cyl


def build_engine_outlet(side="left"):
    """Engine uitlaat — kortere, smallere ring achter nacelle voor visueel
    detail."""
    sign = -1 if side == "left" else 1

    radius = 600
    length = 400
    x_start = -10800
    y_pos = sign * 950
    z_pos = 850

    outlet = Part.makeCylinder(radius, length, Vector(x_start, y_pos, z_pos),
                                 Vector(1, 0, 0))
    App.Console.PrintMessage(f"[F15] Engine outlet {side} built\n")
    return outlet


def build_canopy():
    """Bubble canopy via revolve van profile.

    Strategie: maak 2D profile in XZ-plane (zijaanzicht van canopy),
    revolve dat 180° om X-as voor halve bubble shape.
    """
    # Canopy zit voor cockpit, bovenop fuselage
    # X-range: van 4500 (voorkant canopy) tot 1500 (achterkant)
    # Top Z: 2300, base Z: 1700

    # 2D profile points in XZ-plane (Y=0)
    pts = [
        Vector(4500, 0, 1700),    # voor onderkant
        Vector(4400, 0, 2000),    # voorkant top curve start
        Vector(3500, 0, 2300),    # hoogste punt
        Vector(2500, 0, 2250),    # midden top
        Vector(1500, 0, 1900),    # achterkant taper
        Vector(1500, 0, 1700),    # achter onderkant
        Vector(4500, 0, 1700),    # gesloten — terug naar start
    ]

    # Bouw als wire (lijn-segmenten)
    edges = []
    for i in range(len(pts) - 1):
        line = Part.LineSegment(pts[i], pts[i+1])
        edges.append(line.toShape())
    wire = Part.Wire(edges)
    face = Part.Face(wire)

    # Revolve 180° om X-as — geeft halve bubble
    canopy = face.revolve(Vector(0, 0, 1700), Vector(1, 0, 0), 180)
    App.Console.PrintMessage(f"[F15] Canopy built via revolve\n")
    return canopy


def build_air_intake(side="left"):
    """Air intake onder cockpit — rechthoekig met gerounde bovenkant."""
    sign = -1 if side == "left" else 1

    # Box met chamfer aan binnenkant
    length = 2800   # langs X
    width = 700     # langs Y
    height = 800    # langs Z

    x_start = 2800
    y_pos = sign * (900 + 50)  # naast fuselage
    z_pos = 600  # onder cockpit

    if side == "left":
        x_corner = x_start - length
        y_corner = y_pos - width
    else:
        x_corner = x_start - length
        y_corner = y_pos

    intake = Part.makeBox(length, width, height,
                            Vector(x_corner, y_corner, z_pos))
    App.Console.PrintMessage(f"[F15] Air intake {side} built\n")
    return intake


def build_pylon(side="left"):
    """Underwing pylon — kleine cilinder voor mass/silhouet."""
    sign = -1 if side == "left" else 1

    radius = 150
    length = 2500
    x_start = -1000  # midden onder wing
    y_pos = sign * 3500  # midden van wing-span
    z_pos = 1000  # onder wing

    pylon = Part.makeCylinder(radius, length,
                                Vector(x_start, y_pos, z_pos),
                                Vector(1, 0, 0))
    App.Console.PrintMessage(f"[F15] Pylon {side} built\n")
    return pylon


# ============================================================
# MAIN ASSEMBLY
# ============================================================

def build_f15():
    """Bouw complete F-15 model.
    Returns assembled solid + onderdelen-dict voor debug."""

    components = {}

    try:
        components["fuselage"] = build_fuselage()
    except Exception as e:
        App.Console.PrintError(f"[F15] Fuselage failed: {e}\n")
        raise

    try:
        components["wing_left"] = build_wing("left")
        components["wing_right"] = build_wing("right")
    except Exception as e:
        App.Console.PrintError(f"[F15] Wings failed: {e}\n")
        raise

    try:
        components["v_tail_left"] = build_vertical_tail("left")
        components["v_tail_right"] = build_vertical_tail("right")
    except Exception as e:
        App.Console.PrintError(f"[F15] Vertical tails failed: {e}\n")
        # Niet kritiek — door zonder

    try:
        components["h_stab_left"] = build_horizontal_stabilizer("left")
        components["h_stab_right"] = build_horizontal_stabilizer("right")
    except Exception as e:
        App.Console.PrintError(f"[F15] Horizontal stabs failed: {e}\n")

    try:
        components["engine_left"] = build_engine_nacelle("left")
        components["engine_right"] = build_engine_nacelle("right")
        components["outlet_left"] = build_engine_outlet("left")
        components["outlet_right"] = build_engine_outlet("right")
    except Exception as e:
        App.Console.PrintError(f"[F15] Engines failed: {e}\n")

    try:
        components["canopy"] = build_canopy()
    except Exception as e:
        App.Console.PrintError(f"[F15] Canopy failed: {e}\n")

    try:
        components["intake_left"] = build_air_intake("left")
        components["intake_right"] = build_air_intake("right")
    except Exception as e:
        App.Console.PrintError(f"[F15] Intakes failed: {e}\n")

    try:
        components["pylon_left"] = build_pylon("left")
        components["pylon_right"] = build_pylon("right")
    except Exception as e:
        App.Console.PrintError(f"[F15] Pylons failed: {e}\n")

    # Fuse alles samen
    if not components:
        raise RuntimeError("Geen componenten succesvol gebouwd")

    base = components.pop("fuselage")
    others = list(components.values())

    if others:
        ship = base.fuse(others)
        App.Console.PrintMessage(f"[F15] Fused {len(others)} components onto fuselage\n")
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
        App.Console.PrintMessage(f"[F15] Building v4 model...\n")
        ship, parts = build_f15()

        # Voeg toe als Feature aan document
        feature = doc.addObject("Part::Feature", "F15_Body")
        feature.Shape = ship
        doc.recompute()

        # Export STEP (voor parametric handoff)
        step_path = str(OUTPUT_DIR / "f15_v4.step")
        Part.export([feature], step_path)
        App.Console.PrintMessage(f"[F15] STEP saved: {step_path}\n")

        # Export STL (voor Blender import)
        stl_path = str(OUTPUT_DIR / "f15_v4.stl")
        # STL via mesh conversion
        import Mesh
        mesh = Mesh.Mesh(ship.tessellate(0.5))  # 0.5mm linear deflection
        mesh.write(stl_path)
        App.Console.PrintMessage(f"[F15] STL saved: {stl_path}\n")

        # Save FCStd voor inspectie
        fcstd_path = str(OUTPUT_DIR / "f15_v4.FCStd")
        doc.saveAs(fcstd_path)
        App.Console.PrintMessage(f"[F15] FCStd saved: {fcstd_path}\n")

        # Schrijf parts inventory
        inventory_path = OUTPUT_DIR / "parts_inventory.md"
        with open(inventory_path, "w") as f:
            f.write("# F-15 v4 Parts Inventory\n\n")
            f.write(f"Successfully built: fuselage + {len(parts)} components\n\n")
            f.write("## Components\n\n")
            f.write("| Component | Status |\n|---|---|\n")
            f.write("| fuselage | OK (loft 10 sections) |\n")
            for name in parts.keys():
                f.write(f"| {name} | OK |\n")
            f.write("\n## Bounding Box\n\n")
            bb = ship.BoundBox
            f.write(f"- X (length): {bb.XMin:.0f} to {bb.XMax:.0f}, span {bb.XLength:.0f}\n")
            f.write(f"- Y (width):  {bb.YMin:.0f} to {bb.YMax:.0f}, span {bb.YLength:.0f}\n")
            f.write(f"- Z (height): {bb.ZMin:.0f} to {bb.ZMax:.0f}, span {bb.ZLength:.0f}\n")
        App.Console.PrintMessage(f"[F15] Inventory written: {inventory_path}\n")

        App.Console.PrintMessage("[F15] Build complete\n")
        return 0

    except Exception as e:
        App.Console.PrintError(f"[F15] Build failed: {e}\n")
        import traceback
        App.Console.PrintError(traceback.format_exc() + "\n")
        return 1

    finally:
        App.closeDocument(doc.Name)


# freecadcmd laadt dit als module (__name__ != __main__); altijd main aanroepen.
try:
    sys.exit(main())
except SystemExit:
    raise
except Exception as _e:  # noqa: BLE001
    try:
        App.Console.PrintError(f"f15_v4_freecad failed: {_e}\n")
    except Exception:
        print(f"f15_v4_freecad failed: {_e}", file=sys.stderr)
    sys.exit(1)
