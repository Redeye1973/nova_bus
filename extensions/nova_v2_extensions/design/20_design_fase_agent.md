# 20. Design Fase Agent

## Doel
Genereert en valideert style bibles, color palettes, en concept designs voor nieuwe producten. Zorgt voor visuele consistentie voor productie begint.

## Scope
- Style bible generation
- Color palette management (master palette per product)
- Concept sheet generation per asset
- Silhouette validatie
- Design consistency bewaking

## Jury (3 leden, medium)

**1. Palette Coherence Validator**
- Tool: Python + color theory library
- Checkt: palette kleuren werken samen, factie-kleuren onderscheidbaar
- Detecteert: clashing colors, te donker/te licht

**2. Silhouette Clarity Reviewer**
- Tool: Ollama Qwen VL 7B + Python silhouette extractie
- Checkt: ontwerp herkenbaar op doelgrootte (32x32 voor shmup)
- Test pure silhouette zonder kleur

**3. Style Consistency Specialist**
- Tool: Ollama + Qdrant vector search
- Checkt: nieuw concept past bij bestaande assets van zelfde faction
- Vergelijkt met reference library

## Judge

- Accept: ready voor productie
- Revise: specifieke verbeter-punten
- Reject: concept werkt niet, herontwerp

## N8n Workflow

```
Webhook trigger: nieuw concept voorgelegd
    ↓
Input: palette + concept sheet + silhouette sketch
    ↓
Parallel jury (3x)
    ↓
Judge + feedback
    ↓
Accept → Save naar design library (Qdrant)
Revise → Feedback naar designer
Reject → Clear rejection rationale
```

## Cursor Prompt

```
Bouw NOVA v2 Design Fase Agent:

1. Python service `design/palette_manager.py`:
   - FastAPI POST /palette/create
   - Input: theme, faction_count, restrictions
   - Generate 32-color master palette via color theory
   - Use colorthief + colormath libraries
   - Faction sub-palettes auto-generated
   - Output: palette.yaml compatible met Aseprite + Blender

2. Python service `design/palette_validator.py`:
   - FastAPI POST /palette/validate
   - Check: contrast ratios adequate
   - Check: faction colors distinguishable (delta-E > 15)
   - Check: no clashing adjacents
   - Output: {valid, issues: [], suggestions: []}

3. Python service `design/silhouette_checker.py`:
   - FastAPI POST /silhouette/check
   - Input: concept image
   - Extract silhouette (background removal)
   - Render op doelgrootte (32x32, 64x64)
   - Ollama vision: recognizable?
   - Output: {recognizable_at_sizes: {}, weak_features: []}

4. Python service `design/consistency_checker.py`:
   - FastAPI POST /consistency/check
   - Qdrant similarity search
   - Compare nieuw concept tegen faction reference library
   - Output: {consistent, outlier_aspects: [], reference_samples: []}

5. Python service `design/concept_generator.py`:
   - CLI tool voor design sheet templates
   - Jinja2 templates per asset type (ship, building, character)
   - Auto-fill faction colors from palette
   - Output: markdown design sheet

6. Python service `design/design_judge.py`:
   - Aggregate 3 jury scores
   - Verdict logic
   - Specific feedback generation

7. N8n workflow + docker setup

Gebruik Python 3.11, FastAPI, Qdrant, Ollama Qwen VL, PIL, colormath.
```

## Integratie

- Output wordt gebruikt door alle asset pipelines (ship, building, character)
- Qdrant library wordt opgebouwd over tijd
- Palette file referenced door Aseprite, Blender, PyQt5 agents

## Test Scenario's

1. Nieuwe Corporate fighter concept → validate against Corporate reference
2. Palette voor nieuwe game → check distinguishability
3. Silhouette te complex → revise with simplification advice

## Success Metrics

- Palette coherence accuracy: > 90% (tegen human judgment)
- Silhouette leesbaarheid op 32x32: > 95% correct
- Consistency drift detection: > 80%

## Integratie met bestaande agents

- Feedt Sprite Jury (01) met reference palettes
- Werkt samen met 2D Illustration Jury (09)
- Design library in Qdrant herbruikt door andere agents
