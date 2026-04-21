# 25. PyQt5 Assembly Agent

## Doel
Finale sprite sheet + atlas assembly voor game engine consumption. Batch processing, texture packing, Godot resource generation.

## Scope
- Sprite sheet compositing
- Texture atlas packing (voor projectiles, effects)
- Godot .tres resource generation
- Manifest building
- Version management

## Jury (2 leden, licht - mostly technisch)

**1. Layout Efficiency Validator**
- Tool: Python
- Check: sprite sheet space usage > 70%
- Check: atlas packing efficient
- Detecteert: wasted space, poor bin packing

**2. Resource Integrity Checker**
- Tool: Python + Godot resource parser
- Check: alle .tres references valid
- Verify: metadata JSON matches images
- Check: no broken paths

## Judge

Accept → Ready voor Godot Import
Revise → Re-pack of regenerate references
Reject → Source data issue

## Cursor Prompt

```
Bouw NOVA v2 PyQt5 Assembly Agent:

1. Python service `pyqt_assembly/sprite_sheet_builder.py`:
   - FastAPI POST /build-sheet
   - Input: {source_folder, layout: 'grid|packed', cols?, rows?}
   - Use QImage/QPainter voor compositing
   - Grid layout: uniform frame size
   - Packed layout: skyline bin packing
   - Output: PNG + JSON metadata

2. Python service `pyqt_assembly/atlas_creator.py`:
   - FastAPI POST /atlas
   - Input: multiple small sprites
   - Use rectpack voor efficient packing
   - Generate coordinate map
   - Output: atlas PNG + coord map JSON

3. Python service `pyqt_assembly/godot_resource_generator.py`:
   - FastAPI POST /godot/generate
   - Input: sprite sheet + metadata + target type
   - Generate proper Godot 4 .tres files:
     - SpriteFrames voor animated sprites
     - AtlasTexture subresources
     - Proper animation definitions
   - Template-based met Jinja2

4. Python service `pyqt_assembly/manifest_builder.py`:
   - Crawl finale assets folder
   - Build comprehensive manifest.json:
     - All assets met paths
     - Versions, checksums
     - Size stats, memory estimates
   - Validation: referenced files exist

5. Python service `pyqt_assembly/version_manager.py`:
   - SemVer management
   - Changelog generation
   - Git integration (tag releases)

6. Python service `pyqt_assembly/layout_validator.py`:
   - Jury member 1
   - Analyze sheet efficiency
   - Atlas packing quality

7. Python service `pyqt_assembly/integrity_checker.py`:
   - Jury member 2
   - Validate references
   - Check paths valid
   - Verify metadata consistency

8. Python service `pyqt_assembly/assembly_judge.py`:
   - Lichte judge (2 leden)
   - Accept/revise routing

9. CLI tool voor local use

Gebruik Python 3.11, PyQt5, rectpack, Jinja2, FastAPI.
```

## Godot 4 .tres templates

**SpriteFrames template (Jinja2):**
```
[gd_resource type="SpriteFrames" load_steps={{ frames|length + 2 }} format=3]

[ext_resource type="Texture2D" path="{{ texture_path }}" id="1"]

{% for frame in frames %}
[sub_resource type="AtlasTexture" id="atlas_{{ loop.index0 }}"]
atlas = ExtResource("1")
region = Rect2({{ frame.x }}, {{ frame.y }}, {{ frame.w }}, {{ frame.h }})

{% endfor %}

[resource]
animations = [
{% for anim in animations %}
{
    "frames": [
    {% for frame_idx in anim.frame_indices %}
    {
        "duration": {{ anim.durations[loop.index0] }},
        "texture": SubResource("atlas_{{ frame_idx }}")
    }{{ "," if not loop.last }}
    {% endfor %}
    ],
    "loop": {{ anim.loop|lower }},
    "name": "{{ anim.name }}",
    "speed": {{ anim.speed }}
}{{ "," if not loop.last }}
{% endfor %}
]
```

## Test Scenario's

1. 48 Blender renders → sprite sheet + Godot SpriteFrames
2. 20 projectile sprites → efficient atlas
3. Missing source file → clear error
4. Version bump → changelog generated

## Success Metrics

- Sheet efficiency: > 70% space used
- Atlas efficiency: > 80% space used
- Godot resource validity: 100%
- Manifest accuracy: 100%

## Output

Per batch:
- Sprite sheet PNG
- Atlas PNG (indien applicable)
- .tres Godot resource files
- metadata.json
- manifest.json voor package
- Version tag + changelog entry

## Integratie

- Input van Aseprite Processor (23) + Animation Jury (24)
- Output naar Godot Import Agent (26)
- Sprite Jury (01) validates finale assembled sprites
- Distribution Agent (19) gebruikt manifest voor versioning
