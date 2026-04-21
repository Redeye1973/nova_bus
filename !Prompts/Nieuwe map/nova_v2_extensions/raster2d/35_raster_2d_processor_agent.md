# 35. GIMP/Krita/Inkscape Processor Agent

## Doel
Universele orchestrator voor 2D raster/vector tools. CLI automation voor batch processing van 2D assets.

## Scope
- GIMP: photo editing, texture processing, batch operations
- Krita: digital painting workflows, brush-based art
- Inkscape: vector illustration, SVG export voor UI

## Jury (3 leden, medium)

**1. Format Compliance Validator**
- Tool: Python + file parsers
- Check: output format correct voor use case
- Verify: PSD/XCF/KRA/SVG validity
- Detect: corrupted files

**2. Layer Structure Reviewer**
- Tool: PSD/XCF/KRA parsers
- Check: proper layer naming
- Verify: essential layers present (per project standards)
- Detect: flattened waar niet bedoeld

**3. Export Quality Checker**
- Tool: PIL + format validation
- Check: exports have correct settings (DPI, colorspace, compression)
- Verify: alpha channel correct
- Size vs quality trade-offs

## Judge

Accept → Ready for next pipeline stage
Revise → Fix specific issues
Reject → Source file problematic

## Cursor Prompt

```
Bouw NOVA v2 GIMP/Krita/Inkscape Processor Agent:

1. Python service `raster2d/gimp_automation.py`:
   - FastAPI POST /gimp/process
   - Input: {input_file, script_fu_commands of Python-Fu}
   - Subprocess call: gimp -i -b "batch_command"
   - Or: gimp --no-interface with Python-Fu
   - Common operations:
     - batch_resize
     - batch_export_layers (per layer PNG)
     - color_correction
     - auto_level
   - Output: processed files

2. Python service `raster2d/krita_automation.py`:
   - FastAPI POST /krita/process
   - Krita has Python scripting (Scripter)
   - Headless via: krita --script-run
   - Common operations:
     - brush_stroke_batch
     - export_flatten
     - thumbnail_generation
   - PyKrita API voor in-Krita scripting

3. Python service `raster2d/inkscape_automation.py`:
   - FastAPI POST /inkscape/process
   - Excellent CLI: inkscape --actions="..."
   - Common operations:
     - export_png (with specific DPI)
     - export_pdf
     - batch_process_svgs
     - optimize_svg

4. Python service `raster2d/format_converter.py`:
   - Convert between formats:
     - PSD ↔ XCF ↔ KRA
     - SVG → PNG/PDF
     - Raster → vector (limited via potrace)
   - Batch operations

5. Python service `raster2d/layer_extractor.py`:
   - Parse PSD/XCF/KRA
   - Export each layer as PNG
   - Useful voor game asset separation
   - Use psd-tools, gimpformats, kra-read

6. Python service `raster2d/batch_orchestrator.py`:
   - FastAPI POST /batch/process
   - Input: {folder, operation, parameters}
   - Apply operation to all files in folder
   - Parallel processing waar mogelijk
   - Progress tracking

7. Python service `raster2d/format_validator.py`:
   - Jury member 1
   - Open file, verify integrity
   - Check format correctness

8. Python service `raster2d/layer_reviewer.py`:
   - Jury member 2
   - Parse file structure
   - Check expected layers present
   - Report structural issues

9. Python service `raster2d/export_quality_checker.py`:
   - Jury member 3
   - PIL analysis of exports
   - DPI, colorspace, compression checks

10. Python service `raster2d/raster2d_judge.py`:
    - Aggregate verdict

11. Script libraries:
    - gimp_scripts/ (Script-Fu + Python-Fu)
    - krita_scripts/ (Python)
    - inkscape_scripts/ (XML actions, extensions)

Gebruik Python 3.11, FastAPI, psd-tools, gimpformats, kra-read,
subprocess voor tool invocations.
```

## Common operations per tool

**GIMP use cases:**
- Photo batch processing (resize, color correct, watermark)
- Texture preparation (tile, seamless make, normal maps via Insane Bump)
- Old workflow conversions (batch PSD → PNG)
- Mask generation

