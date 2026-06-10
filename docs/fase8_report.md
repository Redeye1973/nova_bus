# FASE 8 — INTEGRITEITS-FIXES (Z1–Z7 + N1 + FIX 7 PDOK)

**Datum:** 2026-06-11 (~00:00–00:30)
**Baseline:** git-tag `fase7-baseline` (43b39ab) → start-tag `fase8-start`; eind-tag `fase8-integriteit-compleet`.
**Bron van de zwaktes:** `L:\ZZZZZ ZZ 31-05-2026\nova_betrouwbaar\fase7\SABOTAGE_RAPPORT.md`
**Regressie-bewijs (JSON):** `docs/fase8_evidence/` — `regress_a.json` (FIX 1/2/3/6), `regress_fix4.json`, `regress_fix5.json`, `regress_fix7.json`, `health_eind.json`.
**Eind-health:** **15/15 groen** (8000/8101/8111/8116/8129/8136–8142/8170/8191/8500), `_all_green: true`.

> **Eerlijke noot — gecrashte eerdere poging:** vóór deze run was er een eerdere fase 8-poging
> die mid-way crashte (Dale lag eruit, haar eigen `fase8_regressie.json` toonde Z4/Z7 = FAIL).
> Die poging liet residu achter: een al-gepatcht `agent_38` (FIX 5-code, ongecommit), testprojecten
> `fase8_r1_0..9` in `projects.json`, testregels in de art-bible, een verouderd/deels onjuist
> `docs/fase8_report.md` én een **prematuur geplaatste tag `fase8-integriteit-compleet`** die nog
> op de baseline-commit (43b39ab) wees — zonder dat er fixes gecommit waren. Deze run heeft dat
> residu opgeruimd, alle fixes opnieuw geverifieerd (de agent_38-patch is gereviewd, getest en als
> FIX 5 overgenomen), dit rapport vervangen en de tag verplaatst naar de echte fix-commit.
>
> **Noot parallel werk:** tijdens deze run draaide een parallelle sessie "fase 10 vlootcheck" op
> dezelfde repo (commit `aa71991`, 00:13 — agent_42 + canonical v1.2). De fase 8-commit staat daar
> netjes bovenop en raakt die bestanden niet; de eenmalig her-verschenen testprojecten in
> `projects.json` zijn vermoedelijk daaraan toe te schrijven en bij de eindopschoning verwijderd
> (eindstand geverifieerd: alleen de 3 baseline-projecten).

---

## Samenvatting

| Fix | Zwakte (fase 7) | Ernst | Bestand(en) | Regressietest | Verdict |
|---|---|---|---|---|---|
| 1 | Z1 lost-update bij parallelle /part-update | BLOKKEREND | `v2_services/agent_41_resume_agent/main.py` | 10/10 beide parts aanwezig | **PASS** |
| 2 | Z4 job_id-collisie shell-jobs | SERIEUS | `v2_services/agent_70_factory_worker/main.py` | 2 gelijktijdige jobs ≠ id | **PASS** |
| 3 | Z2 proof-replay + toekomst-timestamp | SERIEUS | `shared/proof.py` + agent_41 | ronde3-3c en 6d → 422 | **PASS** |
| 4 | Z3 gefabriceerd job-proof onzichtbaar | SERIEUS | `shared/proof.py`, agent_70, `infrastructure/services/agent_11_monitor/main.py` | nep-job INVALID + Monitor flagt in sweep 1 | **PASS** |
| 5 | Z5 agent-38 non-atomische auto_fix | SERIEUS | `infrastructure/services/agent_38_quality_inspector/main.py` | tempdir crash-sim: origineel intact + .bak | **PASS** |
| 6 | Z6 stille art-default + Z7 substring-dedup | COSMETISCH | agent_41 | 4d/4e herhaald | **PASS** |
| 7 | Agent 13 PDOK: dood endpoint + stille jaargang | — (nieuw in opdracht) | `v2_services/agent_13_pdok_downloader/main.py` | kaartblad 17cz2 + jaargang-regel | **PASS** |
| N1 | Monitor ziet alleen gemounte paden | COSMETISCH | `docs/fase8_n1_monitor_mount_paden.md` | gedocumenteerd, fix later | gedocumenteerd |

---

## Per fix: oude reproductie-uitkomst vs nieuwe uitkomst

### FIX 1 — Z1 lost-update (BLOKKEREND)

