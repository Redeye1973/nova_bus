# 01. Design Fase — Style Bible en Ship Concepten

## Doel
Voor je iets begint te bouwen: helder visueel plan. Dit voorkomt dat 50 ships allemaal anders aanvoelen qua stijl.

## Style Bible componenten

**1. Color palette definitie**

Kies één master palette van 32 kleuren max. Alle ships en effects gebruiken alleen deze kleuren. Voorbeeld voor Black Ledger:

```
Primary (Rex Varn / player):
- Navy blue #1a2b4a
- Light blue #4a8ac0
- White accent #e8f0ff
- Cockpit cyan #5ae0e0

Secondary (Helios Corporate enemies):
- Rust red #8a2a1a
- Orange #e05820
- Yellow warning #ffd040

Tertiary (Remnant Lance pirates):
- Dark purple #3a1a4a
- Magenta #c040a0
- Sickly green #80c040

Neutral (environment/debris):
- Gunmetal #40454a
- Steel #70757a
- Rust brown #604030

Emissive (weapons/engines):
- Plasma white-hot #fff8e0
- Fire orange #ff6020
- Laser pink #ff40a0
- Engine blue #60a0ff
```

Bewaar palette als Aseprite .aseprite-palette file en Blender .blend asset library.

**2. Lighting setup**

Kies één lighting configuration voor ALLE renders:
- Sun direction: 30 graden vanaf boven, 45 graden azimuth
- Sun color: licht warm wit (#fff8e8)
- Fill light: tegenover sun, 20% intensity, cool blue (#a0c0ff)
- Rim light: directly behind, 40% intensity, pure white

Geen uitzonderingen. Als één ship ander licht heeft, valt het op in het team.

**3. Camera angle**

- Top-down met 15 graden tilt (niet helemaal 90)
- Isometric lens (no perspective distortion)
- Consistent field of view
- Zelfde afstand tot model per size category

**4. Pixel density**

- Base render resolutie: 4x target sprite size
- Dus 64x64 sprite = 256x256 render, dan downscale
- Gebruik Blender's pixel perfect compositor node

**5. Silhouette test**

Elk ship moet herkenbaar zijn op:
- 32x32 pixels (gameplay zichtbaarheid)
- Pure zwart silhouet (geen interne details)

Als niet herkenbaar: redesign vorm.

## Ship categorieën voor Black Ledger

**Player ship: Rex Varn's fighter**
- Size: 96x96 pixels
- 16 rotation frames
- 3 damage states (pristine, damaged, critical)
- Engine glow animation (8 frames loop)
- 3 upgrade appearances (basic, mid, max loadout)

**Standard enemy (fighters)**
- Size: 64x64
- 16 rotation frames
- 2 damage states
- Faction variants: Corporate (6), Pirates (6), Aliens (6)

**Heavy enemy (bombers)**
- Size: 96x96
- 8 rotation frames (turnen langzaam)
- 3 damage states
- Per faction 3 varianten

**Mini-boss (elite units)**
- Size: 128x128
- 16 rotation frames
- 4 damage states
- Weapon mounting points animated

**Full boss (act climax)**
- Size: 256x256 of groter
- Sometimes multi-part (mother ship met turrets)
- 5+ damage states
- Animated sections (rotating parts, opening hatches)

**Projectiles**
- Size: 16x16 tot 32x32
- 4-8 animation frames
- Color-coded per weapon type

**Power-ups**
- Size: 32x32
- Floating animation (8 frames)
- Distinct silhouettes per type

**Explosions**
- Size: scales with source (32x32 klein, 128x128 groot)
- 12-16 frame animation
- Smoke debris persisting

## Design sheet per ship

Voor elke unieke ship maak een design sheet:

```
Ship: Corporate Fighter Mk.II
Faction: Helios Corporate
Role: Standard enemy
Size category: Medium (64x64)

Silhouette features:
- Swept wings
- Central cockpit bubble
- Twin engines below

Color priority:
- Rust red primary (40%)
- Gunmetal secondary (30%)
- Orange accent (20%)
- Yellow warning stripes (10%)

Unique features:
- Visible weapon mounts on wings
- Exhaust trails from engines
- Faction insignia visible on wing

Damage state progression:
- Pristine: clean, shining
- Damaged: scorch marks, missing panel on wing
- Critical: engine fire, hull cracks, one engine dead

Animation needs:
- Engine flicker (8 frames)
- Weapon muzzle flash (4 frames when firing)
- Destruction explosion (12 frames)
```

Bewaar deze sheets als Markdown in je project. Verwijs ernaar tijdens design en rendering.

## Cursor prompt: Design document generator

```
Bouw een design sheet generator voor Black Ledger ships:

1. Python script `design/ship_sheet_generator.py`:
   - CLI tool: `python ship_sheet_generator.py --faction corporate --role fighter --tier standard`
   - Gebruikt template (Jinja2)
   - Generates markdown design sheet
   - Reads master palette uit palette.yaml
   - Fills in color recommendations per faction

2. Template bestand `design/templates/ship_sheet.md.j2`:
   - Jinja2 template
   - Placeholders: name, faction, role, size, colors, features

3. Config `design/palette.yaml`:
   - Master color palette
   - Faction mappings
   - Size category definitions

4. Script `design/validate_sheet.py`:
   - Checks of design sheet compleet is
   - Valideert kleuren uit master palette
   - Warns bij inconsistenties

Gebruik Python 3.11, Jinja2, PyYAML.
```

## Master Style Bible document

Maak `docs/style_bible.md` voor je project met:
- Master palette met hex codes
- Lighting setup diagram
- Camera angle specs
- Size category table
- Faction color mappings
- Rendering settings Blender

Dit wordt de bron van waarheid. Elke bouwstap refereert hier terug.

## Workflow voor nieuw ship design

1. Identificeer rol (player, enemy fighter, boss, etc)
2. Kies faction
3. Run design sheet generator
4. Schets silhouette (papier of digital)
5. Test silhouette op 32x32 pixels
6. Accepteer/verwerp op basis van leesbaarheid
7. Verfijn sheet met details
8. Pas naar FreeCAD stap

## Output van deze fase

Per ship:
- Design sheet (markdown)
- Silhouette sketch (PNG)
- Goedgekeurd door jezelf voor productie

Dit lijkt overhead maar bespaart uren aan redo-werk. 30 minuten design vooraf voorkomt 3 uur Blender werk opnieuw doen.

## Success criteria

- 100% ships hebben design sheet voor bouwen begint
- 100% silhouettes herkenbaar op 32x32
- Kleuren 100% uit master palette
- Consistent design taal tussen ships van zelfde faction
