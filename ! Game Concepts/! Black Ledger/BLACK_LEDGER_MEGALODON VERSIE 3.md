# BLACK LEDGER — MEGALODON PROMPT
# Geef dit VOLLEDIG aan de NOVA Prompt Director Agent op N8n.
# De Prompt Director verdeelt het werk en stuurt Cursor aan per blok.

## VOOR DE PROMPT DIRECTOR

Dit is de volledige bouwspecificatie van Black Ledger. 8 prompts, 60+ blocks.
**Canon-project voor uitvoering:** `L:\1 Nova Cursor Output\Dark Ledger\` — volg **`L:\Nova\1ToDo\Inplement Me\Clean\1st.txt`** voor paden, import-stappen en licentie-guards. `L:\Nova\SpaceShooter\` is alleen **referentie-logica**; **niet** terugschrijven.
Voer STRIKT in volgorde uit: A → B → C → D → E → F → G → H.
Na elk BLOCK: parse check + git commit. Bij fout: fix eerst, dan door.
Na elke PROMPT: runtime test met **Dark Ledger** `project.godot`, bijv. `godot --headless --path "L:\1 Nova Cursor Output\Dark Ledger" --quit-after 10`. Bij crash: stop en rapporteer.
**Asset-registratie (2026-update):** geen automatische upload van **gekochte** pixel-art naar externe webhooks/Hetzner/MinIO. Voortgang lokaal loggen of alleen **interne** director-webhook (zonder `res://Assets/` binaries). Zie ook `L:\1 Nova Cursor Output\Dark Ledger\.novaconfig` (verbod redistribution / ComfyUI-input).
Stuur voortgang naar Ntfy: curl -d "Prompt X Block Y klaar" http://localhost:8090/nova-alerts

## GAME VISIE

Black Ledger is een top-down space shooter in de stijl van Tyrian/Raptor GECOMBINEERD met Wing Commander Privateer. Het verschil met een gewone shooter: je bent een freelancer die missies aanneemt, reputatie opbouwt bij facties, en keuzes maakt die de wereld veranderen.

PRIVATEER-ELEMENTEN:
- Missie briefings met geanimeerde portretten en subtitles (Privateer-stijl)
- Cutscenes tussen levels: reisanimaties naar andere planeten/stations
- Bounty board: hogere beloning = moeilijkere vijanden
- Vijand skill scaling: laag bedrag = rookies, hoog bedrag = Aces die van alle kanten aanvallen
- Blockade missies met eindboss
- Verhaalkeuzes die de wereld veranderen
- The Drifter: mysterieuze figuur die verschijnt op onverwachte momenten

TYRIAN/RAPTOR-ELEMENTEN:
- Verticaal scrollend level design
- Wapen upgrade systeem (11 levels per wapen)
- Geheime codes en verborgen levels
- Score streaks en multipliers
- Power-ups en shield/armor systeem

## WAT AL KLAAR STAAT — NIET OPNIEUW BOUWEN

✓ WeaponData.gd + WeaponDatabase.gd + WeaponSlotManager.gd + PowerOrb.gd
✓ **Gekochte SHMUP pixel-art** onder `L:\Nova Assets\Gekochte Assets\Pixel Art\` (import in-game via `AssetCatalog` / `res://Assets/` — zie `L:\Nova\1ToDo\Inplement Me\Clean\1st.txt`)
✓ **Verwijderd uit deze specificatie:** oude **PyQt5/PIL weapon sprite batches**, **66 weapon sprites**-workflow, en **enemy sprite generator** (vervangen door gekochte enemy/faction packs + handmatige Krita/Blender aanvullingen waar nodig)
✓ MissionData.gd + MissionManager.gd + MissionGenerator.gd *(ReputationManager/FactionData/NewsBroadcastSystem/RemnantLance: alleen als ze daadwerkelijk in het actieve project bestaan — anders feature-flag of stub vermijden)*
✓ LevelGenerator.gd + SecretLevelManager.gd
✓ StoryManager.gd + GameConstants.gd (alle enums)
✓ NOVA Pipeline addon (54/54 checks) *(optioneel; niet verplicht voor Dark Ledger-variant)*

## PADEN

| Item | Pad |
|------|-----|
| **Project (Megalodon — werk hier)** | `L:\1 Nova Cursor Output\Dark Ledger\` |
| Referentie-logica (read-only) | `L:\Nova\SpaceShooter\` — **geen** nieuwe visuals of overschrijven |
| Scripts | `L:\1 Nova Cursor Output\Dark Ledger\scripts\BlackLedger\` *(in dit document: `Scripts/BlackLedger/` = `res://scripts/BlackLedger/`)* |
| Scenes | `L:\1 Nova Cursor Output\Dark Ledger\scenes\` |
| UI / Cutscene scenes | `...\scenes\UI\`, `...\scenes\Cutscenes\` |
| **Visuele assets (canon)** | `res://Assets/...` → schijf: `...\Dark Ledger\Assets\` |
| Gekochte bron (read-only import) | `L:\Nova Assets\Gekochte Assets\Pixel Art\` |
| Level data / audio (logic) | `res://assets/levels/`, `res://assets/audio/` of equivalent in Dark Ledger *(behoud structuur uit kopie; geen oude PyQt5-sprite trees)* |
| Krita / Blender (aanvullende art) | Handmatig + `L:\Nova\krita_pipeline\` waar van toepassing — **geen PyQt5/PIL sprite-fabriek** voor productie-art |
| Blender | `C:\Program Files\Blender Foundation\Blender 4.3\blender.exe` *(pad kan afwijken)* |
| Ollama | http://localhost:11434 |
| ~~Asset Registry~~ | **Verwijderd:** externe `nova-assets-register` webhook conflicteert met licentie-guards voor gekochte assets. Gebruik **lokale** manifesten / git / `IMPORT_REPORT.md`. |

## NIEUWE ASSETS — GEBRUIK IN ALLE PROMPTS (samenvatting `1st.txt` STAP 2)

Alle sprites, backgrounds, VFX en UI die in Megalodon genoemd worden, komen uit **gekochte packs** (import → `res://Assets/`) en worden in code opgevraagd via **`/root/asset_catalog`** (`AssetCatalog.gd`), **niet** via hardcoded `res://assets/sprites/...` van de oude variant.

