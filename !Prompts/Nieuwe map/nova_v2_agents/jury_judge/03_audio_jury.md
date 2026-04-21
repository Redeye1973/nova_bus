# 03. Audio Jury Agent

## Doel
Beoordeelt gegenereerde audio (muziek, sound effects, voice) voor game en media productie.

## Scope
- Audiocraft gegenereerde muziek tracks
- Sound effects voor games
- Voice TTS output (RVC + XTTS v2)
- Ambient audio loops

## Jury Leden

**1. Technical Quality Specialist**
- Tool: Python + librosa
- Checkt: clipping, DC offset, peak levels, LUFS loudness
- Geen AI nodig, pure DSP analyse

**2. Frequency Balance Detector**
- Tool: Python + librosa FFT
- Checkt: spectral balance, niet alleen bass/treble
- Output: score + warnings bij extreme imbalance

**3. Genre Coherence Reviewer**
- Tool: Ollama met audio description
- Input: audio sample + intended genre/mood
- Checkt: past audio bij de vraag (cyberpunk, ambient, battle music)
- Uses audio-to-text eerst via Whisper of similar

**4. Loop Point Detector** (voor game music)
- Tool: Python + librosa
- Checkt: begin en einde matchen voor seamless looping
- Detecteert harmonische en ritmische continuïteit

**5. Mood Consistency Checker**
- Tool: Ollama + audio analysis
- Checkt: blijft emotionele toon consistent door track
- Voor 30-seconde game music belangrijk

**6. Mix Quality Analyzer**
- Tool: librosa + Ollama
- Checkt: stereo balance, reverb niveaus, instrument separation

## Judge

**Audio Judge**
- Weeg clipping/peak issues zwaar (technisch kapot = reject)
- Genre match bepaalt context fitness
- Mood consistency voor longer tracks

## N8n Workflow

```
Trigger: bestand upload naar audio_review queue
    ↓
Audio preprocessing (ffmpeg normalisatie)
    ↓
Parallel jury:
    ├─ Technical Quality
    ├─ Frequency Balance
    ├─ Genre Coherence
    ├─ Loop Point (conditioneel)
    ├─ Mood Consistency
    └─ Mix Quality
    ↓
Merge
    ↓
Audio Judge
    ↓
Verdict routing
```

## Cursor Prompt

```
Bouw een NOVA v2 Audio Jury systeem:

1. Python service `audio_jury/technical_quality.py`:
   - FastAPI POST /analyze
   - Input: audio file path (WAV, MP3, OGG)
   - Output: {score: 0-10, clipping_detected: bool, peak_db: float, 
     lufs: float, issues: []}
   - Gebruik librosa + soundfile
   - Check: clipping (>-0.3dBFS sustained), DC offset, silence ratio

2. Python service `audio_jury/frequency_balance.py`:
   - FastAPI POST /spectral
   - Output: {score, spectrum_summary: {low, mid, high}, warnings: []}
   - FFT analyse via librosa.stft
   - Detect: extreme imbalance (> 15dB difference between bands)

3. Python service `audio_jury/genre_coherence.py`:
   - FastAPI POST /coherence
   - Input: audio + expected_genre + mood_tags
   - Gebruik audio analysis (tempo, key, instruments via librosa) + Ollama
   - Output: {score, detected_genre, match: bool, reasoning}

4. Python service `audio_jury/loop_detector.py`:
   - FastAPI POST /loop
   - Checkt of audio seamlessly loopt
   - Cross-correlate eerste 1sec met laatste 1sec
   - Check harmonic continuity
   - Output: {loops_seamlessly: bool, click_at_boundary: bool, score}

5. Python service `audio_jury/mood_consistency.py`:
   - Input: audio
   - Split in 5 sec segments
   - Analyseer mood per segment via spectral features
   - Check dat mood niet abrupt wisselt (tenzij intentioneel)
   - Output: {consistency_score, mood_shifts: [{time, from, to}]}

6. Python service `audio_jury/mix_quality.py`:
   - Stereo balance check (channel correlation)
   - Dynamic range (crest factor)
   - Masking detection (competing frequencies)

7. Python service `audio_jury/audio_judge.py`:
   - FastAPI POST /verdict
   - Aggregeert scores, past domain rules toe
   - Game music: loop detection verplicht, mood stability hoog
   - SFX: peak levels strict, korte duration verwacht
   - Voice: intelligibility belangrijkst

8. N8n workflow `audio_jury_workflow.json`:
   - Trigger op nieuwe files in audio_queue
   - Parallel jury calls
   - Judge
   - Routing naar appropriate output bucket

9. Docker setup voor alle services
10. Test suite met samples: clean audio, clipping audio, bad loop, wrong genre

Gebruik Python 3.11, librosa, soundfile, numpy, FastAPI, Ollama via httpx.
```

## Integratie met Audiocraft

Audiocraft output → tijdelijke folder → N8n watcher triggert jury → verdict routing naar:
- `game/music/approved/` voor accept
- `game/music/experimental/` voor interesting
- `audio_queue/human_review/` voor borderline
- Deleted voor reject

## Test Scenario's

1. Clean Audiocraft ambient track → accept
2. Clipping in generated battle music → reject
3. Mismatched mood (happy tune voor horror scene) → review
4. Ambient met bad loop point → revise (regenerate met loop instructions)

## Success Metrics

- Detectie clipping en technical issues: 99%+
- Genre match accuracy: 80%+
- Human agreement met judge verdicten: 75%+
