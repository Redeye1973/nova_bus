# 05. PyQt5 Assembly — Batch Processing en Packaging

## Doel
Alle sprite work samenvoegen tot production-ready asset packages voor Godot. Dit is waar NOVA v2's bestaande PyQt5 pipeline ervaring direct toepasbaar is.

## Waarom PyQt5 (en niet Aseprite voor dit)

PyQt5 QImage/QPainter zijn bewezen binnen NOVA v2:
- Black Ledger 432 enemy sprites gegenereerd via deze aanpak
- Werkt waar Krita CLI faalde
- Volledige control over pixel manipulation
- Geen GUI dependencies (headless draaien)
- Integratie met andere Python pipeline delen

Voor bulk operations is PyQt5 sneller dan Aseprite CLI.

## Wat deze fase doet

Taken per ship na Aseprite polish:
1. Sprite sheet aggregatie (alle variants per faction samen)
2. Animation timing JSON generatie
3. Godot-compatible SpriteFrames XML/JSON
4. Texture atlases voor performance
5. Metadata consolidation
6. Asset versioning

## Folder structuur output

```
assets_final/
├── ships/
│   ├── player/
│   │   ├── rex_fighter_basic_sheet.png
│   │   ├── rex_fighter_basic_metadata.json
│   │   ├── rex_fighter_mid_sheet.png
│   │   ├── rex_fighter_max_sheet.png
│   │   └── ...
│   ├── enemies/
│   │   ├── corporate/
│   │   │   ├── corp_fighter_mk1_sheet.png
│   │   │   ├── corp_fighter_mk1_data.json
│   │   │   └── ... (6 variants)
│   │   ├── pirates/
│   │   │   └── ...
│   │   └── aliens/
│   │       └── ...
│   └── bosses/
│       └── ...
├── projectiles/
│   ├── plasma_bolts_atlas.png
│   ├── missiles_atlas.png
│   └── atlas_data.json
├── effects/
│   ├── explosions_atlas.png
│   ├── explosions_data.json
│   └── ...
├── power_ups/
│   └── powerups_atlas.png
└── manifest.json
```

## Cursor prompt: Asset assembler

```
Bouw een NOVA v2 shmup asset assembler met PyQt5:

1. Python script `assembly/sprite_sheet_builder.py`:
   - Input: folder met individual PNG frames
   - Use QImage en QPainter voor compositing
   - Output: single sprite sheet PNG met grid layout
   - Metadata JSON met frame coordinates
   - Handle verschillende sizes per sheet
   - Optimal packing algorithm (skyline bin packing)

2. Python script `assembly/atlas_creator.py`:
   - Voor small sprites (projectiles, power-ups):
     - Pack multiple small sprites in one texture atlas
     - Reduce draw calls in Godot
   - Use rectpack library voor efficient packing
   - Output: atlas PNG + JSON coordinaat map

3. Python script `assembly/animation_metadata.py`:
   - Parse Aseprite output metadata
   - Convert to Godot SpriteFrames format
   - Animation definitions:
     - rotation_0 t/m rotation_15 (per angle)
     - engine_idle (8 frames loop)
     - muzzle_flash (4 frames oneshot)
     - damage_intro, damage_loop, etc

4. Python script `assembly/variant_generator.py`:
   - Voor bulk enemy varianten:
     - Take base sprite sheet
     - Apply color substitutions (palette swapping)
     - Generate N variants automatisch
     - Bewaar in memory efficient format
   - Voorbeeld: 1 base fighter → 20 kleur varianten = 20 sheets

5. Python script `assembly/godot_exporter.py`:
   - Generate Godot 4 .tres files voor SpriteFrames
   - Proper resource_local_to_scene = true
   - Animation naming conventions
   - Export als .import files met juiste settings

6. Python script `assembly/manifest_builder.py`:
   - Crawl final assets folder
   - Build manifest.json met:
     - All assets with paths
     - Version info
     - Size stats
     - Checksums
   - Output: `assets_final/manifest.json`

7. Python script `assembly/quality_checker.py`:
   - Before export validation:
     - All sprites are multiple of 2 dimensions
     - No transparent pixels where there shouldn't be
     - Animation frame counts correct
     - Metadata matches actual files
   - Output: QA report

8. CLI wrapper `assembly/cli.py`:
   - `python cli.py build --variant corp_fighter_mk1`
   - `python cli.py build --all`
   - `python cli.py atlas --category projectiles`
   - `python cli.py export --godot-project ~/projects/BlackLedger`

9. FastAPI service wrapper voor N8n integration:
   - POST /assemble met variant config
   - Progress streaming via SSE
   - Output paths in response

Gebruik Python 3.11, PyQt5 (QImage, QPainter, QPixmap),
rectpack voor atlas packing, lxml voor Godot .tres files.
FastAPI voor service wrapper.
```

## PyQt5 patterns voor sprite work

**Loading en saving:**
```python
from PyQt5.QtGui import QImage, QPainter, QPixmap
from PyQt5.QtCore import Qt, QRect

# Load met alpha channel preserved
img = QImage('sprite.png')
img = img.convertToFormat(QImage.Format_ARGB32)

# Save PNG met no compression
img.save('output.png', 'PNG', 100)  # Quality param ignored voor PNG
```

