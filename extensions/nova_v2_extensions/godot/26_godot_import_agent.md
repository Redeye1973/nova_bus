# 26. Godot Import Agent

## Doel
Automated Godot 4 project integration. Van PyQt5 Assembly output naar runnning game code.

## Scope
- .import file generation (juiste settings)
- Scene template generation
- GDScript skeleton generation
- Asset path management
- UID consistency

## Jury (3 leden, medium)

**1. Import Settings Validator**
- Tool: Python + .import parser
- Check: nearest neighbor filter (voor pixel art)
- Check: no mipmaps, no compression (voor 2D)
- Verify: consistent settings across related assets

**2. Scene Structure Validator**
- Tool: Python + Godot scene parser
- Check: node hierarchy correct per entity type
- Verify: required nodes present (CollisionShape2D, etc)
- Check: script attachments

**3. Runtime Integration Tester**
- Tool: Godot headless test mode
- Load scene in test harness
- Verify: geen errors bij instantiate
- Basic gameplay test (spawn enemy, move, collide)

## Judge

Accept → Scene ready voor use
Revise → Fix specific settings/structure
Reject → Fundamental issue, review asset

## Cursor Prompt

```
Bouw NOVA v2 Godot Import Agent:

1. Python service `godot_import/import_file_generator.py`:
   - FastAPI POST /import/generate
   - Input: {asset_path, asset_type, project_root}
   - Template-based .import file generation
   - Per asset type specific settings:
     - Pixel sprite: filter=off, mipmaps=off, compression=lossless
     - Background: filter=off, mipmaps=off, compression=vram compressed
     - UI: filter=off, no compression
   - Output: .import file naast asset

2. Python service `godot_import/scene_generator.py`:
   - FastAPI POST /scene/generate
   - Input: {entity_type, config}
   - Templates per type:
     - player_ship.tscn
     - enemy_fighter.tscn
     - boss_template.tscn
     - projectile.tscn
   - Proper node hierarchy
   - Script attachments
   - Default properties

3. Python service `godot_import/gdscript_generator.py`:
   - FastAPI POST /script/generate
   - Input: {entity_type, customizations}
   - Generate skeleton .gd files
   - Type hints, structured pattern
   - Extend base classes

4. Python service `godot_import/path_manager.py`:
   - Manage res:// paths correctly
   - Consistent naming conventions
   - Prevent path collisions
   - UID management

5. Python service `godot_import/project_integrator.py`:
   - Copy assets naar Godot project
   - Update project.godot als nodig
   - Input map, autoloads, etc

6. Python service `godot_import/settings_validator.py`:
   - Jury member 1
   - Parse .import files
   - Check settings correct per type

7. Python service `godot_import/structure_validator.py`:
   - Jury member 2
   - Parse .tscn files
   - Validate node structure

8. Python service `godot_import/runtime_tester.py`:
   - Jury member 3
   - Spawn godot --headless process
   - Load scene, check for errors
   - Timeout + cleanup

9. Python service `godot_import/import_judge.py`:
   - Aggregate verdict

10. Base GDScript classes library:
    - BaseEnemy.gd
    - BaseBoss.gd
    - BaseProjectile.gd
    - BasePlayerShip.gd

Gebruik Python 3.11, Jinja2 voor templates, subprocess voor Godot.
```

## Template example: enemy_fighter.tscn

```jinja
[gd_scene load_steps=5 format=3 uid="uid://{{ scene_uid }}"]

[ext_resource type="Script" path="res://scripts/entities/enemy_fighter.gd" id="1"]
[ext_resource type="SpriteFrames" path="{{ sprite_frames_path }}" id="2"]
[ext_resource type="Resource" path="{{ enemy_resource_path }}" id="3"]

[sub_resource type="CircleShape2D" id="CollisionShape"]
radius = {{ collision_radius }}

[node name="{{ node_name }}" type="CharacterBody2D"]
collision_layer = 2
collision_mask = 5

[node name="AnimatedSprite2D" type="AnimatedSprite2D" parent="."]
sprite_frames = ExtResource("2")
animation = "rotation_0"

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("CollisionShape")

[node name="HealthComponent" type="Node" parent="."]

[node name="EnemyScript" parent="." instance=ExtResource("1")]
enemy_data = ExtResource("3")
```

## Test Scenario's

1. Nieuwe enemy asset → complete Godot integration (scene + script + resource)
2. Pixel sprite → correct import settings (nearest filter)
3. Broken asset path → clear error + fix suggestion
4. Scene load test fails → specific runtime error captured

## Success Metrics

- Import settings correctness: 100%
- Scene structure validity: 100%
- Runtime load success: > 95%
- Integration tijd: < 5 min per asset

## Output

Per asset integration:
- Asset file in juiste Godot folder
- .import file met correct settings
- .tscn scene file
- .gd script (indien nieuw)
- .tres resource (indien nieuw)
- Validation report

## Integratie

- Input van PyQt5 Assembly (25)
- Output: assets ready in Godot project
- Code Jury (02) valideert generated GDScript
- Integration test voordat main branch merge
