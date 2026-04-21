# Prompt 33: End-to-End Sprite Pipeline Test

## Wat deze prompt doet

Test volledige asset pipeline van concept naar Godot-ready sprite. Valideert dat alle 8 agents in de chain samenwerken.

## Voorwaarden

- [ ] Fase 1-4 compleet (alle 32 agents gebouwd)
- [ ] Fase 1 agents active: 20, 02, 21, 22, 23, 25, 26 + 01 (bestaand)
- [ ] Monitor + Error agents (11, 17) active

## De prompt

```
Voer end-to-end sprite pipeline integration test uit.

DOEL:
Test dat volledige chain werkt voor één concept ship:
Design Fase (20) → FreeCAD (21) → Blender (22) → Aseprite (23) → Sprite Jury (01) → PyQt5 (25) → Godot Import (26)

TEST CASE: "Generic Fighter Ship"
- Geen specifieke game context (wordt Black Ledger specific in later package)
- Neutral design, validates pipeline technisch werkt
- Output moet bruikbaar zijn als placeholder

STAP 1: VOORBEREIDING
- Check alle 8 agents status via status/*.json
- Identificeer eventuele fallback_mode agents
- Log test start naar logs/integration_test_33_YYYY-MM-DD.log

STAP 2: DESIGN FASE AANROEPEN
POST http://178.104.207.194:5680/webhook/design-fase
Body: {
  "theme": "industrial_neutral",
  "faction_count": 3,
  "restrictions": {"max_colors": 32}
}

Verwacht: palette response met 32 kleuren.
Bewaar palette voor volgende stappen.

STAP 3: FREECAD PARAMETRIC
POST http://178.104.207.194:5680/webhook/freecad-parametric
Body: {
  "category": "fighter",
  "dimensions": {"length": 10, "width": 8, "height": 3},
  "mount_points_config": {"wings": 2, "engines": 1, "cockpit": 1}
}

Verwacht: STEP file path response.
Als FreeCAD niet op host: mock response met placeholder pad.

STAP 4: BLENDER GAME RENDERER
POST http://178.104.207.194:5680/webhook/blender-render
Body: {
  "step_file": "<van stap 3>",
  "rotation_frames": 8,  # Reduced voor test speed
  "damage_states": ["pristine"]
}

Verwacht: render output path met 8 PNGs.
Als Blender niet op host: mock met placeholder sprites.

STAP 5: ASEPRITE PROCESSOR
POST http://178.104.207.194:5680/webhook/aseprite-process
Body: {
  "source_folder": "<van stap 4>",
  "palette": "<van stap 2>",
  "output_folder": "./test_output/fighter_ship/"
}

Verwacht: processed sprite sheet + metadata JSON.

STAP 6: SPRITE JURY (01) VALIDATIE
POST http://178.104.207.194:5680/webhook/sprite-review-poc
Body: {
  "sprite_sheet_path": "<van stap 5>",
  "metadata": "<van stap 5>"
}

Verwacht: verdict accept/revise/reject.
Als reject: log reden, test gefaald.

STAP 7: PYQT5 ASSEMBLY
POST http://178.104.207.194:5680/webhook/pyqt-assembly
Body: {
  "source_folder": "<van stap 5>",
  "output_format": "godot_sprite_frames"
}

Verwacht: .tres bestand path + sprite sheet.

STAP 8: GODOT IMPORT
POST http://178.104.207.194:5680/webhook/godot-import
Body: {
  "asset_path": "<van stap 7>",
  "asset_type": "enemy_sprite",
  "project_root": "./test_godot_project/"
}

Verwacht: complete .tscn scene met script + imports.

STAP 9: VALIDATIE GODOT PROJECT
- Check dat generated .tscn valid Godot syntax heeft
- Check dat alle referenced assets bestaan
- Optioneel: run godot --headless --check-only (als Godot op host)

STAP 10: RAPPORT
Schrijf L:\\!Nova V2\\docs\\integration_test_33_report.md:

# Test 33: Sprite Pipeline End-to-End

**Datum**: <timestamp>
**Duur**: <minuten>

## Agent Status per Stap
- [x/✗] Agent 20 Design Fase: <status>
- [x/✗] Agent 21 FreeCAD: <status>
- [x/✗] Agent 22 Blender Game Renderer: <status>
- [x/✗] Agent 23 Aseprite Processor: <status>
- [x/✗] Agent 01 Sprite Jury: <status>
- [x/✗] Agent 25 PyQt5 Assembly: <status>
- [x/✗] Agent 26 Godot Import: <status>

## Output Kwaliteit
- Palette generated: yes/no
- Sprite sheet: readable/unreadable
- Godot project: loads/fails

## Fallback Modes Gebruikt
- <lijst van agents die fallback mode draaiden>

## Bottlenecks
- Slowest agent: <naam> (<duur>)
- Blocking issues: <lijst>

## Verdict
- PASS: alle stappen succesvol
- PARTIAL: sommige fallback modes maar pipeline werkt
- FAIL: kritieke stap mislukt

## Volgende Stappen
- Fix failed agents in aparte sessies
- Upgrade fallback agents naar full versie (Ollama integration)
- Continue naar prompt_34_end_to_end_gis_pipeline.md

STAP 11: COMMIT
git add docs/integration_test_33_report.md logs/integration_test_33*
git commit -m "test: integration test 33 sprite pipeline - <PASS/PARTIAL/FAIL>"

RAPPORT:
Toon in chat:
- Test 33 resultaat
- Duur
- Aantal failed agents
- Volgende: prompt 34
```

## Verwachte output

- Complete test rapport in docs/integration_test_33_report.md
- Test artifacts in test_output/fighter_ship/
- Voorbeeld Godot project met imported sprite
- Log entries voor elke agent call

## Success criteria

**PASS**: alle 7 agents in chain responden, output bruikbaar
**PARTIAL**: fallback modes maar chain compleet
**FAIL**: minstens 1 kritieke stap mislukt

## Volgende prompt

`05_integration/prompt_34_end_to_end_gis_pipeline.md`
