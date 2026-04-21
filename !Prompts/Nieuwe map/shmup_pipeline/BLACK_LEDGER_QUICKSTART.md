# Quickstart: Black Ledger Upgrade naar Raptor-style

Concreet stappenplan om bestaande Black Ledger van simple PyQt5 sprites naar Raptor-style professional quality te brengen.

## Huidige staat

- 66 weapon sprites via PyQt5 (basic)
- 432 enemy sprites (6 factions × 9 presets × 8 playthroughs)
- Alle GDScripts compleet
- Standalone space shooter werkend

## Doel

Visueel niveau gelijk aan Raptor Call of the Shadows of Tyrian 2000. Zelfde gameplay, veel mooiere graphics.

## Aanpak: iteratief upgraden

Niet alles tegelijk. Begin met hoogst zichtbare elementen, werk naar minder kritieke.

### Fase 1: Player ship upgrade (week 1)

Rex Varn's fighter is meest gezien op scherm. Prioriteit #1.

**Stappen:**
1. Ontwerp Rex Varn fighter design sheet (01_design_fase.md)
2. Maak parametric model in FreeCAD voor 3 upgrade tiers
3. Render in Blender met full materials + lighting
4. Polish in Aseprite (dit is hero asset, extra aandacht)
5. Assemble sprite sheet met alle animations
6. Import in Godot, vervang bestaande player scene
7. Jury validatie

**Tijd:** 8-12 uur voor pristine resultaat.

**Success metric:** Player ship opvallen met professionele look, animaties smooth.

### Fase 2: Boss ships (week 2-3)

Bosses zijn memorable moments in shmup. Moeten indruk maken.

**Stappen:**
1. Design 4 bosses (één per act)
2. FreeCAD parametric (multi-part voor attack patterns)
3. Blender met damage states (5 per boss)
4. Aseprite polish (veel handwerk voor bosses)
5. Animation per weapon/pattern
6. Godot integration met boss scripts

**Tijd:** 10-20 uur per boss = 40-80 uur totaal.

**Success metric:** Elke boss visueel onderscheidend, damage states betekenisvol.

### Fase 3: Enemy variants (week 4-6)

De 432 enemies kunnen niet allemaal handwerk krijgen. Hier schijnt de pipeline echt.

**Stappen:**
1. Identificeer 12-20 unique base enemies (rest zijn color variants)
2. FreeCAD parametric per base
3. Blender render base ships in detail
4. Aseprite polish bases
5. PyQt5 color variant generator:
   - Base sprite + faction color scheme = new variant
   - 6 factions × 9 presets uit 12 bases via color substitution
6. Spot check varianten visueel
7. Jury batch validation

**Tijd:** 3-5 uur per base × 15 bases = 60-90 uur, plus 10 uur variant polish.

**Success metric:** Varianten herkenbaar verschillend, geen "slot copies".

### Fase 4: Projectiles + effects (week 7)

Weapons en explosions vaak onderschat maar hebben grote impact.

**Stappen:**
1. Design 66 weapon projectiles (subset is genoeg: ~15 unique)
2. Particle systems voor muzzle flash + impact
3. Explosion sprites per ship class (small/medium/large)
4. Power-up visual polish
5. UI elements (health bar, score, etc)

**Tijd:** 20-30 uur voor alle effects.

**Success metric:** Combat voelt impactvol, weapons onderscheidend.

### Fase 5: Backgrounds + environment (week 8-9)

Parallax backgrounds en mood setting.

**Stappen:**
1. Design 4 act environments (verschillende settings)
2. Blender procedural backgrounds (nebulae, planets, stations)
3. Parallax layering (3-5 layers per scene)
4. Transitional effects tussen acts
5. Godot ParallaxLayer setup

**Tijd:** 20-30 uur totaal.

**Success metric:** Each act voelt verschillend, sense of travel.

## Totale tijdlijn

