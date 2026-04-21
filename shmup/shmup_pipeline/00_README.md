# NOVA v2 Raptor-Style Shmup Pipeline

Complete pipeline voor het maken van Tyrian/Raptor Call of the Shadows stijl shmup graphics. Van parametric FreeCAD design tot Godot engine import met pixel-perfect kwaliteit.

## Waarom deze aanpak

Raptor Call of the Shadows had de mooiste graphics van klassieke shmups omdat het 3D-gerenderde sprites gebruikte. Elk schip, elke vijand, elke power-up was eerst 3D gemodelleerd en vervolgens naar pixel art gerenderd. Dit gaf:
- 3D volumes en belichting die pure pixel art nooit heeft
- Consistentie tussen angles (rotatie-frames kloppen altijd)
- Snelle variaties (zelfde model, andere kleur = nieuwe enemy)
- Runtime performance van 2D sprites

Deze pipeline brengt die aanpak naar moderne tools met NOVA v2 jury-judge kwaliteitsbewaking.

## Pipeline overzicht

```
FreeCAD (parametric models)
    ↓ STEP export
Blender (rendering + materialen + animatie)
    ↓ PNG renders per angle
Aseprite (pixel cleanup + polish)
    ↓ Sprite sheets
PyQt5 batch processor (assembly + metadata)
    ↓
NOVA v2 Sprite Jury (kwaliteit check)
    ↓ Approved sprites
Godot 4 import (game engine)
```

## Document index

Deze pipeline bestaat uit 7 gefaseerde documenten:

1. **01_design_fase.md** — Concept, stijlgids, schip ontwerpen
2. **02_freecad_parametric.md** — Parametric 3D base models
3. **03_blender_rendering.md** — Multi-angle sprite renders
4. **04_aseprite_polish.md** — Pixel cleanup en animatie
5. **05_pyqt_assembly.md** — Sprite sheet batch processing
6. **06_godot_import.md** — Game engine integratie
7. **07_jury_validation.md** — NOVA v2 quality checks

Plus:
- **prompts/** — Cursor prompts per stap
- **examples/** — Voorbeeld workflows per ship type
- **scripts/** — Helper Python scripts

## Visuele kwaliteit targets

Voor professioneel resultaat streef naar:
- 64x64 of 96x96 pixels voor standaard enemies
- 128x128 voor spelerschip
- 192x192 voor mini-bosses
- 256x256 voor full bosses
- 16 rotation frames per object (22.5 graden per frame)
- 4 damage states per destructable object
- 8 animatie frames voor engines/weapons

## Hardware vereisten

Voor comfortabel werken:
- RTX 5060 Ti 16GB voor Blender Cycles renders (komt binnenkort)
- 32GB+ RAM (sprite sheets worden groot)
- 500GB+ SSD voor work-in-progress (renders zijn bulky)

Op huidige Arc A770: werkbaar maar langer rendering tijd.

## Tijdsinvestering

Per ship model (hero ship, enemy type, boss):
- FreeCAD design: 2-4 uur
- Blender setup + materials: 1-2 uur
- Rendering alle angles: 30 min - 2 uur (hardware afhankelijk)
- Aseprite polish: 1-3 uur
- Jury validation + fixes: 30 min

Totaal per ship: 5-12 uur voor professionele kwaliteit.

Voor Black Ledger complete fleet (66 weapons + 432 enemy varianten):
- Unieke base models: ~20 (rest is variatie)
- Geschatte totale tijd: 100-240 uur asset werk

Met NOVA v2 pipeline automation verkort dit significant door parametric variaties en batch rendering.

## Stijlgids essentials

**Palette keuze:**
- Beperkte kleurenpalette (16-32 kleuren totaal)
- Faction kleuren consistent (Rex Varn's ships = blauw/wit, enemies = rood/oranje)
- Emissive kleuren voor weapons en engines (bright core + glow)

**Lighting uniformiteit:**
- Top-down zon op 30-45 graden
- Consistent vanuit alle renders
- Rim lighting voor silhouette separation

**Proportions:**
- Vehicle sizes relative tot player (small=0.5x, medium=1x, large=2x, boss=4x+)
- Screen real-estate budget in gedachten

## Volgende stappen

Lees documenten in volgorde 01-07. Elk bouwt op vorige voort. Bij stap 7 heb je complete assets klaar voor gebruik in Godot.

Eerste concrete actie: lees 01_design_fase.md en maak style bible voor jouw specifieke shmup.
