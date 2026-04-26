"""freecadcmd: one Part::Box, 20 property changes + recompute + STEP each. Env FC_RECOMP_OUT (dir)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import FreeCAD as App  # type: ignore
import Part  # type: ignore


def main() -> int:
    out = Path(os.environ.get("FC_RECOMP_OUT", ""))
    if not out:
        print("FC_RECOMP_OUT required", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    doc = App.newDocument("RecompDemo")
    try:
        box = doc.addObject("Part::Box", "Hull")
        box.Width = 20.0
        box.Height = 15.0
        for i in range(1, 21):
            box.Length = 10.0 + float(i)
            doc.recompute()
            Part.export([box], str(out / ("v%02d.step" % i)))
    finally:
        try:
            App.closeDocument(doc.Name)
        except Exception:
            pass
    return 0


try:
    sys.exit(main())
except SystemExit:
    raise
except Exception as e:  # noqa: BLE001
    print("recompute_demo_failed", e, file=sys.stderr)
    sys.exit(1)
