# SESSIE 08 — Pipeline Integraties (OPTIONEEL — Fase F)

**Doel:** End-to-end pipelines testen en wire-up.
**Tijd:** 90-120 min
**Afhankelijkheden:** 07 compleet

Test pipelines:
- Shmup pipeline (20 → 21 → 22 → 23 → 24 → 25 → 01 → 26)
- Bake pipeline (13 → 15 → 31 → 32 → 14 → 04 → 05 → 19)
- Story pipeline (28 → 07 → 27 → 08 → 09 → 29 → 30)

---

### ===SESSION 08 START===

```
SESSIE 08 — Pipeline integraties Fase F.

Voor elk van 3 pipelines:
1. Maak master N8n workflow die sub-workflows chained
2. Test met dummy input
3. Meet: latency, success rate, jury-scores
4. Log naar docs/pipeline_<n>_report.md

## Shmup pipeline test
Input: dummy enemy concept ("red fighter ship, small")
Expected flow: design → FreeCAD model → Blender render → Aseprite polish →
  animation jury → sprite assembly → sprite jury → Godot import
End state: Godot-ready sprite sheet

## Bake pipeline test
Input: Hoogeveen postcode 7901
Expected flow: PDOK download → QGIS process → QGIS analysis → GRASS →
  Blender bake → 3D jury → GIS jury → Distribution
End state: glTF tiles in MinIO

## Story pipeline test
Input: dummy scene outline "Cathleen ontmoet Thael in Geode lab"
Expected flow: Story integration (canon lookup) → Narrative jury →
  Storyboard visuals → Character art jury → 2D illustration jury →
  [optional ElevenLabs] → Audio asset jury

Rapport: docs/session_08_report.md
Tag: v2.0-pipelines-active

git commit -m "session 08: pipelines F integrated"
```

### ===SESSION 08 EINDE===

---

# SESSIE 09 — Backup + Rapport + Hand-off (OPTIONEEL — Fase G)

**Doel:** Productie-klaar maken.
**Tijd:** 45-60 min

---

### ===SESSION 09 START===

```
SESSIE 09 — Backup + productie hand-off.

## Backup configureren
Cron op Hetzner:
- Daily 02:00: pg_dump + upload naar MinIO /backups/
- Daily 03:00: MinIO snapshot naar externe bucket (Hetzner S3)
- Weekly Sunday 04:00: full .env + config backup

## Build report
File: docs/V2_BUILD_COMPLETE_REPORT.md
Volledig overzicht:
- 30 agents gepland, X active, Y failed, Z stub
- Pipelines F status
- Cost report (totaal build API spending)
- Known issues
- Roadmap Fase H (DAZ + Ren'Py)

## Shared state update
- current_baseline.md → V2 is productie
- decisions.md → architectuur log
- to_build.md → alleen failed agents + Fase H

## Git tagging
git tag -a v2.0-production -m "NOVA v2 production baseline"
git push origin v2.0-production

Print "NOVA V2 BUILD COMPLETE"
```

### ===SESSION 09 EINDE===

---

# SESSIE 10 — Fase H: DAZ + Ren'Py Agents (WEEKEND)

**Doel:** 6 nieuwe agents voor VN pipeline.
**Tijd:** 4-6u verdeeld over weekend

Nieuwe agents:
- 36 Ren'Py Export Agent
- 37 VN Branch Consistency Jury
- 38 DAZ Orchestrator
- 40 Prompt Craftsman
- 41 DAZ Scene Creator
- 42 DAZ Freebies Hunter
- 43 Character Model Maker + Identity Registry

Plus bridge adapter 006 voor DAZ.

---

### ===SESSION 10 START===

