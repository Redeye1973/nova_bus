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


def _placement_from_spec(ps):
    pos = ps.get("position") or [0.0, 0.0, 0.0]
    ax = ps.get("rotation_axis") or [0.0, 0.0, 1.0]
    ang = float(ps.get("rotation_angle", 0.0))
    return FreeCAD.Placement(
        FreeCAD.Vector(float(pos[0]), float(pos[1]), float(pos[2])),
        FreeCAD.Rotation(FreeCAD.Vector(float(ax[0]), float(ax[1]), float(ax[2])), ang),
    )


def _placement_box(ps):
    """Part::Box corner base; optional pivot=center uses position as box center."""
    L = float(ps.get("length", 1.0))
    W = float(ps.get("width", 1.0))
    H = float(ps.get("height", 1.0))
    pos = ps.get("position") or [0.0, 0.0, 0.0]
    ax = ps.get("rotation_axis") or [0.0, 0.0, 1.0]
    ang = float(ps.get("rotation_angle", 0.0))
    rot = FreeCAD.Rotation(FreeCAD.Vector(float(ax[0]), float(ax[1]), float(ax[2])), ang)
    if str(ps.get("pivot", "")).lower() == "center":
        base = FreeCAD.Vector(float(pos[0]) - L / 2, float(pos[1]) - W / 2, float(pos[2]) - H / 2)
    else:
        base = FreeCAD.Vector(float(pos[0]), float(pos[1]), float(pos[2]))
    return FreeCAD.Placement(base, rot)


def _placement_cylinder_center(ps):
    """Cylinder local +Z axis; position = center of cylinder (before rotation)."""
    H = float(ps.get("height", 10.0))
    pos = ps.get("position") or [0.0, 0.0, 0.0]
    ax = ps.get("rotation_axis") or [0.0, 0.0, 1.0]
    ang = float(ps.get("rotation_angle", 0.0))
    rot = FreeCAD.Rotation(FreeCAD.Vector(float(ax[0]), float(ax[1]), float(ax[2])), ang)
    c = FreeCAD.Vector(float(pos[0]), float(pos[1]), float(pos[2]))
    base = c - rot.multVec(FreeCAD.Vector(0, 0, H / 2.0))
    return FreeCAD.Placement(base, rot)


def _shape_box_solid(ps):
    """Oriented box as Part.Shape for booleans."""
    L = float(ps.get("length", 1.0))
    W = float(ps.get("width", 1.0))
    H = float(ps.get("height", 1.0))
    pl = _placement_box(ps)
    b = Part.makeBox(L, W, H)
    return b.transformShape(pl.toMatrix())


def _shape_cylinder_solid(ps):
    """Infinite-precision cylinder along local +Z; placement via pivot=center or position."""
    r = float(ps.get("radius", 1.0))
    h = float(ps.get("height", 10.0))
    cyl = Part.makeCylinder(r, h)
    if str(ps.get("pivot", "")).lower() == "center":
        pl = _placement_cylinder_center(ps)
    else:
        pl = _placement_from_spec(ps)
    return cyl.transformShape(pl.toMatrix())