**Composite sprite sheet:**
```python
def build_sprite_sheet(frame_paths, cols=4, frame_size=(64, 64)):
    rows = (len(frame_paths) + cols - 1) // cols
    sheet_width = cols * frame_size[0]
    sheet_height = rows * frame_size[1]
    
    sheet = QImage(sheet_width, sheet_height, QImage.Format_ARGB32)
    sheet.fill(Qt.transparent)
    
    painter = QPainter(sheet)
    
    for i, path in enumerate(frame_paths):
        frame = QImage(path)
        col = i % cols
        row = i // cols
        x = col * frame_size[0]
        y = row * frame_size[1]
        painter.drawImage(x, y, frame)
    
    painter.end()
    return sheet
```

**Color substitution voor variants:**
```python
def color_substitute(image, color_map):
    """
    Replace colors according to map.
    color_map: {(r,g,b,a): (r,g,b,a)} source -> target
    """
    width, height = image.width(), image.height()
    result = QImage(width, height, QImage.Format_ARGB32)
    
    for y in range(height):
        for x in range(width):
            pixel = image.pixel(x, y)
            rgba = (
                (pixel >> 16) & 0xFF,
                (pixel >> 8) & 0xFF,
                pixel & 0xFF,
                (pixel >> 24) & 0xFF
            )
            
            if rgba in color_map:
                new = color_map[rgba]
                new_pixel = (new[3] << 24) | (new[0] << 16) | (new[1] << 8) | new[2]
                result.setPixel(x, y, new_pixel)
            else:
                result.setPixel(x, y, pixel)
    
    return result
```

**Note:** Voor veel pixels is numpy + PIL sneller dan QImage pixel-by-pixel. Mix tools afhankelijk van taak.

## Performance optimalisaties

**Bulk processing:**
- Parallel met multiprocessing (één ship per worker)
- Shared image cache voor materials
- Avoid QPainter overhead door numpy voor pure pixel ops

**Memory management:**
- Process één ship at a time, flush voor volgende
- QImage takes significant RAM voor large sheets
- Explicit del + gc.collect() na elke ship

**Disk efficiency:**
- Write final PNG direct, skip intermediate files
- Use tempfile voor work-in-progress
- Cleanup after completion

## Atlas vs separate sheets

**Wanneer één atlas:**
- Small sprites (< 64x64)
- Frequently gebruikt samen (projectiles per weapon type)
- Same draw call preferred (UI elements)

**Wanneer separate sheets:**
- Large sprites (boss ships)
- Independent loading (per act/level)
- Animation complexity (ships met veel states)

Rule of thumb: group gerelateerde low-frequency sprites samen. Split high-frequency individuele assets.

## Godot 4 integration setup

Elke asset die naar Godot gaat heeft:

```gdscript
# Voorbeeld .tres file content voor SpriteFrames
[gd_resource type="SpriteFrames" load_steps=5 format=3]

[ext_resource type="Texture2D" path="res://assets/ships/enemies/corp_fighter_mk1_sheet.png" id="1"]

[sub_resource type="AtlasTexture" id="atlas_0"]
atlas = ExtResource("1")
region = Rect2(0, 0, 64, 64)

[sub_resource type="AtlasTexture" id="atlas_1"]
atlas = ExtResource("1")
region = Rect2(64, 0, 64, 64)

# ... etc per frame

[resource]
animations = [{
    "frames": [{
        "duration": 1.0,
        "texture": SubResource("atlas_0")
    }, {
        "duration": 1.0,
        "texture": SubResource("atlas_1")
    }],
    "loop": false,
    "name": "rotation_0",
    "speed": 10.0
}]
```

Python script genereert deze automatisch uit sprite sheets.

## Quality gates

Na PyQt5 assembly, voor export:

**Automated checks:**
- All sheets hebben correct power-of-two dimensions
- Metadata JSON validates tegen schema
- No duplicate variant names
- File sizes redelijk (warn bij > 10MB per sheet)

**Handmatig review:**
- Variant diversity (kleur substitutions werken?)
- Atlas packing efficient (weinig wasted space?)
- Animation timing voelt natuurlijk?

## Integration met NOVA v2 Sprite Jury

Voor export: run Sprite Jury op finaal assembled sheets:
- Pixel integrity check
- Silhouette leesbaarheid  
- Style consistency binnen package
- Damage progression validation

Bij rejection: terug naar Aseprite stap voor fixes, niet helemaal opnieuw.

## Output van deze fase

Per faction/category:
- Assembled sprite sheets PNG
- Godot-ready .tres files
- Animation metadata JSON
- Atlas textures voor small sprites
- Master manifest.json voor het hele pakket

## Versioning strategie

Elke asset package heeft:
- Version tag (semver)
- Changelog sinds vorige versie
- Git commit hash van source
- Build timestamp

Deze metadata in manifest.json. Maakt rollback mogelijk bij issues.

## Volgende stap

Assembled assets → 06_godot_import.md voor game engine integratie.
