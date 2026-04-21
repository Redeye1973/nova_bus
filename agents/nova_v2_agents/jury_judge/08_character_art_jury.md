# 08. Character Art Jury Agent

## Doel
Beoordeelt character art (van Poser/DAZ/Blender) voor NOVA producten met menselijke figuren.

## Scope
- Poser/DAZ Studio character renders
- Blender character sculpts
- Figuranten voor NORA (voetgangers in verkeer)
- Main characters voor potentiele games of Surilians visualisaties

## Jury Leden

**1. Anatomy Correctness Specialist**
- Tool: Ollama vision model + anatomical reference
- Checkt: lichaamsverhoudingen, gewrichten realistisch, handen en gezicht correct

**2. Pose Readability Validator**
- Tool: Ollama + silhouette extraction
- Checkt: silhouet leesbaar, pose duidelijk van contour

**3. Expression Coherence Checker**
- Tool: Ollama vision
- Checkt: gezichtsuitdrukking past bij context/emotie
- Detect: dead eyes, uncanny valley issues

**4. Costume Consistency Reviewer**
- Tool: Ollama + character profile
- Checkt: kleding past bij personage, tijdperk, setting

**5. Lighting Mood Validator**
- Tool: Python color analysis + Ollama
- Checkt: lichtsetting ondersteunt gewenste sfeer

**6. Silhouette Clarity**
- Tool: Python image processing
- Checkt: rim light/contour duidelijk, character pops uit achtergrond

## Judge

**Character Art Judge**
- Voor hoofdfiguren: hoge bar, portfolio quality
- Voor figuranten: gemiddelde bar, volume belangrijker
- Voor specifieke NORA voetganger-assets: silhouette leesbaarheid kritiek

## Cursor Prompt

```
Bouw een NOVA v2 Character Art Jury:

1. Python service `char_jury/anatomy_checker.py`:
   - Input: character render PNG/JPG
   - Ollama Qwen VL prompt: "Analyze anatomy correctness. Check proportions, 
     joint positioning, hand/face detail"
   - Output: {score, issues: []}

2. Python service `char_jury/pose_readability.py`:
   - Extract silhouette via background removal (rembg of PIL)
   - Send silhouette-only naar Ollama
   - Output: {recognizable_pose, score, description}

3. Python service `char_jury/expression_check.py`:
   - Input: render + intended_emotion
   - Ollama vision analysis
   - Detect uncanny valley (dead eyes, frozen expression)

4. Python service `char_jury/costume_reviewer.py`:
   - Input: render + character_profile (era, setting, role)
   - Ollama checkt costume fit
   - Output: {appropriate, anachronisms: []}

5. Python service `char_jury/lighting_mood.py`:
   - Color histogram analysis via PIL
   - Detect mood via hue/saturation/value distribution
   - Ollama validates mood match

6. Python service `char_jury/silhouette_clarity.py`:
   - Edge detection analysis
   - Contrast against background check
   - Output: pop score

7. Python service `char_jury/char_judge.py`:
   - Tier-specific verdict (main character vs extra)
   - Output + recommendations

8. N8n workflow

Gebruik Python 3.11, PIL, rembg voor background removal,
Ollama vision models, FastAPI.
```

## Test Scenario's

1. DAZ hero character render → accept voor portfolio
2. NORA voetganger asset → accept voor bulk use
3. Broken hand model (DAZ artifact) → reject
4. Wrong era costume (future outfit in historic scene) → revise

## Success Metrics

- Broken anatomy detection: > 90%
- Silhouette clarity for game use: > 95% accurate
- Uncanny valley detection: > 70% (hard problem)
