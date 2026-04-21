# Agent Bouwvolgorde — Strategische Redenering

De volgorde van 35 agents is niet willekeurig. Elk besluit:

## Groep 1: Foundational Juries (01-10)

**Waarom eerst:** Jury-judge patroon is kern van NOVA v2. Eerst bewijzen dat werkt, dan uitbreiden.

01. **Sprite Jury** - Meest meetbaar, 432 bestaande sprites om tegen te valideren, MVP bewijs
02. **Code Jury** - Nodig om volgende agents zelf te kunnen valideren, wordt self-reviewing
03. **Audio Jury** - Technisch check, relatief eenvoudig
04. **3D Model Jury** - Voor Blender output later nodig
05. **GIS Jury** - Voor bake pipeline cruciaal
06. **CAD Jury** - Voor FreeCAD output, paradoxaal simpel
07. **Narrative Jury** - Meest subjectief, doe later in groep maar binnen jury fase
08. **Character Art Jury** - Voor storyboard pipeline
09. **2D Illustration Jury** - Voor UI en illustratie werk
10. **Game Balance Jury** - Numeriek, goede fit voor Code Jury test

## Groep 2: Operationele Core (11-19)

**Waarom nu:** Backbone voor alles daarna. Zonder monitoring en orchestratie breekt grote bouw.

11. **Monitor Agent** - Must have voordat grote workloads draaien
12. **Bake Orchestrator** - Binding voor city pipeline (FINN, NORA)
13. **PDOK Downloader** - Pure data, eenvoudig, kan van V1 kopieren
14. **Blender Baker** - Bestaand code kan basis zijn
15. **QGIS Processor** - Bestaand, upgrade naar v2 structuur
16. **Cost Guard** - Voordat dure API agents (ElevenLabs etc)
17. **Error Agent** - Catch-all voor andere bouw fouten
18. **Prompt Director** - Coordinates complexe prompts
19. **Distribution Agent** - End of pipeline, voor productie deliverables

## Groep 3: Game Asset Production (20-26)

**Waarom na core:** Shmup pipeline is product-specifiek, heeft foundation nodig.

20. **Design Fase Agent** - Style bible, palette management
21. **FreeCAD Parametric** - Base models voor shmup
22. **Blender Game Renderer** - 16-angle rendering
23. **Aseprite Processor** - Pixel polish
24. **Aseprite Animation Jury** - Specifiek voor animations
25. **PyQt5 Assembly** - Sprite sheet builder
26. **Godot Import** - Game engine integratie

## Groep 4: Story Production (27-28)

**Waarom als laatste voor audio:** Subjectief domein, Narrative Jury (07) moet bewezen werken eerst.

27. **Storyboard Visual Agent** - Surilians panel generation
28. **Story Text Integration** - Canon tracking, Surilians bible

## Groep 5: Audio (29-30)

**Waarom nu:** ElevenLabs API vraagt cost tracking (16 moet working) en quality validation (30 paired met 03).

29. **ElevenLabs Audio Agent** - Voice + SFX
30. **Audio Asset Jury** - Game audio integration

## Groep 6: GIS Advanced (31-32)

**Waarom nu:** Complement aan GIS Jury (05) en QGIS Processor (15).

31. **QGIS Analysis** - Advanced cartografie
32. **GRASS GIS Analysis** - Hydrology, viewshed

## Groep 7: Architecture Visualisation (33-34)

**Waarom laatst:** Meest complexe integratie, vraagt veel bestaande agents.

33. **Blender Architecture Walkthrough** - Archviz pipeline
34. **Unreal Engine Import** - UE5 integratie

## Groep 8: 2D Raster Utility (35)

**Waarom aller-laatst:** Utility support voor andere agents, niet kritiek pad.

35. **Raster 2D Processor** (GIMP/Krita/Inkscape)

## Parallelisatie opportunities

Binnen elke groep kunnen V1 agents parallel werken aan meerdere:

