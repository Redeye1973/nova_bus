# NOVA v2 Pipeline Build — Complete Sequentiele Opzet

Dit package bouwt de NOVA v2 agents pipeline in volgorde, zonder Black Ledger game code. Dat komt later als apart package.

## Filosofie

- Elke stap = één losse prompt voor Cursor
- Tussen stappen: jij test, debugt, commit
- Failure in stap X blokkeert rest niet (fallback modes overal)
- Max 2 retries per agent, dan verder gaan
- Status tracking per stap
- Rollback mogelijkheden

## Package structuur

```
nova_v2_pipeline_build/
├── README.md (dit)
├── 00_master/
│   ├── MASTER_PLAN.md (totaaloverzicht)
│   ├── PROMPT_INDEX.md (alle prompt nummers + wat ze doen)
│   ├── START_HERE.md (eerste actie voor jou)
│   └── TESTING_CHECKLIST.md (hoe elke fase testen)
├── 01_fase1_foundation/
│   ├── README.md (fase overzicht)
│   ├── prompt_01_agent_20_design_fase.md
│   ├── prompt_02_agent_02_code_jury.md
│   ├── prompt_03_agent_10_game_balance_jury.md
│   ├── prompt_04_agent_21_freecad_parametric.md
│   ├── prompt_05_agent_22_blender_game_renderer.md
│   ├── prompt_06_agent_23_aseprite_processor.md
│   ├── prompt_07_agent_25_pyqt_assembly.md
│   ├── prompt_08_agent_26_godot_import.md
│   ├── prompt_09_agent_11_monitor.md
│   ├── prompt_10_agent_17_error.md
│   └── FASE1_VALIDATIE.md
├── 02_fase2_story/
│   ├── README.md
│   ├── prompt_11_agent_07_narrative_jury.md
│   ├── prompt_12_agent_28_story_text_integration.md
│   ├── prompt_13_agent_13_pdok_downloader.md
│   ├── prompt_14_agent_15_qgis_processor.md
│   ├── prompt_15_agent_14_blender_baker.md
│   ├── prompt_16_agent_05_gis_jury.md
│   └── FASE2_VALIDATIE.md
├── 03_fase3_polish/
│   ├── README.md
│   ├── prompt_17_agent_24_aseprite_animation.md
│   ├── prompt_18_agent_29_elevenlabs_audio.md
│   ├── prompt_19_agent_03_audio_jury.md
│   ├── prompt_20_agent_30_audio_asset_jury.md
│   ├── prompt_21_agent_18_prompt_director.md
│   ├── prompt_22_agent_16_cost_guard.md
│   ├── prompt_23_agent_27_storyboard_visual.md
│   ├── prompt_24_agent_08_character_art.md
│   └── FASE3_VALIDATIE.md
├── 04_fase4_advanced/
│   ├── README.md
│   ├── prompt_25_agent_31_qgis_analysis.md
│   ├── prompt_26_agent_32_grass_gis.md
│   ├── prompt_27_agent_35_raster_2d_processor.md
│   ├── prompt_28_agent_09_2d_illustration.md
│   ├── prompt_29_agent_12_bake_orchestrator.md
│   ├── prompt_30_agent_04_3d_model_jury.md
│   ├── prompt_31_agent_06_cad_jury.md
│   ├── prompt_32_agent_19_distribution.md
│   └── FASE4_VALIDATIE.md
├── 05_integration/
│   ├── README.md
│   ├── prompt_33_end_to_end_sprite_pipeline.md
│   ├── prompt_34_end_to_end_gis_pipeline.md
│   ├── prompt_35_end_to_end_story_pipeline.md
│   ├── prompt_36_cross_agent_integration.md
│   └── INTEGRATION_TESTS.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── AGENT_DEPENDENCIES.md
│   ├── DEBUGGING_GUIDE.md
│   ├── FALLBACK_PROCEDURES.md
│   └── TAILSCALE_SETUP.md
└── utils/
    ├── status_check.ps1
    ├── agent_validator.py
    ├── reset_failed_agent.ps1
    └── full_backup.ps1
```

## Hoe te gebruiken

### Eerste keer

1. Unzip in L:\!Nova V2\pipeline_build\
2. Open 00_master/START_HERE.md
3. Volg instructies

### Per prompt

1. Open prompt_XX bestand
2. Lees de prompt door
3. Kopieer in Cursor Composer
4. Laat Cursor uitvoeren
5. Valideer resultaat met TESTING_CHECKLIST
6. Als OK: commit en volgende prompt
7. Als fail: zie DEBUGGING_GUIDE

### Debugging tussen stappen

Na elke prompt kun jij:
- Code inspecteren
- Tests handmatig runnen
- Issues fixen voordat door te gaan
- Rollback indien nodig

## Tijd inschatting per fase

- **Fase 1**: 10 prompts, 2-3 uur per prompt = 20-30 uur
- **Fase 2**: 6 prompts, 2-3 uur per prompt = 12-18 uur
- **Fase 3**: 8 prompts, 2-3 uur per prompt = 16-24 uur
- **Fase 4**: 8 prompts, 2-3 uur per prompt = 16-24 uur
- **Integration**: 4 prompts, 3-4 uur per prompt = 12-16 uur

**Totaal: 76-112 uur autonoom werk door Cursor + testing tijd.**

Met 24/7 PC draaien = 2-3 weken doorlopend mogelijk.

## Voortgang tracking

Cursor schrijft status naar:
- ./status/agent_XX_status.json (per agent)
- ./logs/pipeline_build_YYYY-MM-DD.log (per sessie)
- ./docs/v2_deployment_report.md (lopend rapport)

Jij kunt altijd checken:
```powershell
Get-Content "L:\!Nova V2\status\agent_XX_status.json" | ConvertFrom-Json
```

## Na dit package

Als alle 32 agents plus 4 integration tests klaar zijn, krijg je:
- Complete NOVA v2 pipeline operationeel
- Alle agents gedocumenteerd
- Rapport voor handoff

Dan volgt **Black Ledger MVP package** die op deze pipeline draait.

## Voorwaarden

Voordat je start:
- ✓ V2 infrastructure draait op Hetzner
- ✓ Agent 01 Sprite Jury live (uit eerder werk)
- ✓ Secrets in L:\!Nova V2\secrets\
- ✓ SSH key access naar Hetzner
- ✓ V1 API key werkt
- ✓ V2 API key werkt
- ✓ Cursor kan PowerShell commando's uitvoeren

Als iets ontbreekt: zie 00_master/START_HERE.md voor setup.
