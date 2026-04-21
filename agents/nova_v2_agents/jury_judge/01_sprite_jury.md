# 01. Sprite Jury Agent

## Doel
Beoordeelt gegenereerde sprites op kwaliteit en consistentie. Eerste implementatie — bewijst jury-judge patroon.

## Scope
- 2D pixel art sprites (characters, enemies, weapons, tiles, UI elements)
- Zowel PyQt5 output als Aseprite exports
- Animaties (sprite sheets met meerdere frames)

## Jury Leden

**1. Pixel Integriteit Specialist**
- Tool: Python + PIL (geen AI nodig voor deze check)
- Checkt: palette adherence, transparantie correctness, geen kapotte pixels, geen edge artifacts
- Output: score 0-10, kapot / mogelijk kapot / ok

**2. Silhouette Leesbaarheid Specialist**
- Tool: Ollama Qwen 2.5 VL 7B
- Checkt: herkenbaarheid op kleine schaal, duidelijke vorm, onderscheidbaar van achtergrond
- Prompt: "Analyseer dit sprite silhouet. Is de vorm herkenbaar op 32x32 pixels? Geef score 0-10 en korte uitleg."

**3. Animation Flow Specialist** (alleen voor animated sprites)
- Tool: Python + PIL + Moondream 2
- Checkt: frame-to-frame coherentie, vloeiende beweging, logische progressie
- Output: detecteert haperingen, ontbrekende frames, timing issues

**4. Style Consistency Specialist**
- Tool: Ollama Qwen 2.5 VL 7B + vergelijkingsset
- Checkt: past bij andere sprites in dezelfde set/faction
- Gebruikt Qdrant voor similarity search tegen approved sprites

**5. Context-Aware Reviewer**
- Tool: Ollama Llama 3.2 Vision 11B
- Checkt: past sprite bij beoogde rol (fighter vs organic creature vs UI element)
- Input includes: asset type, faction, intended use

**6. Damage State Progression** (alleen voor multi-state sprites)
- Tool: Ollama + Python
- Checkt: damage states progressief (schoner naar kapotter), consistent character

## Judge

**Sprite Judge**
- Tool: Ollama Qwen 2.5 72B (of fallback Claude API bij twijfel)
- Input: alle jury scores + reasoning
- Output: verdict (accept/reject/experimental/review)
- Logic:
  - Pixel integriteit < 5: auto reject
  - Alle jury > 7: auto accept  
  - Gemiddelde 5-7 met hoge variantie: experimental (interessant)
  - Gemiddelde 5-7 met lage variantie: review
  - Lager: reject

## N8n Workflow Structuur

```
Webhook Trigger (sprite_review)
    ↓
Set (parse input)
    ↓
Execute Workflow (parallel jury)
    ├─ HTTP Request → pixel_integrity.py
    ├─ HTTP Request → Ollama /silhouette_check
    ├─ HTTP Request → Ollama /animation_flow
    ├─ HTTP Request → Ollama /style_consistency
    ├─ HTTP Request → Ollama /context_aware
    └─ HTTP Request → Ollama /damage_progression
    ↓
Merge (wait all)
    ↓
Code Node (aggregate + validate)
    ↓
HTTP Request → Ollama /sprite_judge
    ↓
Switch (verdict routing)
    ├─ accept → PostgreSQL save + MinIO upload
    ├─ experimental → MinIO experimental bucket + log
    ├─ review → Queue for human + Telegram notify
    └─ reject → Log + discard
    ↓
Webhook Response
```

## Cursor Prompt

Plak in Cursor:

```
Bouw een NOVA v2 Sprite Jury systeem met de volgende componenten:

1. Python script `jury/pixel_integrity.py`:
   - FastAPI endpoint POST /check
   - Input: sprite path, palette_json (optional)
   - Output: {score: 0-10, issues: [], verdict: "ok|warning|broken"}
   - Checks: PNG validity, alpha channel correctness, palette adherence, 
     edge artifacts via PIL.ImageFilter edge detection, orphan pixels
   - Gebruik PIL + numpy

2. Python script `jury/ollama_jury_member.py`:
   - FastAPI endpoint POST /judge/{specialist}
   - Input: sprite path, context dict
   - Output: {score: 0-10, reason: string}
   - Specialists: silhouette, animation, style, context, damage
   - Elk specialist heeft eigen prompt template in /prompts/
   - Roept Ollama aan op localhost:11434/api/generate
   - Gebruik httpx async

3. Python script `jury/sprite_judge.py`:
   - FastAPI endpoint POST /verdict
   - Input: list of jury scores
   - Output: {verdict: accept|reject|experimental|review, reasoning: string}
   - Logic: zie 01_sprite_jury.md judge sectie
   - Roept Ollama aan met Qwen 2.5 72B

4. N8n workflow JSON `sprite_jury_workflow.json`:
   - Webhook trigger op path /sprite-review
   - Parallel HTTP requests naar alle jury endpoints
   - Merge node
   - Code node voor score aggregation
   - HTTP request naar judge endpoint
   - Switch node voor verdict routing
   - 4 output paths: accept/experimental/review/reject
   - Error handling op elke HTTP node

5. Docker compose file `docker-compose.jury.yml`:
   - pixel_integrity service (FastAPI port 8001)
   - ollama_jury service (FastAPI port 8002)
   - sprite_judge service (FastAPI port 8003)
   - Gedeelde volume voor sprite files
   - Health checks

6. Test script `test_sprite_jury.sh`:
   - curl tests voor elk endpoint
   - Test met 3 sample sprites (accept case, reject case, ambiguous)
   - Valideer response format

Belangrijk:
- Werk async waar mogelijk
- Gebruik pydantic voor request/response models
- Log naar stdout in JSON format voor Loki pickup
- Environment variables voor Ollama URL
- Graceful degradation als Ollama niet bereikbaar

Gebruik Python 3.11+ en moderne FastAPI patterns.
```

## Test Scenario's

1. **Clean sprite (Dark Ledger fighter)**: alle jury > 7, judge: accept
2. **Broken sprite (corrupted PNG)**: pixel_integrity 0, judge: reject direct
3. **Ambiguous sprite (experimental design)**: gemengde scores, judge: experimental
4. **Animation met hapering**: animation_flow < 5, judge: reject of review

## Success Metrics

- 80%+ accept rate op known-good sprites (validatie tegen handmatig goedgekeurd)
- < 5% false positive rate (kapotte sprites die accept krijgen)
- Gemiddelde processing tijd < 30 seconden per sprite
- Judge disagreement rate < 15% (hoe vaak verdict conflict met achteraf human review)

## Integratie met Bestaande Pipeline

- Input komt van: PyQt5 generator output in `L:\Nova\SpaceShooter\sprites\generated`
- Accept output naar: `L:\Nova\SpaceShooter\sprites\approved`
- Experimental naar: `L:\Nova\SpaceShooter\sprites\experimental`
- Reject gelogd in PostgreSQL, sprites verwijderd na 7 dagen

## Volgende Stappen na Bouw

1. Run op 100 bestaande Dark Ledger sprites, valideer judge verdicten
2. Fine-tune thresholds op basis van resultaten
3. Export metrics naar Grafana dashboard
4. Documenteer known edge cases
5. Train LoRA op accept-category voor betere generatie
