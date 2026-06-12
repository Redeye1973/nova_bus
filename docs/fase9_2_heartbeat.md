# FASE 9-2 — Liveness via heartbeats (technische specificatie)

**Datum:** 2026-06-11 (spec) · 2026-06-12 (formalisatie)  
**Formeel rapport:** `L:\ZZZZZ ZZ 31-05-2026\nova_betrouwbaar\fase9-2\FASE9-2.md`  
**Fase-nummering:** `nova_betrouwbaar\fase9-2\FASE_NUMMERING.md`  
**Tag (doel):** `fase9-2-liveness-compleet` — **PENDING** tot `all_held: true`  
**Bewijs:** `docs/fase9_1_evidence/` (canon) · kopie in `nova_betrouwbaar\fase9-2\evidence\`

---

## Probleem

Fase 9-1 kapte jobs af op een vast totaal-budget (pixellab 900s; binnen pipelines effectief 250s). PixelLab generate duurt werkelijk **~10 min** per laag (`pixellab_werkelijke_duur.json`): gezonde jobs werden orchestrator-side "timeout" verklaard terwijl Dale gewoon doorwerkte. Regressie B faalde daarop.

**Ontwerpprincipe:** *"duurt lang" ≠ "is dood"*. Totale duur is geen kill-criterium; afwezigheid van heartbeats wél.

---

## Architectuur-overzicht

```
Dale (lopende job)
  │ elke 60s
  ├─► nova_job_events.jsonl  (event_type=heartbeat)
  └─► nova_job_heartbeats.json  (compact, poll elke 2s)

Orchestrator _poll_dale_job (elke 2s)
  ├─ terminal result? → done/failed/…
  ├─ heartbeat < stall_limit geleden? → running (onbeperkte totale duur)
  ├─ geen heartbeat ≥ stall_limit? → stalled (eigen status)
  └─ elapsed > budget? → log-warning + dashboard oranje (geen kill)

Pipeline
  └─ per stap: eigen Dale-job + heartbeats + step_done event
```

---

## Dale (`v2_services/agent_70_factory_worker/main.py`)

| Parameter | Waarde |
|-----------|--------|
| Heartbeat-interval | **60s** (`NOVA_DALE_HEARTBEAT_INTERVAL_S`) |
| Event | `event_type=heartbeat` → `nova_job_events.jsonl` |
| Compact store | `status/nova_job_heartbeats.json` (`job_id → ts/epoch/tool/state`) |
| Poll-kost | Compact bestand goedkoop elke 2s te lezen |
| Wachtende jobs | Bij elke tick + heartbeat-cyclus aangestipt (geen vals stall) |
| Stop | Heartbeat stopt bij result-bestand; entry opgeruimd |
| Testhaak | `payload.no_heartbeat=true` onderdrukt heartbeats (simuleert dode job) |
| Regressietool | `test_sleep` — duration via payload, heartbeat standaard aan |

---

## Orchestrator (`L:\Nova\1 Orchestrator\main.py`)

### `_poll_dale_job`

Poll-interval: **2s**. Beslissingslog: elke **60s**.

| Beslissing | Actie |
|------------|-------|
| Terminal result (done/failed/…) | Klaar, zoals voorheen |
| Heartbeat binnen `stall_limit` | Blijft **`running`**, ongeacht totale duur |
| Geen heartbeat ≥ `stall_limit` | Status **`stalled`**, completion-event, geen proof |
| `elapsed > JOB_TYPE_MAX_WAIT_S` | Alleen log-warning + `over_budget=true` in dashboard |

### stall_limits (`JOB_TYPE_STALL_LIMIT_S`)

| Job-type | stall_limit | Toelichting |
|----------|-------------|-------------|
| pixellab_generate | **300s** (5 min) | 5× heartbeat-interval marge |
| shell | **120s** (2 min) | 2× heartbeat-interval marge |
| godot_* | **120s** | idem shell |
| test_sleep | **120s** | regressie |
| default | **300s** | |

Empirische basis: `pixellab_werkelijke_duur.json` (~600s werkelijke duur; heartbeat 60s → 300s = 5 gemiste heartbeats).

### Budget (waarschuwing only)

| Job-type | max_wait_s | Gedrag |
|----------|------------|--------|
| pixellab | **900s** | Dashboard oranje "over budget — blijft lopen" |
| shell/godot | **300s** | idem |

### Audit

Elke poll-beslissing → `status/nova_liveness_log.jsonl`:
`job_id`, `decision`, `last_heartbeat_age_s`, `elapsed_s`, `over_budget`

Monitor kan dit bestand sweepen.

---

## Pipeline (FIX 2)

Stall-bewaking per **STAP** — elke stap is een eigen Dale-job met eigen heartbeats. Een pipeline van 5 pixellab-stappen mag uren lopen.

| Event | Inhoud |
|-------|--------|
| `step_done` | `step: "n/7"`, `pipeline_id`, proof-referentie |
| Stall op stap N | Pipeline-completion `stalled_at_step_N` |
| Proofs | Intact voor voltooide stappen 1..N-1 |

`step_done`-events houden de pipeline-ouder "levend" in het dashboard-paneel.

---

## Dashboard

Zie `dashboard_job_timer.md` voor volledige endpoint-spec.

**Endpoint:** `GET http://127.0.0.1:8000/jobs/active`