**Parallel veilig:**
- Groep 1 agents 01-10 kunnen grotendeels parallel (verschillende domeinen)
- Groep 2 operationele agents deels parallel
- Groep 4 story agents parallel

**Sequentieel nodig:**
- Groep 2 agent 11 (Monitor) voor rest van Groep 2 (monitor moet eerst live zijn)
- Groep 3 agents opeenvolgend (depend op elkaar)

**Strategische volgorde voor maximale efficientie:**

Dag 1 (parallel):
- 01 Sprite Jury + 02 Code Jury tegelijk
- 03 Audio + 04 3D Model parallel
- 05 GIS + 06 CAD parallel

Dag 1 (sequentieel):
- 07 Narrative (vraagt feedback van eerdere juries)

Dag 2:
- 08, 09, 10 parallel
- Monitor agent (11) eerst, dan 12-19 parallel

Dag 3:
- Groep 3: 20-26 meer sequentieel
- Groep 4-8 parallel waar mogelijk

## Kritieke dependencies

**Agent A afhankelijk van Agent B (B eerst):**

| Agent | Afhankelijk van |
|-------|------------------|
| 11 Monitor | (none, foundational) |
| 12 Bake Orch | 11, 13-15 |
| 17 Error | 11 (monitoring context) |
| 20 Design | (none, foundational) |
| 22 Blender Render | 21 FreeCAD (voor STEP files) |
| 23 Aseprite Proc | 22 (Blender renders als input) |
| 24 Aseprite Anim Jury | 23 |
| 25 PyQt Assembly | 23, 24 (polished sprites) |
| 26 Godot Import | 25 (assembled assets) |
| 27 Storyboard | 08 Character Art, 09 2D Illust |
| 28 Story Text | 07 Narrative Jury |
| 30 Audio Asset Jury | 03 Audio Jury, 29 ElevenLabs |
| 33 Blender Arch | 22 Blender Render, 04 3D Model Jury |
| 34 Unreal Import | 33 Blender Arch |

V1 respecteert deze dependencies in bouwschedule.

## Geschatte tijd per agent

Bij optimale V1 performance:

- Simpele jury agents (01-09): 15-30 min per
- Complexe jury (07 Narrative): 45-60 min
- Operationele agents (11-19): 30-60 min
- Complexe services (14 Blender Baker, 33 Blender Arch): 60-90 min
- Eenvoudige utility (13 PDOK, 35 Raster): 20-30 min
- Integration heavy (34 Unreal): 60-120 min

**Totaal geschat:**
- Parallel execution ideaal: 12-16 uur
- Sequentieel met V1 overload: 20-30 uur
- Met fallback naar Cursor solo: 30-50 uur

## Quality gates tussen groepen

Voor overstap naar volgende groep, valideer huidige:

**Na Groep 1 (juries):**
- Run test: stuur dummy artifact door elke jury
- Verify: verdicts komen terug
- Verify: pipeline patterns werken

**Na Groep 2 (operationeel):**
- Run test: Monitor agent detecteert juries
- Run test: Cost Guard tracked API calls
- Run test: Error Agent vangt simulated error

**Na Groep 3 (game assets):**
- End-to-end test: dummy ship → FreeCAD → Blender → Aseprite → Godot
- Verify: complete asset pipeline functioneel

**Na Groep 7 (archviz):**
- End-to-end test: demo archviz workflow
- Verify: Unreal import werkt

**Na alle:**
- Complete integration test
- Performance benchmark
- Backup + disaster recovery test

## Skip strategy

Als een agent faalt na 2 pogingen:
- Mark as "failed_skipped"
- Continue met volgende
- Failed agents krijgen retry fase aan einde (Fase D?)

Dit voorkomt dat één vastzittende agent hele bouw blokkeert.

## Success metrics

Totale build is succesvol als:
- 30+ van 35 agents actief (85%+)
- Groep 1 (juries) 100% actief
- Groep 2 (operationeel) 80%+ actief
- End-to-end test slaagt voor minstens 1 pipeline
- V1 onaangetast

Daaronder: partial success, plan remediation.