def _run_multi_fuse(spec, workdir, exports, name, result_path):
    """Ship-kit style: multiple Part::Box / Part::Cylinder, boolean fuse, export."""
    parts_spec = list(spec.get("parts") or [])
    if not parts_spec:
        raise ValueError("multi_fuse requires non-empty parts[]")

    doc = FreeCAD.newDocument("MultiFuseShip")
    objs = []
    try:
        for i, ps in enumerate(parts_spec):
            kind = (ps.get("kind") or "box").lower()
            label = "".join(c if c.isalnum() else "_" for c in str(ps.get("name") or "part"))[:24] or "part"
            oname = "P%d_%s" % (i, label)
            if kind == "box":
                pl = _placement_box(ps)
                o = doc.addObject("Part::Box", oname)
                o.Length = float(ps.get("length", 10.0))
                o.Width = float(ps.get("width", 10.0))
                o.Height = float(ps.get("height", 10.0))
                o.Placement = pl
                objs.append(o)
            elif kind == "cylinder":
                if str(ps.get("pivot", "")).lower() == "center":
                    pl = _placement_cylinder_center(ps)
                else:
                    pl = _placement_from_spec(ps)
                o = doc.addObject("Part::Cylinder", oname)
                o.Radius = float(ps.get("radius", 1.0))
                o.Height = float(ps.get("height", 10.0))
                o.Placement = pl
                objs.append(o)
            elif kind == "cone":
                pl = _placement_from_spec(ps)
                o = doc.addObject("Part::Cone", oname)
                o.Radius1 = float(ps.get("radius1", 1.0))
                o.Radius2 = float(ps.get("radius2", 0.1))
                o.Height = float(ps.get("height", 10.0))
                o.Placement = pl
                objs.append(o)
            elif kind == "box_cut":
                pos_spec = ps.get("positive") or {}
                neg_spec = ps.get("negative") or {}
                try:
                    sh_p = _shape_box_solid(pos_spec)
                    sh_n = _shape_box_solid(neg_spec)
                    sh_r = sh_p.cut(sh_n)
                    if sh_r.isNull() or float(sh_r.Volume) < 1e-3:
                        raise ValueError("cut result empty")
                except Exception as _e:
                    raise ValueError("box_cut failed for %s: %s" % (label, _e)) from _e
                o = doc.addObject("Part::Feature", oname)
                o.Shape = sh_r
                objs.append(o)
            elif kind == "box_cut_chain":
                pos_spec = ps.get("positive") or {}
                negs = ps.get("negatives") or []
                if not isinstance(negs, list) or len(negs) == 0:
                    raise ValueError("box_cut_chain requires non-empty negatives[]")
                try:
                    sh = _shape_box_solid(pos_spec)
                    for neg_spec in negs:
                        sh = sh.cut(_shape_box_solid(neg_spec))
                    if sh.isNull() or float(sh.Volume) < 1e-3:
                        raise ValueError("box_cut_chain result empty")
                except Exception as _e:
                    raise ValueError("box_cut_chain failed for %s: %s" % (label, _e)) from _e
                o = doc.addObject("Part::Feature", oname)
                o.Shape = sh
                objs.append(o)
            elif kind == "cylinder_cut":
                cyl_spec = ps.get("positive") or ps.get("cylinder") or {}
                neg_spec = ps.get("negative") or {}
                try:
                    sh_c = _shape_cylinder_solid(cyl_spec)
                    sh_n = _shape_box_solid(neg_spec)
                    sh_r = sh_c.cut(sh_n)
                    if sh_r.isNull() or float(sh_r.Volume) < 1e-3:
                        raise ValueError("cylinder_cut result empty")
                except Exception as _e:
                    raise ValueError("cylinder_cut failed for %s: %s" % (label, _e)) from _e
                o = doc.addObject("Part::Feature", oname)
                o.Shape = sh_r
                objs.append(o)
            else:
                raise ValueError("unknown part kind: %s" % kind)

        doc.recompute()
        merged = objs[0].Shape.copy()
        for o in objs[1:]:
            merged = merged.fuse(o.Shape)
        exp = doc.addObject("Part::Feature", "FusedExport")
        exp.Shape = merged
        doc.recompute()
        shape = merged

        files = {}
        if "fcstd" in exports:
            out_fc = workdir / ("%s.FCStd" % name)
            doc.saveAs(str(out_fc))
            files["fcstd"] = str(out_fc)
        if "step" in exports:
            out_st = workdir / ("%s.step" % name)
            Part.export([exp], str(out_st))
            files["step"] = str(out_st)
        if "stl" in exports:
            out_mesh = workdir / ("%s.stl" % name)
            mesh = Mesh.Mesh()
            mesh.addFacets(shape.tessellate(0.08))
            mesh.write(str(out_mesh))
            files["stl"] = str(out_mesh)

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
            "primitive": "multi_fuse",
            "composition": "multi_fuse",
            "parts_built": len(objs),
            "dimensions": {},
            "mount_points": {},
            "files": files,
            "metrics": metrics,
            "freecad_version": ".".join(str(x) for x in FreeCAD.Version()[:3]),
        }
        Path(result_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
    finally:
        try:
            FreeCAD.closeDocument(doc.Name)
        except Exception:
            pass


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

    if spec.get("composition") == "multi_fuse":
        _run_multi_fuse(spec, workdir, exports, name, result_path)
        return 0

    doc = FreeCAD.newDocument("ParametricBase")
    try:
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

        if primitive.lower() == "box":
            obj = doc.addObject("Part::Box", "BaseShape")
            obj.Length = float(dims.get("length", 1.0))
            obj.Width = float(dims.get("width", 1.0))
            obj.Height = float(dims.get("height", 1.0))
        else:
            shape0 = _make_primitive(primitive, dims)
            obj = doc.addObject("Part::Feature", "BaseShape")
            obj.Shape = shape0

        mp_objs = {}
        for mp_name, xyz in mount_points.items():
            if not (isinstance(xyz, list) and len(xyz) == 3):
                continue
            v = FreeCAD.Vector(float(xyz[0]), float(xyz[1]), float(xyz[2]))
            mp = doc.addObject("Part::Feature", "MP_%s" % mp_name)
            mp.Shape = Part.Vertex(v)
            mp_objs[mp_name] = [v.x, v.y, v.z]

        doc.recompute()
        shape = obj.Shape

        files = {}
        if "fcstd" in exports:
            out_fc = workdir / ("%s.FCStd" % name)
            doc.saveAs(str(out_fc))
            files["fcstd"] = str(out_fc)
        if "step" in exports:
            out_st = workdir / ("%s.step" % name)
            Part.export([obj], str(out_st))
            files["step"] = str(out_st)
        if "stl" in exports:
            out_mesh = workdir / ("%s.stl" % name)
            mesh = Mesh.Mesh()
            mesh.addFacets(shape.tessellate(0.1))
            mesh.write(str(out_mesh))
            files["stl"] = str(out_mesh)

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
    finally:
        try:
            FreeCAD.closeDocument(doc.Name)
        except Exception:
            pass


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