**Per job:** `elapsed_s`, `last_heartbeat_age_s`, `stall_limit_s`, `over_budget`, `max_wait_s`

**Weergave:**
- Live timer (m:ss) + progressbar t.o.v. budget
- **"hb Xs / limiet"** — groen <90s, geel ≥90s, rood ≥ stall_limit
- Over budget (900s pixellab) → oranje balk, **geen kill**

**Bronnen server-side:** `nova_job_events.jsonl`, `nova_job_heartbeats.json`, Dale result-bestanden.

Dashboard pollt elke 3s; timers en hb-leeftijden tikken elke 1s lokaal door.

---

## Regressies (g–l)

Script: `docs/fase9_1_evidence/fase9_1_regressie.py`  
Resultaat: `docs/fase9_1_evidence/fase9_1_regressie.json`

| Test | Verwacht | Snapshot (2026-06-12) |
|------|----------|----------------------|
| **g** G_slow_alive_20min | running → done + proof | **FAIL** (stalled) |
| **h** D_stalled (no_heartbeat) | stalled ≤ stall_limit, geen proof | **HELD** |
| **i/B** B_pixellab_pipeline | heartbeats + step_done + proofs | **FAIL** (5/7, failed) |
| **j/C** C_fase9_T1_T5 | all_held | **HELD** |
| **A** A_sleep_200 | running → done + proof | **FAIL** (stalled) |
| **D** D_stalled | idem h | **HELD** |

**`summary.all_held: false`** · **`health_green: true`**

Diagnose vooraf: `fase9_1_evidence/test_b_diagnose.md`

---

## Herstart-keuze

Dale-jobs zijn file-based (queue/results op disk) en overleven herstarts; orchestrator-herstart verliest alleen lopende achtergrond-polls. Beide services herstart bij `queue_depth=0` en `running_count=0` (Dale `/status`) — drie pixellab-jobs T2-run waren al afgelopen. Niets gekilld.

---

## Relatie tot andere fasen

| Fase | Doc | Tag |
|------|-----|-----|
| Fase 9 (dispatch) | `fase9_report.md` | `fase9-dispatch-compleet` |
| Fase 9-1 (async) | `fase9_1_async_dispatch.md` | `fase9-1-async-dispatch` |
| **Fase 9-2 (liveness)** | dit document | `fase9-2-liveness-compleet` **PENDING** |

Fase 9-1 fix #3 (hard timeout) is **vervangen** door dit heartbeat/stall-mechanisme. Zie ook de "FASE 9.2 update"-sectie in `fase9_1_async_dispatch.md`.

---

## Bekend issue buiten scope (escalatie)

De PixelLab-API faalde tijdens de T2-run: 2× `504 Gateway Time-out` en 1× pydantic-validatie-error (`usage.type 'generations'` — client-lib verwacht `usd`) in de host-bridge. Jobs ronden af maar `response.status=error` en er worden geen PNG's geschreven. Bridge/PixelLab-issue, geen timing-issue — bepaalt of regressie i/B volledig HELD kan worden.

---

## Volgende stap

1. Regressieset opnieuw draaien tot `all_held: true`.
2. Tag `fase9-2-liveness-compleet` zetten.
3. SM Part 1 bewijsrun T2 hervatten (`docs/smpart1_bewijsrun/RAPPORT.md`).
