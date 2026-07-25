# PixelLab — Shopkeeper-variatie voor Aetherion (Grimm Reaper)

**Datum:** 2026-07-25
**Quota:** 0/3800 subscription over — batch liep **op credits** (na runes-batch $25.91).

## Gegenereerd (7 × 120×120, side view, medium shading — zelfde formaat als Aldric)

| Shoptype | Keeper | Object ID |
|---|---|---|
| blacksmith | Brenna — Blacksmith (roodharige smid, aambeeld) | 328e7e02 |
| weapons | Garrick — Arms Dealer (ooglap, gekruiste armen) | a9ca20bb |
| armor | Thorvald — Armorer (dwerg in maliën) | 28634844 |
| potions | Zosia — Alchemist (groen haar, goggles) | 8ac0dcd5 |
| spells | Alarion — Spellwright (witte baard, sterrenmantel) | 5e87f222 |
| jewelry | Seraphine — Jeweler (zilveren knot, monocle) | d14e5c29 |
| general | Odo — Merchant (gestreepte schort, kratten) | 78a985b3 |

Inn hield Mara (bestaande polish-glass strip); Aldric blijft de fallback voor
ontbrekende art of onbekende shoptypes.

## Paden

- Archief: `L:\ZZZZZZ ZZ PROMPTS\Assets\aetherion\pixellab\characters\shopkeeper\keeper_{type}_{id8}.png`
- Game: `aetherion_segment_01\assets\sprites\npc\shopkeeper\keeper_{type}.png`
- Download-script (re-runnable): `L:\!Nova V2\scripts\download_shopkeeper_variants.py`

## Code

- `shopkeeper_stage.gd`: `KEEPERS`-tabel + `set_shop_type()` (laadt keeper-still,
  zet naamlabel, valt terug op Aldric).
- `shop_controller.gd`: roept `set_shop_type(shop_type)` aan bij openen (behalve inn).

## Verificatie

Probe `probe_shopkeepers.gd`: 16/16 PASS — 7 unieke textures, juiste namen,
Aldric-fallback bij onbekend type. Smoke test: PASS.