**Krita use cases:**
- Brush-based character illustrations
- Concept art painting
- Comic panel artwork
- Animations (Krita heeft animation timeline)

**Inkscape use cases:**
- Game UI vectors (icons, buttons, HUD elements)
- Logo creation
- Infographics
- Print layouts

## Script examples

**GIMP Python-Fu voor batch resize:**
```python
# save as gimp_scripts/batch_resize.py
# Run via: gimp --no-interface --batch="(python-fu-batch-resize 'folder/' 800 600)" --batch="(gimp-quit 0)"

from gimpfu import *
import os, glob

def batch_resize(folder, width, height):
    for filename in glob.glob(os.path.join(folder, "*.png")):
        image = pdb.gimp_file_load(filename, filename)
        pdb.gimp_image_scale(image, width, height)
        pdb.gimp_image_flatten(image)
        pdb.file_png_save(image, image.active_drawable, 
                          filename.replace('.png', '_resized.png'),
                          'result', 0, 9, 1, 1, 1, 1, 1)
        pdb.gimp_image_delete(image)

register("python-fu-batch-resize",
         "Batch resize images",
         "Resize all PNGs in folder",
         "NOVA", "NOVA", "2026",
         "<Toolbox>/NOVA/Batch Resize",
         "",
         [(PF_STRING, "folder", "Folder", "."),
          (PF_INT, "width", "Width", 800),
          (PF_INT, "height", "Height", 600)],
         [],
         batch_resize)

main()
```

**Inkscape CLI voor SVG export:**
```bash
# Batch export SVG naar PNG met 300 DPI
for svg in *.svg; do
    inkscape --export-type=png --export-dpi=300 "$svg"
done

# Via Python subprocess met variable DPI
python -c "
import subprocess, os, glob
for svg in glob.glob('*.svg'):
    subprocess.run(['inkscape', '--export-type=png', '--export-dpi=300', svg])
"
```

**Krita Python (headless):**
```python
# krita_scripts/export_layers.py
# Run via: krita --script-run export_layers.py file.kra

from krita import *

doc = Krita.instance().activeDocument()
root = doc.rootNode()

for node in root.childNodes():
    if node.visible():
        node.save(f"/output/{node.name()}.png", doc.xRes(), doc.yRes(), 
                  InfoObject(), doc.bounds())
```

## Integration met andere agents

**Krita + Storyboard Visual (27):**
- Storyboard panel generation
- Individual panel painting
- Export naar composite

**GIMP + 2D Illustration Jury (09):**
- Post-processing van illustraties
- Color correction
- Format conversion voor delivery

**Inkscape + UI Design:**
- Game UI elements
- HUD components
- Export naar Godot-ready SVG/PNG

**Inkscape + GIS:**
- Map legends
- Symbology
- Print layout annotations

## Test Scenario's

1. Batch resize 100 PNGs via GIMP → all processed uniformly
2. Export PSD layers to individual files → structured output
3. Convert SVG icons naar multiple sizes → proper DPI
4. Krita illustration painting → clean export

## Success Metrics

- Format compliance: 100%
- Batch processing success rate: > 95%
- Speed vs manual: 10x+ faster
- Quality consistent met manual output

## Output

Per job:
- Processed files in output folder
- Metadata JSON
- Log van operaties
- Error report indien applicable

## Integratie

- Complement aan Aseprite Processor (23) voor non-pixel art
- Validates via 2D Illustration Jury (09)
- Works with Character Art Jury (08) voor illustrated characters
- Feeds Storyboard Visual (27) voor panel art

## Per tool strengths

**When to use GIMP:**
- Photo manipulation
- Texture work (normal maps, tileable)
- Batch operations via Script-Fu
- Free alternative waar Photoshop hoort

**When to use Krita:**
- Digital painting
- Concept art
- Comic creation
- Animation (basic)

**When to use Inkscape:**
- Vector work (any SVG needs)
- Technical illustrations
- UI design (scalable)
- Logo design

Alle drie zijn open source en passen in NOVA v2 filosofie van geen vendor lock-in.
