# Cursor Werkwijze voor NOVA v2

Hoe je de agent-bestanden in deze catalogus gebruikt met Cursor om NOVA v2 te bouwen.

## Voorbereidingen

**Cursor installeren en configureren:**
1. Download Cursor van cursor.sh
2. Log in met je account (Cursor Pro €20/maand)
3. Open NOVA v2 project folder
4. Bij eerste keer: kies "Start from scratch" of open bestaande repo

**Claude Code CLI (alternatief/complement):**
1. Open terminal in Cursor (Ctrl+`)
2. Check of `claude` command beschikbaar is
3. Zo niet: `C:\Users\awsme\.local\bin\claude.exe` gebruiken
4. Claude Code heeft shell access en kan files direct aanpassen

**Project structuur:**
```
nova_v2/
├── .cursor/
│   ├── rules         # Cursor project rules
│   └── prompts/      # Prompt templates van Prompt Director
├── agents/
│   ├── jury_judge/
│   │   ├── sprite_jury/
│   │   ├── code_jury/
│   │   └── ...
│   └── operational/
│       ├── monitor/
│       ├── bake/
│       └── ...
├── n8n_workflows/    # Geexporteerde workflows
├── shared/
│   ├── models/       # Pydantic models
│   ├── clients/      # Ollama/Claude clients
│   └── utils/
├── docker/
├── tests/
└── docs/
```

## Werkwijze per Agent

**Stap 1: Open het relevante .md bestand**

Elke agent heeft een eigen .md bestand in deze catalogus met:
- Doel en scope
- Jury leden / functionaliteit
- N8n workflow structuur
- Een complete Cursor prompt
- Test scenario's
- Success metrics

Open bijvoorbeeld `jury_judge/01_sprite_jury.md`.

**Stap 2: Lees de prompt sectie door**

Elke agent heeft een sectie "## Cursor Prompt" met een kant-en-klare prompt. Deze is al geoptimaliseerd voor Cursor, maar pas aan waar nodig:
- Paden aanpassen aan jouw lokale setup
- Versies van dependencies checken
- Project-specifieke conventies toevoegen

**Stap 3: Nieuwe folder aanmaken**

In Cursor terminal:
```bash
mkdir -p agents/jury_judge/sprite_jury
cd agents/jury_judge/sprite_jury
```

**Stap 4: Cursor Composer aanroepen**

Open Cursor Composer (Ctrl+I of Cmd+I). Plak de prompt uit het agent-bestand. Cursor gaat meerdere files genereren.

**Stap 5: Review de output**

Voordat je wat Cursor maakt accepteert:
- Check dat bestanden in juiste folder komen
- Verify imports en dependencies
- Kijk of het consistent is met bestaande code

**Stap 6: Integreer met bestaande infrastructuur**

Cursor genereert standalone code. Je moet:
- Config files aanpassen (docker-compose toevoegen)
- Environment variables in .env
- N8n workflow importeren (uit templates/)
- PostgreSQL schema migrations

**Stap 7: Testen**

Elk agent-bestand heeft test scenario's. Run die:
```bash
./test_sprite_jury.sh
```

Fix wat niet werkt voor je door gaat naar volgende agent.

**Stap 8: Commit**

```bash
git add .
git commit -m "feat: implement sprite jury agent"
git push
```

## Cursor Rules File

Maak `.cursor/rules` met project-breed beleid:

```
# NOVA v2 Development Rules

## Algemene principes
- Python 3.11+ met type hints
- FastAPI voor alle services
- Async waar mogelijk
- Pydantic v2 voor data models
- Structured logging in JSON

## Code stijl
- Black formatter voor Python
- Ruff voor linting
- Google docstring format
- Max 100 chars per regel

## Architectuur
- Elke agent is eigen FastAPI service
- Environment variables voor alle endpoints
- Health check endpoints verplicht
- Geen hardcoded paths

## Security
- Geen secrets in code
- Keys via environment of Docker secrets
- Input validation op elke endpoint
- Rate limiting op publieke endpoints

## Testing
- Pytest voor unit tests
- Minimum 70% coverage per service
- Integration tests voor workflows
- Happy path + edge cases

## Documentation
- README per agent folder
- OpenAPI spec automatisch gegenereerd
- Changelog bijwerken per wijziging
```

## Veelgemaakte Fouten

**Fout 1: Te grote prompt in één keer**

Als een agent prompt meer dan 2000 regels code vraagt, splits in sub-prompts:
1. Eerst alleen de FastAPI service structuur
2. Daarna de business logic
3. Dan de tests
4. Tot slot Docker setup

Cursor werkt beter met gerichte prompts dan mega-prompts.

**Fout 2: Context mismatch**

Cursor kent jouw NOVA v2 niet vanuit zichzelf. Bij eerste prompt per agent:
- Geef project context ("Dit is NOVA v2, een content QA platform...")
- Verwijs naar andere agents als relevant
- Specificeer tech stack expliciet

**Fout 3: Geen review**

Cursor genereert snel code die niet altijd werkt. Altijd:
- Run de code voor je committed
- Test edge cases
- Check dependencies matchen versie in project

**Fout 4: Parallel te veel agents**

Bouw één agent af voor je begint aan de volgende. Parallel werk leidt tot integration issues.

## Tips voor Effectief Cursor Gebruik

**Tip 1: Gebruik @ references**

In Cursor chat: `@sprite_jury/pixel_integrity.py` refereert naar specifieke file. Beter dan paste.

**Tip 2: Incrementeel bouwen**

Niet: "Bouw hele sprite jury" 
Wel: "Bouw eerst pixel integrity checker, dan testen, dan volgende member"

**Tip 3: Clear context regelmatig**

Na elke agent: nieuwe Cursor chat. Voorkomt dat oude context nieuwe keuzes beïnvloedt.

**Tip 4: Gebruik Cursor's "Apply" zorgvuldig**

Cursor kan direct files aanpassen. Bij complex werk: eerst "Preview" check, dan "Apply".

**Tip 5: Commits als checkpoints**

Commit na elke werkende feature. Makkelijk om terug te rollen bij Cursor fouten.

## Cursor + Claude Code CLI Combo

Voor complexe taken combineer tools:

**Cursor**: Voor IDE werk, code editing, chat-based development.

**Claude Code CLI**: Voor terminal werk, shell commands, systeem-integratie.

**Claude Opus 4.7 via webchat (deze sessie)**: Voor strategie, review, architectuur beslissingen.

Typisch flow:
1. Cursor genereert code
2. Claude Code CLI deployt en test op systeem
3. Webchat voor review en volgende-stap beslissingen

## Handige Cursor Shortcuts

| Shortcut | Actie |
|----------|-------|
| Ctrl+I | Open Composer |
| Ctrl+K | Inline edit |
| Ctrl+L | Chat met codebase |
| Ctrl+` | Terminal |
| Ctrl+Shift+P | Command palette |
| Ctrl+P | Quick file open |
| @file | Reference file in chat |
| @code | Reference selected code |

## Debugging Workflow

Als Cursor code fout is:
1. Copy error in Cursor chat
2. Vraag: "Fix this error" met context
3. Als nog fout: vraag "Why does this happen, zoek root cause"
4. Als nog fout: split probleem op in kleinere stukken

Nooit meer dan 3 keer zelfde aanpak proberen. Dan stap terug, anders bekijken.

## Integration met N8n

Nadat Cursor een agent service heeft gebouwd:

1. Start service: `docker compose up -d sprite_jury`
2. Test endpoint: `curl http://localhost:8001/health`
3. Import N8n workflow uit `templates/`
4. Pas URL's aan in workflow voor jouw setup
5. Activeer workflow in N8n
6. Test via webhook trigger

Altijd eerst via curl testen, dan via N8n. Makkelijker te debuggen.

## Wanneer Stop Je Met Cursor Voor Een Taak

- Na 3 mislukte pogingen voor zelfde probleem
- Als Cursor output niet meer convergeert (random aanpassingen)
- Als complexiteit te hoog wordt voor prompt (split op)
- Als architecturale beslissing nodig is (vraag eerst Claude Opus/jou)

Dan: stap naar webchat voor advies, of handmatig coderen.

## Eindwoord

Cursor versnelt development maar vervangt niet engineering judgement. De mentale model blijft van jou: wat moet er gebouwd, hoe past het samen, wanneer is iets goed genoeg. Cursor is de typist, jij bent de architect.

Vertrouw niet blind, test altijd, commit vaak.
