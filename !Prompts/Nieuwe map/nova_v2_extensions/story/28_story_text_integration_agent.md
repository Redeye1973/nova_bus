# 28. Story Text Integration Agent

## Doel
Integratie van narratief tekst werk met productie. Surilians bible management, canon tracking, game dialog generation en validation.

## Scope
- Surilians bible als living document
- Canon cross-reference library (Qdrant)
- Dialog generation voor games (NPCs, mission briefings)
- Scene descriptions naar storyboard brief
- Lore consistency over producten heen

## Jury (5 leden, zwaar - canon is complex)

**1. Canon Adherence Validator**
- Tool: Qdrant vector search + Ollama Qwen 72B
- Vector search Surilians bible chunks
- Check nieuwe tekst tegen canon
- Detecteert: contradictions, impossible facts

**2. Character Voice Specialist**
- Tool: Ollama met character profiles
- Check dialog past bij character (Thael ≠ Glitch ≠ Cathleen)
- Vocabulary, speech patterns, tone
- Output: in-character / off-brand

**3. World Logic Coherence Checker**
- Tool: Ollama + worldbuilding rules
- Check: technology levels consistent
- Verify: cultural/political facts align
- Detect: lore inconsistencies tussen projects

**4. Narrative Arc Validator**
- Tool: Ollama + story structure analysis
- Check: scene advances plot
- Identify: pacing issues, filler
- Verify: character arcs coherent

**5. Cross-Product Consistency**
- Tool: Qdrant across product libraries
- Check: Black Ledger references fit Surilians canon
- NORA references don't contradict
- Meta-narrative consistency

## Judge

- Publish: ready voor publication/production
- Revise: specifieke passages fixen
- Rewrite: scene doesn't work, major revision
- Escalate: canon conflict needs Alex decision

## Cursor Prompt

```
Bouw NOVA v2 Story Text Integration Agent:

1. Python service `story_text/bible_manager.py`:
   - FastAPI CRUD voor Surilians bible
   - Ingest .docx chapters via python-docx
   - Chunk text en embed (CLIP text encoder of sentence-transformers)
   - Store in Qdrant met metadata (chapter, date, character)
   - Versioning: bible changes over time

2. Python service `story_text/canon_search.py`:
   - FastAPI POST /canon/search
   - Input: query text of concept
   - Vector search Qdrant
   - Return relevant canon chunks
   - Used door andere juries

3. Python service `story_text/character_profile_manager.py`:
   - Store character profiles:
     - Speech patterns (formal/casual/technical)
     - Vocabulary preferences
     - Catchphrases
     - Mannerisms
     - Relationships
   - For: Thael, Glitch, Cathleen, Rex Varn, etc
   - YAML config files per character

4. Python service `story_text/canon_validator.py`:
   - Jury member 1
   - Input: new text
   - Vector search canon
   - Ollama prompt: "Does this text conflict with established lore? [canon chunks] [new text]"
   - Output: {consistent, conflicts: [], canon_references: []}

5. Python service `story_text/voice_validator.py`:
   - Jury member 2
   - Load character profile
   - Compare dialog patterns
   - Ollama assessment
   - Output: {in_character, off_brand_phrases: []}

6. Python service `story_text/world_coherence.py`:
   - Jury member 3
   - Check: tech levels, cultural details, historical references
   - Against worldbuilding rules (config)
   - Output: {coherent, issues: []}

7. Python service `story_text/arc_validator.py`:
   - Jury member 4
   - Ollama narrative analysis
   - Plot progression check
   - Pacing assessment

8. Python service `story_text/cross_product_checker.py`:
   - Jury member 5
   - Search multiple product libraries
   - Detect: Black Ledger claims conflict met Surilians
   - NORA references don't break canon

9. Python service `story_text/story_judge.py`:
   - Aggregate 5 jury verdicts
   - Weight canon heavily (broken canon = cannot publish)
   - Escalation logic voor disputes

10. Python service `story_text/dialog_generator.py`:
    - FastAPI POST /dialog/generate
    - Input: {character, situation, intent}
    - Use character profile + Ollama
    - Pre-validate via jury before returning
    - Multiple options voor designer choice

11. Python service `story_text/scene_describer.py`:
    - Convert narrative scene naar storyboard brief
    - Extract: characters present, location, action, mood
    - Format voor Storyboard Visual Agent (27)

12. Integration met docx files:
    - Parse Chapter_0 t/m Chapter_9 uit project files
    - Build initial Qdrant library
    - Track chapter updates

Gebruik Python 3.11, FastAPI, Qdrant client, Ollama Qwen 72B,
python-docx, sentence-transformers.
```

## Surilians bible structure

Current bible in project files:
- Surilians_Story_Bible_v5_2.docx (master)
- Chapter_0 t/m Chapter_9 (individual chapters)
- Chat_van_surilians (additional notes)
- World Lore CSVs (characters, worldbuilding outlines)

Agent ingests all, makes searchable. Voor updates: new chapters automatisch geparsed.

## Character profile format

```yaml
# story_text/characters/thael.yaml
name: Thael
species: Silurian (Archivist type)
speech:
  formality: high
  vocabulary: archaic, scholarly
  mannerisms:
    - long pauses voor zinvolle statements
    - references naar ancient events
    - declines using contractions
  catchphrases:
    - "In the long view..."
    - "Such matters require contemplation"
  forbidden:
    - casual slang
    - technological jargon (niet past bij archivist)
relationships:
  glitch: curious allies
  cathleen: protective
  ancient_one: reverent
character_arc:
  current: adjusting to modern cooperation
  trajectory: accepting new allies
canon_facts:
  - "Shares memory-entity heritage met other Archivists"
  - "Millennia old consciousness"
```

Agent gebruikt dit bij voice validation.

## Integration met game productie

**Mission briefings Black Ledger:**
- Rex Varn character profile
- Mission context van game data
- Agent generates dialog options
- Jury validates before accepting

**Surilians chapter expansion:**
- Alex writes new content
- Agent reviews tegen canon
- Flags contradictions
- Suggests fixes

**NPC dialog NORA:**
- In-game characters (driving instructor, etc)
- Nieuwe character profiles
- Generated met narrative-quality dialog

## Test Scenario's

1. New Surilians chapter → canon check tegen chapters 0-9
2. Dialog voor Glitch in Black Ledger → voice validation
3. Character saying something out-of-canon → flag met specifics
4. Cross-product reference issue → escalate naar Alex

## Success Metrics

- Canon violation detection: > 90%
- Character voice accuracy: > 80%
- World coherence catches: > 85%
- False positives: < 15%

## Output

Per text submission:
- Verdict met specific feedback
- Canon references used
- Character voice analysis
- Suggested revisions

## Integratie

- Bible in Qdrant, used door:
  - Storyboard Visual Agent (27) voor visual canon
  - Narrative Jury (07) voor prose quality
- Output feeds storyboard briefs
- Dialog output naar Godot Import (26) als game text
