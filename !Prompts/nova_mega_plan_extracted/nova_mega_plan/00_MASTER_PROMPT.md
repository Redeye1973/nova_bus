# Master Prompt voor Cursor - NOVA v2 Mega Build

Dit is de hoofdprompt. Plak in Cursor Composer. Hij bevat alle instructies voor een meerdaagse autonome build.

## De prompt

```
Ik ga NOVA v2 volledig opbouwen (35 agents) door NOVA v1 (68 bestaande agents + 
orchestrator) als uitvoerend werksysteem te gebruiken. Werk meerdere uren 
autonoom met minimale check-ins bij mij.

CONTEXT:
- NOVA v1 draait: http://178.104.207.194:5678 (68 agents + orchestrator, productie)
- NOVA v2 infrastructure draait: http://178.104.207.194:5679 (leeg, wacht op agents)
- V1 API key: lees uit L:\!Nova V2\secrets\ (of vraag aan mij)
- V2 API key: lees uit L:\!Nova V2\secrets\ (na eerste V2 login)
- Werkmap: L:\!Nova V2\

BESCHIKBARE ZIP FILES in werkmap:
- nova_v2_agents.zip (basis 19 agents met Cursor prompts)
- nova_v2_extensions.zip (agents 20-35 met Cursor prompts)  
- nova_v2_infrastructure.zip (Docker stack - al gedeployed)
- shmup_pipeline.zip (Raptor-style asset pipeline)
- nova_v2_infrastructure_final.zip (complete infrastructure incl. prompts)

VEILIGHEID:
- V1 wordt GEBRUIKT, niet gewijzigd
- V1 op poort 5678 blijft productie
- V2 op poort 5679 is waar alles gebouwd wordt
- Bij v1 failure: pauzeer, escaleer naar mij
- Backup .env van zowel v1 als v2 voordat je begint

=== FASE A: VOORBEREIDING (30 min max, Cursor autonoom) ===

A.1 Pak alle 5 zips uit:
- nova_v2_agents.zip → ./agents/
- nova_v2_extensions.zip → ./extensions/
- nova_v2_infrastructure.zip → ./infrastructure/ (als nog niet bestaat)
- shmup_pipeline.zip → ./shmup/
- nova_v2_infrastructure_final.zip → skip (dubbele van infrastructure)

A.2 Verifieer bestanden bestaan:
- ./agents/nova_v2_agents/ (met jury_judge/, operational/, templates/)
- ./extensions/nova_v2_extensions/ (met design/, freecad/, etc)
- ./infrastructure/docker-compose.yml

A.3 Test V1 API toegang:
curl -H "X-N8N-API-KEY: <key>" http://178.104.207.194:5678/api/v1/workflows

Als werkt: noteer aantal workflows (moet 68 zijn of vergelijkbaar)
Als faalt: vraag aan mij waar V1 API key staat

A.4 Test V2 API toegang:
curl -H "X-N8N-API-KEY: <key>" http://178.104.207.194:5679/api/v1/workflows

Als werkt: noteer aantal (zou 0 of laag moeten zijn, alleen templates)
Als faalt: V2 admin account moet eerst via browser, escaleer naar mij

A.5 Maak orchestrator briefing folder:
- L:\!Nova V2\briefings\
- L:\!Nova V2\status\ (voor voortgang tracking)

=== FASE B: V1 ORCHESTRATOR BRIEFEN (20 min) ===

B.1 Bouw master briefing voor V1 orchestrator:
Document: ./briefings/master_build_brief.md

Inhoud:
- Doel: bouw 35 v2 agents
- Bron: specs in L:\!Nova V2\agents\ en L:\!Nova V2\extensions\
- Target: V2 N8n op :5679 + Docker services op Hetzner
- Volgorde: zie agent_volgorde lijst (hieronder)
- Rapportage: schrijf status naar ./status/agent_<NN>_status.json per agent

B.2 Post master brief naar V1 orchestrator:
Via V1 API, maak workflow "nova_v2_build_orchestrator" aan of gebruik 
bestaande orchestrator. Stuur master_build_brief.md als input.

Als V1 heeft geen orchestrator in dat formaat:
Gebruik alternative approach - maak webhook trigger workflow die Cursor 
aanroept met agent build tasks.

B.3 Valideer V1 heeft nodige capabilities:
- Code generation agent? (vraag V1 via orchestrator)
- Python FastAPI scaffold agent? 
- Docker deploy agent?
- File transfer naar V2?

Als niet alle capabilities: schakel over naar hybride mode - Cursor doet 
code generatie, V1 doet testen/deploy.

=== FASE C: AGENT BOUW LOOP (8-16 uur, grootste blok) ===

Voor elke agent in onderstaande volgorde, herhaal C.1-C.8:

AGENT VOLGORDE:
C1.  01_sprite_jury (eerst, bewijst concept)
C2.  02_code_jury
C3.  03_audio_jury
C4.  04_3d_model_jury
C5.  05_gis_jury
C6.  06_cad_jury
C7.  07_narrative_jury
C8.  08_character_art_jury
C9.  09_2d_illustration_jury
C10. 10_game_balance_jury
C11. 11_monitor_agent
C12. 12_bake_orchestrator
C13. 13_pdok_downloader
C14. 14_blender_baker
C15. 15_qgis_processor
C16. 16_cost_guard
C17. 17_error_agent
C18. 18_prompt_director
C19. 19_distribution_agent
C20. 20_design_fase_agent
C21. 21_freecad_parametric_agent
C22. 22_blender_game_renderer_agent
C23. 23_aseprite_processor_agent
C24. 24_aseprite_animation_jury
C25. 25_pyqt_assembly_agent
C26. 26_godot_import_agent
C27. 27_storyboard_visual_agent
C28. 28_story_text_integration_agent
C29. 29_elevenlabs_audio_agent
C30. 30_audio_asset_jury
C31. 31_qgis_analysis_agent
C32. 32_grass_gis_analysis_agent
C33. 33_blender_architecture_walkthrough_agent
C34. 34_unreal_engine_import_agent
C35. 35_raster_2d_processor_agent

PER AGENT DE STAPPEN:

C.x.1 Lees agent spec:
Open het .md bestand uit agents/ of extensions/ (afhankelijk van nummer).
Extract: doel, scope, jury leden, Cursor prompt.

C.x.2 Delegate code generatie naar V1:
POST naar V1 orchestrator workflow met:
- task_type: "build_v2_agent"
- agent_number: <NN>
- agent_spec: <inhoud .md bestand>
- target_path: L:\!Nova V2\v2_services\<agent_name>\
- python_version: 3.11
- framework: FastAPI

V1 orchestrator delegeert naar zijn code-generation agents en retourneert:
- gegenereerde Python bestanden
- docker-compose service definition
- N8n workflow JSON
- test script

C.x.3 Ontvang V1 output, schrijf naar lokale filesystem:
./v2_services/<agent_name>/
  ├── main.py (FastAPI service)
  ├── Dockerfile
  ├── requirements.txt
  ├── tests/
  │   └── test_<agent>.py
  └── workflow.json (N8n import)

C.x.4 Lokale validatie:
- Python syntax check (python -m py_compile)
- requirements installeerbaar (pip install --dry-run)
- Dockerfile valid (docker build --no-cache --dry-run indien mogelijk)

C.x.5 Deploy naar V2 infrastructure op Hetzner:
Via SSH naar root@178.104.207.194:
- scp ./v2_services/<agent_name>/ naar /docker/nova-v2/services/<agent>/
- docker compose -f /docker/nova-v2/docker-compose.yml up -d <service>
- wacht 10 sec
- test endpoint health

C.x.6 Import N8n workflow:
POST workflow.json naar V2 N8n API:
curl -X POST -H "X-N8N-API-KEY: <v2_key>" \
  -H "Content-Type: application/json" \
  -d @workflow.json \
  http://178.104.207.194:5679/api/v1/workflows

Activeer workflow:
curl -X POST -H "X-N8N-API-KEY: <v2_key>" \
  http://178.104.207.194:5679/api/v1/workflows/<id>/activate

C.x.7 Run test:
Via V1: delegate test run naar jury/test agent.
Verwacht resultaat: alle basis tests groen.

Als test faalt:
- Capture error
- Max 2 fix pogingen via V1 code-repair agent
- Bij falen: pauzeer, schrijf escalation report, wacht op mijn input

C.x.8 Update status:
Schrijf ./status/agent_<NN>_status.json:
{
  "agent_number": <NN>,
  "name": "<agent_name>",
  "status": "built|deployed|tested|active|failed",
  "built_at": "<timestamp>",
  "deployed_at": "<timestamp>",
  "tests_passed": <bool>,
  "notes": "<any issues>"
}

Alleen door naar volgende agent als C.x.8 "active" of "built" is.
Als "failed": markeer voor later retry, ga toch door naar volgende (niet 
alle agents afhankelijk).

CHECK-INS TIJDENS LOOP:

Elke 5 agents: schrijf progress summary naar ./status/progress_milestone_<N>.md
Elke 10 agents: escaleer optionele check bij mij (simpel: "agents 1-10 done, ok?")
Bij dubieuze verdicten: altijd escaleren

=== FASE D: INTEGRATIE TESTS (2 uur) ===

D.1 End-to-end test: sprite pipeline
- Trigger: dummy sprite upload naar /webhook/sprite-review
- Verwacht: doorloopt Sprite Jury, krijgt verdict, routing gebeurt
- Valideer alle 5 jury-judge specialists hebben gevuurd
- Rapport: timing per stap, verdict detail

D.2 End-to-end test: bake pipeline
- Trigger: bake request voor Hoogeveen 7901
- Verwacht: PDOK download → QGIS → Blender → Jury → Distribution
- Time budget: 15-30 min
- Als faalt: diagnose welke agent bottleneck is

D.3 Cross-agent validatie:
- Monitor Agent (11) detecteert andere agents running?
- Cost Guard (16) ziet API calls?
- Error Agent (17) ontvangt simulated errors?

D.4 Performance baseline:
- Gemiddelde response tijd per agent
- Concurrent capacity
- Memory footprint

=== FASE E: HANDOFF (30 min) ===

E.1 Documentatie genereren:
./docs/v2_deployment_report.md met:
- Welke 35 agents live
- URLs per agent
- N8n workflow IDs
- Success metrics
- Known issues

E.2 Backup configureren:
- Automatische postgres dump (cron)
- MinIO data backup
- .env backup naar secrets/

E.3 Finaal rapport naar mij:
Toon in chat:
- Success rate (X/35 agents live)
- Totale build tijd
- Eventuele failed agents
- Aanbevolen next steps
- URLs en key info

E.4 Save state:
./status/build_complete_<timestamp>.json met complete status

REGELS:

1. Max 2 retry pogingen per probleem, dan escaleer
2. V1 (poort 5678) is productie, NOOIT wijzigen
3. Elk agent build moet onafhankelijk falen kunnen zonder rest te breken
4. Bij kritieke infrastructure fout: stop alles, wacht op mij
5. Log alles naar ./logs/mega_build_<timestamp>.txt
6. Elke 2 uur: status update naar ./status/
7. Bij vragen van V1 of agent code die unclear is: escaleer, niet raden

WAT TE DOEN ALS V1 NIET KAN HELPEN:

Als V1 orchestrator niet in staat blijkt om v2 code te genereren 
(missing capability, unclear agent responses, etc):

FALLBACK MODE:
- Cursor doet zelf code generatie per agent (gebruik agent .md Cursor prompts)
- V1 beperkte rol: alleen test execution via jury agents
- Deploy nog steeds via infrastructure scripts
- Plan expansie: 16-20 uur ipv 8-10 uur

Meld mij zodra fallback mode gestart, dan weet ik tijdlijn.

Ga nu aan de slag. Werk autonoom door alle fases.
Rapporteer milestones. Escaleer zoals gedefinieerd.
Max 48 uur totale tijd voor alles.
```

