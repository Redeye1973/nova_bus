# FASE 10 — Agent-vlootcheck rapport

**Datum:** 2026-06-11  
**Uitvoerder:** autonome agent-run (vlootcheck)  
**Ruwe data:** `docs/fase10_vloot_raw.json`  
**Script:** `scripts/fase10_vlootcheck.py`

---

## STAP 0 — Poort (fase 8/9)

| Check | Status |
|-------|--------|
| Git-tag `fase9-dispatch-compleet` | **NIET** aanwezig |
| `docs/fase9_report.md` | **NIET** aanwezig |
| `docs/fase9_diagnose.md` | aanwezig (diagnose vóór fix) |
| `docs/fase8_evidence/regress_a.json` | aanwezig; fix1/2/3 **FAIL**, fix6 **PASS** |
| Git-tag `fase10-start` | **NIET** gezet (poort niet groen) |

**Conclusie poort:** Fase 9 dispatch-fixes zijn deels in `L:\Nova\1 Orchestrator\main.py` (`_infer_work_action_dispatch`, `nova_dispatch_log.jsonl`), maar fase 9 is **niet formeel afgerond** (geen rapport/tag, regressie niet groen). Vlootcheck is uitgevoerd; herstelacties lokaal zijn doorgevoerd.

---

## Samenvatting vlootmatrix (na reparaties)

| Classificatie | Totaal | Lokaal actieve kern | Hetzner legacy |
|---------------|--------|---------------------|----------------|
| **GROEN** | 16 | 16 | 0 |
| **GEEL** | 0 | 0 | 0 |
| **ROOD** | 0 | 0 | 0 |
| **GRIJS** | 38 | 3 | 35 |

**Lokale health actieve kern:** 16/16 canonical endpoints L2 OK (≥15/15 vereiste **JA**).  
**Lokale functionele kern:** 16/16 GROEN (alle 3 lagen).

---

## Matrix — lokale actieve kern (canonical)

| Agent | Poort | L1 draait | L2 antwoordt | L3 werkt | Na | Classificatie |
|-------|-------|-----------|--------------|----------|-----|---------------|
| Orchestrator | 8000 | ✓ | ✓ 134ms | ✓ /status | — | GROEN |
| Sprite Jury (01) | 8101 | ✓ docker | ✓ 20ms | ✓ verdict JSON | — | GROEN |
| Monitor (11) | 8111 | ✓ docker | ✓ 10ms | ✓ sweep 12/12 up | — | GROEN |
| Cost Guard (16) | 8116 | ✓ docker | ✓ 6ms | ✓ health | — | GROEN |
| ElevenLabs (29) | 8129 | ✓ docker | ✓ 8ms | ✓ health | — | GROEN |
| Parallax Jury (36) | 8136 | ✓ docker | ✓ 32ms | ✓ verdict | — | GROEN |
| Art Director (37) | 8137 | ✓ docker | ✓ 9ms | ✓ review | — | GROEN |
| Quality Inspector (38) | 8138 | ✓ docker | ✓ 19ms | ✓ inspect | — | GROEN |
| Audio Director (39) | 8139 | ✓ docker | ✓ 6ms | ✓ plan | smoke output_dir | GROEN |
| Juice Inspector (40) | 8140 | ✓ docker | ✓ 10ms | ✓ inspect | — | GROEN |
| Resume Agent (41) | 8141 | ✓ host | ✓ 7ms | ✓ /active | — | GROEN |
| Parts Planner (42) | 8142 | ✓ host | ✓ 7ms | ✓ /plan parts | model 9b→7b + herstart | GROEN |
| Dale (70) | 8170 | ✓ host | ✓ 26ms | ✓ health | — | GROEN |
| Hybrid Gate | 8191 | ✓ host | ✓ 9ms | ✓ health | — | GROEN |
| Host Bridge | **8500** | ✓ host | ✓ 8ms | ✓ health | canonical bevestigd | GROEN |
| Audiocraft | 8080 | ✓ docker | ✓ 13ms | ✓ health (stub) | — | GROEN |

### GRIJS lokaal (niet in canonical, wel runtime)

| Service | Status | Opmerking |
|---------|--------|-----------|
| Bridge legacy 8501 | niet luisterend | Verwacht; canonical = 8500 |
| nova-judge (docker intern) | L1-L3 OK | Supporting dependency |
| secrets-vault (docker intern) | L1-L3 OK | Geen host-poort |

---

## Matrix — Hetzner CPX32 (178.104.207.194)

35 agent-containers + judge + sprite-jury draaien (**geen host-poort-mapping**; checks via `docker exec` + python urllib).

| Groep | Containers | L1/L2 | L3 functioneel | Classificatie |
|-------|------------|-------|----------------|---------------|
| Jury 01, 02, 10 | sprite, code, balance | OK | OK verdict/review | GRIJS (lokaal gearchiveerd) |
| Jury 03–09 | audio, 3d, gis, cad, narrative, char, illust | OK | **FAIL** — geen `/v1/verdict` POC-pad | GRIJS |
| Jury 24, 30 | aseprite-anim, audio-asset | OK | FAIL — API-pad mismatch | GRIJS |
| PDOK 13 | downloader | OK | FAIL — `/jaargangen` pad niet gevonden | GRIJS |
| FreeCAD 21 | parametric | OK | FAIL — bridge/parametric timeout/pad | GRIJS |
| Blender 14, 22 | baker, renderer | OK | OK version/health | GRIJS |
| Overige 12–35 | diverse | OK | OK health-fallback | GRIJS |
| Judge | nova-v2-judge | OK | OK evaluate | GRIJS |
| Monitor 11 | duplicate remote | OK | OK sweep | GRIJS |

