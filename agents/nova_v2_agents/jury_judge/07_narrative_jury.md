# 07. Narrative Jury Agent

## Doel
Beoordeelt narratieve content (verhalen, dialoog, scene beschrijvingen) op consistentie en kwaliteit.

## Scope
- Surilians manuscript chapters
- Black Ledger dialoog en story events
- Game scenario scripts voor NORA
- Marketing copy voor producten

## Jury Leden

**1. Canon Consistency Detector**
- Tool: Ollama + vector search over Surilians bible
- Checkt: nieuwe content strookt met gevestigde lore
- Kritiek voor Surilians universe (Ancient One, Silurians, etc)

**2. Character Voice Validator**
- Tool: Ollama met character profiles
- Checkt: dialoog past bij personage's stem
- Thael klinkt anders dan Glitch klinkt anders dan Cathleen

**3. Pacing Analyzer**
- Tool: Ollama
- Checkt: scene beweegt of stagneert
- Detect te lange beschrijvingen, traag dialoog

**4. Tonal Consistency Checker**
- Tool: Ollama
- Checkt: sfeer past bij hoofdstuk/scene context
- Geen humor in serieuze scenes (tenzij ironic intent)

**5. Plot Progression Evaluator**
- Tool: Ollama met outline comparison
- Checkt: brengt scene het verhaal vooruit?
- Filtert filler content

**6. POV Consistency Validator**
- Tool: Python + Ollama
- Checkt: perspectief (first/third person) blijft behouden
- Detecteert POV-breaches

**7. Prose Quality Reviewer**
- Tool: Ollama
- Checkt: sentence variety, niet-cliche phrasing, show-don't-tell

## Judge

**Narrative Judge**
- Tool: Ollama Qwen 72B of Claude API
- Most subjective domain, judge needs flexibiliteit
- Verdict: publish / revise / rewrite / reject

**Let op**: narratief is meest subjectief. Jury-judge helpt maar vervangt niet final human oordeel. Zie verdicten als adviezen.

## N8n Workflow

```
Trigger: nieuw hoofdstuk of scene aangeleverd
    ↓
Load canon context (Surilians bible in Qdrant)
    ↓
Parallel jury:
    ├─ Canon consistency (vector + Ollama)
    ├─ Character voice (per character)
    ├─ Pacing
    ├─ Tone
    ├─ Plot progression
    ├─ POV
    └─ Prose quality
    ↓
Merge
    ↓
Narrative Judge
    ↓
Verdict met specific feedback
    ↓
Human review altijd voor publish
```

## Cursor Prompt

```
Bouw een NOVA v2 Narrative Jury voor Surilians en game story content:

1. Python service `narrative_jury/canon_consistency.py`:
   - FastAPI POST /check
   - Input: text_excerpt, project_id
   - Load Surilians bible chunks uit Qdrant
   - Vector search relevant lore
   - Ollama prompt: "Strookt deze tekst met de gevestigde lore? [lore] [new_text]"
   - Output: {consistent, conflicts: [...], score}

2. Python service `narrative_jury/character_voice.py`:
   - Input: dialog excerpt, character_name
   - Load character profile (speech patterns, vocabulary, mannerisms)
   - Ollama checkt dialoog match
   - Output: {in_character, off_brand_phrases: [], score}

3. Python service `narrative_jury/pacing.py`:
   - Analyseer sentence lengths, paragraph structure
   - Ollama: "Beweegt deze scene of stagneert hij?"
   - Output: {pace_score, slow_sections: [...]}

4. Python service `narrative_jury/tone_checker.py`:
   - Input: text + expected_tone (serious|humorous|tense|melancholic)
   - Ollama analyse
   - Output: {tone_match, score, tonal_shifts: []}

5. Python service `narrative_jury/plot_progression.py`:
   - Input: scene + story outline
   - Ollama: "Welke plot elementen advance deze scene?"
   - Detect filler content
   - Output: {progression_score, elements_advanced: []}

6. Python service `narrative_jury/pov_checker.py`:
   - Python regex + Ollama
   - Detect POV shifts (I→he, internal→external)
   - Output: {consistent, shifts: [{location, from, to}]}

7. Python service `narrative_jury/prose_quality.py`:
   - Sentence variety analysis (length distribution, structure)
   - Cliche detection via pattern matching
   - Ollama: show vs tell balance
   - Output: {quality_score, issues: []}

8. Python service `narrative_jury/narrative_judge.py`:
   - Aggregate
   - Output verdict: publish/revise/rewrite/reject
   - ALWAYS generate specific feedback for author

9. Qdrant setup script voor Surilians bible:
   - Parse docx files (Chapter_0 t/m Chapter_9)
   - Chunk en embed
   - Store met metadata

10. N8n workflow
11. Human review routing: ALL verdicts go to Alex voor final say

Gebruik Python 3.11, FastAPI, Qdrant client, Ollama via httpx.
docx parsing via python-docx.
```

## Integratie met Surilians Workflow

Nieuw hoofdstuk geschreven → docx upload → N8n trigger → jury analyse → feedback report → Alex reviewt en beslist.

Niet auto-publish. Narratief blijft mensenwerk, agents ondersteunen alleen.

## Test Scenario's

1. Hoofdstuk dat Ancient One canon respecteert → publish
2. Scene waar Thael out-of-character dialoog heeft → revise met highlights
3. Trage exposition-heavy scene → revise met pacing advies  
4. Scene met POV shift midden in → revise

## Success Metrics

- Canon conflict detection (known lore violations): > 90%
- Character voice issues detected: > 75%
- Human author vindt feedback bruikbaar: > 60% (subjective metric)
- False positives niet frustrerend maar minimaal

## Belangrijk

Laatste in implementatie-volgorde om goede reden. Narrative is waar AI het minst betrouwbaar is. Bouw pas als andere domeinen stable zijn en je data hebt over jury-judge effectiviteit.
