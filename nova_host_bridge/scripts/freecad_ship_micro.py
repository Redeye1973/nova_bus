"""freecadcmd: hull + cockpit Part::Fuse, two STEP exports (variant length). Env: FC_SHIP_OUT, FC_SHIP_VERDICT (json paths)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import FreeCAD as App  # type: ignore
import Part  # type: ignore


def main() -> int:
    out = Path(os.environ.get("FC_SHIP_OUT", ""))
    vpath = Path(os.environ.get("FC_SHIP_VERDICT", ""))
    if not out or not vpath:
        print("FC_SHIP_OUT and FC_SHIP_VERDICT required", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    verdict: dict[str, object] = {}
    doc = App.newDocument("ShipMicro")
    try:
        hull = doc.addObject("Part::Box", "Hull")
        hull.Length = 100.0
        hull.Width = 40.0
        hull.Height = 20.0
        cock = doc.addObject("Part::Box", "Cockpit")
        cock.Length = 30.0
        cock.Width = 20.0
        cock.Height = 15.0
        cock.Placement.Base = App.Vector(10.0, 0.0, 25.0)
        doc.recompute()
        fuse = doc.addObject("Part::Fuse", "Ship")
        fuse.Base = hull
        fuse.Tool = cock
        doc.recompute()
        p1 = out / "ship_v01.step"
        Part.export([fuse], str(p1))
        hull.Length = 150.0
        doc.recompute()
        p2 = out / "ship_v02.step"
        Part.export([fuse], str(p2))
        b1, b2 = p1.read_bytes(), p2.read_bytes()
        verdict["v1_bytes"] = len(b1)
        verdict["v2_bytes"] = len(b2)
        verdict["different"] = b1 != b2
        verdict["ok"] = verdict["different"] is True
    finally:
        try:
            App.closeDocument(doc.Name)
        except Exception:
            pass
    vpath.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    return 0 if verdict.get("ok") else 1


# freecadcmd loads this file as a module; invoke main at import (same pattern as freecad_parametric).
try:
    sys.exit(main())
except SystemExit:
    raise
except Exception as e:  # noqa: BLE001
    print("ship_micro_failed", e, file=sys.stderr)
    sys.exit(1)
