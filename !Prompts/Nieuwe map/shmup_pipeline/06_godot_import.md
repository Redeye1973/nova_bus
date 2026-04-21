# 06. Godot 4 Engine Integratie

## Doel
Van assembled assets naar runtime-ready Godot 4 game. Asset import, scene setup, animation wiring, performance optimalisaties.

## Godot 4 project setup voor shmup

**Project structure:**
```
BlackLedger/
├── addons/              # Plugins
├── assets/
│   ├── ships/
│   │   ├── player/
│   │   ├── enemies/
│   │   └── bosses/
│   ├── projectiles/
│   ├── effects/
│   ├── backgrounds/
│   └── ui/
├── scenes/
│   ├── ships/
│   ├── levels/
│   ├── ui/
│   └── main.tscn
├── scripts/
│   ├── managers/
│   ├── entities/
│   └── utils/
├── resources/
│   ├── weapons/
│   ├── enemies/
│   └── missions/
└── project.godot
```

## Import settings voor pixel art

Critical voor sprites die er goed uit moeten zien:

**Project settings:**
```
Rendering → Textures → Default Texture Filter: Nearest
Rendering → 2D → Snap 2D Transforms to Pixel: On
Rendering → 2D → Snap 2D Vertices to Pixel: On
Display → Window → Stretch → Mode: viewport
Display → Window → Stretch → Aspect: keep
```

**Per-sprite import:**
```
Filter: Off (nearest neighbor)
Mipmaps: Off
Fix alpha border: On
Premultiply alpha: Off (depends op shader usage)
```

**Import settings via .import file (automation):**
```ini
[remap]
importer="texture"
type="CompressedTexture2D"

[deps]
source_file="res://assets/ships/player/rex_fighter_basic_sheet.png"

[params]
compress/mode=0  # Lossless
compress/lossy_quality=0.7
compress/hdr_compression=1
compress/bptc_ldr=0
compress/normal_map=0
compress/channel_pack=0
mipmaps/generate=false
mipmaps/limit=-1
roughness/mode=0
roughness/src_normal=""
process/fix_alpha_border=true
process/premult_alpha=false
process/normal_map_invert_y=false
process/hdr_as_srgb=false
process/hdr_clamp_exposure=false
process/size_limit=0
detect_3d/compress_to=1
```

## Cursor prompt: Godot asset importer

```
Bouw een Godot 4 asset import automation voor shmup:

1. Python script `godot/import_assembler.py`:
   - Read NOVA v2 assembly output (manifest.json)
   - Generate proper Godot .import files per asset
   - Generate SpriteFrames .tres files
   - Copy textures naar Godot project assets folder
   - Respects project structure conventions

2. Python script `godot/scene_generator.py`:
   - Generate Godot .tscn files voor standaard ship types:
     - player_ship.tscn (AnimatedSprite2D, CollisionShape2D, script)
     - enemy_fighter.tscn (per variant)
     - boss_template.tscn
   - Include proper node hierarchy
   - Wire up SpriteFrames references

3. GDScript templates `godot/templates/`:
   - `enemy_base.gd` - Standard enemy logic
   - `boss_base.gd` - Boss patterns
   - `projectile_base.gd` - Weapon behavior
   - Jinja2 templates met variable substitution

4. Python script `godot/animation_linker.py`:
   - Wire sprite animations naar game logic:
     - Rotation based op movement direction
     - Damage state based op health percentage
     - Engine animation based op thrust
   - Generate bindings GDScript snippets

5. Python script `godot/optimization_checker.py`:
   - Scan imported assets
   - Identify performance issues:
     - Duplicate textures (should atlas)
     - Oversized sprites voor usage
     - Unused animations
     - Memory estimates
   - Generate optimization report

6. Python script `godot/resource_builder.py`:
   - Generate .tres resources voor:
     - WeaponResource (stats, sprite refs)
     - EnemyResource (stats, scene path)
     - MissionResource
   - Follow Godot 4 Resource patterns

7. Godot project template:
   - `project.godot` met juiste settings
   - Input map voor shmup controls
   - Audio bus layout
   - Autoloads voor managers

8. Python script `godot/validator.py`:
   - Check dat alle references klopen
   - UIDs consistent
   - No broken paths
   - Report issues

9. CLI `godot/cli.py`:
   - `python cli.py import --variant corp_fighter_mk1 --project ~/BlackLedger`
   - `python cli.py scene --type enemy --variant <n>`
   - `python cli.py validate --project <path>`

Gebruik Python 3.11, Jinja2, toml voor .godot files,
proper UUID generation voor Godot UIDs.
```

## Scene template voor standaard enemy

```gdscript
# scripts/entities/enemy_fighter.gd
extends CharacterBody2D
class_name EnemyFighter

@export var enemy_data: EnemyResource
@export var sprite_frames: SpriteFrames
@export var move_speed: float = 100.0

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var collision: CollisionShape2D = $CollisionShape2D
@onready var health_component: HealthComponent = $HealthComponent

var current_angle: float = 0.0
var target_direction: Vector2 = Vector2.DOWN

func _ready() -> void:
    sprite.sprite_frames = sprite_frames
    health_component.max_health = enemy_data.max_health
    health_component.damage_taken.connect(_on_damage_taken)

func _physics_process(delta: float) -> void:
    velocity = target_direction * move_speed
    move_and_slide()
    _update_rotation_sprite()

func _update_rotation_sprite() -> void:
    # Map velocity direction to sprite rotation frame (16 frames = 360 deg)
    var angle = target_direction.angle()
    var angle_normalized = fmod(angle + TAU, TAU)
    var frame_index = int(angle_normalized / TAU * 16) % 16
    sprite.play("rotation_%d" % frame_index)

func _on_damage_taken(current_health: float, max_health: float) -> void:
    var health_pct = current_health / max_health
    var damage_state = "pristine"
    if health_pct < 0.33:
        damage_state = "critical"
    elif health_pct < 0.66:
        damage_state = "damaged"
    
    # Switch to appropriate sprite state
    sprite.sprite_frames = enemy_data.sprite_frames[damage_state]
```

