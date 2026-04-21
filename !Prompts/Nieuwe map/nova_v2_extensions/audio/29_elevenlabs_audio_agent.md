# 29. ElevenLabs Audio Agent

## Doel
ElevenLabs API integratie voor voice generation en SFX creation. Managed audio asset production voor games en andere producten.

## Scope
- Voice generation (character dialog)
- Voice cloning (als voor consistency needed)
- Sound effects generation
- Audio format conversion
- Voice library management per character

## Jury (3 leden, medium)

**1. Voice Identity Consistency**
- Tool: Python + audio fingerprinting
- Check: zelfde character heeft herkenbare stem across recordings
- Detect: voice drift tussen generations
- Compare tegen reference samples

**2. Emotional Delivery Validator**
- Tool: Ollama audio description + acoustic analysis
- Check: emotional tone matches scene intent
- Detect: flat/robotic delivery, mismatched emotion
- Per line: angry, calm, excited, etc

**3. Technical Quality Checker**
- Tool: librosa + audio analysis
- Check: clean audio (no artifacts)
- LUFS normalization
- No clipping, adequate dynamic range
- Background noise minimal

## Judge

Accept → Ready voor game/product use
Revise → Regenerate met adjusted parameters
Reject → Fundamental issue, try different voice/prompt

## ElevenLabs API integration

**API endpoints used:**
- `/v1/text-to-speech/{voice_id}` - Voice generation
- `/v1/voices` - Voice library management
- `/v1/sound-generation` - SFX creation (recent feature)
- `/v1/voices/add` - Custom voice upload (cloning)

**Cost awareness:**
- Free tier: 10k chars/month
- Starter: $5/month, 30k chars
- Creator: $22/month, 100k chars
- Pro: $99/month, 500k chars

NOVA Cost Guard (16) tracks usage, alerts bij budget limits.

## Cursor Prompt

```
Bouw NOVA v2 ElevenLabs Audio Agent:

1. Python service `elevenlabs/api_client.py`:
   - Wrapper around ElevenLabs SDK (pip install elevenlabs)
   - Methods:
     - generate_voice(text, voice_id, settings)
     - generate_sfx(prompt, duration)
     - list_voices()
     - upload_voice(name, samples)
   - Proper error handling, retry logic
   - Cost tracking via Cost Guard (16)

2. Python service `elevenlabs/voice_library.py`:
   - Map characters naar ElevenLabs voice IDs
   - Per character:
     - voice_id (ElevenLabs)
     - voice_settings (stability, similarity, style)
     - sample_count (trained on)
     - last_used, total_chars_generated
   - YAML config

3. Python service `elevenlabs/dialog_generator.py`:
   - FastAPI POST /dialog/generate
   - Input: {character, text, emotion, speed}
   - Lookup voice settings
   - Call API
   - Return audio + metadata
   - Cache to avoid regenerating same dialog

4. Python service `elevenlabs/sfx_generator.py`:
   - FastAPI POST /sfx/generate
   - Input: {description, duration, variations}
   - Use ElevenLabs sound generation
   - Generate multiple options voor choice

5. Python service `elevenlabs/voice_consistency.py`:
   - Jury member 1
   - Audio fingerprinting (use something like resemblyzer)
   - Compare tegen reference voice samples
   - Output: {consistent, drift_score}

6. Python service `elevenlabs/emotion_validator.py`:
   - Jury member 2
   - Acoustic features (pitch, energy, tempo)
   - Compare tegen expected emotion profile
   - Ollama optional voor high-level check
   - Output: {emotion_match, detected_emotion, expected_emotion}

7. Python service `elevenlabs/quality_checker.py`:
   - Jury member 3
   - librosa analysis
   - LUFS, peak levels, DC offset
   - Clipping detection
   - Background noise analysis

8. Python service `elevenlabs/audio_judge.py`:
   - Aggregate verdict

9. Python service `elevenlabs/cache_manager.py`:
   - Cache generated audio by (character, text, settings) hash
   - Prevent duplicate API calls
   - Disk-based cache met expiry

10. Integration met ffmpeg voor format conversion:
    - MP3 naar WAV/OGG (Godot prefers OGG)
    - Normalization
    - Trim silence

Gebruik Python 3.11, FastAPI, elevenlabs SDK, librosa, ffmpeg-python,
resemblyzer voor voice fingerprinting.
```

## Voice library voor Black Ledger + Surilians

**Black Ledger characters:**
- Rex Varn (player, gruff veteran)
- Corporate Announcer (corporate, clinical)
- Pirate Radio (chaotic, threatening)
- Mission Control (authoritative)

**Surilians characters:**
- Thael (archaic, measured)
- Glitch (energetic, playful)
- Cathleen (warm, protective)
- Ancient One (deep, resonant)
- Various other chars

Elk heeft:
- ElevenLabs voice_id (gekozen or cloned)
- Settings finetuned
- Reference samples
- Generation history

## Workflow voor dialog generation

```
1. Alex writes dialog in Surilians chapter
    ↓
2. Story Text Integration (28) validates canon + voice
    ↓
3. Dialog approved → send to ElevenLabs Audio Agent (29)
    ↓
4. Generate audio via API
    ↓
5. Audio Asset Jury (30) validates for game integration
    ↓
6. Store in audio library, cache for reuse
    ↓
7. Reference in game resource (Godot Import 26)
```

## SFX generation voor shmup

**Black Ledger SFX needs:**
- Weapon fire (per weapon type: plasma, missile, laser)
- Explosions (small, medium, large, boss)
- Engine sounds (player, enemy)
- UI sounds (menu clicks, alerts)
- Ambient (space, planet atmosphere)

**ElevenLabs sound generation strengths:**
- Good voor impact sounds
- Ambient textures
- Mechanical sounds

**Weaknesses:**
- Not perfect voor complex music
- Pair met Audiocraft voor music (already in stack)

## Test Scenario's

1. Generate Thael dialog → voice consistency met previous samples
2. Generate SFX "plasma cannon firing" → multiple variations
3. Detect drift bij voice regeneration → flag inconsistency
4. Technical quality issue (clipping) → reject

## Success Metrics

- Voice consistency across generations: > 90%
- API success rate: > 98%
- Cache hit rate: > 50% (saves API costs)
- Audio technical quality: > 95% accept rate

## Output

Per generation:
- Audio file (OGG format voor Godot)
- Metadata JSON (character, text, settings, generation time)
- Quality report
- Cost tracking entry

## Integratie

- Audio Jury (03) validates technical quality
- Audio Asset Jury (30) validates game integration fit
- Cost Guard (16) tracks API usage
- Godot Import (26) references audio resources
- Distribution Agent (19) handles deliverables
