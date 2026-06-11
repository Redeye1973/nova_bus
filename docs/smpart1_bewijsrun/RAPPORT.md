# SM Part 1 Bewijsrun — Rapport (deelrun)

**Start-tag:** `smpart1-bewijsrun-start`  
**Eind-tag:** niet gezet (run niet compleet)  
**Datum:** 2026-06-11

## Poort (STAP 0)

| Check | Status |
|-------|--------|
| git-tag `fase8-integriteit-compleet` | PASS |
| git-tag `fase9-dispatch-compleet` | PASS |
| Health kern 15/15 | PASS (8000 via `/status`) |
| regress_a fix1/2/3 | PASS |

## Taakoverzicht

| Taak | Eindstatus | Bewijsketen |
|------|------------|-------------|
| T1 Nulmeting | **DONE** | job_id + proof + godot_validate exit 0 |
| T2 Parallax-fix | **IN PROGRESS** | dispatch-events OK; pipeline+jury lopen |
| T3 Minigun | **NIET GESTART** | geblokkeerd door T2 FAIL (sequentieel) |
| T4 Missiles | **NIET GESTART** | idem |
| T5 Muisbesturing | **NIET GESTART** | idem |
| T6 Juice-pass | **NIET GESTART** | idem |
| T7 Eindvalidatie | **NIET GESTART** | idem |

---

## T1 — Nulmeting (DONE)

**Opdracht:** godot_validate SM_Part1 via Orchestrator.

- **job_id:** `chat_godot_validate_1781182680`
- **dispatch:** `infer_job_from_text` → `godot_validate` (geen no_dispatch)
- **proof:** job proof in `nova_proofs.jsonl`, exit_code 0, geen script_errors
- **Nulmeting werkt:** speler-beweging (player.gd toets + muis), enemy spawning (spawner.gd elke 2s)

Bewijs: `docs/smpart1_bewijsrun/taak_01.json`

---

## T2 — Parallax-fix + stijlconsistentie (HERSTART na fase 9.1)

**Infra-fix:** fase 9.1 async dispatch — zie `docs/fase9_1_async_dispatch.md`

### a) Stijlcontract

- `docs/smpart1_bewijsrun/stijlcontract.json` (ongewijzigd geldig)

### b) Schone T2-retry (cyclus 1, na fix)

- **Dispatch:** POST `/chat` parallax agent pipeline → direct `job_id` + `status=running` (<2s)
- **Dispatch-events:** per pixellab-laag `event_type=dispatch` in `nova_job_events.jsonl` vóór voltooiing
- **Geen 120s tick-timeout meer** — poll via Dale result-bestanden, max 900s per pixellab-laag
- **Status:** IN PROGRESS — pipeline draait op achtergrond; jury 8136+8137 volgt na generatie

### c) Jury 8136 + 8137

**PENDING** — wacht op voltooide 5-laags keten

### d) Eerdere FAIL (vóór fix)

2 cycli gefaald door Orchestrator tick timeout 120s (gedocumenteerd hieronder).

**Eindstatus T2:** **IN PROGRESS** (infra groen, game-keten loopt)

---

## T2 — Parallax-fix (FAIL vóór fase 9.1, historisch)

### a) Stijlcontract

- `docs/smpart1_bewijsrun/stijlcontract.json` vastgelegd
- Palet-regel via POST `/feedback` agent 8141 (patroon=true) → proof in bible

### b) Generatie (2 cycli, max 2 orchestrator-pogingen)

Beide pogingen via POST `/chat` :8000:

1. **Cyclus 1 poging 1** — failed na 120s (Orchestrator→Dale read timeout), geen job_id
   - Dale voltooide achtergrond: lagen 1–3 met proofs (`1781182712`, `1781182759`, `1781182850`)
2. **Cyclus 2 poging 2** — failed na 120s, geen job_id
   - Dale regenereerde opnieuw alleen `bg_layer_1_sky` (`1781183552`, `1781184169`)

**Lagen 4 en 5 niet regenereerd** (oude hashes ongewijzigd). Stijlprobleem (drie werelden gestapeld) **niet aantoonbaar opgelost**.

### c) Jury 8136 + 8137

Geen geldige jury-responses via Orchestrator — pipeline ketting nooit tot jury-stap gekomen. Vereiste checks palet/thema/diepte/geheel: **alle MISSING**.

### d) FAIL-handling

2 orchestrator-pogingen uitgeput (R4). Infra-blokkade gedocumenteerd; geen Cursor-fallback op game files.

---

## Wat NOVA niet zelf kon (vóór fase 9.1 — OPGELOST)

- ~~Orchestrator/Dale timeout 120s~~ → **OPGELOST** in fase 9.1 (`_poll_dale_job`, dispatch-events, async /chat)
- **Huidige blokkade:** geen — T2-retry loopt via NOVA pipeline

---

## Wat NOVA niet zelf kon (historisch)

---

## Eindcheck health

**15/15 groen** (eind van run).

---

## Eindoordeel

| Vraag | Antwoord |
|-------|----------|
| SM Part 1 speelbaar | **NEE** (T2 nog niet PASS; pipeline loopt) |
| Bewijsketen compleet | **NEE** (T2 IN PROGRESS, T3–T7 wachten) |

---

## Volgende stap (NOVA)

1. ~~Infra-fix fase 9.1~~ **DONE**
2. Wacht pipeline T2 completion + jury 8136/8137 (max 3 cycli)
3. Bij T2 PASS → T3–T7 sequentieel
