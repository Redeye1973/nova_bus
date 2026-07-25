# Aetherion — Game review & polish (25 juli 2026)

Vervolg op de dungeon secrets/breekbare vloeren sessie: brede nacontrole van de game en fixes.

## Inventarisatie

- Smoke test (34 checks): **PASS** — geen functionele fouten gevonden.
- Enige structurele warning: `missing_shop_icons count=5` (torch_longburn, spell_ward, spell_regen, key_dungeon_iron, key_gate_cipher).
- Visuele probes (world/city/village/battle): battle en plaza stonden goed; drie visuele problemen gevonden.

## Fixes

### 1. Vijf ontbrekende shop-icons (PixelLab, 64×64)

| Icon | Object-ID |
|---|---|
| `icon_torch_longburn.png` | afdd63e8 |
| `icon_spell_ward.png` | 1afb3ee6 |
| `icon_spell_regen.png` | 13ec745e |
| `icon_key_dungeon_iron.png` | be45d6e0 |
| `icon_key_gate_cipher.png` | 93f2b58a |

Smoke log na fix: `missing_shop=0`, icons 166→171.

### 2. Overworld stadsmuren — gap-vrije ring

**Probleem:** de oude ring plaatste 32px atlas-stukken per iso-cel → diagonale gaten, zwevende beige "planken".

**Fix:** nieuwe `CityWallTerrain.paint_perimeter_ring()` — schermruimte-rechthoek rond het stadsblob, PixelLab-stukken aansluitend getegeld:

- `wall_segment.png` (c351bf2a, 64×40) — N/S-rijen + gestapelde W/O-kolommen
- `tower.png` (ec7fdda0, 40×64) — vier hoektorens
- `gate.png` (a1f1bdff, 64×56) — zuidelijk poorthuis (fallback: `interior_gate_arch.png`)

Oude atlas-route blijft als fallback wanneer de PNG's ontbreken. Bestanden: `scripts/city_wall_terrain.gd`, `scripts/settlement_placer.gd`, assets onder `assets/buildings/city_walls/pixellab/`.

### 3. Stads-/dorpsgras neon-groen

`town_ground/grass.png` (gecarvede Wang-tegel) was één vlakke felgroene kleur. Interior-gras gebruikt nu de overworld PixelLab `tiles/pixellab/plains.png` (getextureerd, gedempt groen); oude tegel blijft fallback. Bestand: `scripts/settlement_interior.gd`.

### 4. Tan parcel-kaders verwijderd

`_paint_lot_borders()` (SimCity-outlines) tekende lege tan rechthoeken op gras-lots — leest als debug-clutter in de JRPG-look. Aanroep verwijderd.

### 5. Cave-ingang overworld

Procedurele zwarte ellips vervangen door PixelLab cave-mouth sprite (78ec4cd8) via `assets/props/entrances/cave.png`; `EntranceArt` laadt PNG eerst, procedureel blijft fallback (dungeon-keep facade blijft procedureel — leest prima).

## Verificatie

- Smoke test na alle wijzigingen: **PASS (all checks ok)**, `missing_shop=0`.
- World probe: gesloten stenen ring met torens + poort, cave-mouth zichtbaar, gras getextureerd, geen kaders.
- Screenshots: `L:\!Nova V2\Z Cost Reports\_world_view_probe\`.

## PixelLab verbruik

9 generaties (5 icons, 3 muurstukken, 1 cave). **Let op: abonnementsquota is op (3893/3800 gebruikt); generaties lopen nu op credits ($26.04 resterend).** Details: `Z Cost Reports\pixellab_game_polish_2026-07-25.md`. Alle assets gearchiveerd onder `L:\ZZZZZZ ZZ PROMPTS\Assets\aetherion\pixellab\{icons,buildings,landmarks}\`; download-script: `L:\!Nova V2\scripts\download_game_polish_assets.py` (re-runnable).