Dit template werkt voor alle standard fighters. Per variant alleen enemy_data resource verschillend.

## Performance optimalisatie in Godot

**1. Sprite atlasing:**
- Multiple kleine sprites in één texture
- Godot ondersteunt native via AtlasTexture
- Vermindert draw calls dramatisch

**2. Instance pooling:**
- Enemy ships pool (instance spawning duur)
- Projectile pool (100+ op scherm mogelijk)
- Explosion effect pool

**3. Culling:**
- Off-screen enemies via VisibleOnScreenNotifier2D
- Pause processing wanneer off-screen
- Delete wanneer far off-screen

**4. Collision layers:**
- Player op layer 1
- Enemies op layer 2
- Player projectiles op layer 3
- Enemy projectiles op layer 4
- Proper masks om onnodige checks te voorkomen

**5. Particle systems:**
- Use GPUParticles2D voor effects
- CPU particles alleen bij kleine aantallen

## Object pooling pattern

```gdscript
# scripts/managers/projectile_pool.gd
extends Node
class_name ProjectilePool

@export var projectile_scene: PackedScene
@export var pool_size: int = 100

var pool: Array[Node2D] = []
var active: Array[Node2D] = []

func _ready() -> void:
    for i in pool_size:
        var proj = projectile_scene.instantiate()
        proj.process_mode = Node.PROCESS_MODE_DISABLED
        proj.visible = false
        add_child(proj)
        pool.append(proj)

func spawn(position: Vector2, direction: Vector2, stats: Dictionary) -> Node2D:
    if pool.is_empty():
        push_warning("Pool exhausted, instancing new")
        var new_proj = projectile_scene.instantiate()
        add_child(new_proj)
        pool.append(new_proj)
    
    var proj = pool.pop_back()
    active.append(proj)
    
    proj.global_position = position
    proj.direction = direction
    proj.apply_stats(stats)
    proj.process_mode = Node.PROCESS_MODE_INHERIT
    proj.visible = true
    
    proj.expired.connect(_return_to_pool.bind(proj), CONNECT_ONE_SHOT)
    
    return proj

func _return_to_pool(proj: Node2D) -> void:
    active.erase(proj)
    proj.process_mode = Node.PROCESS_MODE_DISABLED
    proj.visible = false
    pool.append(proj)
```

## Visual polish in Godot

**CanvasLayer voor parallax backgrounds:**
- 3-5 layers voor starfield depth
- Verschillende scroll speeds
- Tiles repeated via texture

**Post-processing via WorldEnvironment:**
- Bloom voor engine/weapon glow
- Vignette voor focus on play area
- Chromatic aberration subtle

**Screen shake:**
- Camera2D met offset shake
- Per explosion intensity
- Satisfies "game feel" zoals Raptor had

**Particle effects voor juice:**
- Engine exhaust trails
- Damage sparks
- Explosion debris + smoke
- Power-up pickups glow

## Shader tips voor shmup

**Hit flash shader:**
```glsl
shader_type canvas_item;

uniform float flash_amount : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);

void fragment() {
    vec4 tex = texture(TEXTURE, UV);
    vec4 flash = vec4(flash_color.rgb, tex.a * flash_amount);
    COLOR = mix(tex, flash, flash_amount);
}
```

Apply aan sprite wanneer enemy damage krijgt. Classieke shmup feel.

**Engine glow shader:**
- Additive blending voor engine exhaust
- Pulsing via sin(TIME)
- Color shift voor power-up state

## Testing in Godot

Per asset import:
- Open scene in editor
- Scene run (F6) test
- Check: animations play correctly
- Check: collision shapes accurate
- Check: movement feels right

Automate via:
```gdscript
# scenes/testing/asset_validator.tscn
# Play-mode scene die elke enemy spawnt, test movement, destruction
# Rapporteer issues naar console
```

## Integration met NOVA v2

Bij asset update via pipeline:
1. Pipeline produceert nieuwe version
2. Distribution Agent uploadt naar MinIO
3. Godot project heeft hot-reload script
4. Bij development: auto-refresh assets
5. Bij production: requires rebuild

## Tijd per ship type

Met automation:
- Import + scene gen: 5 minuten per variant
- Animation wiring: 2 minuten per variant
- Custom behavior (bosses): 1-4 uur per unique
- Testing + tweaks: 30 min per variant

Voor 20 enemy variants: ~2-3 uur total.
Voor 5 unique bosses: ~10-20 uur total.

## Output van deze fase

Compleet functioneel shmup project:
- Alle ships importeerbaar
- Enemy varianten werkend
- Bosses met unieke patterns
- Player ship met upgrade tiers
- Projectiles + effects
- Ready voor level design

## Quality checklist

Voor finale release:
- [ ] 60 FPS stable met 50+ enemies op scherm
- [ ] Geen memory leaks (monitor over 10 min gameplay)
- [ ] Asset loading < 3 seconden voor level start
- [ ] Alle animations smooth (geen stutters)
- [ ] Audio sync met visuals
- [ ] Proper error handling bij missing assets

## Volgende stap

Alles werkt → 07_jury_validation.md voor finale NOVA v2 kwaliteitscontrole.
