# FASE 9.1 — Async Dispatch-fix (Orchestrator/Dale timeout)

**Datum:** 2026-06-11  
**Tag:** `fase9-1-async-dispatch`  
**Bewijs:** `docs/fase9_1_evidence/fase9_1_regressie.json`

---

## Probleem (T2 bewijsrun)

`_run_dale_job` blokkeerde op Dale `/invoke` tick met `timeout=120`. PixelLab-jobs duren regelmatig **>120s** (tot ~600s). Orchestrator rapporteerde `failed` **zonder job_id** terwijl Dale jobs op de achtergrond wél voltooiden → bewijsketen gebroken.

---

## Architectuur-fix (`L:\Nova\1 Orchestrator\main.py`)

| # | Wijziging |
|---|-----------|
| 1 | **Dispatch-event bij DISPATCH** — `_record_dispatch_job_event()` schrijft `event_type=dispatch` + `job_id` naar `nova_job_events.jsonl` op submit-moment |
| 2 | **Async dispatch voor langlopende jobs** — submit → direct `status=running` + `job_id`; achtergrond-poll via `_poll_dale_job()` (result-bestanden, geen blocking tick-loop) |
| 3 | **Per job-type max-duur** — pixellab: 900s, shell/godot: 300s → status `timeout` (eigen status, geen `failed`, geen stil doorlopen) |
| 4 | **/chat langlopende jobs** — geldig antwoord: *"Dispatched — job_id=X, status=running"*; completion via bewijsketen (proof + completion-event) |
| 5 | **Snelle tools sync** — `godot_validate` e.d. blijven sync poll (<30s) zodat fase 9 T1–T5 regressies groen blijven |

### Dale (`agent_70_factory_worker/main.py`)

- `test_sleep` tool toegevoegd voor regressie (a) en (d).

---

## Regressietests

| Test | Verwacht | Script |
|------|----------|--------|
| a) 200s sleep | Direct job_id, dispatch vóór completion, final done+proof | `fase9_1_regressie.py` A |
| b) T2 pixellab 5 lagen | job_id bij dispatch, geen timeout <900s | B |
| c) Fase 9 T1–T5 | all_held | C |
| d) Hang > max-duur | status timeout, geen proof | D |

---

## Herstart

Orchestrator (:8000) en Dale (:8170) herstart na patch.

---

## Volgende stap

Hervat SM Part 1 bewijsrun vanaf schone T2-retry (`docs/smpart1_bewijsrun/RAPPORT.md`).
