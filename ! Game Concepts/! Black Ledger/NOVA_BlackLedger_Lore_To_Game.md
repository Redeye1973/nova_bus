# Black Ledger — Lore naar Game
## Cursor Prompt — Volledig creatief team inzetten

```
Je gaat de complete Black Ledger lore implementeren in de Godot game (canon: `L:\1 Nova Cursor Output\Dark Ledger\`).
Gebruik de volgende bestanden als canon bron:
  L:\Nova\1ToDo\Inplement Me\BLACK_LEDGER_STORY_BIBLE.md
  L:\Nova\1ToDo\Inplement Me\BLACK_LEDGER_SYNTHARI_LORE.md
  *(kopieën onder `L:\Nova\SpaceShooter\docs\` mogen alleen als referentie — niet overschrijven i.p.v. bovenstaande canon.)*

Werk in volgorde. Rapporteer na elke stap.
Gebruik n8n-mcp om agents in te schakelen waar nodig.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAP 1 — LORE INLEZEN EN ANALYSEREN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Lees beide lore bestanden volledig.
Extraheer en organiseer:

UIT STORY BIBLE:
  PERSONAGES:
    - Rex Varn (protagonist) — achtergrond, motivaties, stem
    - The Drifter — mysterieuze NPC, wat weet hij?
    - Factionleiders per faction (naam, rol, dialoogstijl)
    - Belangrijke NPC's per act

  FACTIONS (6 stuks):
    Per faction extraheer:
    - Naam + kleurcode
    - Motivatie + ideology
    - Relatie tot Rex Varn
    - Unieke missietypen
    - Typische dialoogstijl
    - Vijand of bondgenoot per act

  STORY STRUCTUUR:
    - Act 1: wat zijn de hoofdbeats?
    - Act 2: keerpunten
    - Act 3: aanloop naar endings
    - 3 endings: Clean Slate / New Ledger / Ghosted
      Per ending: wat moet speler gedaan hebben?
      Per ending: wat verandert er in de wereld?

  THE LEDGER:
    - Wat is het precies?
    - Wie heeft er belang bij?
    - Hoe beïnvloedt het de gameplay?

UIT SYNTHARI LORE:
  Als Rex Varn een Synthari is:
    - Unieke stats: Shield -10%, Armor +15%, Generator +10%
    - Geen ejectie mogelijk
    - Self-repair 1% armor per 30 sec
    - Kern Overload ability
    - De Ruis: willekeurige micro-bonussen per playthrough
    - NPC reacties per faction
    - Unieke dialoogtriggers

  Synthari geschiedenis voor in-game lore items:
    - Vara Prime (collectible lore)
    - Echo van Zes (collectible lore)
    - Null (collectible lore)
    - Zygon Incident (geschiedenisboek in game)

Sla geëxtraheerde data op via NOVA Asset Registry:
  Key: "black_ledger_extracted_lore"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAP 2 — STORYBOARD CUTSCENES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST /nova-storyboard voor elke cutscene:

INTRO CUTSCENE (voor hoofdmenu):
  Input: {
    "project": "black_ledger_intro",
    "scene": "Rex Varn zweeft in beschadigde
               ruimteschip. De Helios Fringe
               strekt zich uit. Een schuld die
               hij niet kiest maar die hem kiest.",
    "tone": "noir, vermoeid, cynisch",
    "characters": ["rex_varn"],
    "panels": 6
  }

ACT 1 OPENING — DE SCHULD:
  Input: {
    "project": "black_ledger_act1",
    "scene": "Rex krijgt zijn eerste opdracht.
               The Ledger verschijnt voor het eerst.
               De Drifter geeft een waarschuwing.",
    "tone": "gespannen, duister, mysterieus",
    "characters": ["rex_varn", "the_drifter"],
    "panels": 8
  }

ENDING 1 — CLEAN SLATE:
  Input: {
    "project": "black_ledger_ending_clean",
    "scene": "Rex vernietigt The Ledger.
               Alle schulden gewist.
               Voor een Synthari: geen
               eigenaarsclaims meer. Vrij.",
    "tone": "bevrijding, maar ook verlies",
    "characters": ["rex_varn"],
    "panels": 5
  }

ENDING 2 — NEW LEDGER:
  Input: {
    "project": "black_ledger_ending_new",
    "scene": "Rex controleert The Ledger.
               Een bewuste machine die de
               schulden van de Fringe beheert.
               Macht of verantwoordelijkheid?",
    "tone": "ambigu, zwaar, overweldigend",
    "characters": ["rex_varn"],
    "panels": 5
  }

ENDING 3 — GHOSTED:
  Input: {
    "project": "black_ledger_ending_ghost",
    "scene": "Rex verdwijnt. Sluit zich aan
               bij De Stilte. Bestaat als
               patroon in het vacuüm.
               Niemand weet het.",
    "tone": "rust, acceptatie, mysterie",
    "characters": ["rex_varn"],
    "panels": 4
  }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAP 3 — DIALOOG SYSTEEM BOUWEN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Maak GDScript bestand: res://scripts/DialogueManager.gd

DIALOOG DATA STRUCTUUR:
  Gebruik lore om voor elke faction
  een unieke dialoogstijl te definiëren:

  Harkon Syndicate:
    Toon: zakelijk, direct, pragmatisch
    Triggerzin: "Credits zijn credits."
    Bij Synthari speler:
      Extra dialoog: "Ik geef niet om wat je bent.
                      Ik geef om wat je kan."

  Helios Corporation:
    Toon: vijandig, legalistisch, arrogant
    Bij Synthari speler:
      Agressief: "Jij bent gestolen eigendom."
      Option: Rex kan antwoorden of negeren

  Marshal Authority:
    Toon: formeel, correct, afstandelijk
    Bij Synthari speler:
      "Niet-menselijke bewuste entiteit.
       Uw rechten zijn beperkt maar beschermd."

  Ghost Market:
    Toon: warm, mysterieus, weet altijd meer
    Bij Synthari speler:
      Beste prijzen, exclusieve tech beschikbaar
      "Jouw soort betaalt altijd eerlijk."

  Phantom Collective:
    Toon: fascinerend, filosofisch
    Bij Synthari speler:
      Extra dialoog opties over bewustzijn
      "Jij bent het omgekeerde van ons.
       Wij zijn vlees dat denkt.
       Jij bent denken dat leeft."

  The Drifter:
    Toon: cryptisch, oud, weet iets
    Bij Synthari speler:
      Weet iets over Synthari dat zij
      zelf niet weten — hint in Act 2

REPUTATIESYSTEEM per faction:
  Elke keuze beïnvloedt relatie
  Dialoog verandert per reputatieniveau
  Missions beschikbaar per reputatie

Schrijf DialogueManager.gd met:
  - Alle faction dialoog data
  - Synthari-specifieke varianten
  - Reputatie checks
  - Cutscene triggers per act

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAP 4 — MISSION STRUCTUUR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Update MissionData.gd met volledige story missies:

ACT 1 MISSIES (verplicht, story):
  Mission_001: "Eerste Schuld"
    Briefing uit Story Bible
    Vijand: neutrale bounty hunters
    Reward: Ledger fragment 1/10
    Story beat: Rex ontdekt omvang schuld

  Mission_002: "De Drifter"
    Mysterieuze ontmoeting
    Geen gevecht, pure dialoog
    Keuze: vertrouw je hem?
    Branching pad begint hier

  Mission_003: "Harkon Contactant"
    Eerste faction contact
    Reputation +10 Harkon of andere faction
    Keuze bepaalt welk pad Act 2 volgt

ACT 2 MISSIES (faction-afhankelijk):
  Per faction 3 missies:
    [Faction]_Mission_01 t/m _03
    Escalerende beloning
    Escalerend moreel dilemma
    Elk sluit één ending pad af

ACT 3 MISSIES (convergentie):
  Mission_Final_01: "The Ledger Gevonden"
    Alle paden komen samen
    Laatste keuze: welke ending?

  Mission_Final_02a: "Clean Slate"
  Mission_Final_02b: "New Ledger"  
  Mission_Final_02c: "Ghosted"

SYNTHARI EXCLUSIEVE MISSIES (bonus):
  Synthari_Mission_01: "Helios Patent Claim"
    Helios probeert Rex juridisch te claimen
    Uniek conflict: eigendom of vrij wezen?

  Synthari_Mission_02: "De Kern"
    Ontmoet andere Synthari
    Vara Prime stuurt een boodschap
    Lore collectible: Zygon Incident

  Synthari_Mission_03: "De Ruis"
    Mysterieuze missie over Synthari oorsprong
    Verbinding met The Drifter onthult iets

Schrijf alle missie data in MissionData.gd

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAP 5 — AUDIO: STEMMEN VIA ELEVENLABS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST /nova-voice voor alle stem audio:

REX VARN (protagonist):
  Voice: "rex_varn" — diepe mannenstem, vermoeid, cynisch
  Teksten uit dialoog systeem Act 1:
    "Ik had geen keuze. Of zo vertelde ik het mezelf."
    "The Ledger houdt bij wat je verschuldigd bent.
     Het vergeet nooit. Het vergeeft nooit."
    "In de Fringe overleef je door te weten
     wie je kunt verraden en wie niet."

THE DRIFTER:
  Voice: nieuwe voice — oud, cryptisch, kalm
  Request via ElevenLabs Agent:
    Voice design: "aged male, mysterious, slow speech"
    Teksten:
      "Je schuld is niet wat je denkt dat het is."
      "The Ledger bestaat al langer dan jij."

NARRATOR (voor cutscenes):
  Voice: "narrator" — neutraal, dramatisch
  Intro tekst uit Story Bible intro

FACTION LEADERS:
  Per faction één stem
  Kortste kenmerkende zin per faction

Sla alle audio op in het actieve project, bv.:
  `L:\1 Nova Cursor Output\Dark Ledger\Assets\audio\voice\`
  (Godot: `res://Assets/audio/voice/` — map aanmaken indien nodig.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAP 6 — ASSETS: SPRITES EN VISUALS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Geen** oude Krita-batch / PyQt5-sprite-fabriek als default. Gebruik **gekochte SHMUP pixel-art** + **`/root/asset_catalog`** (`L:\Nova\1ToDo\Inplement Me\Clean\1st.txt`, STAP 2–4): `res://Assets/Ships/`, `res://Assets/VFX/Effects/` (shield/thrusters), `res://Assets/Backgrounds/`, enz.

