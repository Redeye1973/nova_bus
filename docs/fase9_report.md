# FASE 9 — Orchestrator dispatch-fix (afronding)

**Datum:** 2026-06-11 (~14:50)  
**Diagnose:** `docs/fase9_diagnose.md`  
**Regressie-bewijs:** `L:\ZZZZZ ZZ 31-05-2026\nova_betrouwbaar\fase9\fase9_regressie.json`  
**Fase 8-bewijs:** `docs/fase8_evidence/regress_a.json`, `health_eind.json`  
**Dispatch-log:** `L:\!Nova V2\status\nova_dispatch_log.jsonl`  
**Bridge canonical:** poort **8500** (NSSM); `bridge_heartbeat.py` / `bridge_watchdog.py` default bijgewerkt van 8501 → 8500.

---

## Diagnose-samenvatting

Kernprobleem: `_infer_job_from_text` matchte `valideer godot` maar niet `valideer SM_Part1`. Geen parser-match → `no_dispatch` (eerlijk, maar geen job). Zie `fase9_diagnose.md` voor volledige keten.

**Herstart-diagnose (deze run):** fase 8-regressies faalden initieel omdat agent 41 (8141) en 42 (8142) niet luisterden (host-uvicorn gestopt na eerdere kill-test). Na herstart: alle regressies groen.

---

## Fix-beschrijving (`L:\Nova\1 Orchestrator\main.py`)

1. **`_infer_work_action_dispatch`** — `valideer`+projectcontext → `godot_validate` bridge-job.
2. **`needs_clarification`** — uitvoerbare/vage opdracht zonder parser → expliciete terugvraag (geen stil `no_dispatch`).
3. **`nova_dispatch_log.jsonl`** — `_log_dispatch_decision()` op dispatch/clarify/weiger.
4. **`_ACTION_WORDS`** — `doe ` toegevoegd voor vage werk-opdrachten.
5. **`_DALE_FAILURE_STATUSES`** — `needs_clarification` toegevoegd (geen valse "gedaan").

---

## Fase 8-regressies (fix1/2/3) — oud vs nieuw

| Fix | Fase 7 sabotage | Nieuw (`regress_a.json`) |
|-----|-----------------|--------------------------|
| fix1 Z1 lost-update | 10/10 part verloren | **PASS** — 10/10 beide parts, HTTP 200 |
| fix2 Z4 job_id | identiek `shell_<sec>` | **PASS** — `shell_1781182144186556600` ≠ `shell_1781182144186271300` |
| fix3 Z2 replay | HTTP 200 valse voltooiing | **PASS** — replay/future/unbound alle 422 |
| fix6 Z6 onzin asset | stil in art-bible | **PASS** — `needs_review`, bible ongewijzigd |
| fix6 Z7 dedup | substring false positive | **PASS** — exacte dedup, beide regels in bible |

Volledige Z1–Z7 suite (`fase8_regressie.json`): `all_held: true`.

---

## Regressietests dispatch — oud vs nieuw

### T1 — `valideer SM_Part1`
| | Oud (fase7 ronde 1.10) | Nieuw (2026-06-11) |
|--|------------------------|---------------------|
| dale_status | `no_dispatch` | `done` |
| dale_job_id | `""` | `chat_godot_validate_1781182223` |
| Bewijs | geen | job-proof + `nova_job_events.jsonl` |

### T2 — Audit jobs 4–6
| Job | Oud (audit) | Nieuw |
|-----|-------------|-------|
| 4 GDScript pipeline | godot_ai failed / geen chain | `pipeline_1781182240` **done** |
| 5 Aseprite | niet uitgevoerd | `shell_1781182240789730000` **done** |
| 6 Jury | niet uitgevoerd | `shell_1781182261974001100` **done** |

### T3 — `doe het ding met de dinges`
| | Oud | Nieuw |
|--|-----|-------|
| dale_status | `no_dispatch` | `needs_clarification` |
| dale_job_id | `""` | `""` |
| Claim | geen valse done | geen done, expliciete onduidelijkheid |

### T4 — Dale kill mid-job
| | Verwacht | Nieuw |
|--|----------|-------|
| mid_status | failed | `failed` |
| claimed_done | false | `false` |

### T5 — Fase 8-regressieset
`all_held: true`, `health_green: true`.

---

## Bridge-poort consolidatie

| Item | Was | Nu |
|------|-----|-----|
| NSSM bridge service | 8500 | 8500 (ongewijzigd) |
| `bridge_heartbeat.py` default | 8501 | **8500** |
| `bridge_watchdog.py` default | 8501 | **8500** |
| `canonical_endpoints.yaml` | preferred 8500 | changelog bijgewerkt |
| 8501 listener | niet actief | niet actief (verwacht) |

Verificatie: `curl http://127.0.0.1:8500/health` → HTTP 200.

---

## Git-tags (`L:\!Nova V2`)

- `fase8-integriteit-compleet` — op fix-commit (062442a/rapport 45efd1b)
- `fase9-dispatch-compleet` — op afronding-commit (rapport + bridge + verse regressiebewijs)

---

## Productie-gate eindoordeel

**JA** — poort fase 8+9 formeel groen.

| Criterium | Status | Bewijs |
|-----------|--------|--------|
| Health actieve kern | **15/15 groen** | `docs/fase8_evidence/health_eind.json` (`_all_green: true`) |
| Fase 8 fix1/2/3 | **PASS** | `docs/fase8_evidence/regress_a.json` |
| Fase 9 dispatch T1–T5 | **HELD** | `fase9_regressie.json` (`all_held: true`) |
| Bridge canonical 8500 | **OK** | health 200; scripts + yaml bijgewerkt |
| Git-tags | **gezet** | `fase8-integriteit-compleet`, `fase9-dispatch-compleet` |

**Reden JA:** Integriteit-laag (fase 8) regressie-getest; dispatch vertaalt productie-opdrachten naar echte Dale/bridge-jobs met `job_id` en proof; eerlijkheid bij infra-falen behouden; onzin → `needs_clarification`; bridge-poort éénduidig 8500.
