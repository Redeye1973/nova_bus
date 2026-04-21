# 24. Aseprite Animation Jury

## Doel
Specifieke jury-judge voor Aseprite animations. Beoordeelt frame-level kwaliteit, timing, smoothness.

## Scope
- Rotation animations (16 frames consistentie)
- Engine/weapon loops
- Damage state transitions
- Character action animations (voor storyboard)
- Effect animations (explosions, muzzle flashes)

## Jury (5 leden, zwaar - pixel-perfect animation is kritiek)

**1. Frame Smoothness Detector**
- Tool: Python + PIL frame-by-frame diff
- Checkt: geen abrupt changes tussen frames
- Detecteert: skipped frames, stuttering
- Output: smoothness score per animation

**2. Loop Continuity Validator**
- Tool: Python + numpy
- Voor looping animations: check laatste frame matches eerste
- Pixel-level continuity
- Output: seamless bool + mismatch pixels

**3. Timing Coherence Checker**
- Tool: Python + Aseprite JSON parser
- Check frame durations logisch
- Action poses langer dan transition frames
- Engine flicker op natuurlijk ritme (niet perfect metronome)

**4. Silhouette Volume Tracker**
- Tool: OpenCV
- Track silhouette volume across frames
- Detecteert: volume fluctuation (ship worden kleiner/groter onbedoeld)
- Voor rotation: expected volume variation OK

**5. Color Coherence per Frame**
- Tool: Python + PIL
- Check kleuren blijven uit master palette binnen animation
- Detecteert: accidental non-palette frames na edits
- Validates damage state color progression

## Judge

- Accept: smooth professional animation
- Revise: specifieke frames fixen
- Reject: fundamenteel geanimeerd issue, opnieuw

## Cursor Prompt

```
Bouw NOVA v2 Aseprite Animation Jury:

1. Python service `aseprite_anim/smoothness_detector.py`:
   - FastAPI POST /smoothness
   - Input: sprite sheet + metadata
   - Load frames as array
   - Compute pixel diff between consecutive frames
   - Detect anomalies (sudden large changes)
   - Output: {smoothness_score, jumpy_transitions: []}

2. Python service `aseprite_anim/loop_validator.py`:
   - FastAPI POST /loop
   - For looping animations: compare frame[0] vs frame[-1]
   - Compute SSIM or exact pixel diff
   - Output: {seamless, mismatch_pixels: int, diff_locations}

3. Python service `aseprite_anim/timing_checker.py`:
   - FastAPI POST /timing
   - Parse Aseprite JSON (durations)
   - Apply heuristics per animation type:
     - Rotation: uniform timing expected
     - Engine loop: natural variation OK
     - Action: key poses longer
   - Output: {coherent, issues: []}

4. Python service `aseprite_anim/volume_tracker.py`:
   - FastAPI POST /volume
   - Use OpenCV contour detection
   - Calculate silhouette area per frame
   - Track changes over animation
   - Classify: expected (rotation) vs unexpected (volume drift)

5. Python service `aseprite_anim/color_coherence.py`:
   - FastAPI POST /colors
   - Per frame: extract palette
   - Compare tegen master palette
   - Check progression (damage states)

6. Python service `aseprite_anim/animation_judge.py`:
   - Aggregate 5 jury scores
   - Weight smoothness + loop heavily
   - Output: accept/revise/reject + detailed feedback

7. N8n workflow template

Gebruik Python 3.11, FastAPI, PIL, numpy, OpenCV, scikit-image voor SSIM.
```

## Specific animation types handling

**Rotation animations:**
- Frame interval: expected uniform (22.5° per frame)
- Volume: minor variation (elongated vs end-on)
- Smoothness: kritiek - must flow

**Engine loops:**
- Natural flicker expected
- No strict metronome rhythm
- Brightness variation encouraged
- 8-12 frames typical

**Damage state transitions:**
- Not looped, one-shot
- Progressive changes (accumulating damage)
- Key moments emphasized

**Explosion animations:**
- Fast growth, slower dissipation
- 12-16 frames
- Fade to transparent

**Muzzle flashes:**
- Very short (4-6 frames)
- Bright peak frame 1
- Quick fade

## Test Scenario's

1. Clean rotation animation → accept
2. Missing frame 7 (jump) → revise
3. Loop not closing → revise with specific fix
4. Volume drift over rotation → revise
5. Non-palette pixel introduced via edit → revise

## Success Metrics

- Smoothness detection: > 90% accurate
- Loop issue detection: > 95%
- False positives: < 5%
- Human agreement met jury: > 85%

## Output

Per animation:
- Verdict + detailed report
- Frame-by-frame analysis
- Specific fix instructions bij revise

## Integratie

- Werkt na Aseprite Processor (23)
- Feeds into Sprite Jury (01) voor finale check
- Failure routing naar manual Aseprite queue
- Success → PyQt5 Assembly (25)

## Manual queue integration

Bij complex revise verdicts (bv. Aseprite kan niet automated fix):
- Push naar manual_queue/aseprite_anim/
- Telegram notification
- Open file in Aseprite GUI voor Alex
- Wait for save, re-run jury
