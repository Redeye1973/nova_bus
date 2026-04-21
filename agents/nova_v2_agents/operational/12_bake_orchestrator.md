# 12. Bake Orchestrator Agent

## Doel
Coördineert het volledige bake-proces voor city packages. Van PDOK download tot gevalideerde, gedistribueerde asset package.

## Scope
- Trigger en coördinatie van bake-stappen
- Resource management (GPU allocatie, disk space)
- Progress tracking
- Failure recovery
- Version management van city packages

## Workflow Fases

**Fase 1: Preparation**
- Check resources beschikbaar (disk, GPU)
- Lock target postcode om dubbele bakes te voorkomen
- Archive previous version indien aanwezig

**Fase 2: Data Download**
- Trigger PDOK Downloader agent voor target postcode
- Parallel: BAG, BGT, AHN4, NWB
- Verify download completeness

**Fase 3: Processing**
- QGIS Processor agent doet data-bewerking
- Cleanup, reproject, filter, enrich met attributes

**Fase 4: 3D Generation**
- Blender Baker agent genereert geometry
- Asset-kit toepassing
- LOD generation (low/mid/high)

**Fase 5: Validation**
- GIS Jury validates geometry en data
- 3D Model Jury validates output meshes
- Bij fail: auto-fix attempt of escalatie

**Fase 6: Packaging**
- Compile city package met metadata
- Version tag, checksum, provenance info
- Package in gestandaardiseerd format

**Fase 7: Distribution**
- Distribution agent uploadt naar MinIO
- Updates PostgreSQL met nieuwe versie
- Notify downstream consumers (NORA, FINN)

**Fase 8: Cleanup**
- Remove temp files
- Unlock postcode
- Log completion

## N8n Workflow

```
Trigger (manual or from Monitor recommendation)
    ↓
Set: target_postcode, priority, version
    ↓
Preparation:
    - Check resources (HTTP to resource monitor)
    - Lock postcode (Redis)
    - Archive old (if exists)
    ↓
Execute: PDOK Downloader (subworkflow)
    ↓ (wait for completion)
Execute: QGIS Processor (subworkflow)
    ↓
Execute: Blender Baker (subworkflow)
    ↓
Parallel validation:
    ├─ GIS Jury
    └─ 3D Model Jury
    ↓
Merge
    ↓
IF validation failed:
    → Auto-fix attempt (max 2 tries)
    → Re-validate
    → If still failed: escalate to human
ELSE:
    → Package + version
    → Execute: Distribution agent
    ↓
Cleanup + notify
```

## Cursor Prompt

```
Bouw een NOVA v2 Bake Orchestrator:

1. Python service `bake/orchestrator.py`:
   - FastAPI POST /bake
   - Input: {postcode, priority, force_rebuild: bool}
   - Output: job_id voor tracking
   - Starts orchestration workflow
   - Tracks progress in PostgreSQL

2. Python service `bake/resource_manager.py`:
   - Check available GPU (nvidia-smi via subprocess)
   - Check disk space per storage volume
   - Lock/unlock postcodes via Redis
   - Output: {can_proceed: bool, reason: string}

3. Python service `bake/version_manager.py`:
   - Read current version of postcode in DB
   - Generate new version tag (semver: major.minor.patch)
   - Archive old version to cold storage
   - Maintain version history table

4. Python service `bake/packager.py`:
   - Input: processed data + metadata
   - Create city_package bundle:
     * geometry.glb (unified mesh)
     * layers/ (individual meshes per category)
     * metadata.json (provenance, version, sources)
     * preview.png (thumbnail render)
   - Calculate checksums
   - Output: package_path

5. Python service `bake/progress_tracker.py`:
   - Track job status in PostgreSQL
   - WebSocket endpoint voor real-time updates
   - ETA calculation based on historical times
   - Output: {job_id, phase, progress_pct, eta}

6. N8n workflow `bake_orchestrator_workflow.json`:
   - Main workflow die sub-workflows aanroept
   - Each phase is Execute Workflow node
   - Error handling with retry logic
   - Progress updates to tracking service
   - Failure escalation to human review queue

7. CLI tool `bake_cli.py`:
   - `nova-bake start --postcode 7901 --priority high`
   - `nova-bake status --job <id>`
   - `nova-bake list --active`
   - `nova-bake cancel --job <id>`
   - Connects to orchestrator API

8. Dashboard view (HTML + HTMX):
   - Active jobs with progress bars
   - Queue of pending bakes
   - Recent completions
   - Failure reasons voor review queue

9. PostgreSQL schema:
   - bake_jobs table: id, postcode, status, started, completed, duration
   - city_versions: postcode, version, created, checksum, path
   - bake_logs: job_id, phase, timestamp, message, level

Gebruik Python 3.11, FastAPI, Redis, PostgreSQL via psycopg3.
```

## Resource Limits

Max concurrent bakes: 2 (bij RTX 5060 Ti constraint)
Max disk per bake: 10GB temp
Max bake duration: 6 hours (timeout)
Retry attempts bij failure: 2

## Failure Recovery

Bij crash tijdens bake:
1. Redis lock blijft max 6 uur (auto-expire)
2. Orchestrator detecteert crashed jobs bij startup
3. Cleanup partial files
4. Mark job as failed in DB
5. Alert via monitor agent
6. Allow manual retry

## Integration Points

- **Triggered by**: Monitor agent recommendations, manual CLI, or scheduled cron
- **Triggers**: PDOK Downloader → QGIS Processor → Blender Baker → Juries → Distribution
- **Feeds data to**: NORA, FINN, other city-package consumers
- **Reports to**: Monitor agent, Cost Guard

## Success Metrics

- Bake success rate: > 90%
- Average bake time per city: < 4 hours
- Failure recovery success: > 95%
- Resource utilization: 70-80% (not starved, not overbooked)
