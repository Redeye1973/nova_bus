# Aetherion — Eye of the Beholder / Lands of Lore dungeon-stijl (25 juli 2026)

Opdracht Alex: "voor de dungeons en caves een Lands of Lore 1 en Eye of the Beholder look en gameplay stijl".

## Look — renderer herschreven (`dungeon_fps_view.gd`)

**Was:** platte, geneste rechthoeken per diepte ("dozen-in-dozen", geen perspectief).
**Nu:** echt verdwijnpunt-perspectief zoals EoB/LoL1:

- Schaalfunctie `s(x) = C/(C+x)` (C=1.15); cel op index d beslaat gridafstand d+0.5 → d+1.5.
- **Zijmuren** = trapezium-vlakken (near-edge groot, far-edge klein richting verdwijnpunt).
- **Vloer/plafond** = convergerende full-width banden per diepte.
- **Junction closures**: open zijgangen tonen de frontmuur van de zijtak één vlak dieper (geen zwarte gaten).
- Frontmuur gezien = zijcellen face-on gevuld (doorlopende muur zoals EoB).
- Painter's algorithm gefixt: niets rendert voorbij de eerste frontmuur; dieptelagen in juiste volgorde (bug: banden tekenden over de frontmuur heen).
- Polygon2D affine-UV zigzag opgelost door quads in 6 stroken te subdividen (`_add_quad_sliced`), UV-as per vlaktype (muren u-as, vloer/plafond v-as).
- Vierkante oranje torch-halo's vervangen door radiale gradient-glow (`GradientTexture2D`).
- Bestaande SHP-pack (LoL-stijl per-side/depth frames), thema-tilesets, flood-shader, decals (crack/hole) en props werken door op de nieuwe geometrie.

## Gameplay — EoB-interactie

- **Muurhendels ("V")**: 1 per verdieping gegenereerd naast de bestaande locked door "K" (`_place_puzzles_and_locks`). Hendel overhalen opent de dichtstbijzijnde K-deur zonder sleutel — sleutel blijft alternatief. Gebruikte hendel wordt "v" (handle omlaag), procedurele sprite in de view, eigen automap-kleur.
- **Klikbare corridor-view** (EoB-muisbediening): linker-/rechterrand = draaien, onderrand = stap vooruit, midden = gebruiken (hendel/deur/kist/vijand/plate — routes door bestaand `_open_chest_here`).
- Al aanwezig en passend bij de stijl: grid-movement met facing, hidden walls (bump-to-reveal), breekbare vloeren/pits, niches, pressure plates, torch-fuel licht.

## Chrome

`_apply_eob_chrome()` in `dungeon_controller.gd`: stenen frame (6px border) om de corridor-view, stenen knoppen met goud-accent bij indrukken, rond kompas-medaillon met rode windletter.

## Verificatie

- Nieuwe probe `scripts/tools/probe_dungeon_eob.gd`: lever+deur op elke verdieping gevonden, pull → V→v en K→. bevestigd, klikzones draaien/herstellen facing. **PASS**
- Bestaande `probe_dungeon_secrets.gd`: secrets/fragile floors/val-mechaniek blijven werken op de nieuwe renderer. **PASS**
- Smoke test (34 checks): **PASS (all checks ok)**.
- Screenshots: `Z Cost Reports\_dungeon_eob_probe\` en `_dungeon_secrets_probe\`.

## Gewijzigde bestanden

| Bestand | Wat |
|---|---|
| `scripts/dungeon_fps_view.gd` | perspectief-geometrie, sliced quads, junction closures, halo, lever-sprite, click-signal |
| `scripts/dungeon_controller.gd` | lever-generatie + pull, klikzone-routing, EoB-chrome, automap-kleuren |
| `scripts/dungeon_lighting.gd` | "V"/"v" walkable |
| `scripts/tools/probe_dungeon_eob.gd` | nieuw — lever/klik-verificatie + screenshots |

Geen PixelLab-verbruik voor deze sessie (alles procedureel / bestaande assets).