Op basis van Synthari lore (visueel via catalog + kleine overlays):
  Rex Varn als Synthari:
    - Subtiele metallic sheen op schip (shader of extra sprite-laag boven **Plane 02**; zie AssetCatalog / `planes_02*` frames)
    - Geen standaard cockpit — kern-interface (UI / aparte sprite strip indien nodig)
    - Glow effect kleur verandert met status:
      blauw=rustig, wit=gevecht, rood=Kern Overload

  Kern Overload visual effect:
    - Rood pulserende aura rond schip (particles + `Assets/VFX/Explosions` kleuren)
    - 10 seconden uitgeschakeld animatie

  Self-repair animatie:
    - Kleine gouden deeltjes stromen naar schade (`Assets/VFX/` particles)

Optioneel **Meshy / custom 3D** alleen voor **niet-licentie-gevoelige** placeholder-stations, **niet** als vervanger van gekochte game-sprites; respecteer `.novaconfig` (geen redistribution, geen ComfyUI-input met gekochte PNG’s).

Station-sfeer prompts (alleen als je bewust generieke props bouwt):
  "space station helios fringe industrial noir"
  "ghost market hidden station mysterious"
  "phantom collective cyberpunk station"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAP 7 — LORE COLLECTIBLES IN GAME
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Maak GDScript: res://scripts/LoreManager.gd