**Oud (fase 7, ronde 5c):** 2 threads gelijktijdig `/part-update` voor partA/partB van hetzelfde project, 10 herhalingen → **10/10 keer één part verloren** (read-modify-write zonder lock; `os.replace` beschermt per save, niet tegen lost updates).

**Fix:** `filelock.FileLock` (multi-proces-veilig; `pip install filelock` in `L:\Nova\agent_env`) als `STATE_LOCK` op `projects.json.lock`. ALLE load-modify-save-paden van agent 41 — `/part-update` én `/feedback` (incl. bible-append) — draaien volledig binnen de lock. Fallback naar `threading.Lock` als filelock ontbreekt.

**Nieuw (regress_a.json → fix1_z1_lost_update):** 10/10 reps beide parts aanwezig, alle 20 updates HTTP 200.

```json
{"geslaagd": "10/10", "PASS": true,
 "reps": [{"rep": 0, "status_a": 200, "status_b": 200, "both_present": true}, "... 9 idem ..."]}
```

### FIX 2 — Z4 job_id-collisie (triviaal)

**Oud (ronde 5a):** 2 shell-jobs binnen 1 seconde → beide `shell_1781126787` (`int(time.time())`, seconde-resolutie).

**Fix:** `job_id = f"shell_{time.time_ns()}"` in Dale `_execute_shell`; ook de queue-fallback `job-{int(time.time())}` → `time.time_ns()`.

**Nieuw (regress_a.json → fix2_z4_job_id):** gelijktijdige jobs → `shell_1781129410946084000` ≠ `shell_1781129410945766700` (zelfde seconde, ns-resolutie, uniek).

### FIX 3 — Z2 proof-replay + versheid

**Oud (ronde 3c/6d):** oud geldig file-proof (2026-06-05) van een ONGERELATEERD bestand bij een nieuwe taak → **HTTP 200, pct=100 valse voltooiing**; timestamp jaar 2099 → geaccepteerd.

**Fix:** nieuwe functie `proof.verify_proof_for_task()` die `/part-update` (agent 41) bij elke completed_task-claim gebruikt:
- **(a) versheid:** timestamp > now+5min (toekomst) of ouder dan 24u → weigeren;
- **(b) taak-binding:** proof.path/id/note/agent moet project/part/taak refereren (tokens ≥4 tekens), of het file-pad ligt onder de geregistreerde project-outputmap; anders `proof_not_bound_to_task`.

**Bewuste ontwerpkeuze:** de versheids-/bindingscheck zit in een aparte submissie-functie en NIET in het generieke `verify_proof` — anders zou de Monitor alle legitiem-oude proofs in de historische registry vals-positief gaan flaggen. De spec vroeg "verify_proof aanpassen"; dit is functioneel hetzelfde gat gedicht, zonder de Monitor te breken (gevalideerd: agents 38/40-proofvormen passeren de binding, replay niet).

**Nieuw (regress_a.json → fix3_z2_replay):**

```json
{"replay_status": 422, "replay_reason": "timestamp_too_old:132.2h",
 "future_status": 422, "future_reason": "timestamp_in_future",
 "unbound_status": 422, "unbound_reason": "proof_not_bound_to_task",
 "geen_nep_projecten_in_state": true, "PASS": true}
```

### FIX 4 — Z3 gefabriceerd job-proof

**Oud (ronde 3b):** `{"type":"job","id":"nep_job_99999"}` in nova_proofs.jsonl → `verify_proof OK`; 35 Monitor-sweeps flagden het nooit.

**Fix (drie onderdelen):**
1. `shared/proof.py`: job-proofs zijn alleen geldig als hun id voorkomt in het job-events-grootboek (`nova_job_events.jsonl`, sibling van de proofs-registry — pad klopt dus óók in containers via `/nova_status`). Grootboek onleesbaar → gedegradeerd accepteren (geen vals-positieven), gelogd in checks.
2. Dale registreert elke voltooide shell-job nu zelf in het grootboek (`record_job_event`), zodat ook direct-/invoke-jobs cross-checkbaar zijn (voorheen schreef alleen de orchestrator job-events).
3. Monitor: bovenop de random steekproef worden per sweep ALLE recente job-proofs gecontroleerd → detectie is deterministisch binnen 1 sweep i.p.v. steekproef-geluk. Containers `agent-11-monitor` en `agent-38` herbouwd + herstart.

