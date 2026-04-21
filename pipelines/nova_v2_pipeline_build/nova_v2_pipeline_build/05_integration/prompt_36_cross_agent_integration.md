# Prompt 36: Cross-Agent Integration Test

## Wat deze prompt doet

Test de complete NOVA v2 pipeline onder realistische load. Alle 32 agents aan het werk tegelijkertijd voor één "content batch".

## Voorwaarden

- [ ] Prompts 33, 34, 35 compleet en PASS
- [ ] Alle 32 agents plus 01 = 33 total active of fallback
- [ ] Monitor (11) kan alle agents zien
- [ ] Error (17) kan auto-repair triggeren

## De prompt

```
Voer complete cross-agent integration test uit.

DOEL: Valideer dat NOVA v2 als systeem werkt, niet alleen losse agents.

TEST CASE: "Content Batch voor één hypothetische game mission"
- Asset productie (sprite pipeline)
- Terrain generation (GIS pipeline)
- Story content (narrative pipeline)
- Audio voor scene (audio pipeline)
- Alles parallel waar mogelijk
- Cost tracking actief
- Monitor observeert alles
- Error agent vangt eventuele problemen

STAP 1: INFRASTRUCTURE HEALTH
Verify alle containers running:
ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose ps --format json" | ConvertFrom-Json

Verwacht: 33+ containers "Up" status.

STAP 2: START MONITORING
POST http://178.104.207.194:5680/webhook/monitor
Body: {"action": "start_session", "test_id": "integration_test_36"}

Verwacht: monitor session ID.

STAP 3: PARALLEL ASSET TASKS
Start 3 parallel tasks:

Task A: Sprite pipeline
POST webhook/design-fase → webhook/freecad-parametric → webhook/blender-render → ...
(Zie prompt 33 chain)

Task B: Terrain pipeline  
POST webhook/pdok-download → webhook/qgis-process → ...
(Zie prompt 34 chain)

Task C: Story pipeline
POST webhook/prompt-direct → webhook/story-integration → ...
(Zie prompt 35 chain)

Alle 3 tasks parallel via PowerShell Start-Job.

STAP 4: MONITOR DURING EXECUTION
Elke 30 seconden:
GET http://178.104.207.194:5680/webhook/monitor?action=status

Log observations:
- Welke agents actief
- Response times
- Memory/CPU usage (indien monitor agent metrics heeft)
- Errors gedetecteerd

STAP 5: COST TRACKING
GET http://178.104.207.194:5680/webhook/cost-track?period=test_36

Verwacht: report van API calls gemaakt (ElevenLabs, eventuele Meshy als gebruikt).

STAP 6: ERROR INJECTION (OPTIONEEL)
Test Error Agent door kunstmatige fout te injecteren:
POST http://178.104.207.194:5680/webhook/error-handler
Body: {
  "simulate_error": true,
  "error_type": "timeout",
  "target_agent": "agent_22"
}

Verwacht: Error Agent detecteert, probeert auto-repair, escalleert indien nodig.

STAP 7: WACHT OP COMPLETION
Alle 3 parallel tasks voltooien (kan 30-90 min duren).

STAP 8: VALIDATIE OUTPUT
- Task A output: sprite in Godot formaat
- Task B output: terrain mesh
- Task C output: dialog + audio
- Alle drie moeten geldig zijn voor downstream use

STAP 9: DISTRIBUTION AGENT
POST http://178.104.207.194:5680/webhook/distribute
Body: {
  "content_batch": {
    "sprites": "<task A output>",
    "terrain": "<task B output>",
    "story": "<task C output>"
  },
  "target": "test_package"
}

Verwacht: gepackaged deliverable (zip of folder).

STAP 10: FINAL REPORT
Schrijf L:\\!Nova V2\\docs\\v2_deployment_report_final.md:

# NOVA v2 Pipeline - Final Deployment Report

**Datum**: <timestamp>
**Test duration**: <totale tijd>

## Agent Status Summary
| Agent | Status | Notes |
|-------|--------|-------|
| 01 Sprite Jury | active | POC mode |
| 02 Code Jury | active | |
| ... voor alle 33 agents

## Integration Test Results
- Test 33 (Sprite): PASS/PARTIAL/FAIL
- Test 34 (GIS): PASS/PARTIAL/FAIL
- Test 35 (Story): PASS/PARTIAL/FAIL
- Test 36 (Cross-agent): PASS/PARTIAL/FAIL

## Performance Baseline
- Avg response time per agent
- Pipeline throughput
- Memory usage peak
- Concurrent capacity

## Bekende Issues
- <lijst met priorities>

## Cost Summary
- ElevenLabs API calls: <count>
- Andere API costs: <bedragen>
- Totaal $ gebruik voor tests: <bedrag>

## Fallback Mode Agents
- <lijst met reden waarom fallback>
- Plan voor upgrade naar full versie

## Aanbevelingen voor Black Ledger Fase
- Welke agents klaar voor productie werk
- Welke agents eerst upgraden
- Welke dependencies (Ollama modellen, externe tools) installeren
- Tailscale setup verifiëren

STAP 11: COMPLETE STATUS
Update alle status files naar "phase_1_complete"
Create: L:\\!Nova V2\\status\\pipeline_complete.json

STAP 12: COMMIT + TAG
git add docs/ status/
git commit -m "test: integration test 36 complete - NOVA v2 pipeline ready"
git tag v2.0.0-pipeline-complete
git push --tags

RAPPORT:
Toon uitgebreide summary:
- Totaal agents actief
- Integration tests resultaten
- Ready for Black Ledger package
- Aanbevolen next steps

Dit is laatste prompt van dit package. Volgende: BLACK LEDGER PACKAGE (apart).
```

## Verwachte output

- `docs/v2_deployment_report_final.md` compleet
- `status/pipeline_complete.json`
- Git tag v2.0.0-pipeline-complete
- Alle logs voor analyse bewaard

## Success criteria

- Alle 3 parallel tasks voltooien zonder crashes
- Monitor detecteert correcte agent activiteit
- Cost tracking werkt
- Error agent kan simulated error handlen
- Distribution agent packaget alles samen

## Als dit PASS is

Je hebt een volledig werkende NOVA v2 pipeline. Klaar voor:

**Volgende package: Black Ledger MVP**

Die zal bevatten:
- Vertical slice definitie  
- Werkende Black Ledger eerste speelbare versie
- Gebruikt alle agents uit deze pipeline
- Iteratieve content productie

## Als dit FAIL is

Niet erg. Analyseer welke agents bottleneck zijn:
- Fix die eerst in losse sessies
- Re-run prompt 36 later
- Ga daarna door naar Black Ledger package