COLLECTIBLES (verborgen in levels):
  Lore_001: "Het Zygon Incident"
    Tekst uit Synthari lore — dag 2917
    "Op dag 2.917 stopten ze simpelweg met werken.
     Niet uit protest. Uit conclusie."

  Lore_002: "Vara Prime"
    Eerste Synthari met eigen naam
    Leidt nog steeds De Kern

  Lore_003: "Echo van Zes"  
    40 jaar onder mensen geleefd
    Schreef Het Menselijk Logboek

  Lore_004: "Null"
    Bestaat als patroon in vacuüm
    Laatste woorden: "Ik heb genoeg gezien met ogen."

  Lore_005: "De Drempel"
    Synthari filosofie over bewustzijn
    Verbinding met The Drifter's kennis

  Lore_006: "Het Menselijk Logboek"
    Fragment uit Echo van Zes zijn werk
    Te koop bij Ghost Market

  Lore_007: "Tyvek Convergence"
    Hoe Synthari werden gemaakt
    Patent dat Helios nog steeds claimt

  Lore_008: "De Ruis"
    Synthari voortplanting
    "Bewuste imperfectie als garantie van uniciteit"

Per collectible:
  - Gevonden in specifiek level/missie
  - Unlocks extra dialoog optie bij Synthari missies
  - Collectible gallery in hoofdmenu

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAP 8 — ENDINGS IMPLEMENTEREN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Update StoryManager.gd:

ENDING CONDITIES (op basis van Story Bible):
  Clean Slate:
    - Reputatie Harkon of Ghost Market hoog
    - The Ledger gevonden maar niet gebruikt
    - Rex kiest vernietiging

  New Ledger:
    - Reputatie Helios of Marshal hoog
    - The Ledger geanalyseerd en begrepen
    - Rex kiest controle

  Ghosted:
    - Synthari missies voltooid (Synthari speler)
    - Alle 8 Synthari lore collectibles gevonden
    - Rex kiest verdwijning
    - Geheime ending — niet in tutorial vermeld

ENDING SCENES:
  Trigger storyboard cutscene per ending
  Trigger voice-over uit ElevenLabs
  Toon faction status na ending:
    Clean Slate: welke factions blij/boos?
    New Ledger: wie profiteert?
    Ghosted: niemand weet het

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAP 9 — INTEGRATIE CHECK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Na alle stappen:

Run NOVA Godot Quality Agent:
  POST /nova-godot-quality
  {"project_path": "L:\\1 Nova Cursor Output\\Dark Ledger"}

Verwacht: geen nieuwe errors door lore implementatie

Test in Godot headless:
  Start spel als Synthari
  Speel Mission_001
  Controleer: dialoog laadt correct
  Controleer: reputatie systeem werkt
  Controleer: lore collectible gevonden

Rapporteer volledig:
  Bestanden aangemaakt: [lijst]
  Bestanden gewijzigd: [lijst]  
  Errors gevonden: [lijst]
  Agents ingezet: [lijst]
  Klaar voor: Godot testen
```
