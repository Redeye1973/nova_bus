# NOVA F-15 v4 — Runner-prompt voor Cursor

## Wat dit is

Twee Python-scripts die F-15 model bouwen via geavanceerde
FreeCAD features (Loft, Sweep, Revolve) ipv primitive fusing.

Eindresultaat: STEP + STL + GLB + 4 renders + mesh stats.

## Canonieke locatie (repo)

`L:\!Nova V2\scripts\f15\`

- `f15_v4_freecad.py`
- `f15_v4_blender_render.py` (silhouet / matte grey)
- `f15_v4_blender_textured.py` (optioneel: USAF-style materials + hogere res)
- `f15_v4_runner_prompt.md` (dit bestand)

Kopieën onder `!     @  !! CLAUDE\` zijn archief; onderhoud in **`scripts\f15`**.

## Bestanden (inhoud)

- `f15_v4_freecad.py` — FreeCAD parametric script, gebruikt
  Part.makeLoft() voor smooth fuselage en wings, Revolve voor
  bubble canopy. Pure Python, geen JSON-spec via primitive
  fuse adapter.

- `f15_v4_blender_render.py` — Blender headless render script.
  Cleanup mesh (delete_loose), matte grey material, single
  sun light van boven, 4 angles (topdown ortho, front ortho,
  side ortho, threequarter perspective), GLB export voor
  mogelijke Godot-import.

## Cursor-prompt

```
NOVA F-15 v4 — runner via geharde bridge.

CONTEXT: F-15 v3 via primitive-fuse adapter loopt
parallel maar levert beperkte shapes (rechthoek-wings,
geen tapered fuselage). v4 gebruikt geavanceerde FreeCAD
features (Loft, Sweep, Revolve) via direct Python-script
in plaats van JSON-spec.

INPUT-BESTANDEN: Alex levert twee Python-scripts:
  - f15_v4_freecad.py
  - f15_v4_blender_render.py

OUTPUT-MAP: L:\! 2 Nova v2 OUTPUT !\Ship_F15_v4\
Subfolders: 01_freecad\ en 02_blender\ (worden door
scripts zelf aangemaakt).

== TAAK 1: SCRIPTS PLAATSEN ==

GEDAAN: `L:\!Nova V2\scripts\f15\` (inclusief textured variant).

== TAAK 2: FREECAD BUILD ==

**Let op:** `nova_host_bridge` heeft **geen** `POST /freecad/script` (alleen
`/freecad/parametric` voor JSON multi_fuse). v4-script is **standalone**
FreeCAD-Python.

Run headless op dezelfde machine als FreeCADCmd, met output-map:

- Zet `F15_OUTPUT_DIR` naar `L:\! 2 Nova v2 OUTPUT !\Ship_F15_v4\01_freecad`
  (map bestaat of wordt aangemaakt).
- Start: `FreeCADCmd.exe` met argument het pad naar
  `L:\!Nova V2\scripts\f15\f15_v4_freecad.py` (zie FreeCAD-docs voor exacte
  CLI op jouw install).

Script bouwt F-15 via Loft/Sweep/Revolve, exporteert STEP + STL +
FCStd naar die `F15_OUTPUT_DIR`.

Verifieer na run:
  - exit code 0
  - f15_v4.step bestaat (file size > 1 KB)
  - f15_v4.stl bestaat (file size > 10 KB)
  - parts_inventory.md bestaat met component-tabel

Bij fail:
  - Lees FreeCAD console / stderr
  - Log naar `Ship_F15_v4\03_runner_log.md` indien gewenst
  - Stop, niet doorgaan naar Blender met kapotte STL

== TAAK 3: BLENDER SCRIPT VIA BRIDGE ==

Roep aan:
  POST http://127.0.0.1:8501/blender/script
  body: {"script": "L:/!Nova V2/scripts/f15/f15_v4_blender_render.py"}

Script importeert STL uit Taak 2, cleanup mesh, render
4 angles, export GLB.

Verifieer na call:
  - HTTP 200
  - f15_v4_topdown.png bestaat (> 5 KB)
  - f15_v4_front.png bestaat
  - f15_v4_side.png bestaat
  - f15_v4_threequarter.png bestaat
  - f15_v4.glb bestaat (> 50 KB)
  - mesh_stats.json bestaat met vertices/polygons counts

== TAAK 4: VERGELIJKING MET V3 ==

Maak L:\! 2 Nova v2 OUTPUT !\Ship_F15_v4\03_comparison\
met:

  - v3_topdown.png (kopie uit Ship_F15_v3 of Ship_F15_Silhouette)
  - v4_topdown.png (uit deze run)
  - comparison.md objectief:
    - Vertex/poly count v3 vs v4
    - File size STL/GLB
    - Bounding box aspect ratio top-down (target 13/19 ≈ 0.68)
    - Visuele observatie (geen subjectief mooi/lelijk,
      wel: heeft v4 tapered wings? canopy bubble shape?
      smooth fuselage taper?)

== TAAK 5: EINDRAPPORT ==

L:\! 2 Nova v2 OUTPUT !\Ship_F15_v4\f15_v4_report.md:
  - Welke FreeCAD operations succesvol
    (loft fuselage, loft wings, revolve canopy)
  - Welke component-builds faalden (en error)
  - Render-paden voor Alex
  - Mesh stats (vertex/poly count)
  - GLB beschikbaar voor Godot ja/nee
  - Aanbeveling: is loft-aanpak betere basis voor
    Modulaire Ship Kit dan primitive-fuse?

ALEX MOET DAARNA:
  v4_topdown.png + v4_threequarter.png openen,
  vergelijken met F-15 photo-reference. Kantelt het
  silhouet richting echte F-15?

== REGELS ==

- Bridge 8500 niet aanraken
- Geen Black Ledger
- Max 30 min Cursor-werk
- Bij fail in Taak 2: stop, escaleer met stderr_tail
- Bij fail in Taak 3: STL bestaat maar Blender struikelt
  — log specifieke error, geen workaround
- Verboden PowerShell aan Alex teruggeven
- Niet de scripts wijzigen tijdens execution. Als script
  bug heeft: log + escaleer, Alex past aan in nieuwe
  ronde.
```

## Nota voor Alex

De FreeCAD-script gebruikt features die de huidige bridge-adapter
mogelijk nooit heeft uitgevoerd (Loft, Revolve, BSplineCurve.interpolate).
Drie scenario's mogelijk:

1. **Werkt direct** — FreeCADCmd voert het script uit; STEP/STL kloppen;
   daarna Blender via bridge voor renders/GLB.

2. **Werkt deels** — sommige components (canopy revolve, wing loft)
   kunnen falen door FreeCAD API-quirks. `build_f15()` heeft try/except
   per component.

3. **Wil je alles via bridge** — voeg dan een endpoint toe (bv.
   `/freecad/script`) dat FreeCADCmd met willekeurig script-path start;
   tot die tijd: Taak 2 lokaal met FreeCADCmd.

In alle drie gevallen levert het info: óf je krijgt een veel betere
F-15 dan v3, óf je weet welke beperkingen de bridge nog heeft voor
volledig parametric werk.
