# NOVA v2 Mega Build Plan — V1 bouwt V2

Complete autonome opbouw van NOVA v2 (35 agents) door NOVA v1 (68 bestaande agents + orchestrator) als uitvoerend systeem.

## Architectuur concept

```
┌──────────────────────────────────────────────────┐
│ Cursor (jouw PC) - Strategic layer               │
│ - Leest mega plan                                │
│ - Coordineert met V1 orchestrator                │
│ - Monitort voortgang                             │
└──────────┬───────────────────────────────────────┘
           │
           ▼ (HTTP/webhook naar V1)
┌──────────────────────────────────────────────────┐
│ NOVA v1 Orchestrator (Hetzner :5678)             │
│ - 68 bestaande agents beschikbaar                │
│ - Ontvangt build tasks van Cursor                │
│ - Delegeert naar specific agents                 │
│ - Rapporteert status terug                       │
└──────────┬───────────────────────────────────────┘
           │
           ▼ (delegatie)
┌──────────────────────────────────────────────────┐
│ V1 Agents (werkbijen)                            │
│ - Code generator agents schrijven Python         │
│ - Scaffold agents zetten FastAPI services op     │
│ - Jury agents reviewen output                    │
│ - Deploy agents pushen naar V2 infrastructure    │
└──────────┬───────────────────────────────────────┘
           │
           ▼ (output)
┌──────────────────────────────────────────────────┐
│ NOVA v2 Infrastructure (Hetzner :5679)           │
│ - 35 v2 agents geïnstalleerd                     │
│ - Workflows geactiveerd                          │
│ - End-to-end pipelines draaien                   │
└──────────────────────────────────────────────────┘
```

## Waarom deze aanpak

**Voordelen van V1 gebruiken voor V2 bouw:**

1. V1 heeft al 68 werkende agents - volle productiecapaciteit beschikbaar
2. Orchestrator ervaren met complex werk delegatie
3. Schaalt automatisch - meerdere agents parallel
4. Ingebouwde error handling en retry logica
5. Menselijke tussenkomst minimaal nodig

**Wat Cursor NIET doet:**
- Code handmatig schrijven voor elk van 35 agents
- Elke Python service zelf opzetten
- Testen runnen in isolatie

**Wat Cursor WEL doet:**
- Strategische beslissingen nemen
- V1 orchestrator aansturen via API
- Voortgang monitoren
- Menselijke escalaties afhandelen
- Finale validatie

## Volledige werkflow overzicht

```
Fase A: Voorbereiding (Cursor autonoom)
├── A.1 Zips uitpakken
├── A.2 Structuur in L:\!Nova V2\
├── A.3 V1 API toegang valideren
└── A.4 V2 infrastructure status check

Fase B: V1 Orchestrator Briefing (Cursor → V1)
├── B.1 Master brief document bouwen
├── B.2 Uploaden naar V1 orchestrator
├── B.3 Agent catalogus beschikbaar maken
└── B.4 Bouw-plan ingelezen door V1

Fase C: Agent Bouw Loop (V1 doet werk)
├── C.1 V1 pakt agent 01 Sprite Jury
├── C.2 V1 genereert code via code-agent
├── C.3 V1 test via test-agent
├── C.4 V1 deployt naar V2 infrastructure
├── C.5 V1 rapporteert naar Cursor
└── C.6 Cursor valideert, next agent

(Loop van C.1-C.6 voor alle 35 agents)

Fase D: Integratie Tests (V1 + Cursor)
├── D.1 End-to-end pipeline tests
├── D.2 Jury-judge cross-agent tests
├── D.3 Performance baseline
└── D.4 Final report

Fase E: Handoff naar productie
├── E.1 Documentatie gegenereerd
├── E.2 Backup strategie actief
└── E.3 Cursor informeert gebruiker
```

## Document structuur

Dit mega-plan bestaat uit:

1. **00_MASTER_PROMPT.md** - Hoofdprompt voor Cursor
2. **01_fase_A_voorbereiding.md** - Voorbereiding details
3. **02_fase_B_orchestrator_brief.md** - V1 briefing
4. **03_fase_C_agent_bouw_loop.md** - Agent bouw proces
5. **04_fase_D_integratie.md** - Integratie tests
6. **05_fase_E_handoff.md** - Finale handoff
7. **agent_volgorde.md** - 35 agents in bouwvolgorde
8. **v1_delegation_format.md** - Hoe V1 taken ontvangt
9. **error_escalation.md** - Wanneer Cursor tussenbeide

## Geschatte tijd

- Fase A: 5-10 min (setup)
- Fase B: 10-20 min (briefing V1)
- Fase C: 8-16 uur (35 agents bouwen, zwaar werk)
- Fase D: 1-2 uur (integratie tests)
- Fase E: 30 min (handoff)

**Totaal: 10-20 uur autonoom werk, grotendeels door V1 agents.**

Kan doorlopen terwijl jij slaapt, werkt, of andere dingen doet. Cursor checkt periodiek in.

## Hoe gebruiken

1. Unzip deze package in `L:\!Nova V2\mega_plan\`
2. Ken dat NOVA v1 draait met 68 agents en orchestrator toegankelijk is
3. Ken V1 API key (voor Cursor toegang tot v1)
4. Open Cursor in `L:\!Nova V2\`
5. Plak inhoud van `00_MASTER_PROMPT.md` in Composer
6. Enter en laat Cursor werken

## Kritische aannames

Cursor werkt onder deze aannames:

1. NOVA v1 draait op http://178.104.207.194:5678
2. V1 API key in secrets file (of Cursor vraagt)
3. NOVA v2 infrastructure draait op :5679 (uit eerdere deploy)
4. V2 infrastructure heeft N8n API werkend
5. 5 zip files beschikbaar in Cursor werkmap:
   - nova_v2_agents.zip (basis 19 agents)
   - nova_v2_extensions.zip (agents 20-35)
   - nova_v2_infrastructure.zip
   - shmup_pipeline.zip
   - nova_v2_infrastructure_final.zip (indien nog niet gebruikt)

## Veiligheidsgaranties

- V1 (68 agents) wordt NIET gewijzigd, alleen gebruikt
- V1 orchestrator delegeert, maar V1 agents bouwen V2 code in gescheiden V2 omgeving
- Bij V1 failure: Cursor schakelt over naar handmatig fallback
- V2 build faalt nooit V1
- Alle V1 operaties zijn read-heavy, minimale writes (alleen work queue)

## Volgende stappen

Lees `00_MASTER_PROMPT.md` voor de complete Cursor prompt.

Voor achtergrond per fase: andere nummered docs.
