# NOVA v2 Agent Catalogus

Complete catalogus van agents voor NOVA v2 platform met Cursor-prompts en N8n workflow templates.

## Architectuur

Twee typen agents:

**Jury-Judge Agents** — Evaluatie agents die output beoordelen per domein. Elk domein heeft een jury (meerdere specialisten) en een judge (eindverdict).

**Operationele Agents** — Agents die werk uitvoeren in de pipeline. Monitor, bake, debug, orchestratie.

## Structuur

```
nova_v2_agents/
├── README.md (dit bestand)
├── 00_architectuur.md (overall ontwerp)
├── jury_judge/
│   ├── 01_sprite_jury.md
│   ├── 02_code_jury.md
│   ├── 03_audio_jury.md
│   ├── 04_3d_model_jury.md
│   ├── 05_gis_jury.md
│   ├── 06_cad_jury.md
│   ├── 07_narrative_jury.md
│   ├── 08_character_art_jury.md
│   ├── 09_2d_illustration_jury.md
│   └── 10_game_balance_jury.md
├── operational/
│   ├── 11_monitor_agent.md
│   ├── 12_bake_orchestrator.md
│   ├── 13_pdok_downloader.md
│   ├── 14_blender_baker.md
│   ├── 15_qgis_processor.md
│   ├── 16_cost_guard.md
│   ├── 17_error_agent.md
│   ├── 18_prompt_director.md
│   └── 19_distribution_agent.md
├── templates/
│   ├── jury_judge_subworkflow.json (N8n)
│   ├── bake_workflow.json (N8n)
│   └── monitor_workflow.json (N8n)
└── stappenplan/
    ├── implementatie_volgorde.md
    └── cursor_werkwijze.md
```

## Implementatie volgorde

Volg deze volgorde voor bouwen (conform memory #17):

1. **Sprite jury** (volume + meetbaar, perfecte start)
2. **Code jury** (uitbreiding UE5 debugger)
3. **Audio jury**
4. **3D model jury**
5. **GIS jury**
6. **CAD jury**
7. **Narrative jury** (laatste want meest subjectief)

Operationele agents parallel bouwen waar nodig.

## Gebruik

Per agent is er een markdown bestand met:
- Doel en scope
- Jury leden (voor jury-judge agents)
- Input/output specificatie
- N8n workflow structuur
- Cursor prompt om te laten bouwen
- Test scenario's

Open elk bestand in Cursor, copy-paste de prompt, laat Cursor bouwen.
