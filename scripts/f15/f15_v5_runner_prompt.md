# NOVA F-15 v5 — runner

## Wat dit is

Twee scripts samen:

1. **`f15_v5_freecad.py`** — smoother model
   - 14 fuselage cross-sections (was 10)
   - Finer tessellation (0.1mm vs 0.5mm)
   - Smoothere canopy profile
   - Wing root meer geïntegreerd

2. **`f15_v5_blue_angels.py`** — aggressieve Blue Angels paint
   - Bbox-relative thresholds (was vaste percentages)
   - Wing-tips outer 30%
   - Tail-tops bovenste 40%
   - Fuselage horizontal stripe (iconic Blue Angels marking)
   - Nose-tip yellow accent
   - Shade smooth + auto-smooth 30°

Output: `L:\! 2 Nova v2 OUTPUT !\Ship_F15_v5\`
- `01_freecad\` — STEP, STL, FCStd
- `blue_angels\run_NNN\` — renders, GLB

## Cursor-prompt

```
NOVA F-15 v5 — runner via geharde bridge.

INPUT: Alex levert twee scripts:
  - f15_v5_freecad.py
  - f15_v5_blue_angels.py

PLAATSING:
  L:\!Nova V2\scripts\f15\f15_v5_freecad.py
  L:\!Nova V2\scripts\f15\f15_v5_blue_angels.py
  (overschrijf indien bestaand)

== TAAK 1: FREECAD V5 BUILD ==

**Let op:** bridge heeft geen `POST /freecad/script` (alleen
`/freecad/parametric` voor JSON). v5 = **standalone** FreeCAD-Python.

- Zet `F15_OUTPUT_DIR` naar
  `L:\! 2 Nova v2 OUTPUT !\Ship_F15_v5\01_freecad`
- Run **FreeCADCmd.exe** met script
  `L:\!Nova V2\scripts\f15\f15_v5_freecad.py`

Verifieer na run:
  - exit code 0
  - L:\! 2 Nova v2 OUTPUT !\Ship_F15_v5\01_freecad\
    f15_v5.step bestaat (>1 KB)
    f15_v5.stl bestaat (groter dan v4 STL ivm finer
    tessellation — verwacht > 50 KB)
    parts_inventory.md bestaat met "14 sections"
    in tekst

Bij fail:
  - Lees FreeCAD-console / stderr
  - Stop, niet doorgaan naar Blender

== TAAK 2: BLUE ANGELS V5 RENDER ==

Roep aan:
  POST http://127.0.0.1:8501/blender/script
  body: {"script": "L:/!Nova V2/scripts/f15/f15_v5_blue_angels.py"}

Script doet zelf:
  - Detecteer next run_NNN in
    Ship_F15_v5\blue_angels\
  - Smooth shading + auto-smooth
  - Aggressieve material assignment
  - 5 renders + GLB

Verifieer:
  - HTTP 200
  - Geen Python errors in stderr_tail (geharde adapter
    detecteert dit nu)
  - Nieuwste run-directory bevat:
    f15_v5_blue_angels_topdown.png
    f15_v5_blue_angels_front.png
    f15_v5_blue_angels_side.png
    f15_v5_blue_angels_threequarter.png
    f15_v5_blue_angels_hero.png
    f15_v5_blue_angels.glb
    run_info.json
  - run_info.json face_distribution.yellow > 1000
    (als geel < 1000 dan is heuristic nog niet
    aggressief genoeg, maar log + ga door)

== TAAK 3: VERGELIJKING V4 vs V5 ==

Maak L:\! 2 Nova v2 OUTPUT !\Ship_F15_v5\
v5_vs_v4_comparison.md met:

  - Vertex/poly count v4 vs v5 (verwacht v5 hoger
    door finer tessellation)
  - Yellow face count v4 vs v5 (verwacht veel hoger
    door aggressieve heuristics)
  - File-paden voor visuele vergelijking:
    Ship_F15_v4\blue_angels\run_002\f15_blue_angels_threequarter.png
    Ship_F15_v5\blue_angels\run_001\f15_v5_blue_angels_threequarter.png

== TAAK 4: KORT RAPPORT ==

In nieuwste run-dir: runner_summary.md met
HTTP-statussen + file-list + face distribution.

== REGELS ==

- Bridge 8500 niet aanraken
- Geen Black Ledger
- Bij script-fail: log + escaleer
- Bij stderr Python errors: STOP
- Verboden PowerShell aan Alex teruggeven
- GEEN aanpassingen aan scripts tijdens execution
```

## Wat te verwachten visueel

**Smoothness (v5 vs v4):**
- Vloeiende fuselage taper, geen knik bij neus-body overgang
- Geen zaagtand bij wing-fuselage junction
- Smooth bubble canopy (was te hoekig)
- Wings sluiten beter aan op fuselage

**Paint scheme (v5 vs v4):**
- Wing-tips groot geel gebied (was: bijna geen geel)
- Hele leading edge wings geel
- Bovenste deel verticale tails fors geel (was: dun randje)
- Horizontale gele stripe over fuselage zijkant
- Geel neuspunt
- Canopy-frame geel randje

Als geel% in face_distribution onder 10% zit: aggressiever
needed. Als boven 25%: te aggressief, model wordt te bont.
Sweet spot: 12-20%.