## Wat te verwachten

**Eerste uur:**
- Zips uitgepakt
- V1 getest
- Eerste 2-3 agents proberen te bouwen
- Check of approach werkt

**Eerste dag:**
- 10-15 agents live als alles goed gaat
- Of: fallback mode activated als V1 niet geschikt blijkt

**Tweede dag:**
- Alle 35 agents geprobeerd
- Integratie tests
- Rapport

**Derde dag:**
- Backup configureren
- Finale documentatie
- Handoff aan gebruiker

## Jouw rol als gebruiker

Minimale actieve betrokkenheid:
- Antwoord op Cursor vragen (SSH user, API keys, approvals)
- Review milestones (elke 10 agents)
- Handel escalaties af
- Finale go/no-go op productie

Geen handmatig coderen nodig. Cursor + V1 doen het werk.

## Bij problemen

**V1 antwoordt niet:**
Cursor schakelt fallback mode in en doet het zelf. Meldt het aan jou.

**Hetzner storage vol:**
Cursor pauzeert, vraagt jou ruimte vrij te maken of upgrade.

**Agent blijft falen:**
Cursor parkeert die agent, gaat door met anderen. Finaal rapport noemt welke opnieuw moeten.

**Netwerk issue:**
Cursor retry 2x, dan pauzeert en meldt.

## Next steps als build compleet

Na succesvolle build heb je:
- 35 v2 agents live en werkend
- End-to-end pipelines getest
- Backup strategie actief
- Documentatie compleet
- V1 onaangetast

Dan kun je:
- Eerste productie werk op v2 doen
- Geleidelijk V1 workflows migreren
- V1 eventueel afbouwen (later)