| Domein | `res://` doel | Bronpack (onder `L:\Nova Assets\Gekochte Assets\Pixel Art\`) |
|--------|----------------|----------------------------------------------------------------|
| Player | `Assets/Ships/Player/` | Animated_Pixel_Ships … **Plane 02** (Normal + Powered Up) |
| 6 factions | `Assets/Enemies/<faction_id>/` | Pixel_Enemies_for_SHMUP — mapping Harkon/Syndicate/Corp/Remnant/Frontier/Void per `1st.txt` |
| Bosses | `Assets/Bosses/` | Boss enemies + 07 Emperor; Act 4 final = **Plane 09 Powered Up** |
| Allies / escort | `Assets/Ships/Allies/` | Pixel Spaceships for SHMUP 2 |
| Varianten | `Assets/Enemies/_variants/` | Pixel_Spaceships_for_SHMUP (kleursets) |
| Projectiles | `Assets/VFX/Projectiles/` | Animated_Pixel_Ships Projectiles + SHMUP 1.5.1 Projectiles |
| Explosions | `Assets/VFX/Explosions/` | Pixel_Art_VFX_Explosions + White Blast (shield break) |
| Backgrounds | `Assets/Backgrounds/` | Pixel Art Space Background SHMUP + Animated_Pixel_Ships Background |
| HUD icons / drops | `Assets/UI/Icons/`, `Assets/UI/PowerUps/` | Animated_Pixel_Ships Icons + Power-Ups |
| Portraits | `Assets/UI/Portraits/` | Animated_Pixel_Ships **Character Portrait** |
| Shield / thrusters | `Assets/VFX/Effects/` | Animated_Pixel_Ships Shield + Large Thrusters |

**Regels:** filter UIT op PNG-import; atlas/SpriteFrames waar nodig; **LICENSE_ASSETS.md** + **.novaconfig** in projectroot respecteren.

## STIJLGIDS

Kleuren: bg #0d0d1a, panel #14142a, border #3c50b4, accent goud #f5a623, rood #e94560, tekst #e0e0e0
Fonts: system of DynamicFont, geen externe dependencies
Animaties / cutscenes: **Krita** (2D frames) en/of **Blender** (pre-render → downscale in Krita). **Geen** PyQt5/PIL-procedural batches als primaire asset-pijplijn.
Portretten: **Character Portrait**-set uit gekocht pack (`res://Assets/UI/Portraits/`), 128×128 pixel art, per faction eigen kleurpalet waar geen canon-portret bestaat
Subtitles: wit met zwarte outline, onderaan scherm

---

# ================================================================
# PROMPT A — GAMEPLAY KERN
# ================================================================

## A1: HealthComponent.gd
Scripts/BlackLedger/HealthComponent.gd
- Shield + Armor systeem, Tyrian stijl
- Shield regenereert na 2.5s zonder schade
- Signals: shield_changed, armor_changed, shield_depleted, died
- take_damage(): shield eerst, overflow naar armor
- @export: max_shield=100, max_armor=100, shield_regen_rate=8.0, shield_regen_delay=2.5

## A2: ScoreManager.gd
Scripts/BlackLedger/ScoreManager.gd
- Kill streak met 3s timeout
- Multipliers: 5kills=x2, 10=x3, 20=x4, 40=x5
- Signals: score_changed, streak_changed, streak_broken

## A3: WaveManager.gd
Scripts/BlackLedger/WaveManager.gd
- 5 segmenten per level: intro, escalation, complication, crisis, finale
- Spawnt enemies per segment via formaties
- Next segment na alle enemies dood + 1.5s delay
- Boss spawn in finale segment

## A4: DifficultyManager.gd
Scripts/BlackLedger/DifficultyManager.gd
- 6 levels: EASY, NORMAL, HARD, IMPOSSIBLE, SUICIDE, LORD_OF_GAME
- HP/DMG/Speed multipliers per difficulty
- Geheime codes via toetsaanslagen: IMPOSSIBLE, SUICIDE, LORDOFTHEGAME, REXVARN

## A5: BountyBoard.gd (NIEUW — Privateer stijl)
Scripts/BlackLedger/BountyBoard.gd
- Genereert bounty missies met variabele beloning
- Beloning bepaalt vijand skill: 500cr=rookies, 2000cr=veterans, 5000cr=elites, 10000cr+=Aces
- Aces: vliegen in formatie, flanken van alle kanten, actief ontwijken, schieten gericht
- Rookies: voorspelbaar, rechte lijnen, trage reactie
- Meerdere bounties tegelijk accepteren mogelijk
- Signal: bounty_completed(reward, target_name)

## A6: EnemyAI.gd (NIEUW — skill-based)
Scripts/BlackLedger/EnemyAI.gd
- AI behavior per skill level:
  ROOKIE: fly_straight, shoot_forward, no_dodge
  VETERAN: follow_player, lead_shots, occasional_dodge
  ELITE: flank_player, burst_fire, active_dodge, use_abilities
  ACE: coordinate_with_squad, predict_player, constant_pressure, retreat_when_low
- Aces werken samen: als er 3+ Aces zijn, flanken ze van meerdere kanten tegelijk
- Skill level komt van BountyBoard of DifficultyManager

## A7: EjectionSystem.gd (NIEUW)
Scripts/BlackLedger/EjectionSystem.gd
- Vijanden hebben kans om te ejecten bij lage HP (< 15%)
- Kans gebaseerd op vijand skill: rookie=80% eject, ace=20% (aces vechten door)
- Ejected pilot = klein sprite dat wegdrijft
- Ejected ship drijft beschadigd maar intact
- Speler kan kiezen: vernietigen (credits) of enteren (ship capture)

## A8: BoardingMinigame.gd (NIEUW)
Scripts/BlackLedger/BoardingMinigame.gd
- Triggert wanneer speler een ejected ship nadert en ENTER drukt
- Minigame: timing-based (druk op juiste moment voor success)
- Succes kans gebaseerd op:
  - Hoeveel schade JIJ aan het schip hebt toegebracht (meer schade = lager succes)
  - Of shields uitgeschakeld waren via EMP (bonus +25%)
  - Vijand skill level (ace ship = moeilijker minigame)
  - Je eigen ship hull upgrade level (hoger = beter)
- Uitkomsten:
  SUCCESS_PERFECT: schip intact, alle wapens + upgrades overnemen
  SUCCESS_PARTIAL: schip beschadigd, 50% wapens + geen upgrades
  SUCCESS_MINIMAL: alleen cargo/credits, schip te beschadigd
  FAILURE: booby trap, jij neemt schade, schip explodeert
  CRITICAL_FAIL: ejected pilot keert terug, miniboss gevecht
- Captured ships: verkopen voor credits OF toevoegen aan hangar (max 3 reserve ships)

## A9: EMPWeapon.gd (NIEUW)
Scripts/BlackLedger/EMPWeapon.gd
- Nieuw wapen type in WeaponDatabase: EMP
- Doet weinig hull schade maar draint shields snel
- Volledig shield drain = "OVERLOADED" status op vijand (visueel: blauw flicker)
- Overloaded vijand:
  - Shields regeneren niet voor 8 seconden
  - Boarding success +25% bonus
  - Alle wapens van vijand offline voor 3 seconden
  - Visueel: elektrische vonken over het schip
- EMP heeft cooldown (10s) en beperkte range
- Upgrade levels 1-11 (zoals andere wapens):
  - Hogere levels = snellere shield drain + langere overload duration
  - Level 11: chain EMP — slaat over naar nabijgelegen vijanden

## A10: Update Player.gd + Autoloads
- HealthComponent als child node op Player
- ScoreManager, DifficultyManager, WaveManager als autoloads
- BountyBoard als autoload

## A11: VERIFY + COMMIT
- Parse check, runtime test
- Test ejection: schiet vijand tot <15% HP, kijk of hij eject
- Test boarding: nader ejected ship, speel minigame
- Test EMP: vuur EMP, shields moeten draaien, overload visueel
- git commit -m "feat(A): gameplay core + bounty + enemy AI + ejection + boarding + EMP"

---

# ================================================================
# PROMPT B — UI COMPLEET
# ================================================================

## B1: HUD.tscn + HUD.gd
- Shield/Armor bars TOP LEFT
- Wave + Level name TOP CENTER
- Credits + Score + Streak TOP RIGHT
- Weapons BOTTOM LEFT, Sidekicks BOTTOM RIGHT
- News ticker BOTTOM CENTER
- Connect alle signals

## B2: WeaponsStore.tscn
- Ship preview links, wapen tabs center, stats rechts
- 11 level blokjes per wapen, faction discount

## B3: MissionBriefing.tscn (Privateer stijl!)
- GEANIMEERD portret van missie-gever (128x128, idle animatie)
- Tekst verschijnt karakter voor karakter (typewriter effect)
- Subtitles onderaan
- Factie logo + kleuren
- Missie details: beloning, difficulty sterren, side objectives
- START / WEIGER knoppen
- Bij bounty missies: doelwit foto + "WANTED" stempel

## B4: MissionDebriefing.tscn
- VOLTOOID/MISLUKT groot, stats, credits tellen omhoog, rep wijzigingen

## B5: BountyBoardUI.tscn (NIEUW — Privateer stijl)
- Lijst van beschikbare bounties
- Per bounty: naam target, beloning, difficulty indicator (schedels 1-5)
- Kleur: groen=makkelijk, geel=medium, oranje=hard, rood=extreem
- Accept knop, max 3 tegelijk actief
- Actieve bounties sidebar met progress

## B6: CommsMessage.tscn
- Popup bottom-left tijdens level, factie kleur, auto-sluit 4s

## B7: DrifterDialog.tscn
- ANDERS dan normale UI: geen kaders, wit op zwart, typewriter, statische ruis

## B8: MainMenu.tscn
- NIEUW SPEL, DOORGAAN, JUKEBOX, OPTIES, AFSLUITEN
- Geheime code input, sterren achtergrond + schip animatie

## B9: BoardingUI.tscn (NIEUW)
- Minigame scherm: timing indicator (groene zone beweegt, druk op moment)
- Ship status display: hull integrity %, shield status, overload indicator
- Success kans percentage zichtbaar
- Uitkomst animatie: SUCCESS (groen flash) / FAIL (rood + explosie)
- Loot display bij success: wapens, credits, ship stats
- Keuze na capture: VERKOPEN (credits) / HANGAR (bewaren, max 3)

## B10: GameOver + Victory + ShipSelect
- GameOver: rode tekst, score, OPNIEUW/HOOFDMENU
- Victory: goud, rep overzicht, DOORGAAN/WINKEL
- ShipSelect: 9 schepen grid met stats bars

## B11: VERIFY + COMMIT
- Parse check, alle UI scenes openen
- Test boarding minigame UI
- git commit -m "feat(B): complete UI + bounty board + boarding + Privateer briefings"

---

# ================================================================
# PROMPT C — GAME MODES + ENDINGS
# ================================================================

## C1: ArcadeMode.gd
- Geen winkel, power-ups droppen, 3 levens, score progression

## C2: TimedBattleMode.gd
- Tijdslimiet, score = tijd_bonus + kills + integriteit

## C3: DatacubeSystem.gd
- 5 datacubes met lore fragmenten
- Collectie ontgrendelt secret level "DATACUBES"
- Lore teksten over Rex Varn, The Ledger, Project Phantom

## C4: RemnantLanceVFX.gd
- 6 tiers visueel: small orb → beam → burst → chain lightning → black hole → GAMMA RAY BURST
- GRB: scherm wit, alles weg, stilte 1.5s, schild=0, pantser=50%

## C5: EndingManager.gd — 3 endings
- CLEAN SLATE: Rex vernietigt The Ledger, vrij maar verliest alles
- NEW LEDGER: Rex neemt controle, machtigste speler
- GHOSTED: Rex verdwijnt, wordt legende

## C6: AudioManager.gd
- SFX per wapen type: ballistic=crack, energy=hum, exotic=unique, precursor=silence+thunder
- Music tracks: menu, combat, boss, shop, ending_a/b/c
- Placeholder: Godot AudioStreamGenerator voor procedural tonen, later Audiocraft

## C7: SaveLoadSystem.gd
- 3 slots, slaat op: rep, credits, weapons, story flags, datacubes, playtime

## C8: VERIFY + COMMIT
- Test GRB visueel, test endings, test save/load
- git commit -m "feat(C): game modes + 3 endings + audio + save system"

---

# ================================================================
# PROMPT D — SHIP UPGRADE SYSTEEM
# ================================================================

## D1: CharacterCreation.gd (NIEUW)
Scripts/BlackLedger/CharacterCreation.gd
- Speler kiest:
  - NAAM: vrij tekstveld, max 20 chars
  - TYPE: Man / Vrouw / Robot
  - Elk type heeft subtiel andere base stats:
    Man: +5% armor, standaard shield, standaard speed
    Vrouw: standaard armor, +10% shield regen, +5% speed
    Robot: -10% shield, +15% armor, +10% generator power, geen ejection mogelijk
  - Elk type heeft eigen portret sprite (3 varianten in portraits/)
  - Naam wordt gebruikt in briefings, dialogen, save files
  - Type bepaalt sommige dialoog opties (Robot krijgt andere reacties van NPC's)
- Signal: character_created(name, type)
- Opslaan in save file

## D2: CargoSystem.gd (NIEUW)
Scripts/BlackLedger/CargoSystem.gd
- Elk schip heeft een vast aantal SLOTS (weapon slots + cargo slots samen)
- Speler kiest verdeling: meer cargo = minder wapens
- Cargo slots:
  - Per slot: 1 cargo crate (transport missies)
  - Cargo types: standard (100cr), valuable (500cr), contraband (2000cr), classified (5000cr)
  - Contraband: risico op Marshal scannen → rep verlies als gevonden
  - Classified: alleen voor story missies
- Slot verdeling per schip:
  | Ship | Total slots | Min weapons | Max cargo |
  | USP Talon | 4 | 1 front | 3 cargo |
  | Harkon Blade | 5 | 2 (front+rear) | 3 cargo |
  | Helios Excavator | 7 | 1 front | 6 cargo (mining ship!) |
  | Marshal Enforcer | 5 | 2 | 3 cargo |
  | Ghost Runner | 4 | 1 | 3 cargo |
  | Phantom Wraith | 6 | 2 | 4 cargo |
  | Void Stalker | 5 | 2 | 3 cargo |
  | The Remnant | 8 | 3 | 5 cargo |
  | The Drifter | 6 | 1 | 5 cargo |
- Speler kan in station cargo configuratie wijzigen
- Bij schade: kans dat cargo vernietigd wordt (rear cargo eerst)
- Transport missies vereisen minimum X cargo slots vrij
- Signal: cargo_changed(slots_used, slots_available)
- CargoUI in station: drag-drop slots, wapen vs cargo toggle

## D3: ShipData.gd (Resource)
- ship_id, naam, faction, base_price, description, lore, special_ability
- Base stats: speed, boost, shield, armor, generator, maneuverability
- NIEUW: total_slots, min_weapon_slots (rest is cargo)

## D4: ShipDatabase.gd — 9 schepen
1. USP Talon (6000cr) — starter, snel, zwak
2. Harkon Blade (12000cr) — agressief, Syndicate
3. Helios Excavator (15000cr) — zware shields, miner
4. Marshal Enforcer (18000cr) — balanced, law
5. Ghost Runner (25000cr) — stealth, Ghost Market
6. Phantom Wraith (30000cr) — cyborg tech
7. Void Stalker (45000cr) — mysterieus
8. The Remnant (100000cr) — Rex's true ship
9. The Drifter (secret) — niet koopbaar, gevonden in secret level

## D5: ShipUpgradeManager.gd
- 5 componenten: engine, shield, armor, generator, hull — elk level 1-5
- Exponentiële kosten (zelfde als wapens)
- Stats bonussen per level

## D6: Ship sprite overlays (gekocht + handmatig)
- Gebruik **Animated Pixel Ships** / `AssetCatalog` voor basisschepen; overlays (engine glow, shield ring) als **losse lagen in Krita** of kleine sprite-strips onder `res://Assets/VFX/Effects/`.
- **Geen** `generate_ship_sprites.py` (PyQt5) meer als vereiste in deze prompt.

## D7: ShipUpgradeUI.tscn
- Live ship preview met overlays, 5 component rijen, stats radar, special ability display

## D8: Generator mechanic
- Wapen shots kosten generator power
- Generator recharges over tijd
- Laag power = tragere fire rate
- Level 5 = bijna onbeperkt

## D9: Update Player.gd + Autoloads
- ShipUpgradeManager autoload
- CargoSystem autoload
- CharacterCreation scene als eerste bij NIEUW SPEL

## D10: VERIFY + COMMIT
- Test character creation: naam + type selectie
- Test cargo: slots toewijzen, transport missie met cargo requirement
- Test upgrades, test ship koop, test sprite overlays
- git commit -m "feat(D): character creation + cargo system + 9 ships + upgrades"

---

# ================================================================
# PROMPT E — LEVEL DESIGN (28 LEVELS)
# ================================================================

## E1: LevelData.gd (Resource)
- level_id, naam, theme, scroll_length, segments, background_layers, ground_objects, boss_id
- unlock_code, is_secret

## E2: LevelDesigner.gd (Ollama generator)
- Genereert level JSON via Ollama (llama3.2:3b of codestral)
- Prompt bevat: act, difficulty, theme, faction
- Output: volledig level als JSON

## E3: ScrollingLevel.gd
- Verticaal scrollend met parallax layers
- Spawnt segments, mist patches, ground objects
- ArmorShip + ShieldCrate spawns

## E4: 28 Level definities
18 NORMALE LEVELS:
  Act 1 (3): space / asteroid / desert
  Act 2 (3): jungle / city / ocean
  Act 3 (3): volcano / arctic / ruins
  Act 4 (3): nebula / station / space
  Bonus (3): graveyard / storm / void
  Arcade (3): city / volcano / nebula

10 SECRET LEVELS:
  REXVARN=graveyard d2.5, GHOSTED=storm d3.0, THEDRIFTER=void d3.5
  BLACKLEDGER=asteroid d4.0, PHANTOM=ruins d4.5, HELIOS7741=station d5.0
  LORDOFTHEGAME=nebula d5.5, SUICIDE=void d6.0, IMPOSSIBLE=graveyard d7.0
  DATACUBES=void d9.9

## E5: BlockadeMission.gd (NIEUW — Privateer stijl)
- Speciaal level type: blokkade doorbreken
- Meerdere golven vijanden die een lijn vormen
- Je moet er doorheen breken om bij de eindboss te komen
- Eindboss = groot schip met meerdere wapen turrets
- Turrets individueel te vernietigen
- Boss HP bar bovenaan scherm

## E6: Level achtergrondkunst (gekochte packs + parallax)
- Bouw parallax uit **Pixel Art Space Background SHMUP** + **Animated Pixel Ships / Background** (zie `1st.txt` mapping naar `res://Assets/Backgrounds/`).
- Thema's: space, desert, jungle, city, volcano, arctic, nebula — afgestemd op JSON/LevelCatalog.
- **Geen** `generate_level_art.py` (PyQt5/PIL) meer als verplichting; optionele Krita-export voor unieke scenes.

## E7: VERIFY + COMMIT
- Genereer minimaal 3 levels via Ollama
- Test scrolling + spawning
- git commit -m "feat(E): 28 levels + blockade missions + level art"

---

# ================================================================
# PROMPT F — UI STYLING + SPRITES
# ================================================================

## F1: UI-sprites (gekocht + Theme overrides)
- Startpunt: **Animated Pixel Ships — Icons + Power-Ups** (`res://Assets/UI/Icons`, `res://Assets/UI/PowerUps`) + Godot **Theme** / StyleBox voor buttons/panels.
- Buttons: start, menu, upgrade, buy, back, confirm (3 states) — **vector/9-patch of handpixel in Krita**, geen PyQt5-generator.
- Progress bars: shield (blauw), armor (oranje), generator (groen), exp (goud) — Theme `StyleBoxFlat` of kleine PNG-strips.
- Main menu: gebruik bestaande sterren/nebula **achtergrond-PNG's** uit gekochte packs i.p.v. procedurally generated textures.

## F2: Portretten (Privateer stijl — Krita)
- 128x128 pixel art portretten per faction contact
- Idle animatie: 4 frames, subtiele beweging (ogen knipperen, mond beweegt)
- Per factie eigen kleurpalet:
  Harkon Syndicate: rood/zwart
  Helios Corp: goud/wit
  Marshal Authority: blauw/zilver
  Ghost Market: groen/donker
  Phantom Collective: paars/grijs
  The Fringe (neutraal): bruin/oranje
- The Drifter: apart — glitch effect, statische ruis, onscherp

## F3: Cutscene art (Privateer stijl — Krita/Blender)
- Reisanimaties tussen planeten: schip vliegt door sterren (parallax)
- Station aankomst: schip docked aan station
- Planet landing: schip vliegt naar planeet oppervlak
- Frames **handmatig** of Blender pre-render → **480×270** (of native res) → export PNG-sequence onder `res://Assets/` (cutscenes-map in het actieve project, niet hardcoded naar oude generator-output).

## F4: CutscenePlayer.gd (NIEUW)
- Speelt cutscene frames af als animatie
- Subtitle tekst onderaan met typewriter effect
- Optioneel: audio track (later via Piper TTS of Audiocraft)
- Skip mogelijk met spatiebalk
- Gebruikt tussen levels en bij story momenten

## F5: TravelAnimation.gd (NIEUW — Privateer stijl)
- Wordt afgespeeld bij planet/station wisseling
- Keuze: welk station/planeet bezoek je?
- Simpele galaxy map met beschikbare bestemmingen
- Reistijd = laadscherm met cutscene
- Random encounters mogelijk tijdens reizen (pirate ambush)

## F6: Font setup + Animatie helpers
- AnimatedPortrait.gd: laadt 4 frames, loopt idle animatie
- TypewriterLabel.gd: tekst verschijnt karakter voor karakter
- SubtitleDisplay.gd: wit + zwarte outline, onderaan scherm

## F7: VERIFY + COMMIT
- Run alle generatie scripts
- Verifieer assets in juiste mappen
- Registreer alle assets in Asset Registry
- git commit -m "feat(F): UI sprites + portraits + cutscenes + travel animations"

---

# ================================================================
# PROMPT G — PRIVATEER MISSIE SYSTEEM (NIEUW)
# ================================================================

## G1: ProceduralMissionGenerator.gd (NIEUW — vervangt simpele MissionGenerator)
Scripts/BlackLedger/ProceduralMissionGenerator.gd
- Genereert oneindige missie combinaties uit bouwblokken:
  
  MISSIE TYPE (6):    bounty | escort | transport | blockade | recon | assassination
  LOCATIE (28):       alle 28 levels als mogelijke locatie
  FACTIE (6):         wie geeft de missie + wie is de vijand
  DIFFICULTY (1-10):  schaal van rookie tot legend
  MODIFIERS (mix):    nacht | nebula | ambush | time_limit | no_shields | stealth_only
  OBJECTIVES (mix):   kill_all | kill_target | survive_time | reach_zone | protect_ship | collect_cargo
  COMPLICATIES (mix): betrayal | reinforcements | environment_hazard | intel_wrong | decoy_target
  
- Combinatie engine:
  - Kiest random type + locatie + factie
  - Past difficulty aan op basis van bounty bedrag
  - Voegt 1-3 modifiers toe (hogere difficulty = meer modifiers)
  - Genereert 1-2 objectives + 0-2 side objectives
  - Kans op complicatie: 10% bij easy, 50% bij hard, 90% bij legend
  - Output: volledig MissionData object
  
- Unieke namen via Ollama:
  - Stuurt kort prompt naar Ollama: "Generate a space bounty mission name for faction [X] targeting [Y]"
  - Fallback: template naam als Ollama niet beschikbaar
  
- Missie beschrijving via Ollama:
  - "Generate 2-sentence briefing for [type] mission, faction [X], target [Y], difficulty [Z]"
  - Geeft Privateer-stijl tekst terug

- Seed systeem: zelfde seed = zelfde missie (voor save/load + delen met andere spelers)

## G2: MissionValidator.gd (NIEUW)
Scripts/BlackLedger/MissionValidator.gd
- Checkt ELKE gegenereerde missie VOOR hij aan de speler wordt aangeboden:
  - Heeft de missie een geldige locatie? (level bestaat)
  - Kloppen de vijand types voor deze factie?
  - Is de beloning realistisch voor de difficulty?
  - Zijn de objectives haalbaar? (bijv. geen "kill 50" in een 3-enemy level)
  - Conflicteren modifiers niet? (bijv. stealth_only + time_limit is oneerlijk bij difficulty < 5)
  - Is deze combinatie al eerder aangeboden? (anti-herhaling buffer van laatste 20 missies)
- Bij ongeldige missie: gooit weg en genereert nieuwe
- Logt statistieken: hoeveel gegenereerd, hoeveel afgekeurd, meest voorkomende afkeur-reden

## G3: BountyScaling.gd
- Bounty beloning direct gekoppeld aan vijand kwaliteit:
  500cr: 3 rookies, rechte lijnen, trage reactie
  1000cr: 5 rookies + 1 veteran
  2000cr: 3 veterans, lead shots, occasional dodge
  5000cr: 2 elites + 3 veterans, flanking, burst fire
  10000cr: 3 Aces, gecoördineerde aanval van alle kanten
  20000cr: 5 Aces + 2 elites + support ships, extreme druk
  50000cr: LEGEND class — één superboss met escorts
- Elke bounty heeft een naam + korte beschrijving:
  "Krix 'Deadshot' Varren — Ex-Marshal sniper. Laatst gezien Sector 7. Voorzichtig."
  "The Ember Twins — Harkon hitteam. Altijd samen. Nooit alleen aanvallen."

## G4: ContractMission.gd
- TRANSPORT: breng cargo van A naar B, vijanden proberen je te stoppen
- ESCORT: bescherm NPC schip door vijandelijk gebied
- BLOCKADE: breek door vijandelijke linie naar doel

## G5: RandomEncounter.gd
- Tijdens reizen: kans op willekeurige ontmoeting
- Pirates, patrouilles, distress signals, The Drifter
- Keuze: fight, flee, negotiate (afhankelijk van rep)

## G6: GalaxyMap.gd
- Simpele 2D kaart met stations en planeten
- Per locatie: beschikbare missies, winkel, rep status
- Reislijnen tussen locaties
- Unlock nieuwe locaties via story progressie

## G7: StationScene.gd
- Hub tussen missies (Privateer stijl)
- Tabs/deuren: Missie Board, Winkel, Ship Upgrade, Bar (lore), Hangar (ship select)
- Bar NPC's geven hints en lore fragmenten
- The Drifter verschijnt soms in de bar

## G8: VERIFY + COMMIT
- Test generator: genereer 50 missies, check of alle uniek + valide
- Test validator: forceer ongeldige missie, moet afgewezen worden
- Test bounty scaling: 500cr → rookies, 10000cr → Aces
- git commit -m "feat(G): procedural missions + validator + galaxy map + stations"

---

# ================================================================
# PROMPT H — INTEGRATIE + POLISH
# ================================================================

## H1: GameFlow.gd
- Verbindt alles: MainMenu → ShipSelect → GalaxyMap → Station → MissionBriefing → Level → Debriefing → terug naar Station
- Story missies triggeren cutscenes
- Act transitions met speciale cutscenes
- Ending trigger op basis van keuzes + rep

## H2: Tutorial level
- Eerste level leert basis: bewegen, schieten, shield, power-ups
- Simpele vijanden, geen stress
- Eindigt met eerste station bezoek

## H3: Balance pass
- Test alle 28 levels op difficulty curve
- Verify bounty scaling voelt eerlijk
- Check dat credits economy niet breekt (niet te snel rijk, niet te traag)
- Adjust multipliers indien nodig

## H4: Audio integratie
- Koppel AudioManager aan alle scenes
- Menu muziek, combat muziek per thema, boss muziek
- SFX voor UI clicks, wapen vuur, explosies, shield hit
- Placeholder procedural audio nu, Audiocraft/Piper later

## H5: APK + Windows build
- Export Android APK
- Export Windows .exe
- Test beide via BlueStacks (APK) en direct (exe)
- Upload builds naar MinIO
- Registreer builds als assets

## H6: FINAL VERIFY
- Volledige playthrough: menu → tutorial → 3 missies → winkel → bounty → station wisseling → boss
- Alle 3 endings bereikbaar
- Save/load werkt
- Geen crashes
- git tag v0.3.0-alpha
- git push --tags
- Ntfy: "BLACK LEDGER v0.3.0 ALPHA COMPLEET"

---

# ================================================================
# SAMENVATTING VOOR PROMPT DIRECTOR
# ================================================================

| Prompt | Blocks | Focus | Afhankelijkheid |
|--------|--------|-------|-----------------|
| A | 11 | Gameplay + Bounty + Enemy AI + Ejection + Boarding + EMP | Geen |
| B | 11 | UI + Privateer briefings + Bounty Board + Boarding UI | A |
| C | 8 | Game modes + Endings + Audio + Save | A, B |
| D | 10 | Character creation + Cargo + 9 Ships + Upgrades + Generator | A |
| **I** | **11** | **Tractor Beam + Loot + Cargo + Trade + Commodities** | **D** |
| E | 7 | 28 Levels + Blockade + Level art | A, C |
| F | 7 | Sprites + Portraits + Cutscenes + Travel | B |
| G | 8 | Procedural missions + validator + galaxy map + stations | A, B, D, I, E |
| H | 6 | Integratie + Tutorial + Balance + Builds | Alles |

Totaal: ~77 blocks + Game Master Agent + Economy Agent + Asset Factory op N8n.
Volgorde: A → B → C → D → I → E → F → G → H
Aparte prompts: Asset Factory, Economy Agent (parallel te bouwen)

COMMIT CONVENTIE:
feat(X): block beschrijving
fix(X): bugfix beschrijving
test(X): test toegevoegd

RAPPORTEER na elke prompt naar Ntfy + Session Save webhook.

---

# ================================================================
# N8N AGENT: NOVA Game Master (bouw apart op Hetzner)
# ================================================================

## Doel
24/7 agent die Black Ledger bewaakt, begeleidt, corrigeert en repareert.
Draait als N8n workflow op Hetzner, onafhankelijk van Cursor.

## Webhook: POST /webhook/nova-game-master

## Wat hij doet:

### 1. BUILD MONITOR (elke 30 min via cron)
- SSH naar PC via Tailscale: `godot --headless --check-only "L:\1 Nova Cursor Output\Dark Ledger\project.godot"` *(Megalodon-canonical; optioneel ook referentie-project scannen)* 
- Parse resultaat: 0 errors = groen, >0 = rood
- Bij rood: automatisch Error Agent triggeren met error details
- Log resultaat in nova_debug_log tabel

### 2. MISSIE VALIDATOR (webhook trigger)
- Ontvangt gegenereerde missies van ProceduralMissionGenerator
- Checkt via Ollama: "Is deze missie logisch? Klopt de difficulty? Zijn objectives haalbaar?"
- Reject of approve
- Bij reject: stuurt reden terug + genereert alternatief via Ollama
- Houdt statistieken bij: acceptance rate, meest voorkomende problemen

### 3. BALANCE CHECKER (na elke playtest)
- Ontvangt gameplay data: welke missies gekozen, success rate, gemiddelde credits per uur, deaths per level
- Detecteert: 
  - Te makkelijk: success rate >95% bij difficulty >5 → verhoog enemy stats
  - Te moeilijk: success rate <20% bij difficulty <3 → verlaag enemy stats
  - Credits inflatie: speler >100k credits na 10 missies → verhoog prijzen
  - Credits tekort: speler <500 credits na 10 missies → verhoog beloningen
- Stuurt balance suggesties naar Postgres + Ntfy

### 4. ASSET INTEGRITY (dagelijks via cron)
- Scant `L:\1 Nova Cursor Output\Dark Ledger\Assets\` (en evt. `assets/` voor data/audio) via Tailscale — **niet** alleen oude `SpaceShooter\assets\sprites`
- Checkt: alle sprites bestaan, geen 0-byte bestanden, geen broken referenties
- Vergelijkt met **lokale** asset-manifest (git-tracked lijst / `IMPORT_REPORT.md`) — **geen** Postgres “Asset Registry” verplichting voor gekochte art.
- Bij mismatch: registreert ontbrekende assets of markeert kapotte
- Ntfy alert bij problemen

### 5. STORY CONTINUITY (bij elke story-gerelateerde commit)
- Leest StoryManager.gd, EndingManager.gd, DatacubeSystem.gd
- Checkt via Ollama: "Kloppen de 3 endings nog? Zijn alle datacubes bereikbaar? Contradiceert nieuwe code de bestaande lore?"
- Bij probleem: Ntfy + log in debug tabel

### 6. AUTO-REPAIR (trigger van Error Agent of Build Monitor)
- Bij bekende errors (shader, type inference, missing resource):
  - Zoekt in nova_debug_log naar eerdere fixes voor zelfde error type
  - Past meest succesvolle fix toe
  - Test opnieuw
  - Bij success: commit + Ntfy "auto-repaired: [error]"
  - Bij fail: escaleer naar Self-Monitor → Ntfy "manual fix needed"

### 7. NIGHTLY BUILD (cron: 03:00)
- Volledige parse check
- Runtime test 10 seconden
- Als beide slagen:
  - Android APK export
  - Windows exe export
  - Upload naar MinIO **alleen build-artefacten** (APK/exe); **geen** `res://Assets/**` of bron-PNG’s van gekochte packs (`.novaconfig`: redistribution forbidden)
  - Test APK via BlueStacks script
  - Ntfy: "Nightly build: PASS" of "Nightly build: FAIL — [reden]"
- Bij fail: NIET builden, alleen loggen

### 8. PROGRESS TRACKER
- Houdt bij welke Megalodon prompts/blocks af zijn
- Rapporteert dagelijks: "Prompt A: 11/11 ✅, Prompt B: 7/11 ⏳, Prompt C: 0/8 ⬜"
- Ntfy weekly summary elke zondag
- Schat resterende tijd op basis van gemiddelde block-duur

## Postgres tabellen voor Game Master:

```sql
CREATE TABLE IF NOT EXISTS nova_game_balance (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metric TEXT NOT NULL,
    value NUMERIC,
    suggestion TEXT
);

CREATE TABLE IF NOT EXISTS nova_mission_stats (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    mission_type TEXT,
    difficulty INT,
    generated INT DEFAULT 0,
    validated INT DEFAULT 0,
    rejected INT DEFAULT 0,
    rejection_reason TEXT
);

CREATE TABLE IF NOT EXISTS nova_build_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    build_type TEXT,
    parse_ok BOOLEAN,
    runtime_ok BOOLEAN,
    apk_ok BOOLEAN,
    exe_ok BOOLEAN,
    error_details TEXT
);

CREATE TABLE IF NOT EXISTS nova_progress (
    id SERIAL PRIMARY KEY,
    prompt CHAR(1) NOT NULL,
    block INT NOT NULL,
    status TEXT DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    notes TEXT,
    UNIQUE(prompt, block)
);
```

## Samenvatting Game Master functies:

| Functie | Trigger | Actie bij probleem |
|---------|---------|-------------------|
| Build Monitor | Cron 30 min | Error Agent → auto-repair |
| Missie Validator | Webhook | Reject + genereer alternatief |
| Balance Checker | Na playtest | Suggest stats aanpassing |
| Asset Integrity | Cron dagelijks | Alert + registreer |
| Story Continuity | Bij commit | Alert bij contradictie |
| Auto-Repair | Van Error Agent | Fix uit historie toepassen |
| Nightly Build | Cron 03:00 | Build + test + upload |
| Progress Tracker | Cron dagelijks | Weekly summary via Ntfy |