- Solo fulltime: 9-12 weken
- Solo parttime (20u/week): 4-6 maanden
- Met NOVA v2 automation assistance: 30-40% sneller na initial setup

## Critical success factors

**1. Style bible strict following**
Maak en volg style bible. Één uitglijder verpest het geheel.

**2. Hero assets first**
Player ship en bosses krijgen extra tijd. Rest mag sneller.

**3. Variant strategie**
Don't make 432 unique ships. Make 15 great ones + color substitution system.

**4. Iteratief testen**
Elke week nieuwe batch in gameplay testen. Visueel acceptabel in context?

**5. Niet perfectioneren voor release**
Release met Fase 1-3 compleet. Fase 4-5 in post-launch updates mogelijk.

## Bestaande assets migratie

**Voor bestaande PyQt5 sprites (huidige 432):**

Optie A: Complete vervanging (aanbevolen)
- Alle bestaande sprites archiveren
- Volledige pipeline doorlopen
- Clean slate met professionele look

Optie B: Hybride (sneller)
- Bosses en player 100% nieuw (pipeline)
- Enemies: upgrade via re-render maar zelfde design
- Mix van oud en nieuw zal zichtbaar zijn

Optie C: Geleidelijke vervanging
- Release huidige versie
- Per update een fase upgrade
- Gebruikers zien verbeteringen over tijd

Aanbeveling: Optie A voor echte kwaliteit sprong, Optie C als je al klanten hebt.

## Quality comparison

**Voor (huidige):**
- Flat pixel art uit PyQt5
- Limited rotation frames
- Simple damage indication
- Geen custom lighting per asset
- Variants via color shift only

**Na (pipeline):**
- 3D-rendered sprites met volumes
- 16 smooth rotation frames per ship
- 3-5 progressive damage states met visuele impact
- Consistent lighting per faction
- Variants met material + detail differences

## Parallel game development

Tijdens asset pipeline werk, andere Black Ledger taken die nog open staan:
- BackgroundManager shader error fixen
- PowerOrb error oplossen
- Error Agent testing
- Final gameplay balancing

Deze parallel naast asset werk.

## Beslisboom voor start

Wil je starten met deze pipeline?

**Ja, ik wil Raptor-style graphics:**
→ Begin met Fase 1 (player ship)
→ Lees 01_design_fase.md vandaag
→ FreeCAD installatie + training deze week
→ Blender setup volgende week

**Nee, huidige quality is goed genoeg:**
→ Focus op andere Black Ledger taken (shader fix, error agent)
→ Pipeline bewaren voor volgende game project
→ Release Black Ledger zoals het nu is

**Deels, selectieve upgrade:**
→ Alleen player ship + bosses nieuwe quality
→ Enemies blijven PyQt5
→ Minder tijd, hybride look

## Risico's

**Risk 1: Scope creep**
Pipeline verleidt tot eindeloos verbeteren. Zet deadline.

**Risk 2: Tool learning curve**
FreeCAD + Blender zijn serieus leren. Eerste ship duurt langer.

**Risk 3: Inconsistentie**
Als één ship pipeline-kwaliteit is en ander PyQt5, valt dat op. Consistent zijn.

**Risk 4: Over-perfecting**
Raptor was niet perfect. Gameplay > pixel perfection altijd.

## Alternatief: huidige op niveau houden

Als pipeline te veel is, verbeter bestaande PyQt5 output:
- Betere palette discipline
- Meer rotation frames (van 4 naar 16)
- Damage states toevoegen
- Jury validation op bestaande assets
- Aseprite polish zonder Blender/FreeCAD

Minder impressief maar veel sneller resultaat.

## Volgende stap

Kies:
1. Volle pipeline (9-12 weken) → start met player ship
2. Hybride (4-6 weken) → bosses + player nieuw, rest oud
3. PyQt5 upgrade (2-3 weken) → verbeter bestaand
4. Niks → focus op andere Black Ledger taken

Welke past bij jouw huidige situatie en ambitie?
