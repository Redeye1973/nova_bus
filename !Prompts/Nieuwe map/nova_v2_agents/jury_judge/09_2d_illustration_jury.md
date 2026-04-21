# 09. 2D Illustration Jury Agent

## Doel
Beoordeelt 2D illustraties, UI art, concept art uit GIMP/Krita/Inkscape.

## Scope
- UI elementen voor games
- Concept art
- Marketing illustraties
- Vector art uit Inkscape
- Textures voor 3D models

## Jury Leden

**1. Color Harmony Detector**
- Tool: Python color theory + Ollama
- Checkt: palette werkt samen, niet clashing colors
- Gebruikt color wheel analysis

**2. Composition Validator**
- Tool: Ollama vision
- Checkt: rule of thirds, focal points, balance
- Output: composition score + suggestions

**3. Contrast Detector**
- Tool: Python analysis
- Checkt: readability op verschillende schermgroottes
- Belangrijk voor UI (kleine thumbnails)

**4. Edge Quality Reviewer**
- Tool: Ollama + pattern detection
- Checkt: crisp lines (indien gewenst) of intentional rough
- Detecteert: AI-blur artifacts, compression issues

**5. Negative Space Analyzer**
- Tool: Python image analysis
- Checkt: niet overladen, breathing room
- Mass/space balance

**6. Asset Separation Validator**
- Tool: Python + layer analysis
- Voor game assets: lagen correct, transparency right
- Checkt .xcf, .kra, .psd structure

## Judge

**2D Judge**
- UI art: contrast en readability prioritair
- Concept art: composition en mood
- Marketing: polish en appeal

## Cursor Prompt

```
Bouw een NOVA v2 2D Illustration Jury:

1. Python service `2d_jury/color_harmony.py`:
   - Input: image file
   - Extract dominant colors (k-means clustering)
   - Analyze color wheel relationships (analogous/complementary/triadic)
   - Ollama review
   - Output: {harmony_score, palette_type, clashes: []}

2. Python service `2d_jury/composition.py`:
   - Ollama vision analysis met composition principles
   - Detect focal points via saliency (OpenCV)
   - Check rule of thirds alignment
   - Output: {composition_score, focal_points: [], balance}

3. Python service `2d_jury/contrast_checker.py`:
   - Multiple scales thumbnail generation
   - Contrast ratio calculation per scale
   - WCAG compliance check voor UI
   - Output: {readability_scores: {16px, 32px, 64px, 128px}}

4. Python service `2d_jury/edge_quality.py`:
   - Edge detection analysis
   - Detect blur artifacts (AI signature)
   - Detect JPEG compression patterns
   - Output: {edge_quality_score, issues}

5. Python service `2d_jury/negative_space.py`:
   - Detect empty vs filled regions
   - Calculate mass distribution
   - Output: {breathing_room_score, overcrowded_areas}

6. Python service `2d_jury/asset_separation.py`:
   - Parse PSD/XCF/KRA files
   - Check layer structure
   - Verify transparency, naming conventions
   - Output: {layer_valid, missing_layers, issues}

7. Python service `2d_jury/illustration_judge.py`:
   - Context-aware verdict per asset type
   - Output: {verdict, tier: "portfolio|production|draft", feedback}

8. N8n workflow met auto-sort naar folders

Gebruik Python 3.11, PIL, OpenCV, psd-tools, gimpformats,
Ollama Qwen VL, FastAPI.
```

## Test Scenario's

1. Clean game UI icon → production-ready
2. Concept art met goede composition → portfolio
3. Cluttered illustration → revise (negative space)
4. AI-blur artifacts zichtbaar → reject
5. PSD zonder layer separation voor game → revise

## Success Metrics

- Contrast readability: 95%+ accurate at 16px
- Composition issues detection: > 80%
- AI-artifact detection: > 85%
