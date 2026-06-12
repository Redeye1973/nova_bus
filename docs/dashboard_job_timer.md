# Dashboard job-timer — paneel "Lopende jobs"

**Datum:** 2026-06-11 · onderdeel van fase 9.2 (liveness)

## Wat

Het NOVA-dashboard (`L:\ZZZZZ ZZ 10-05-2026\nova_dashboard_v2.html`) heeft een
paneel **LOPENDE JOBS — DALE DISPATCH** tussen de build-progressbar en
PROJECT PARTS. Per actieve job toont het:

- **job_id + type** (pixellab_generate / shell / godot_validate / pipeline / test_sleep)
- **live timer** (m:ss) sinds dispatch, client-side doortikkend (geen klok-drift:
  de server geeft `elapsed_s` op fetch-moment, de browser telt lokaal door)
- **progressbar** t.o.v. het budget voor dat job-type ("4:32 / 15:00");
  budget overschreden → **oranje** balk + "over budget — blijft lopen"
  (waarschuwing, géén kill — fase 9.2)
- **hb Xs / limiet** — seconden sinds de laatste Dale-heartbeat, hét
  liveness-getal (groen <90s, geel ≥90s, rood ≥ stall_limit)
- **status** (running / stalled / done / timeout / failed) — afgeronde jobs
  blijven ~2,5 min zichtbaar met eindduur
- **schatting** "verwacht ~X:XX" op basis van het gemiddelde van eerdere
  done-jobs van hetzelfde type uit `nova_job_events.jsonl`

## Endpoint

`GET http://127.0.0.1:8000/jobs/active` (orchestrator, CORS `*` — dashboard
draait als `file://`). Respons:

```json
{
  "ok": true,
  "server_time": "2026-06-11T17:16:35",
  "active": [
    {
      "job_id": "chat_test_sleep_...", "job_type": "test_sleep",
      "project_id": "sf1", "status": "running",
      "started_at": "2026-06-11T17:16:30",
      "elapsed_s": 5.2, "max_wait_s": 900,
      "last_heartbeat_age_s": 4.0, "stall_limit_s": 120,
      "over_budget": false, "avg_duration_s": 209.0
    }
  ],
  "recent": [ { "...": "idem + duration_s + ended_ago_s" } ],
  "avg_duration_s_by_type": { "pixellab_generate": 594.5 }
}
```

Bronnen server-side (`_scan_job_events_for_timer` in orchestrator `main.py`):

1. `nova_job_events.jsonl` — dispatch/running = start, completion = einde,
   `event_type=heartbeat` = levensteken, `step_done` houdt de pipeline-ouder levend
2. `nova_job_heartbeats.json` — compact heartbeat-bestand van Dale (goedkoop pollen)
3. Dale result-bestanden (`NOVA_renders/*.result.json`) — fallback voor
   pipeline-stappen zonder eigen completion-event

Dashboard pollt elke 3s; timers en heartbeat-leeftijden tikken elke 1s lokaal door.

## Getest

- `godot_validate` (sync, 8s) → verschijnt in "recent klaar" met eindduur
- `test_sleep` 90s/20min → timer loopt op, heartbeat-leeftijd reset elke 60s,
  na afloop eindduur zichtbaar
- `no_heartbeat`-job → hb-teller loopt op, status wordt `stalled` (rode pill)
- bestaande panelen (agents, parts, geleerde regels, jury) onaangetast

Zie ook `fase9_2_heartbeat.md` voor het onderliggende liveness-mechanisme.
