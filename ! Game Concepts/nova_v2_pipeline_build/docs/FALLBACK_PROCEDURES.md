# Fallback Procedures

Elke agent heeft een fallback mode zodat pipeline build niet blokkeert op één probleem.

## Fallback filosofie

**Primair doel**: agent klaar krijgen tot webhook responsief is.
**Secundair doel**: volledige AI-powered capability.

Als secundair niet lukt: fallback mode met deterministische logic, markeer voor latere upgrade.

## Fallback modes per agent type

### Jury agents (02, 03, 04, 05, 06, 07, 08, 09, 10, 24, 30)

**Full mode**: Ollama-powered review met vision/language models
**Fallback**: Regel-gebaseerde checks zonder AI

Voorbeeld Code Jury:
- Full: Ollama Qwen 9B reviewt code kwaliteit, stijl, security
- Fallback: ast.parse + pycodestyle + bandit (geen AI maar werkend)

Status file markeer: `"fallback_mode": true, "reason": "ollama_not_available"`

### Operational agents (11, 12, 13, 14, 15, 16, 17, 18, 19)

**Full mode**: alle externe tools beschikbaar (PDOK API, QGIS, Blender, etc)
**Fallback**: mock responses met cached data

Voorbeeld PDOK Downloader:
- Full: live PDOK API call, download AHN4 tiles
- Fallback: return cached tiles uit test data directory

Status: `"fallback_mode": true, "reason": "pdok_api_unreachable"`

### Extension agents (21, 22, 23, 25, 26, 27, 28, 29, 31, 32, 33, 34, 35)

**Full mode**: desktop tool (Blender/FreeCAD/etc) via subprocess of bridge
**Fallback**: placeholder output met correct metadata

Voorbeeld FreeCAD Parametric:
- Full: FreeCAD headless python genereert .FCStd, export STEP
- Fallback: return placeholder STEP bestand met correct metadata JSON

## Wanneer fallback accepteren

### Acceptabel voor pipeline progression

- Tool niet op host geïnstalleerd (bv. QGIS niet op jouw PC)
- API rate limit hit (ElevenLabs, Meshy)
- Ollama model nog niet gedownload
- Netwerk issue tijdelijk

### NIET acceptabel, moet opgelost worden

- Security fout (skip quality check = risico)
- Core infra down (PostgreSQL, Redis)
- V1 geraakt
- Data corruption

## Fallback recovery

Na pipeline build compleet, recover fallback agents:

```powershell
# Lijst van fallback agents
Get-ChildItem "L:\!Nova V2\status\agent_*_status.json" | ForEach-Object {
    $s = Get-Content $_.FullName | ConvertFrom-Json
    if ($s.fallback_mode -eq $true) {
        Write-Host "FALLBACK: Agent $($s.agent_number) - $($s.notes)"
    }
}

# Per agent upgrade plan:
# 1. Install missing tool
# 2. Test tool werkt
# 3. Re-run pipeline prompt voor die agent
# 4. Verify status flipt naar full mode
```

## Fallback strategieën per kritieke dependency

### Ollama niet beschikbaar

**Impact**: alle jury agents met AI review, storyboard, narrative
**Fallback**: deterministische checks (syntax, format, size)
**Recovery**: 
- Start Ollama service op PC
- `ollama pull qwen2.5-coder:9b`
- `ollama pull llama3.2-vision:3b`
- Re-deploy affected agents

### Blender niet beschikbaar

**Impact**: agent 22 (Game Renderer), 14 (Baker), 33 (Architecture)
**Fallback**: placeholder PNG/GLB outputs
**Recovery**:
- Install Blender 4.x
- Add to PATH or nova_config.yaml
- Test: `blender --version`
- Re-deploy Blender agents

### FreeCAD niet beschikbaar

**Impact**: agent 21 (Parametric), 06 (CAD Jury)
**Fallback**: skip parametric, gebruik placeholder STEP
**Recovery**:
- Install FreeCAD 1.x
- Add to PATH
- Test: `freecad --console -c "print('ok')"`
- Re-deploy

### Aseprite niet beschikbaar

**Impact**: agents 23, 24
**Fallback**: Pillow-based pixel art approximation (niet hetzelfde als Aseprite)
**Recovery**:
- Install Aseprite (paid tool, heb jij al)
- Add to PATH
- Test: `aseprite --help`
- Re-deploy

### QGIS niet beschikbaar

**Impact**: agents 15, 31
**Fallback**: GDAL direct (geen GUI workflows)
**Recovery**:
- Install QGIS 3.x
- Add `qgis_process` to PATH
- Test: `qgis_process list`
- Re-deploy

### GRASS GIS niet beschikbaar

**Impact**: agent 32
**Fallback**: SciPy-based approximations (minder accuraat)
**Recovery**:
- Install GRASS GIS 8.x
- Create default location
- Re-deploy

### GIMP/Krita/Inkscape niet beschikbaar

**Impact**: agent 35
**Fallback**: Pillow voor basic raster, cairosvg voor basic vector
**Recovery**:
- Install de tools
- Python bridges configureren
- Re-deploy

### ElevenLabs API key missing

**Impact**: agent 29 (Audio Generation)
**Fallback**: offline TTS via pyttsx3 (veel lagere kwaliteit)
**Recovery**:
- Get API key van elevenlabs.io
- Add to .env als `ELEVENLABS_API_KEY=...`
- Re-deploy

### Meshy credits op

**Impact**: optionele reference model generation
**Fallback**: gebruik FreeCAD parametric ipv Meshy
**Recovery**:
- Top up credits OF
- Accept dat parametric altijd primair is
- Meshy blijft "nice to have"

## Partial fallback

Sommige agents kunnen deels werken:

**Agent 20 Design Fase**:
- Palette generation: werkt zonder AI (color theory)
- Consistency check: vereist Qdrant + Ollama (fallback: color histogram)

Status in JSON:
```json
{
  "agent_number": 20,
  "status": "active",
  "fallback_mode": true,
  "partial_capabilities": {
    "palette_create": "full",
    "palette_validate": "full",
    "silhouette_check": "full",
    "consistency_check": "fallback_color_histogram"
  }
}
```

## Fallback tracking in deployment report

Final report moet duidelijk maken:
- Welke agents full mode
- Welke fallback (met reden)
- Plan per fallback voor upgrade
- Urgentie per upgrade

Dit bepaalt volgorde voor fix-sessions.

## Edge case: alle fallbacks accepteren?

Als infrastructure kapot raakt midden in build:
- Skip stap, markeer "infrastructure_unavailable"
- Continue met volgende agents
- Na herstel infrastructure: return naar skipped agents

Pipeline progressie belangrijker dan perfect deployment.

## Post-pipeline: validatie

Na alle 36 prompts compleet:
1. Run `utils/agent_validator.py --check-fallbacks`
2. Output: lijst met "agents_in_fallback_mode"
3. Per fallback: reden + upgrade path
4. Prioritize upgrades:
   - High: blockers voor Black Ledger critical path
   - Medium: quality impact maar niet blocker
   - Low: nice-to-have optimizations