**Scope-notitie (eerlijk):** report-proofs blijven adviserend (alleen id/path-aanwezigheid). Ze koppelen aan een verplicht rapportbestand zou agents 38/39/40 breken; ze worden niet als voltooiings-claim bij /part-update gebruikt (daar geldt FIX 3). Gedocumenteerd als bewuste restbeperking.

**Nieuw (regress_fix4.json):**

```json
{"verify_proof": {"ok": false, "reason": "job_id_not_in_ledger", "id": "nep_job_fase8b_99999"},
 "sweeps": [{"sweep": 1, "fake_geflagd": true, "reason": "job_id_not_in_ledger"}],
 "geflagd_binnen_sweep": 1, "nep_entry_verwijderd": true, "PASS": true}
```

### FIX 5 — Z5 agent-38 atomic write + backup

**Oud (ronde 2c, structureel):** `fix_layer_ordering`/`fix_parallax_speeds` schreven met `path.write_text()` — crash mid-patch truncate het scenebestand zonder rollback.

**Fix:** `_atomic_write_with_backup()`: eerst `.bak`-kopie, dan schrijven naar `.tmp`, dan `os.replace`. (Code was al aanwezig uit de gecrashte eerdere poging; deze run heeft hem gereviewd — geen directe `write_text` meer buiten de helper — getest en het container-image daadwerkelijk herbouwd.)

**Nieuw (regress_fix5.json, dummy-scene in tempdir, NIET onder game output):** crash gesimuleerd tussen tmp-write en replace →

```json
{"crash_tussen_write_en_replace": {"crash_gesimuleerd": true, "origineel_intact": true,
  "bak_aanwezig": true, "bak_is_origineel": true},
 "normale_fix": {"gepatcht": true, "bak_is_origineel": true},
 "parallax_speeds_fix": {"gepatcht": true, "bak_is_origineel": true}, "PASS": true}
```

### FIX 6 — Z6 (stille art-default) + Z7 (substring-dedup)

**Oud (ronde 4d):** `/feedback` met onzin asset-type (`qzx_volstrekte_onzin_type_999`) → regel belandde **stil in de art-bible**.
**Nieuw:** geen keyword-match → `needs_review: true`, entry in `status\feedback_needs_review.jsonl`, **geen** bible-write. (regress_a → fix6_z6: `art_bible_ongewijzigd: true`, `needs_review_log_entry: true`.)

**Oud (ronde 4e):** dedup met substring-`in`: "RACE regel uniek 1" geweigerd als duplicaat van "…uniek 1X" (19/20).
**Nieuw:** dedup op de exacte YAML-regel (`regel: "<volledig-gequoteerde scalar>"`). Korte variant gaat er nu naast de lange in; exact duplicaat blijft geweigerd. (regress_a → fix6_z7: lange + korte toegevoegd, exact duplicaat `duplicate: true`, `PASS: true`.)

### FIX 7 — Agent 13 PDOK Downloader: OGC API + jaargang-regel

**Situatie:** agent 13 was in fase 4 **gearchiveerd** (`_archief\v2_services\agent_13_pdok_downloader`). Voor deze fix **teruggehaald** naar `v2_services\` (gedocumenteerd hierbij) en gestart als host-uvicorn op **poort 8113** (bewust niet toegevoegd aan de 15-koppige actieve kern/startup-keten; op afroep startbaar).

**a) Endpoints:** geen `brt.kadaster.nl`- of hardcoded `download.pdok.nl/kadaster/basisvoorziening-3d`-paden meer in de agent; alles loopt via `https://api.pdok.nl/kadaster/3d-basisvoorziening/ogc/v1`. (De download-zips zelf komen via de `enclosure`-links die de API teruggeeft — dat is de actuele, door PDOK aangeleverde locatie.) Nieuwe actie `download_kaartblad` voor de CityJSON-collecties `basisbestand_gebouwen_terreinen` (alias "volledig") en `basisbestand_gebouwen` (alias "gebouwen"), items-filter `?bladnr=<kaartblad>`.

**b) Jaargang-regel:** vóór elke download worden de daadwerkelijk beschikbare jaargangen per kaartblad+collectie opgevraagd (`jaargang_luchtfoto` per feature); gekozen wordt `max(beschikbaar)` — nooit een default of hardcoded jaartal. Beide staan in het job-resultaat (`beschikbare_jaargangen`, `gekozen_jaargang`, `jaargang_bron`) én in de agent-log.

**c) Override:** request-parameter `jaargang` (reproduceerbare bakes); een niet-beschikbare jaargang wordt geweigerd met de beschikbare lijst in de foutmelding.

