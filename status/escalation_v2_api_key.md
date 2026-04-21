# Escalatie: V2 n8n API key (Fase A blocker voor volledige automatisering)

**Datum:** 2026-04-19

## Observatie

- `GET /api/v1/workflows` op **:5679** geeft **401** met keys uit `N8n Key.txt` en `N8n WorkHorse.txt`.
- **V1** (:5678) werkt met `N8n WorkHorse.txt` — **68** workflows (`?limit=250`, `data` array).

## Vereiste actie (gebruiker)

1. Log in op `http://178.104.207.194:5679` (admin).
2. n8n → **Settings → API** → maak een API key aan voor V2.
3. Zet in `L:\!Nova V2\secrets\nova_v2_passwords.txt` (of apart bestand dat je in scripts gebruikt):

   `N8N_V2_API_KEY=<nieuwe key>`

4. Herstart geen stack nodig — alleen API-clients updaten.

## Daarna

- Hervat **Fase C** (workflow-import / API-gestuurde deploy) vanuit `mega_plan/00_MASTER_PROMPT.md`.
- Optioneel: zet dezelfde key in `N8n Key.txt` alleen als je die file exclusief voor V2 wilt gebruiken (niet aanbevolen als die naam voor V1 bedoeld is); liever expliciet `N8N_V2_API_KEY` in passwords-bestand.