```
SESSIE 10 — Fase H uitbreiding (6 agents + DAZ bridge adapter).

Voorwaarden:
- DAZ Studio geïnstalleerd op PC
- DAZ license geactiveerd (één keer handmatig)
- Genesis 9 base essentials beschikbaar
- Bridge draait volledig (niet recovery mode)

## Stap 1: Bridge adapter 006 DAZ
In L:\!Nova V2\bridge\nova_host_bridge\app\adapters\daz_adapter.py:
- detect DAZStudio.exe locatie
- endpoint POST /tools/daz/render
  input: .dsa script content + output_dir
  action: subprocess "DAZStudio.exe -noPrompt -scriptArg <temp>.dsa"
  output: resulting PNG paths

## Stap 2: Agent 38 DAZ Orchestrator
v2_services/daz_orchestrator/
- Leest character + scene profiles uit Postgres
- Jinja2 templates voor .dsa generatie
  (templates in /templates/expression_set.dsa.j2, /templates/cg_scene.dsa.j2)
- Roept bridge /tools/daz/render aan
- Wacht op output
- Registreert PNG's in nova_assets tabel
- Triggert Character Art Jury (08) voor validatie

## Stap 3: Agent 43 Character Model Maker + Identity Registry
v2_services/char_model_maker/
Postgres tabel:
CREATE TABLE character_identity (
  character_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  character_name TEXT NOT NULL,
  project TEXT NOT NULL,
  base_figure TEXT,
  face_morph_hash TEXT,
  body_morph_hash TEXT,
  hair_asset TEXT,
  hair_color TEXT,
  eye_color TEXT,
  skin_tone TEXT,
  identity_hash TEXT UNIQUE,
  twin_of UUID REFERENCES character_identity(character_id),
  created_at TIMESTAMP DEFAULT NOW(),
  duf_path TEXT
);

Logic:
- POST /character → check identity_hash conflict
  - exact match blocked (except twin)
  - soft match >90% → waarschuwing
  - clean → create .duf + register

## Stap 4: Agent 41 DAZ Scene Creator
Input: scene requirement (description + characters + mood)
Output: .dsa file die Agent 38 kan renderen
Logic:
- Asset library scan (uit DAZ content path)
- Selecteer environment match
- Plaats characters
- Camera framing heuristiek
- Belichting setup per mood

## Stap 5: Agent 42 DAZ Freebies Hunter
Cron dagelijks (N8n schedule):
- Scrape DAZ3D weekly, Render-State, ShareCG, Renderosity
- License parse (regex patterns voor CC licenses)
- Filter GREEN/YELLOW/RED
- Auto-download GREEN naar L:\DAZ Library\Nova\
- Notificatie naar Alex (Monitor agent webhook)

Postgres:
CREATE TABLE daz_assets (
  asset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source TEXT NOT NULL,
  name TEXT NOT NULL,
  url TEXT,
  license_class TEXT CHECK (license_class IN ('GREEN','YELLOW','RED')),
  license_text TEXT,
  downloaded BOOLEAN DEFAULT false,
  downloaded_path TEXT,
  discovered_at TIMESTAMP DEFAULT NOW()
);

## Stap 6: Agent 36 Ren'Py Export Agent
Genereert .rpy files uit story bible + scene outputs
Template-driven: Jinja2 per scene-type (dialog, CG, choice)
Output: volledig Ren'Py project structure

## Stap 7: Agent 37 VN Branch Consistency Jury
Checks Ren'Py .rpy files voor:
- Dangling labels
- Unreachable routes
- Save-variable consistency
- Romance flag coherence

## Stap 8: Agent 40 Prompt Craftsman
Input: scene outline + bible context
Output: Sudowrite-ready prompts
Uses Claude API of lokale Qwen 72B (na RTX)

## Rapport
docs/session_10_report.md
Git tag v2.1-faze-h

Print "FASE H COMPLETE — DAZ + VN pipeline ready"
```

### ===SESSION 10 EINDE===

---

## Volgorde advies Fase H

Binnen sessie 10 zelf, sub-volgorde:
1. Bridge adapter 006 (DAZ connection)
2. Agent 38 Orchestrator (meest fundament)
3. Agent 43 Character Registry (nodig voor andere)
4. Agent 41 Scene Creator
5. Agent 42 Freebies Hunter (lose van rest, kan parallel)
6. Agent 36 Ren'Py Export
7. Agent 37 Branch Consistency
8. Agent 40 Prompt Craftsman

Als sessie 10 te lang: split in 10a (bridge + 38 + 43 + 41) en 10b (42 + 36 + 37 + 40).
