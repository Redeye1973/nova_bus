# Bridge Protocol

Hoe claude.ai en Cursor communiceren via de handoff folder.

## Naming convention

Opdrachten: `YYYYMMDD_NNN_korte_titel.md`
- YYYYMMDD = datum
- NNN = volgnummer die dag (001, 002, ...)
- korte_titel = snake_case, max 5 woorden

Responses: `YYYYMMDD_NNN_response.md` (zelfde timestamp+nummer als opdracht, suffix `_response`)

Voorbeelden:
- `20260419_001_batch2_agents_11_17_21.md`
- `20260419_001_response.md` (antwoord op bovenstaande)
- `20260420_001_fix_agent_22_blender.md`

## Headers en metadata

Elke opdracht start met:

```markdown
# [Timestamp ID] - [Titel]

**Van**: claude.ai
**Naar**: Cursor
**Prioriteit**: normal | high | blocker
**Expected duration**: [schatting]
```

Elke response start met:

```markdown
# Response: [Timestamp ID]

**Van**: Cursor
**Naar**: claude.ai
**Status**: success | partial | blocked | failed
**Duration**: [actueel]
```

## Secties verplicht in opdracht

1. **Context** - staat van systeem
2. **Doel** - één zin
3. **Opdracht** - genummerde stappen
4. **Constraints** - wat niet mag
5. **Success criteria** - meetbaar
6. **Rapporteer terug** - waar response schrijven

## Secties verplicht in response

1. **Samenvatting** - één alinea
2. **Resultaten per stap** - met status icons
3. **Issues** - wat fout ging
4. **Wijzigingen** - files/containers/commits
5. **Tests uitgevoerd** - concrete outputs
6. **Aanbeveling** - volgende handoff
7. **Shared state updates** - wat is bijgewerkt

## Status icons

- ✓ Gelukt zoals bedoeld
- ⚠️ Gelukt maar met waarschuwingen/workaround
- ✗ Gefaald
- ⏸️ Gepauzeerd/uitgesteld
- 🔒 Blocked (externe afhankelijkheid)

## Flow

```
claude.ai schrijft opdracht → to_cursor/
                                   ↓
                    watcher detecteert + notificeert
                                   ↓
                    Cursor leest + voert uit
                                   ↓
                    Cursor schrijft response → from_cursor/
                                   ↓
                    jij upload naar Claude project
                                   ↓
                    claude.ai leest + schrijft volgende opdracht
```

## Shared state

`handoff/shared_state/` bevat files die beide Claudes lezen/schrijven:

- `current_baseline.md` - wat werkt nu
- `blockers.md` - wat is vast
- `decisions.md` - beslissingen met reasoning

Beide Claudes moeten deze updaten als er relevante wijzigingen zijn.

## Conflict resolution

Last-write-wins op shared state files. Als beide Claudes tegelijk schrijven (zeldzaam): jij als mens beslist welke versie geldt.

Opdrachten/responses zijn immutable na eerste write. Eventuele correcties: nieuwe handoff starten.

## Archivering

Na X dagen (default 30, config in bridge_watcher.py): voltooide handoffs (opdracht + response paar) naar `archive/YYYY-MM/`.

Shared state blijft altijd in huidige map.

## Audit trail

Alle handoffs bewaard. Voor debugging: zoek op handoff ID, zie opdracht + response + shared state updates van die periode.

## Principes

1. **Expliciet beter dan impliciet**: schrijf liever te veel context dan te weinig
2. **Testbaar**: success criteria moeten meetbaar zijn
3. **Autonoom**: Cursor kan handoff uitvoeren zonder menselijke tussenkomst
4. **Traceable**: elke wijziging staat in git + shared state
5. **Graceful degradation**: als iets mislukt, document en ga door
6. **Jury-judge principe**: belangrijke beslissingen documenteren met reasoning

## Niet doen

- Geen secrets (API keys, passwords) in opdracht/response - gebruik verwijzing naar secrets file
- Geen giant log dumps - summariseer, link naar log file op disk
- Geen "nog doen later" zonder concrete volgende handoff
- Geen opdrachten > 4 uur scope - splits in kleinere handoffs
