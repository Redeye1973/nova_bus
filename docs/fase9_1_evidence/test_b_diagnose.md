# FASE 9.2 — Diagnose vóór de liveness-fix

Datum: 2026-06-11 · door Cursor (infra-werk)

## 1. Werkelijke duur van de drie pixellab_generate jobs (T2 parallax bewijsrun)

Geen van de jobs is gekilld. Alle drie zijn natuurlijk afgelopen; duur gemeten
door Dale zelf (result-bestanden in `NOVA_renders/`). Details + conclusie in
`pixellab_werkelijke_duur.json` (zelfde map).

| job_id | start | einde | duur | Dale-status |
|---|---|---|---|---|
| chat_pixellab_generate_1781189552631311000 | 16:52:34 | 17:02:35 | 10:01 | done |
| chat_pixellab_generate_1781189565696579700 | 16:52:48 | 17:02:49 | 10:01 | done |
| chat_pixellab_generate_1781189892737937900 | 16:58:20 | 17:08:02 | 09:41 | done |

Kern: PixelLab generate duurt werkelijk **~10 minuten** per laag. Het oude
orchestrator-plafond binnen de pipeline (timeout_s 220 + 30 = 250s) kapte dus
gezonde jobs af terwijl Dale gewoon doorwerkte — exact het "duurt lang ≠ is
dood"-probleem. De derde job gaf op API-niveau `generation_failed`
(PixelLab response-validatie-error), maar dat is een los PixelLab-issue, geen
timing-issue; de job zelf rondde netjes af.

Empirische basis voor de limits:
- heartbeat-interval 60s → stall_limit pixellab 300s = 5 gemiste heartbeats
- budget 900s blijft ruim boven de echte ~600s → alleen oranje waarschuwing

## 2. Waarom was test_b_run2.log leeg?

`test_b_run2.log` is **niet permanent leeg** — het bestand bevat nu het
volledige resultaat van run 2 (`pipeline_1781189892737389400`, geschreven
17:02:24, identiek aan `test_b_pixellab.json`). Verklaring van de lege
waarneming:

- Run 2 is om **16:58:12 wél gestart** (zie `nova_job_events.jsonl`: event
  `source=chat`, `dale_job_id=pipeline_1781189892737389400`).
- Het testscript schrijft zijn log **pas bij afronding** (write-at-end, geen
  streaming). Tussen 16:58 en 17:02 bestond het bestand al wel maar was het
  0 bytes.
- De waarneming "run2 leeg" viel precies in dat venster. Geen crash, geen
  output elders — alleen uitgestelde write.

Conclusie: run 2 is normaal gestart en afgerond (met FAIL-verdict door het
oude timeout-mechanisme, final_status=timeout na 250s per pixellab-stap).
De FAIL is het bewijs van het mechanisme-probleem dat fase 9.2 oplost, niet
van een crash.
