# Aetherion — D&D-laag: classes, runes, need-vs-greed, morality

**Datum:** 2026-07-25
**Project:** `L:\! 2 Nova v2  OUTPUT !\Z Aetherion\blockout\aetherion_segment_01`
**Status:** probe 34/34 PASS · smoke test PASS

## 1. Class-systeem (proficiencies)

Party had al classes (`progression.json`), maar zonder gevolgen. Nu:

| Member | Class | Wapens | Armor max | Spell-scholen |
|---|---|---|---|---|
| Aria | Knight | sword, axe, spear, bow | heavy | — (geen caster) |
| Brock | Guardian | mace, hammer, axe, crossbow | heavy | — (geen caster) |
| Cyra | Mage | staff, focus, dart | light | arcane/ice/fire/lightning/dark/earth/poison |
| Rowan | Cleric | mace, hammer, staff, focus | medium | holy/water/arcane |

- Universele wapens (iedereen): dagger, thrown, sling, bolo, net.
- Alle 28 wapens hebben `weapon_type`, alle 53 armorstukken `weight` (light/medium/heavy).
- Alle 23 spells hadden al `element`; de affinity-gate (`QuestManager.can_equip_spell`) werkt daar nu echt op.
- Enforcement zit in `Inventory.equip_to_slot` (+ UI-feedback met reden, bv. "Cyra (Mage) cannot wear heavy armor (max light)").
- Ammo blijft gekoppeld aan ranged weapon type (bow→arrow, crossbow→bolt); wie het wapen niet mag dragen, komt nooit aan die ammo toe.

## 2. Rune-systeem

- Nieuwe catalogus-categorie `runes` (10 stuks) in `shop_catalog.json`; blacksmith verkoopt een roterende plank van 4 (Packs-tab).
- Gear tier ≥3 heeft 1 rune-socket, tier ≥5 heeft 2 (`rune_sockets` op wapens én armor).
- Runes socketen via de equip-UI: klik een rune in de bag terwijl een gear-slot geselecteerd is (`Inventory.socket_rune_into_equipped`).
- Stat-runes: might +2 ATK, warding +2 DEF, swiftness +1 SPD, vigor +6 HP, mind +4 MP.
- Element-runes (flame/frost/storms/shadows/light): +1 ATK en zetten `element` op het wapen (enchant).
- Rune-bonussen tellen mee in `_apply_equipment_stats`; tooltip toont "Runes: … (1/2)" of "Sockets: n empty".
- Drops: runes zitten in `loot_rare`, `dungeon_rare` en `loot_jackpot`.
- 10 PixelLab-icons gegenereerd (op credits) → `assets/icons/icon_rune_of_*.png` + archief.

## 3. Need vs Greed

Bij gear-drops (wapens/armor/ringen/amuletten) rolt elk levend partylid d100:
**Need** alleen als het lid het item met z'n class mag gebruiken, anders **Greed**.
Hoogste Need wint; zonder Need-rollers wint hoogste Greed. Voorbeeld uit de probe:

> Steel Blade — Aria N16 · Broc G88 · Cyra G48 · Rowa G44 → Aria

Need-winnaar met leeg slot krijgt het item direct aangetrokken; anders gaat het de
bag in met `owner`-tag. Logging via `GameLog loot/need_greed`.

## 4. Morality

- `GameState.morality` (-100..+100), labels: Honorable / Good / Neutral / Shady / Ruthless.
- Hooks: siren helpen **+3**, gevallen avonturiers plunderen **−2** (via loot-alias).
- Effect: shop-prijzen — Honorable −8%, Good −4%, Shady +8%, Ruthless +15% (`morality_price_mult` in `Inventory.buy`).
- Zichtbaar in de equip-screen supplies-rij; persist in savegames; reset bij nieuwe game.

## 5. PixelLab Objects-pagina — beoordeling

Remote: **2551 completed**, 1 review, 6 failed. Bulk sync haalde 675 ontbrekende
objects binnen (0 fail) — alles staat nu onder `L:\ZZZZZZ ZZ PROMPTS\Assets\aetherion\pixellab\`.

Bruikbaar en al aangesloten: 449+ bestiary battle-sprites, ~700 wapen-renders
(sword/mace/bow/…), 141 armor-icons, 140 gems, 107 potions, 88 d20-dice-frames,
NPC-roster met 8-richting rotaties, 9 dungeon-thema's, town/city-wall kits, UI-panels.

Kansen (nog niet in game aangesloten):
- **Dice/d20-frames** → zichtbare need/greed- en d20-skill-rolls in UI.
- **icons\armor (141)** → itemcatalogus dekt ~53 stukken; ruimte voor meer armor-tiers zonder nieuwe generaties.
- **Weapons\mace (161) e.a. batch-renders** → battle-layer wapenoverlays per class.
- **characters (zittende hero-portretten)** → inn/rest-scènes.
- Failed (6) zijn oude gem/crossbow/jewelry-pogingen; opnieuw genereren is optioneel, iconen bestaan al lokaal.

## 6. Gewijzigde bestanden

| Bestand | Wat |
|---|---|
| `scripts/class_system.gd` (nieuw, autoload) | proficiencies, need/greed, rune-API |
| `data/progression.json` | weapon_types + armor_weight per class |
| `data/shop_catalog.json` | weapon_type, weight, rune_sockets, runes-categorie |
| `data/loot_tables.json` | rune-drops (rare/jackpot/dungeon_rare) |
| `scripts/inventory_manager.gd` | equip-gate, need/greed in add_loot, rune-socket + stats, morality-prijs, class-loadout |
| `scripts/game_state.gd` | morality + label + price_mult |
| `scripts/save_manager.gd` | morality persist |
| `scripts/loot_roller.gd` | grave-robbing hook |
| `scripts/dungeon_controller.gd` | siren-help hook |
| `scripts/equip_controller.gd` | class/rune-tooltips, rune-socket-klik, morality-weergave, blokkeer-reden |
| `scripts/shop_stock.gd` + `shop_controller.gd` | blacksmith runes-plank |
| `scripts/smoke_test_runner.gd` | equip-test class-proof gemaakt + gate-regressietest |
| `scripts/tools/probe_class_rune_ng.gd` (nieuw) | 34 checks, allemaal PASS |

## 7. Verificatie

- Probe: `PROBE_DONE fails=0` (34 checks: gates, spells, need/greed, runes, morality, icons, shop).
- Smoke test: `SMOKE_TEST: PASS (all checks ok)` — incl. nieuwe regressietest dat de guardian géén zwaard meer kan dragen.
