# Prompt 35: End-to-End Story Pipeline Test

## Wat deze prompt doet

Test narrative pipeline: Prompt Director → Story Text Integration → Narrative Jury → ElevenLabs Audio → Audio Jury.

## Voorwaarden

- [ ] Prompt 34 compleet
- [ ] Agents 07, 18, 28, 29, 03, 30 active

## De prompt

```
Voer end-to-end story pipeline integration test uit.

DOEL: Test narrative chain werkt van idee tot gecanoniseerde + audio output.

TEST CASE: "Generic NPC greeting line"
- Geen Black Ledger specific content nog
- Neutrale test of pipeline werkt
- Later wordt dit Rex Varn voor Black Ledger

STAP 1: PROMPT DIRECTOR
POST http://178.104.207.194:5680/webhook/prompt-direct
Body: {
  "task": "generate_dialog",
  "context": "Generic station NPC greeting to player",
  "constraints": {"max_length": 100, "tone": "casual"}
}

Verwacht: structured prompt voor dialog generation.

STAP 2: STORY TEXT INTEGRATION
POST http://178.104.207.194:5680/webhook/story-integration
Body: {
  "prompt": "<van stap 1>",
  "canon_scope": "test_canon",  # Geen Black Ledger canon nog
  "character": "generic_npc"
}

Verwacht: generated dialog text.

STAP 3: NARRATIVE JURY
POST http://178.104.207.194:5680/webhook/narrative-review
Body: {
  "text": "<van stap 2>",
  "context": "npc_greeting",
  "checks": ["voice", "tone", "length"]
}

Verwacht: verdict accept/revise.

STAP 4: (Optioneel) ELEVENLABS AUDIO
Als Meshy credits niet opmaken voor test, gebruik mock:
POST http://178.104.207.194:5680/webhook/audio-generate
Body: {
  "text": "<van stap 2/3>",
  "voice": "generic_neutral",
  "emotion": "casual",
  "use_cache": true  # Cache om credits te sparen
}

Verwacht: audio file path of cached URL.

STAP 5: AUDIO JURY
POST http://178.104.207.194:5680/webhook/audio-review
Body: {
  "audio_file": "<van stap 4>",
  "expected_duration_range": [1.0, 5.0],
  "checks": ["loudness", "clipping", "format"]
}

Verwacht: verdict.

STAP 6: AUDIO ASSET JURY
POST http://178.104.207.194:5680/webhook/audio-asset-review
Body: {
  "audio_file": "<van stap 4>",
  "use_case": "voice_line",
  "integration_target": "godot"
}

Verwacht: verdict met game-integration feedback.

STAP 7: RAPPORT naar docs/integration_test_35_report.md

STAP 8: COMMIT

RAPPORT:
- Test 35 resultaat
- ElevenLabs credits gebruikt
- Audio kwaliteit
- Volgende: prompt 36
```

## Cost note

ElevenLabs API calls kosten credits. Zet use_cache=true tenzij expliciet nodig. Test audio hoeft niet uniek te zijn.

## Volgende prompt

`05_integration/prompt_36_cross_agent_integration.md`
