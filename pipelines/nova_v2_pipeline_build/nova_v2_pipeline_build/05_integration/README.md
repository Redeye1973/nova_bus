# Fase 5: Integration Tests (4 prompts)

## Doel

Test dat alle agents samen als pipeline werken voor echte scenarios:

- **Prompt 33**: End-to-end Sprite Pipeline Test
- **Prompt 34**: End-to-end GIS Pipeline Test
- **Prompt 35**: End-to-end Story Pipeline Test
- **Prompt 36**: Cross-agent Integration Test

## Wat elke test doet

### Test 33: Sprite Pipeline
Input: concept voor nieuwe enemy ship  
Chain: Design Fase → FreeCAD → Blender → Aseprite → PyQt5 → Godot
Output: bruikbaar game asset in Godot project
Duration: 15-30 min per run
Expected: alle agents passeren, output kwaliteit acceptabel

### Test 34: GIS Pipeline
Input: Hoogeveen coordinates + zone of interest
Chain: PDOK Downloader → QGIS Processor → Blender Baker → 3D Model Jury
Output: terrain mesh bruikbaar voor alien planet
Duration: 30-60 min per run (afhankelijk van area size)
Expected: geldige topologie, performance OK

### Test 35: Story Pipeline  
Input: nieuwe scene idee (bv. Rex Varn dialogue)
Chain: Prompt Director → Story Text Integration → Narrative Jury → ElevenLabs Audio → Audio Jury
Output: gecanoniseerde tekst + voice audio
Duration: 5-15 min per run
Expected: canon consistent, voice matches character

### Test 36: Cross-agent Integration
Input: volledige content batch voor één mission
Chain: Orkestreert 15+ agents parallel/sequentieel
Output: complete mission asset package
Duration: 1-3 uur
Expected: monitor detects all agents, cost guard tracks correct, error agent handles eventuele failures

## Na Fase 5

- Complete NOVA v2 pipeline geverifieerd werkend
- Deployment rapport gegenereerd
- Klaar voor Black Ledger package start

## Tijd

13-18 uur Cursor werk, 2-3 dagen.

## Tussenresultaat: Final Report

Na Fase 5, Cursor genereert:
`L:\!Nova V2\docs\v2_deployment_report_final.md`

Met:
- Welke agents active/fallback/failed
- Integration test resultaten
- Performance metrics
- Bekende issues
- Aanbevelingen voor Black Ledger fase
