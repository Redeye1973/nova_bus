"""FreeCAD headless script: build parametric base + export.

Invoked by freecadcmd.exe. Reads paths from env vars (FC_SPEC, FC_RESULT,
FC_WORKDIR) because freecadcmd.exe on Windows treats trailing CLI args as
files to open rather than script args. Produces .FCStd / .step / .stl in
the work directory.

Spec shape (see nova_host_bridge.adapters.freecad.build_parametric for
the exact contract):

{
  "category": "fighter|ship|boss|vehicle|building|prop|sphere",
  "primitive": "box|cylinder|capsule|cone|sphere",
  "dimensions": {"length":..., "width":..., "height":..., "radius":...},
  "mount_points": {"name": [x,y,z]},
  "exports": ["fcstd", "step", "stl"]
}
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

# FreeCAD modules. Available when running under freecadcmd.exe.
import FreeCAD  # type: ignore
import Part  # type: ignore
import Mesh  # type: ignore


def _make_primitive(primitive: str, dims):
    p = primitive.lower()
    if p == "box":
        length = float(dims.get("length", 1.0))
        width = float(dims.get("width", 1.0))
        height = float(dims.get("height", 1.0))
        return Part.makeBox(length, width, height)
    if p == "cylinder":
        radius = float(dims.get("radius", 1.0))
        height = float(dims.get("height", 1.0))
        return Part.makeCylinder(radius, height)
    if p == "cone":
        r1 = float(dims.get("radius", 1.0))
        r2 = float(dims.get("radius_top", 0.1))
        height = float(dims.get("height", 1.0))
        return Part.makeCone(r1, r2, height)
    if p == "sphere":
        radius = float(dims.get("radius", 1.0))
        return Part.makeSphere(radius)
    if p == "capsule":
        radius = float(dims.get("radius", 1.0))
        length = float(dims.get("length", 2.0))
        body_h = max(0.0, length - 2.0 * radius)
        cyl = Part.makeCylinder(radius, body_h) if body_h > 0 else None
        s_bot = Part.makeSphere(radius)
        s_top = Part.makeSphere(radius)
        s_top.translate(FreeCAD.Vector(0, 0, body_h))
        if cyl is not None:
            shape = cyl.fuse([s_bot, s_top])
        else:
            shape = s_bot.fuse([s_top])
        return shape.removeSplitter()
    raise ValueError("unknown primitive: %s" % primitive)


def _bbox(shape):
    bb = shape.BoundBox
    return {
        "x": [bb.XMin, bb.XMax],
        "y": [bb.YMin, bb.YMax],
        "z": [bb.ZMin, bb.ZMax],
        "extents": [bb.XLength, bb.YLength, bb.ZLength],
    }


def main():
    spec_path = os.environ.get("FC_SPEC")
    result_path = os.environ.get("FC_RESULT")
    workdir_path = os.environ.get("FC_WORKDIR")
    if not (spec_path and result_path and workdir_path):
        raise SystemExit("FC_SPEC, FC_RESULT, FC_WORKDIR env vars required")

    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    workdir = Path(workdir_path)
    workdir.mkdir(parents=True, exist_ok=True)

    primitive = spec.get("primitive") or "box"
    dims = spec.get("dimensions") or {}
    mount_points = spec.get("mount_points") or {}
    exports = [e.lower() for e in (spec.get("exports") or ["fcstd", "step", "stl"])]
    name = spec.get("name") or "parametric_base"

    doc = FreeCAD.newDocument("ParametricBase")
    sheet = doc.addObject("Spreadsheet::Sheet", "Parameters")
    row = 1
    for k, v in dims.items():
        sheet.set("A%d" % row, str(k))
        try:
            sheet.set("B%d" % row, float(v))
        except Exception:
            sheet.set("B%d" % row, str(v))
        row += 1
    doc.recompute()

    shape = _make_primitive(primitive, dims)
    obj = doc.addObject("Part::Feature", "BaseShape")
    obj.Shape = shape

    mp_objs = {}
    for mp_name, xyz in mount_points.items():
        if not (isinstance(xyz, list) and len(xyz) == 3):
            continue
        v = FreeCAD.Vector(float(xyz[0]), float(xyz[1]), float(xyz[2]))
        mp = doc.addObject("Part::Feature", "MP_%s" % mp_name)
        mp.Shape = Part.Vertex(v)
        mp_objs[mp_name] = [v.x, v.y, v.z]

    doc.recompute()

    files = {}
    if "fcstd" in exports:
        out = workdir / ("%s.FCStd" % name)
        doc.saveAs(str(out))
        files["fcstd"] = str(out)
    if "step" in exports:
        out = workdir / ("%s.step" % name)
        Part.export([obj], str(out))
        files["step"] = str(out)
    if "stl" in exports:
        out = workdir / ("%s.stl" % name)
        mesh = Mesh.Mesh()
        mesh.addFacets(shape.tessellate(0.1))
        mesh.write(str(out))
        files["stl"] = str(out)

    metrics = {
        "vertex_count": int(len(shape.Vertexes)),
        "edge_count": int(len(shape.Edges)),
        "face_count": int(len(shape.Faces)),
        "solid_count": int(len(shape.Solids)),
        "bounding_box": _bbox(shape),
        "volume": float(shape.Volume),
        "surface_area": float(shape.Area),
        "is_closed": bool(shape.isClosed()),
    }

    result = {
        "ok": True,
        "name": name,
        "primitive": primitive,
        "dimensions": {k: float(v) if isinstance(v, (int, float)) else v for k, v in dims.items()},
        "mount_points": mp_objs,
        "files": files,
        "metrics": metrics,
        "freecad_version": ".".join(str(x) for x in FreeCAD.Version()[:3]),
    }
    Path(result_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0


# freecadcmd.exe loads scripts as modules (__name__ == file stem), so we
# always invoke main() at import time.
try:
    main()
except SystemExit:
    raise
except Exception as _exc:
    try:
        _res = {
            "ok": False,
            "error": "%s: %s" % (type(_exc).__name__, _exc),
            "traceback": traceback.format_exc(),
        }
        _rp = os.environ.get("FC_RESULT")
        if _rp:
            Path(_rp).write_text(json.dumps(_res, indent=2), encoding="utf-8")
    except Exception:
        sys.stderr.write(traceback.format_exc())
    sys.exit(1)
