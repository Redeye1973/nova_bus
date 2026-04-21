# 27. Storyboard Visual Agent

## Doel
Panel-based storyboard generation voor narrative visualization. Surilians scenes, Black Ledger cinematics, marketing materialen.

## Scope
- Panel layout (traditional comic / storyboard grid)
- Character posing per panel
- Camera angle variaties
- Action flow visualization
- Consistency tussen panels (same character = same appearance)

## Jury (5 leden, zwaar - consistency is cruciaal)

**1. Panel Composition Specialist**
- Tool: Ollama Qwen VL + Python
- Checkt: rule of thirds, focal points, visual flow
- Detecteert: cluttered composition, weak focal point

**2. Character Consistency Validator**
- Tool: Ollama + embedding similarity
- Compare character across panels
- Check: same character recognizable (face, costume, proportions)
- Alert bij character drift tussen panels

**3. Action Flow Analyzer**
- Tool: Ollama + sequence analysis
- Check: eye movement natural left-to-right (Western) or appropriate direction
- Verify: action continues logically tussen panels
- Detect: confusing camera jumps

**4. Camera Variety Checker**
- Tool: Python + Ollama
- Analyze shot types per panel (wide, medium, close-up)
- Check: variety appropriate voor scene
- Detect: monotonous framing

**5. Canon Visual Consistency**
- Tool: Qdrant + Ollama
- Compare tegen Surilians visual references
- Check: ships look like Surilians ships, characters like canon descriptions
- Integration met Story Text Integration (28)

## Judge

- Publish: ready voor use
- Revise: specific panels herwerken
- Rewrite: sequence doesn't work, herontwerp
- Reject: fundamenteel probleem

## Cursor Prompt

```
Bouw NOVA v2 Storyboard Visual Agent:

1. Python service `storyboard/panel_generator.py`:
   - FastAPI POST /panels/generate
   - Input: {scene_description, panel_count, style}
   - Option A: AI generation via API (Midjourney, DALL-E voor concepts)
   - Option B: Template-based composition met bestaande assets
   - Output: panel PNG images + layout JSON

2. Python service `storyboard/layout_manager.py`:
   - Arrange panels in comic/storyboard grid
   - Handle variable panel sizes (key moments bigger)
   - Gutters, bleed area, reading order
   - Output: composite storyboard PNG

3. Python service `storyboard/composition_specialist.py`:
   - Jury member 1
   - Ollama Qwen VL vision analysis
   - Rule of thirds detection
   - Focal point analysis
   - Output: composition score per panel

4. Python service `storyboard/character_consistency.py`:
   - Jury member 2
   - Extract character crops per panel
   - Embed via CLIP or similar
   - Cosine similarity tussen same character across panels
   - Flag drift > threshold

5. Python service `storyboard/action_flow.py`:
   - Jury member 3
   - Ollama reads panel sequence
   - Check narrative flow coherent
   - Detect confusing jumps

6. Python service `storyboard/camera_variety.py`:
   - Jury member 4
   - Classify shot type per panel (OpenCV + Ollama)
   - Check variety across sequence
   - Flag monotony

7. Python service `storyboard/canon_checker.py`:
   - Jury member 5
   - Qdrant search Surilians visual library
   - Compare panels met canon references
   - Flag visual inconsistencies

8. Python service `storyboard/storyboard_judge.py`:
   - Aggregate 5 jury scores
   - Weight consistency heavily
   - Output verdict + panel-specific feedback

9. Integration with Aseprite:
   - If pixel art storyboard: use Aseprite Processor
   - If illustration: use GIMP/Krita Processor (35)
   - If photorealistic: use 2D Illustration chain

10. N8n workflow + Surilians asset library setup

Gebruik Python 3.11, FastAPI, Ollama, Qdrant, CLIP voor embeddings,
PIL voor composition, OpenCV voor analysis.
```

## Asset reuse strategie

Voor consistency:
- Character model sheets per main character
- Reference images voor factions
- Ship references uit game assets
- Pose library for common actions

Panel generatie hergebruikt deze waar mogelijk. Voorkomt "nieuwe" character in elk panel.

## Panel types

**Establishing shot:** wide, context, location
**Character moment:** medium-close, expression focus
**Action panel:** dynamic angle, motion lines/effects
**Detail shot:** close-up, important object/gesture
**Reaction panel:** character response to prior action
**Splash panel:** full-page impact moment

Agent kan suggest panel type based op scene needs.

## Integration met Aseprite Animation Jury (24)

Als storyboard animated wordt (bv. voor game cutscene):
- Individual panels → Aseprite frames
- Animation Jury valideert smoothness
- Aseprite Processor handelt polish

## Test Scenario's

1. Surilians Chapter 3 scene → 6 panel storyboard
2. Black Ledger cinematic sequence → action flow validation
3. Character drift detectie: zelfde character met andere features
4. Canon violation: ship looks wrong voor Surilians lore

## Success Metrics

- Character consistency detection: > 85%
- Canon violation detection: > 80%
- Composition scoring agreement met human: > 75%
- Panel flow accuracy: > 80%

## Output

Per storyboard:
- Individual panel PNG files
- Composite storyboard PNG (all panels together)
- JSON metadata (panel types, character present, camera angles)
- Quality report per panel

## Integratie

- Werkt met Story Text Integration (28) voor canon check
- Uses Character Art Jury (08) voor character-level quality
- 2D Illustration Jury (09) voor overall visual quality
- Output door Distribution Agent (19) naar consumers
