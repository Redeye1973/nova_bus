# NOVA v2 Implementatie Volgorde

Logische bouwvolgorde voor alle agents. Volg deze stappen om rommelige implementatie en integration issues te voorkomen.

## Fase 0: Foundation (Week 1)

Voordat je agents begint te bouwen, zorg dat de fundamentele infrastructuur staat.

**Prerequisites:**
- N8n draait op Hetzner met PostgreSQL backend (niet SQLite)
- Redis voor queue mode en caching
- Ollama geïnstalleerd op lokale machine met minstens Qwen 2.5 VL 7B en Codestral 22B
- Python 3.11+ op lokale PC
- MinIO voor asset storage (kan ook lokaal via Docker)
- Git repo voor alle NOVA v2 code

**Taken deze week:**
1. N8n queue mode activeren + Redis configureren
2. PostgreSQL schema aanmaken voor agent state
3. Git repo structuur opzetten met mappen per agent
4. Docker compose file maken voor shared services
5. `.env` file template met alle environment vars
6. Basis CI/CD via GitHub Actions (test op commit)

**Validatie**: N8n webhook kan triggers ontvangen, Ollama reageert op localhost:11434, Redis is bereikbaar.

## Fase 1: Sprite Jury (Week 2)

Eerste jury-judge implementatie. Volume + meetbaar = goede start.

**Waarom eerst:**
- Veel bestaande sprites om tegen te testen (Black Ledger 432 enemy sprites)
- Objectieve meetbaarheid (pixel integrity, etc)
- Minder afhankelijk van subtiliteit dan andere domeinen

**Volgorde binnen fase:**
1. Pixel Integrity specialist (Python only, geen AI)
2. N8n jury-judge template eerst deployen
3. Silhouette reviewer via Ollama toevoegen
4. Style consistency specialist (gebruikt Qdrant)
5. Judge implementation
6. Integration test met 100 Black Ledger sprites

**Success criterium**: 80%+ accept rate op bekend-goede sprites, < 5% false positive.

**Tijd**: 5-7 dagen fulltime werk.

## Fase 2: Code Jury (Week 3-4)

Uitbreiding van bestaande UE5 debugger naar volwaardig systeem.

**Waarom tweede:**
- Kritiek voor AI-gedreven development workflow
- Direct impact op kwaliteit van andere agents
- Meetbaar via bestaande test suites

**Volgorde:**
1. Syntax validator (Python ast, GDScript parser)
2. API existence checker (godot_api_cache.json builden)
3. Security scanner (semgrep integratie)
4. Regression detector (git diff + testing)
5. Logic flow detector (Ollama)
6. Judge met Cursor feedback loop

**Success criterium**: 95%+ detectie van bewust kapotte test cases.

**Tijd**: 10-14 dagen. Groter omdat meerdere languages.

## Fase 3: Monitor Agent + Error Agent (Week 5)

Operationele backbone. Moeten bestaan voordat grote pipelines draaien.

**Waarom nu:**
- Voorkomt blind vliegen wanneer het complex wordt
- Alle volgende agents rapporteren hierheen
- Geen complex AI werk, meer engineering

**Volgorde:**
1. Error Agent eerst (andere agents kunnen errors rapporteren)
2. Monitor Agent workflow
3. Grafana dashboard basis
4. Alerting naar Telegram/Discord

**Success criterium**: Errors worden gevangen en gerouteerd, monitor draait elke uur.

**Tijd**: 5-7 dagen.

## Fase 4: Bake Pipeline (Week 6-8)

Grote investering maar kern van NOVA v2 waarde.

**Sub-fasen:**

**4a: PDOK Downloader (Week 6, 3-4 dagen)**
- Pure data handling, geen AI
- Cache management kritiek
- Test tegen Hoogeveen postcode

**4b: QGIS Processor (Week 6-7, 4-5 dagen)**
- Pure data processing
- Kan stressvol zijn door QGIS quirks
- Gebruik qgis_process CLI voor robuustheid

**4c: Blender Baker (Week 7-8, 5-7 dagen)**
- Meest complexe component
- Asset library bouwen neemt tijd
- Start met simpele extrusies, voeg detail toe

