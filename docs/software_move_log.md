# Software Verplaatsing Log

**Beleid (25 april 2026):** Geen `Move-Item` of verwijderen van bronnen. Geen kopieën naar ZZZ buiten plan — inventarisatie-only.

| Datum | Tool | Source | Target | Status | Test | Notes |
|-------|------|--------|--------|--------|------|-------|
| 2026-04-25 | — | — | — | **NO_OP** | — | Eerste consolidatie-run: alle relevante tools staan al op policy-conforme locaties (ZZZ vs Program Files vs Steam). Categorie B leeg. |

## Toekomstige verplaatsing (sjabloon)

1. `Copy-Item -Recurse` naar `L:\ZZZ Software\<Tool>\`
2. Test executable (`--version` of minimale GUI/CLI)
3. Log resultaat hier
4. Pas **daarna** (na Alex-OK) bron opruimen
