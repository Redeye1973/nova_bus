# Testing Checklist

Master checklist voor elk type test in NOVA v2 pipeline build.

## Per prompt test levels

### Level 1: Syntax/Build check
- [ ] Python files parseren zonder errors
- [ ] requirements.txt bevat alle imports
- [ ] Docker build succeeds

### Level 2: Unit tests
- [ ] pytest slaagt lokaal
- [ ] Minimaal 4 tests
- [ ] Dekking: happy path + edge case + error case + integration

### Level 3: Container test
- [ ] Container start zonder crash
- [ ] /health endpoint respond 200
- [ ] Logs tonen geen critical errors

### Level 4: Deploy test
- [ ] Container draait op Hetzner
- [ ] Docker compose ps toont "Up"
- [ ] Port bereikbaar via docker network

### Level 5: N8n integration
- [ ] Workflow geïmporteerd
- [ ] Workflow active
- [ ] Webhook path correct

### Level 6: End-to-end
- [ ] Webhook respond met expected shape
- [ ] Response time < 30s voor eenvoudige calls
- [ ] Error handling werkt

## Per fase test levels

### Na Fase 1
- [ ] Asset pipeline test: concept → sprite (via test 33)
- [ ] Code review werkt voor Python + GDScript
- [ ] Monitor observeert 8+ agents

### Na Fase 2
- [ ] Narrative canon search werkt
- [ ] GIS downloads + processes Hoogeveen data
- [ ] Combined story + asset pipeline mogelijk

### Na Fase 3
- [ ] Audio generation + review chain
- [ ] Cost tracking registreert API calls
- [ ] Storyboard generation van text → visual

### Na Fase 4
- [ ] Full bake pipeline (PDOK → final GLB)
- [ ] CAD + 3D model validatie werkt
- [ ] Distribution agent packaget correct

### Na Fase 5
- [ ] Alle 4 integration tests PASS of PARTIAL
- [ ] Deployment report compleet
- [ ] Pipeline klaar voor productie werk

## Black Ledger specific tests (straks, in volgende package)

Deze tests KOMEN in volgende package (Black Ledger MVP):
- Ship component generation werkt
- Enemy sprite batch generation mogelijk
- Mission text generation gecanoniseerd
- Voice acting pipeline functioneel
- Complete asset batch voor 1 level in <2 uur

## Kwaliteitscriteria

### Wat "PASS" betekent per test type

**Unit test PASS**: pytest exit code 0, alle tests groen
**Container test PASS**: 15s na start geen crash, healthcheck OK
**Webhook test PASS**: status code 200, response schema valid
**Integration test PASS**: alle stappen succesvol, output bruikbaar

### Acceptabele fallbacks

Een agent in fallback mode mag "PASS" zijn als:
- Fallback output is valid
- Upgrade path is gedocumenteerd
- Niet in critical path voor huidige fase

Unacceptabele fallbacks (moet fix):
- Security checks skipped
- Data integrity compromised
- V1 dependency gebroken

## Test automatisering

Run alle tests met één command:

```powershell
# Quick health check
.\utils\status_check.ps1

# Agent validation
python utils\agent_validator.py --all --verbose

# Full integration tests (duurt lang, gebruik als nightly)
# ALTIJD na een fase compleet is, voor doorgaan
```

## Te vermijden

**DON'T**:
- Skip tests om "sneller te zijn"
- Accept fails zonder documentatie
- Deploy tests overslaan
- V1 raken tijdens V2 tests

**DO**:
- Test per level
- Documenteer fallbacks
- Commit tussen tests
- Backup voor grote stappen

## Test rapport

Elke fase eindigt met test rapport:

```markdown
# Fase X Test Rapport

## Agents
- Built: X/Y
- Active: X/Y  
- Fallback: X/Y
- Failed: X/Y

## Tests
- Unit tests: X/Y passed
- Integration tests: X/Y passed
- Performance: OK/Degraded

## Issues
- [lijst met prioriteit]

## Ready for next phase: YES/NO
```

Commit deze rapporten in `docs/` directory.