**4d: Bake Orchestrator (Week 8, 2-3 dagen)**
- Binds alles samen
- N8n workflow met sub-workflows
- Progress tracking + resource management

**4e: GIS Jury + 3D Model Jury (Week 8, parallel waar mogelijk)**
- Validatie van bake output
- Reuse jury-judge template

**Success criterium**: Hoogeveen volledig gebakken, gevalideerd, gedistribueerd binnen 4 uur.

**Tijd totaal**: 15-20 dagen.

## Fase 5: Audio + 3D Model Juries (Week 9-10)

Nu de pipeline draait, breid validatie uit.

**Audio Jury (5-7 dagen):**
- Voor game music en SFX
- Librosa voor technische checks
- Ollama voor coherence

**3D Model Jury (5-7 dagen):**
- Naast GIS jury voor Meshy/Blender assets
- Topology + budget checks

## Fase 6: Cost Guard + Distribution (Week 11)

Productie-klaar maken.

**Cost Guard (3-4 dagen):**
- Track alle AI en cloud spending
- Budget alerts
- Dashboard integratie

**Distribution Agent (3-4 dagen):**
- Van validatie naar consumer
- Versioning + changelog
- Access control basis

## Fase 7: Prompt Director (Week 12)

Meta-agent voor workflow management.

**3-5 dagen:**
- Template library
- Cursor dispatcher
- Workflow orchestrator

## Fase 8: Specialized Juries (Week 13-14+)

Afhankelijk van product prioriteit.

**Volgorde keuze:**
- Character Art Jury → als NORA voetgangers prio
- 2D Illustration Jury → als UI werk veel
- CAD Jury → als FINN engineering werk prio
- Game Balance Jury → voor Black Ledger balancing
- Narrative Jury → laatste, meest subjectief

Elk 4-6 dagen.

## Totale Tijdlijn

**Minimum viable NOVA v2 (Fase 0-6)**: 11 weken = ~3 maanden fulltime.

**Parttime realiteit (20 uur/week)**: 6 maanden.

**Met leren en debuggen**: plan 9-12 maanden voor stabiel systeem.

## Risico's per Fase

**Fase 0**: N8n queue mode kan tricky zijn, Redis config fouten.

**Fase 1**: Ollama vision models vereisen juiste quantization voor RTX 5060 Ti.

**Fase 2**: AST parsing per language heeft edge cases, godot_api_cache moet up-to-date.

**Fase 4b**: QGIS CLI is slecht gedocumenteerd, verwacht debugging tijd.

**Fase 4c**: Blender headless + asset libraries is complex, plan iteraties.

**Fase 8 (Narrative)**: Verwacht dat dit nooit 100% werkt. Blijf menselijke review vereisen.

## Tips per Fase

**Universeel:**
- Schrijf tests meteen, niet later
- Log alles in structured JSON format
- Environment variables voor alle endpoints (easy switch lokaal/remote)
- Docker containerize elke service

**Specifiek:**
- Fase 1-2: focus op FastAPI patronen, hergebruik voor volgende agents
- Fase 3: error handling templates maken, reuse in alle latere agents
- Fase 4: stress test met grote postcode (Amsterdam binnenstad) voor je productie gaat
- Fase 5-6: performance optimalisaties, niet meer features

## Milestones

**End Fase 1**: Eerste jury-judge werkt op 100 sprites. Bewijs van concept.

**End Fase 4**: Hoogeveen bake end-to-end. Grootste functionele mijlpaal.

**End Fase 6**: Platform is productie-capable. Kan betalende klanten serieus bedienen.

**End Fase 8**: Alle domeinen gecovered. NOVA v2 compleet.

## Wanneer Te Stoppen / Pauzeren

Als na Fase 4 (bake werkt) blijkt dat focus beter elders ligt (bijvoorbeeld bij een specifiek product succes dat prioriteit verdient), pauzeer rest van NOVA v2 implementatie. Gebouwde fundament blijft bestaan en kan later worden uitgebreid.

Perfectie is vijand van progress. Liefde MVP level agents die draaien boven ideaal-uitgewerkte agents die nooit af komen.
