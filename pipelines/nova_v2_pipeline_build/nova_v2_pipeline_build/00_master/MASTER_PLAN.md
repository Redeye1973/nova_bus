# NOVA v2 Pipeline Build - Master Plan

## Doel

Bouw 32 NOVA v2 agents plus 4 integration tests in sequentiele prompts die Cursor autonoom kan uitvoeren. Jij test en debugt tussen prompts.

## Waarom sequentieel

- Elke prompt bouwt 1 agent (of 1 test)
- Failure in prompt X blokkeert rest niet
- Jij hebt controle: kunt pauzeren, debuggen, rollback
- Cursor hoeft geen enorme context vast te houden
- Resultaten meetbaar per prompt

## Wat elke prompt doet

Een agent bouwen volgt consistent patroon:

1. **Spec lezen**: Load agent spec uit agents/ of extensions/
2. **V1 delegation check**: Try V1 orchestrator capability
3. **Code genereren**: FastAPI service met Python 3.11
4. **Tests maken**: Unit tests met pytest
5. **Docker setup**: Dockerfile + compose service
6. **Hetzner deploy**: Via SSH upload + docker compose up
7. **N8n workflow**: Import + activeer via API
8. **Integration test**: Webhook call, verify response
9. **Status update**: Schrijf status file
10. **Log**: Append naar pipeline log

Elke prompt bevat al deze stappen expliciet.

## Prompt nummering

Sequentieel 01-36:

**Fase 1 Foundation (10 prompts):**
- 01: Agent 20 Design Fase
- 02: Agent 02 Code Jury
- 03: Agent 10 Game Balance Jury
- 04: Agent 21 FreeCAD Parametric
- 05: Agent 22 Blender Game Renderer
- 06: Agent 23 Aseprite Processor
- 07: Agent 25 PyQt5 Assembly
- 08: Agent 26 Godot Import
- 09: Agent 11 Monitor Agent
- 10: Agent 17 Error Agent

**Fase 2 Story+GIS (6 prompts):**
- 11: Agent 07 Narrative Jury
- 12: Agent 28 Story Text Integration
- 13: Agent 13 PDOK Downloader
- 14: Agent 15 QGIS Processor
- 15: Agent 14 Blender Baker
- 16: Agent 05 GIS Jury

**Fase 3 Polish+Audio (8 prompts):**
- 17: Agent 24 Aseprite Animation Jury
- 18: Agent 29 ElevenLabs Audio
- 19: Agent 03 Audio Jury
- 20: Agent 30 Audio Asset Jury
- 21: Agent 18 Prompt Director
- 22: Agent 16 Cost Guard
- 23: Agent 27 Storyboard Visual
- 24: Agent 08 Character Art Jury

**Fase 4 Advanced (8 prompts):**
- 25: Agent 31 QGIS Analysis
- 26: Agent 32 GRASS GIS
- 27: Agent 35 Raster 2D Processor (Krita/GIMP/Inkscape)
- 28: Agent 09 2D Illustration Jury
- 29: Agent 12 Bake Orchestrator
- 30: Agent 04 3D Model Jury
- 31: Agent 06 CAD Jury
- 32: Agent 19 Distribution Agent

**Fase 5 Integration (4 prompts):**
- 33: End-to-end sprite pipeline test
- 34: End-to-end GIS pipeline test
- 35: End-to-end story pipeline test
- 36: Cross-agent integration test

## Niet in deze build

Deze agents **NIET** in scope:
- Agent 33 Blender Architecture Walkthrough (voor FINN/archviz, niet games)
- Agent 34 Unreal Engine Import (jij gebruikt Godot)

Als je later archviz product wilt, kunnen die apart.

## Agent 01 status

Agent 01 Sprite Jury is al live (POC versie, deterministisch). In Fase 5 integration tests wordt getest of hij goed integreert. Eventuele upgrade naar Ollama-powered versie = aparte sessie later.

## Volgorde rationale

Zie `AGENT_DEPENDENCIES.md` voor detail. Samengevat:

- Design Fase (20) eerst: alle andere agents gebruiken palette/style
- Code Jury (02): valideert alle volgende GDScript output
- Game Balance (10): numeriek eenvoudig, goed voor Code Jury test
- FreeCAD (21) → Blender (22) → Aseprite (23) → PyQt5 (25) → Godot (26): shmup pipeline keten
- Monitor (11) + Error (17): vangt problemen in volgende builds

## Success criteria

**Minimum viable (70% success)**: 22/32 agents live, alle fases 1 tests slagen
**Comfortable (85% success)**: 27/32 agents live, 3/4 integration tests slagen  
**Excellent (95%+ success)**: 30+/32 agents, alle integration tests groen

## Parallelisatie

**Binnen een fase**: Cursor kan niet parallel (single context).

**Over fases**: Na Fase 1 compleet, kan Fase 2 parallel met nog outstanding Fase 1 retry's.

**Aanbevolen aanpak**: sequentieel blijven, maar dat is OK want 24/7 PC draait gewoon door.

## Recovery strategieen

**Per-prompt failure**:
- Max 2 retries zelfde aanpak (NOVA regel)
- Dan alternative: V1 delegation OF Cursor solo OF skip naar volgende
- Markeer in status: "failed, retry_later"

**Phase failure**:
- Als > 50% van fase agents falen: stop, escaleer naar jou
- Herziening nodig voor verder gaan

**Complete build failure**:
- Rollback via `utils/reset_failed_agent.ps1`
- Hetzner database restore uit backup
- Begin opnieuw met lessons learned

## After pipeline complete

Zodra 32 agents + 4 tests klaar zijn:
1. Volledig deployment rapport
2. Backup maken van complete staat
3. Black Ledger package start mogelijk
4. Optioneel: upgrade agent 01 POC naar Ollama-powered versie
