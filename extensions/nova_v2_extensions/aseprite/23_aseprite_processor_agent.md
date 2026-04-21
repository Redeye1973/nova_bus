# 23. Aseprite Processor Agent

## Doel
CLI-gedreven Aseprite automation voor batch sprite processing. Palette enforcement, format conversion, sprite sheet export.

## Scope
- Blender renders → Aseprite indexed palette
- Master palette remapping
- Edge cleanup via Lua scripts
- Sprite sheet generation met Aseprite CLI
- Animation metadata (tags) management

## Jury (3 leden, medium)

**1. Palette Adherence Validator**
- Tool: Python + PIL
- Check 100% pixels uit master palette
- Detect non-palette pixels (shouldn't exist after remap)
- Histogram analysis

**2. Sprite Sheet Layout Checker**
- Tool: Python + PIL
- Verify grid alignment (frames op exacte pixel boundaries)
- Check no overlap tussen frames
- Validate metadata matches actual frames

**3. Animation Tag Validator**
- Tool: Python + Aseprite JSON parser
- Check tags consistent (rotation_0 t/m rotation_15, damage_pristine, etc)
- Verify frame counts per tag expected
- Validate frame durations consistent

## Judge

- Accept: ready voor PyQt5 assembly
- Revise: auto-fix (re-run processing) of manual Aseprite edit
- Reject: fundamenteel probleem, terug naar Blender

## Cursor Prompt

```
Bouw NOVA v2 Aseprite Processor Agent:

1. Python service `aseprite/processor.py`:
   - FastAPI POST /process
   - Input: {source_folder, output_folder, palette, animations_config}
   - Orchestrate Aseprite CLI calls
   - Handle failure retry
   - Output: processed files + metadata

2. Python module `aseprite/cli_wrapper.py`:
   - Wrapper around Aseprite CLI
   - Functions:
     - convert_to_indexed(input, output, palette)
     - run_lua_script(input, script, output)
     - export_spritesheet(input, output, metadata_path)
     - import_palette(file)
   - Aseprite path configurable (env var ASEPRITE_PATH)

3. Aseprite Lua scripts `aseprite/scripts/`:
   - palette_remap.lua - Force all pixels to master palette
   - edge_cleanup.lua - Remove orphan pixels
   - animation_tag_creator.lua - Programmatically add tags
   - frame_resizer.lua - Adjust canvas per frame

4. Python module `aseprite/palette_converter.py`:
   - Convert palette.yaml (from Design Fase) naar .aseprite-palette format
   - Handles Aseprite's ASE/GPL/HEX palette formats

5. Python module `aseprite/batch_processor.py`:
   - Loop over folder of Blender renders
   - Per file: processing chain (import → remap → cleanup → export)
   - Progress tracking
   - Parallel processing (multiple Aseprite instances)

6. Python module `aseprite/palette_validator.py`:
   - Jury member 1
   - Load sprite, extract pixel colors
   - Compare tegen master palette (exact match)
   - Report non-palette pixels met locations

7. Python module `aseprite/layout_checker.py`:
   - Jury member 2
   - Load sprite sheet
   - Verify grid alignment
   - Check metadata matches actual content

8. Python module `aseprite/tag_validator.py`:
   - Jury member 3
   - Parse Aseprite JSON metadata
   - Validate tags compleet en consistent

9. Python module `aseprite/processor_judge.py`:
   - Aggregate verdict

10. Docker setup (Aseprite needs license - handle per legal docs)
    - Alternative: use LibreSprite (open source fork) als Aseprite niet beschikbaar

Gebruik Python 3.11, FastAPI, subprocess, Pillow.
Aseprite CLI via command line invocation.
```

## Aseprite CLI critical commands

```bash
# Convert to indexed met specific palette
aseprite -b --color-mode indexed --palette master.ase \
    input.png --save-as output.aseprite

# Run Lua script
aseprite -b input.aseprite --script scripts/palette_remap.lua

# Export sprite sheet + metadata
aseprite -b input.aseprite \
    --sheet output_sheet.png \
    --data output_data.json \
    --format json-array \
    --list-tags \
    --sheet-pack
```

## Test Scenario's

1. Blender render folder → indexed sprites met master palette
2. Non-palette pixels in input → forced to nearest palette color
3. Missing animation tags → auto-generated
4. Malformed Aseprite file → graceful error

## Success Metrics

- Palette adherence: 100% (zero non-palette pixels)
- Sprite sheet layout: 100% grid-aligned
- Animation tags: 100% expected tags present
- Batch success rate: > 95%

## Output

Per batch:
- .aseprite files (editable sources)
- Sprite sheet PNG
- JSON metadata (frames, tags, timing)
- Quality report

## Integratie

- Input van Blender Game Renderer (22)
- Output naar PyQt5 Assembly (25)
- Aseprite Animation Jury (24) doet dieper quality check
- Palette komt van Design Fase Agent (20)

## Handmatig vs Automated split

Automated (agent handelt zelf):
- Standard enemy varianten
- Projectile sprites
- UI elements
- Power-ups

Manual queue (requires human Aseprite editing):
- Hero player ship
- Unique bosses
- Animated characters met veel expressie
- Signature effects

Agent routeert automatisch naar manual queue waar nodig.
