# PixelLab — dungeon floor decals (2026-07-25)

Feature: hidden walls + secret chambers ("H") en brekende vloertegels ("R" → "O")
in de Aetherion dungeon crawler.

## Generaties (3× map object, basic mode, 64×64, high top-down)

| Asset | Object ID | Status | Bestand |
|---|---|---|---|
| floor_crack (v1, dun spinnenweb) | `c0641a98-151d-4699-b6c1-5795d9ada46d` | afgekeurd (te subtiel) | archief `incoming\dungeon_floor_crack_thin_unused_c0641a98.png` |
| floor_crack (v2, gebarsten plaat) | `8e95b517-fc6a-463d-94ca-499c9c90aaa2` | in gebruik | `assets\dungeon\props\floor_crack.png` + archief `tiles\dungeon_floor_crack_8e95b517.png` |
| floor_hole (zwart gat + puin) | `93e2778d-45e9-4f84-a244-7ca6d4707fe0` | in gebruik | `assets\dungeon\props\floor_hole.png` + archief `tiles\dungeon_floor_hole_93e2778d.png` |

Archief-root: `L:\ZZZZZZ ZZ PROMPTS\Assets\aetherion\pixellab\`
Download-script (re-runnable): `L:\!Nova V2\scripts\download_dungeon_floor_decals.py`

## Gameplay (scripts gewijzigd)

- `dungeon_controller.gd` — secret chambers (3×3, verzegeld, chest, flood-fill
  connectiviteits-guard), fragile floors, bump-to-reveal, val naar verdieping
  eronder met ~12% max-HP schade (nooit dodelijk), ledge-grab boven flooded floors.
- `dungeon_fps_view.gd` — "H" rendert als muur; crack/hole decals in de zichtbare
  strook per diepte-band.
- `dungeon_lighting.gd` — fixtures alleen nog op kale vloer (overschreven anders
  de secret chest).

## Verificatie

Probes: `probe_dungeon_secrets.gd` (5 secret chambers / 3 verdiepingen, reveal OK,
val 1→2 OK, R→O OK) en `probe_floor_decals.gd` (decal-rendering).
Screenshots: `L:\!Nova V2\Z Cost Reports\_dungeon_secrets_probe\`
