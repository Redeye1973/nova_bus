# 30. Audio Asset Jury

## Doel
Game-specifieke validatie voor audio assets. Anders dan de generieke Audio Jury (03): focus op integratie met gameplay context.

## Scope
- SFX timing voor gameplay (niet te lang, niet te kort)
- Mixing levels relatief tot andere sounds
- Loop-ability voor repeating sounds
- 3D positional audio geschiktheid
- Performance in Godot/Unreal

## Jury (2 leden, licht - mostly integration-focused)

**1. Gameplay Context Validator**
- Tool: Python + audio analysis + context checks
- Input: audio + intended use (weapon fire, UI, ambient)
- Check duration appropriate voor use case
- Verify peak timing matches gameplay event
- Output: {fit_for_purpose, timing_issues: []}

**2. Integration Quality Checker**
- Tool: Python + librosa + game engine sim
- Check: relative volume vs reference assets
- Loop points seamless voor ambient
- Fade in/out appropriate
- Memory size reasonable voor engine use

## Judge

Accept → Ready for game integration
Revise → Adjustments needed (trim, normalize, etc)
Reject → Re-generate with different parameters

## Cursor Prompt

```
Bouw NOVA v2 Audio Asset Jury:

1. Python service `audio_asset_jury/gameplay_context.py`:
   - FastAPI POST /context
   - Input: audio file + usage_type
   - Usage types: 
     - weapon_fire: expect < 0.5s, sharp attack
     - explosion: 0.5-3s, impact + tail
     - ui_click: < 0.2s, clean
     - ambient_loop: 10-60s, seamless loop
     - music_track: 30-180s, varies
     - voice_line: depends on text length
   - Check duration vs expectation
   - Analyze attack/sustain/decay
   - Output: {appropriate, adjustments: []}

2. Python service `audio_asset_jury/integration_checker.py`:
   - FastAPI POST /integration
   - Compare tegen reference asset bundle
   - Check: relative loudness (LUFS) consistent
   - Verify: fade in/out smooth
   - Loop detection voor marked loops
   - Size checks (KB budget per asset)

3. Python service `audio_asset_jury/game_integration_test.py`:
   - Optional: actually test in game engine
   - Godot headless: load audio, play, verify
   - Unreal: similar test
   - Catch engine-specific issues

4. Python service `audio_asset_jury/asset_judge.py`:
   - 2-member light jury
   - Aggregate
   - Output: accept/revise/reject

5. Asset registry `audio_asset_jury/registry.py`:
   - Track all game audio assets
   - Per asset: usage, duration, file size, LUFS
   - Enable comparison tegen library

Gebruik Python 3.11, FastAPI, librosa, soundfile, pydub.
```

## Duration expectations per type

```yaml
audio_types:
  weapon_fire:
    min_duration: 0.05
    max_duration: 0.5
    expected_attack: sharp
    typical_file_size_kb: 20-100
  
  explosion:
    min_duration: 0.5
    max_duration: 3.0
    expected_shape: impact_tail
    typical_file_size_kb: 100-500
    
  ui_feedback:
    min_duration: 0.05
    max_duration: 0.3
    expected_shape: clean_brief
    typical_file_size_kb: 10-50
    
  ambient_loop:
    min_duration: 10.0
    max_duration: 120.0
    loop_required: true
    typical_file_size_kb: 500-3000
    
  music_track:
    min_duration: 30.0
    max_duration: 300.0
    loop_optional: true
    typical_file_size_kb: 1000-10000
    
  voice_line:
    min_duration: 0.5
    max_duration: 30.0
    expected_shape: speech
    typical_file_size_kb: 50-1000
```

## Integration checks

**Volume consistency:**
- Reference assets define expected LUFS per category
- Weapon fire: -12 LUFS typical
- Music: -18 LUFS typical
- Voice: -16 LUFS typical
- New assets checked tegen reference

**Loop seamlessness:**
- Extract first 100ms and last 100ms
- Check waveform continuity
- Harmonic match at boundary
- Flag if click/pop detected

**Format compliance:**
- Godot: OGG Vorbis preferred (compressed)
- WAV voor critical SFX (uncompressed)
- Sample rate: 44.1kHz or 48kHz (not higher, wastes space)
- Channels: mono voor 3D positioned, stereo voor ambient/music

## Test Scenario's

1. New plasma weapon SFX → context check + loudness match
2. Ambient space loop → seamless validation
3. Overlong weapon fire (2s audio voor 0.1s game event) → revise trim
4. Mono audio where stereo expected (music) → revise

## Success Metrics

- Duration appropriateness: > 95% accurate
- Loudness consistency: within ±2 LUFS of target
- Loop seamlessness: 100% for marked loops
- Format compliance: 100%

## Output

Per asset:
- Verdict
- Specific issues + fix recommendations
- Comparison tegen similar assets
- Ready-for-integration flag

## Integratie

- Validates output van ElevenLabs Audio (29)
- Also validates Audiocraft output
- Handmatig uploaded audio assets
- Werkt samen met Audio Jury (03) voor technische quality
- Output naar Godot Import (26) of Unreal Import (34)
