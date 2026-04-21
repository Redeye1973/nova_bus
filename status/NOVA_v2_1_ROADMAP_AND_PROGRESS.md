# NOVA v2.1 — uitvoeringsplan en voortgang (stroomuitval-veilig)

**Laatst bijgewerkt:** 2026-04-21  
**Doel:** Black Ledger + NOVA v2 pipeline, met host-bridge voor tools op de Windows-host.

Na stroomuitval: open dit bestand, lees **Sessielog**, werk de checkboxes bij, ga verder waar **Niet gestart** / **Bezig** staat.

---

## GitHub (remote nog instellen)

Deze repo had **geen `origin` remote** op het moment van aanmaken van dit document. Lokaal committen gebeurt wel; voor push:

```powershell
cd "L:\!Nova V2"
git remote add origin https://github.com/<jouw-org>/<jouw-repo>.git
git push -u origin master
```

Daarna na elke sessie: `git add …`, `git commit -m "…"`, `git push`.

---

## Baseline (wat al in git zit — korte referentie)

| Onderwerp | Status | Notities |
|-----------|--------|----------|
| Host bridge + FreeCAD via bridge | Gedaan | o.a. `62cd745`, Task Scheduler auto-start |
| FreeCAD pad L: | Gedaan | `4c65354` |
| Adapters Aseprite / Krita / Blender / Godot | Gedaan | `20728d7` |
| Godot `validate_project` (exit-code / flags) | Gedaan | `15b362b` |
| User-sidecar scripts (8501) | Bestanden aanwezig | `nova_host_bridge/service/*.ps1` — registratie/verificatie nog af te ronden |
| Proxy 8500 → 8501 in FastAPI | **Niet gedaan** | Geen `sidecar`/`8501` in `.py` codebase |
| `via:user` in `nova_config.yaml` | **Niet gedaan** | Nog te ontwerpen |
| Task Bus (Postgres) | **Niet gestart** | Ontwerp volgt |

---

## Kritisch pad (fases)

### Fase 0 — Hygiëne & bridge

- [x] Host-bridge core + FreeCAD + Task Scheduler basis
- [x] Tool-adapters (Aseprite, Krita, Blender, Godot) — code
- [ ] **Sidecar:** taak registreren, na login poort **8501** bereikbaar, logfile verschijnt
- [ ] **Sidecar:** `GET /tools` (of equivalent) toont werkende Aseprite-versie
- [ ] **Smoke:** spritesheet / minimale Aseprite-job via 8501
- [ ] **Config:** `via: user` (of gelijkwaardig) voor Aseprite + Krita in `nova_config.yaml`
- [ ] **Proxy:** main bridge (8500) merged `/tools` + forward `/aseprite/*`, `/krita/*` naar 127.0.0.1:8501
- [ ] **Verify:** unified client op 8500
- [ ] Nova bridge / watcher: oude handoffs archiveren, batch2 opruimen (zoals in eerdere analyse)

### Fase 1 — Task Bus

- [ ] Postgres schema + state machine + agent-contracten (ontwerpdoc)
- [ ] Client library + POC (bv. agent 21)

### Fase 2 — Planner

- [ ] Agent 00 planner + critic

### Fase 3 — Sprite pipeline POC

- [ ] Keten 22→23→25→26 + E2E-test volgens pipeline-build prompts

### Fase 4 — Black Ledger content-infra

- [ ] Qdrant, lore JSON, paletten, MinIO (schets in lore-to-game)

### Fase 5 — Overige agenten

- [ ] Parallelle tracks volgens `PROMPT_INDEX` / dependencies

### Fase 6 — Integratie

- [ ] Prompts 33–36 (E2E pipelines)

### Fase 7 — Black Ledger implementatie

- [ ] `NOVA_BlackLedger_Lore_To_Game.md` STAP 1–9 uitvoeren

---

## Sessielog (nieuwste bovenaan)

| Datum | Wat gedaan | Wat niet / volgende |
|-------|------------|---------------------|
| 2026-04-21 | Dit roadmap + voortgangsbestand toegevoegd; sidecar-scripts klaar om mee te committen | `git remote add` + `git push`; sidecar task debuggen (8501 kwam niet omhoog); proxy in Python |

*(Voeg hier na elke werksessie een rij toe — kort en concreet.)*

---

## Stroomuitval — snelle checklist

1. `cd "L:\!Nova V2"` → `git status` → `git pull` (als remote er is)
2. Open dit bestand → laatste **Sessielog** + open checkboxes hierboven
3. Bridges: main 8500 + sidecar 8501 (Taakplanner → NOVA-taken)
4. Verder waar de eerste lege `[ ]` staat op het kritisch pad

---

## Bronnen in workspace

- Pipeline: `! Game Concepts/nova_v2_pipeline_build/…` en `pipelines/nova_v2_pipeline_build/…`
- Black Ledger lore: `! Game Concepts/! Black Ledger/`
- Host bridge: `nova_host_bridge/`
- Config: `nova_config.yaml`