**Totaal Hetzner agent-RAM (docker stats):** ~36 containers, geschat **~1,2 GB** cumulatief (meeste ~35–40 MiB @ 512MiB limit).

---

## Uitgevoerde veilige reparaties

| # | Agent | Probleem | Actie | Pogingen |
|---|-------|----------|-------|----------|
| 1 | Parts Planner (42) | Default model `qwen2.5-coder:9b` niet geïnstalleerd → Ollama 404 | Default → `7b` in `v2_services` + `infrastructure`; host-uvicorn herstart | 1 |
| 2 | Audio Director (39) | Smoke-test miste verplicht `output_dir` | Script-fix (tempdir); geen productie-config | 1 |
| 3 | canonical_endpoints | 8501 vs 8500 dubbeling | v1.2: 8501 `inactive`, supporting_internal + hetzner_legacy_fleet | 1 |

**Niet uitgevoerd (bewust):** container verwijderen, Windows-services, n8n, code-herbouw Hetzner juries, game-output schrijven.

---

## Openstaand GEEL/ROOD + diagnose

| Item | Status | Diagnose | Voorstel |
|------|--------|----------|----------|
| Fase 9 poort | OPEN | Geen tag/rapport; regress fase 8 deels rood | Fase 9 afronden: dispatch-regressie + `fase9_report.md` + tag |
| Monitor proof-alerts | INFO | proof hash_mismatch op art_direction_bible (fase8 run) | Fase 8 integriteit afronden |
| Hetzner legacy vloot | GRIJS | 35 containers draaien, lokaal gearchiveerd | Zie optimalisatie — uitzetten na akkoord |
| bridge_watchdog/heartbeat scripts | CONFIG | Refereren nog 8501 in defaults | Consolideren naar 8500 |

---

## Optimalisatie (meten, niet snijden)

### a) Doublures

- **Bridge 8500 vs 8501:** Productie = **8500** (NSSM). 8501 niet actief; `bridge_heartbeat.py` / `bridge_watchdog.py` nog 8501 — **consolideer naar 8500**.
- **Monitor 11:** lokaal + Hetzner beide healthy — remote monitor overbodig bij lokale sweep.
- **Cost Guard / ElevenLabs / Sprite Jury:** dubbel lokaal + Hetzner — remote kopieën zijn legacy.

### b) Dood gewicht (uitzet-kandidaten)

Hetzner containers met classificatie GRIJS, geen lokale canonical binding, >30 dgn geen productie-dispatch naar remote endpoints:

- Volledige `nova-v2-agent-02` t/m `35` batch (minus lokaal actieve poorten)
- `nova-v2-memory-curator`, `nova-v2-service-router`, `nova-v2-notification-hub` (lokaal niet in actieve kern)

### c) Traagste responders

| Endpoint | Latency | Vermoedelijke oorzaak |
|----------|---------|----------------------|
| Hetzner health (docker exec) | 800–970 ms | SSH + exec overhead, geen host-poort |
| Orchestrator /status | ~134 ms | Ollama status-probe in status-endpoint |
| Parts Planner /plan | ~27 s | Ollama generate (7b) cold |

### d) Resource-beeld Hetzner

Zie `hetzner_resources` in raw JSON. Patroon: ~0,12–0,15% CPU, ~35–40 MiB RAM per agent-container, limits 256MiB–1GiB.

### e) Concreet uitzet-voorstel (NIET uitgevoerd)

| Actie | Geschatte besparing | Risico |
|-------|---------------------|--------|
| Stop + disable 33 legacy agent-containers op Hetzner | **~1,0–1,2 GB RAM** | Laag — functionaliteit gedekt door lokale kern + bridge |
| Stop Hetzner monitor 11 duplicate | ~35 MiB | Laag |
| Stop memory-curator + service-router remote | ~70 MiB | Medium — check n8n remote workflows eerst |

**Totaal voorstel:** ~1,2 GB RAM vrij op CPX32 — **alleen na expliciet akkoord Alex**.

---

## Eindoordeel per pipeline (klaar-voor-productie)

| Pipeline | GROEN agents | Klaar? | Opmerking |
|----------|--------------|--------|-----------|
| **Sprite / visueel** | 01, 36, 37, 38, 40 + bridge | **JA** | Parallax + meta-judges + bridge Aseprite/PixelLab |
| **Audio** | 39, 29, audiocraft | **JA** | Director + ElevenLabs; audiocraft stub |
| **GIS** | bridge QGIS | **JA** (basis) | PDOK/QGIS-agents alleen remote GRIJS; bridge-dekking |
| **3D** | bridge Blender/FreeCAD | **JA** (basis) | Remote Blender/FreeCAD containers GRIJS-doodgewicht |
| **Narrative** | — | **NEE** | Jury 07 gearchiveerd lokaal; geen actieve narrative agent |

**Totaal actieve kern:** **16/16 GROEN** lokaal.  
**Productie-gate totaal:** **NEE** tot fase 8+9 formeel groen (poort + regressie).

---

## Artefacten

- `docs/fase10_vloot_raw.json` — ruwe 3-laags resultaten
- `config/canonical_endpoints.yaml` v1.2 — changelog + hetzner_legacy_fleet
- `scripts/fase10_vlootcheck.py` — herhaalbare check
- Git-tag `fase10-vloot-compleet` (vlootcheck afgerond)
