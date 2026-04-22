# NOVA v2 Build — Sessie Index

**Gemaakt:** 22 april 2026 nacht
**Context:** Mega "17-uurs autonoom" bleek niet haalbaar in Cursor Composer. Daarom opgesplitst in 7 focus-sessies die elk passen in één Composer-run.

---

## Werkwijze

Elke sessie:
1. Heeft eigen `.md` bestand
2. Begint met een `PREREQUISITES` block — wat moet waar zijn
3. Eindigt met een `OUTPUT` block — wat heb je nu
4. Commit + push na succes
5. Schrijft kort rapport naar `docs/session_XX_report.md`

## Volgorde (strikt)

| # | Sessie | Duur | Afhankelijk van | Kritiek? |
|---|--------|------|-----------------|----------|
| 01 | V1 API key + secrets | 5 min handwerk | — | JA |
| 02 | Bridge fix + TB-001 | 45-90 min | 01 | JA |
| 03 | V1 orchestrator brief + capability test | 30-45 min | 01, 02 | JA |
| 04 | Judge + self-heal laag deployen | 60-90 min | 02, 03 | JA |
| 05 | Agent bouw batch 1 — juries 03-09 | 90-150 min | 04 | Hoog |
| 06 | Agent bouw batch 2 — operationele 11-19 | 90-150 min | 05 | Hoog |
| 07 | Agent bouw batch 3 — asset prod 22-35 | 120-180 min | 06 | Medium |

## Optionele vervolg

| # | Sessie | Wanneer |
|---|--------|---------|
| 08 | Pipeline integraties (F-fase) | Na 07 |
| 09 | Backup + rapport + tagging (G-fase) | Na 08 |
| 10 | Fase H — DAZ + Ren'Py agents | Weekend |

## Aanbevolen planning

**Morgen na werk (18:00-22:00)**: sessie 01, 02, 03
**Overmorgen**: sessie 04, 05
**Weekend**: sessie 06, 07, eventueel 08
**Weekend daarna**: sessie 09, 10

Elke sessie levert concrete progress. Geen alles-of-niets.

## Als sessie faalt

Lees `docs/session_XX_report.md`, fix blocker, draai die ene sessie opnieuw. Andere sessies onaangeraakt.

## Git strategy

Elke sessie:
- Start met `git checkout -b session/XX-name` (optioneel)
- Commit bij elke succesvolle sub-stap
- Merge naar main of direct op main committen
- Tag na elke complete sessie: `session-XX-complete`

## Gebruik

1. Open relevante sessie `.md`
2. Kopieer blok tussen `===SESSION START===` en `===SESSION EINDE===`
3. Plak in Cursor Composer (Ctrl+I)
4. Enter
5. Wacht tot Cursor rapporteert "SESSION XX COMPLETE"
6. Volgende sessie