**Technische noot:** PDOK's CA-keten faalt de Python 3.13+ `VERIFY_X509_STRICT`-controle ("Basic Constraints of CA cert not marked critical"); de agent gebruikt een SSL-context zonder die strict-vlag — certificaatverificatie zelf blijft aan.

**Regressietest (regress_fix7.json), kaartblad 17cz2 (Hoogeveen):**

```json
{"volledig_default": {"status": 200,
  "beschikbare_jaargangen": [2018, 2019, 2020], "gekozen_jaargang": 2020,
  "jaargang_bron": "max_beschikbaar", "zip_size_bytes": 261349771,
  "cityjson_validatie": {"valid": true, "methode": "volledige_parse",
    "version": "1.0", "cityobjects": 3234, "vertices": 3319041},
  "proof_ok": true, "gekozen_is_max": true},
 "gebouwen_default": {"gekozen_jaargang": 2020, "cityjson_validatie": {"valid": true}},
 "override_2019": {"status": 200, "gekozen_jaargang": 2019, "jaargang_bron": "request_override"},
 "override_onbeschikbaar_2099": {"status": 400, "geweigerd": true,
  "detail": "jaargang 2099 niet beschikbaar voor kaartblad '17cz2'; beschikbaar: [2018, 2019, 2020]"},
 "PASS": true}
```

**Expliciete notitie (zoals gevraagd):** de meest recente CityJSON-jaargang voor kaartblad **17cz2 is 2020** — ouder dan verwacht. Dat is een **PASS** (criterium = max van wat de API biedt), maar: nieuwere jaargangen (2022+) van de 3D Basisvoorziening worden door PDOK **niet meer per kaartblad** maar per **kilometergrid-blad** gepubliceerd (bv. bladnr `228000_526000`, jaargang 2022 — zichtbaar in de bbox-queryresultaten van de handmatige test van vandaag). Wie ná 2020 wil, moet dus op bbox/km-grid zoeken i.p.v. kaartbladcode; de oude "stilzwijgend 2018" kwam doordat het handmatige script de kléínste zip pakte i.p.v. de nieuwste jaargang.

Gedownloade data staat onder `L:\! 2 Nova v2 OUTPUT !\pdok_3d\` (zips + uitgepakte CityJSON, met file-proof in de registry).

### N1 — Monitor ziet alleen gemounte paden

Alleen gedocumenteerd (fix later): `docs/fase8_n1_monitor_mount_paden.md` — probleem, waarom nu acceptabel (game-output is gemount; FIX 3 verifieert submissies host-side), en twee kleine fix-opties (host-side her-verificatie heeft de voorkeur).

---

## Afronding & verificatie

- **Volledige regressieset opnieuw gedraaid** na alle fixes: FIX 1/2/3/6 (regress_a), FIX 4, FIX 5, FIX 7 → **alles PASS**. (Eén her-run-artefact gefixt: de Z7-test was niet idempotent — duplicaat van zijn éígen eerdere testregel, precies wat de dedup hoort te doen; test nu met unieke run-id.)
- **Opschoning testresidu:** testprojecten (incl. `fase8_r1_0..9` van de gecrashte eerdere poging) uit `projects.json` (→ 3 baseline-projecten), art-bible terug naar baseline (1 legitieme regel), feedback_log hersteld, 244 test-proofentries verwijderd (6 legitieme agent_13-proofs behouden), needs_review-testlog verwijderd.
- **Eind-health: 15/15 groen** (`docs/fase8_evidence/health_eind.json`), `projects.json` stabiel op de 3 baseline-projecten; agent 13 (8113) draait en is gezond.
- **Synchronisatie:** de slapende `infrastructure/services/agent_41_resume_agent`-kopie is gelijkgetrokken met de canonieke host-versie (fase 6-les: geen drift tussen kopieën).
- **Git:** wijzigingen gecommit op `L:\!Nova V2`, tag **`fase8-integriteit-compleet`**.

## Eindoordeel

Alle in fase 7 gevonden zwaktes Z1–Z7 zijn gefixt en regressie-getest tegen hun originele sabotage-reproductie; N1 is gedocumenteerd; agent 13 draait op de nieuwe PDOK OGC API met afgedwongen jaargang-regel. Daarmee zijn de blokkades voor **parallel bouwen** (Z1, Z2, Z3, Z4, Z5) weggenomen: NOVA is nu klaar voor de SM Part 1-bouw, inclusief parallelle part-updates.
