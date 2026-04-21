# 03. Blender Rendering — Multi-angle Sprites

## Doel
FreeCAD STEP models omzetten naar pixel-perfecte sprite renders. Dit is waar de visuele kwaliteit wordt bepaald.

## Waarom Blender

**Materials en shading:**
- PBR metals voor ship hulls
- Emissive materials voor engines/weapons
- Subsurface scattering voor cockpit bubbles
- Procedural weathering (scratches, stains)

**Rendering engines:**
- Cycles: hoogste kwaliteit, slower
- Eevee: snel, goed genoeg voor sprite work
- Eevee aanbevolen voor productie

**Automation:**
- Python scripting volledig
- Headless rendering (geen GUI needed)
- Batch processing
- Compositor nodes voor post-processing

## Rendering pipeline per ship

```
Import STEP (1 file)
    ↓
Apply materials (per faction template)
    ↓
Setup scene (lights, camera)
    ↓
Render 16 angles (rotation loop)
    ↓
Per damage state: modifier material values
    ↓
Post-process in compositor (pixel perfect)
    ↓
Output: sprite sheet per damage state
```

## Critical rendering settings

**Voor pixel-perfect results:**

```python
# Blender Python snippet
bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 256  # 4x target
bpy.context.scene.render.resolution_y = 256
bpy.context.scene.render.resolution_percentage = 100

# Anti-aliasing off voor pixel art
bpy.context.scene.eevee.taa_render_samples = 1

# Of: hoge samples + aggressive pixelation in compositor
bpy.context.scene.eevee.taa_render_samples = 64

# Film filter pixel perfect
bpy.context.scene.render.filter_size = 1.5

# Output format
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.render.image_settings.color_mode = 'RGBA'
bpy.context.scene.render.image_settings.compression = 0
```

## Material library

Maak `materials.blend` asset library met pre-configured materials:

**Ship hull materials:**
- hull_navy_pristine (Rex Varn default)
- hull_navy_damaged (scratches, scorch)
- hull_navy_critical (major damage, sparks)
- hull_rust_pristine (Corporate)
- hull_rust_damaged
- hull_rust_critical
- hull_purple_pristine (Pirates)
- ... etc per faction

**Engine materials:**
- engine_blue_glow (player)
- engine_orange_fire (corporate)
- engine_purple_plasma (pirate)

**Weapon emissive:**
- plasma_white
- laser_pink
- missile_trail

**Cockpit:**
- cockpit_cyan_glass
- cockpit_amber_glass

Alle materials met slots voor damage blending.

## Lighting rig

Standardize lighting via append/link asset:

```python
def setup_standard_lighting(scene):
    # Sun light (main)
    sun = bpy.data.lights.new('SunKey', 'SUN')
    sun.energy = 3.0
    sun.color = (1.0, 0.98, 0.90)  # Warm white
    sun_obj = bpy.data.objects.new('SunKey', sun)
    scene.collection.objects.link(sun_obj)
    sun_obj.rotation_euler = (
        math.radians(45),  # 45 deg down
        0,
        math.radians(30)   # 30 deg azimuth
    )
    
    # Fill light (cool blue from opposite)
    fill = bpy.data.lights.new('Fill', 'SUN')
    fill.energy = 0.6
    fill.color = (0.65, 0.75, 1.0)  # Cool blue
    fill_obj = bpy.data.objects.new('Fill', fill)
    scene.collection.objects.link(fill_obj)
    fill_obj.rotation_euler = (
        math.radians(30),
        0,
        math.radians(210)  # Opposite side
    )
    
    # Rim light (pure white from behind)
    rim = bpy.data.lights.new('Rim', 'SUN')
    rim.energy = 1.2
    rim.color = (1.0, 1.0, 1.0)
    rim_obj = bpy.data.objects.new('Rim', rim)
    scene.collection.objects.link(rim_obj)
    rim_obj.rotation_euler = (
        math.radians(20),
        0,
        math.radians(180)  # Directly behind
    )
```

Deze functie in elke render script. Guaranteert consistency.

## Camera setup

```python
def setup_orthographic_camera(scene, size_category='medium'):
    cam = bpy.data.cameras.new('SpriteCamera')
    cam.type = 'ORTHO'
    
    # Orthographic size per ship size
    sizes = {
        'small': 2.0,
        'medium': 3.0,
        'large': 4.0,
        'boss': 6.0,
        'mini_boss': 5.0
    }
    cam.ortho_scale = sizes[size_category]
    
    cam_obj = bpy.data.objects.new('SpriteCamera', cam)
    scene.collection.objects.link(cam_obj)
    
    # Position: slightly angled top-down
    cam_obj.location = (0, -3, 10)  # Back and up
    cam_obj.rotation_euler = (
        math.radians(15),  # 15 deg tilt (niet 90!)
        0,
        0
    )
    
    scene.camera = cam_obj
```

15 graden tilt is sweet spot. Geeft 3D volume zonder perspective van verre camera.

## Rotation rendering

```python
def render_rotation_frames(ship_obj, output_dir, frames=16, damage_state='pristine'):
    """Render ship from N angles around vertical axis."""
    
    angle_step = 360 / frames
    
    for i in range(frames):
        angle = i * angle_step
        ship_obj.rotation_euler = (0, 0, math.radians(angle))
        
        # Apply damage state materials
        apply_damage_state(ship_obj, damage_state)
        
        # Render
        scene = bpy.context.scene
        scene.render.filepath = os.path.join(
            output_dir,
            f'{damage_state}_angle{i:02d}.png'
        )
        bpy.ops.render.render(write_still=True)
```

## Compositor voor pixel-perfect output

Na rendering op 4x resolutie, downscale in compositor:

```python
def setup_pixelart_compositor():
    scene = bpy.context.scene
    scene.use_nodes = True
    tree = scene.node_tree
    
    # Clear existing
    for node in tree.nodes:
        tree.nodes.remove(node)
    
    # Render layer input
    render_layers = tree.nodes.new('CompositorNodeRLayers')
    
    # Scale down (pixelate)
    scale = tree.nodes.new('CompositorNodeScale')
    scale.space = 'RELATIVE'
    scale.frame_method = 'STRETCH'
    scale.inputs[1].default_value = 0.25  # 1/4
    scale.inputs[2].default_value = 0.25
    
    # No anti-aliasing interpolation
    scale.use_custom_color = True
    # Set filter type to 'CLOSEST' for pixel perfect
    
    # Output
    composite = tree.nodes.new('CompositorNodeComposite')
    
    # Connect
    tree.links.new(render_layers.outputs['Image'], scale.inputs[0])
    tree.links.new(scale.outputs[0], composite.inputs[0])
```

Of render direct op target size met lage samples. Beide werken.

## Cursor prompt: Complete render pipeline

```
Bouw een Blender rendering pipeline voor shmup sprites:

1. Python script `blender/render_ship.py`:
   - Entry point voor Blender: `blender --background --python render_ship.py -- --input ship.step --output ./renders/`
   - CLI args parsing (sys.argv na --)
   - Import STEP via Blender STEP importer addon
   - Apply materials from library
   - Setup lighting, camera
   - Render rotation frames per damage state
   - Post-process in compositor
   - Export individual PNG files

2. Python module `blender/material_library.py`:
   - Load materials.blend via append
   - Apply material by name to object
   - Handle damage state blending
   - Material slots management

3. Python module `blender/lighting_rig.py`:
   - Factory function setup_standard_lighting(scene)
   - Configurable intensities
   - Named lights voor later access

4. Python module `blender/camera_rig.py`:
   - Orthographic camera per size category
   - Angle preset
   - Framing helpers

5. Python module `blender/rotation_renderer.py`:
   - Function render_rotation_frames(obj, frames, ...)
   - Handles animation if engines moeten glowen
   - Batch writes PNG files

6. Python module `blender/compositor.py`:
   - Setup pixel-perfect compositor
   - Or alternative: setup high-sample + downscale approach
   - Configurable per sprite size

7. Python module `blender/damage_states.py`:
   - Material variations per damage level
   - Procedural damage (Blender modifiers: displacement, etc)
   - Color shifts towards "damaged" look

8. Python script `blender/batch_render.py`:
   - Input: variants.yaml (from FreeCAD stap)
   - For each variant: call render_ship.py
   - Tracks progress
   - Parallelization waar mogelijk (multiple Blender instances)

9. Python script `blender/sprite_assembly.py`:
   - Post-processing: combine rotation frames into sprite sheet PNG
   - Generate JSON metadata (frame positions, damage state mapping)
   - Output ready for Godot import

10. Shell script `render_all.sh`:
    - Wrapper script
    - Handles Blender path
    - Manages temp files
    - Final cleanup

Gebruik Blender 4.3+, Python 3.11, bpy API.
Headless: xvfb-run als display nodig is.
FastAPI service wrapper voor N8n integration.
```

## Materials best practices

**PBR waarden voor ship hulls:**
```
Metallic: 0.8-0.95 (highly metallic)
Roughness: 0.3-0.5 (matte metal, niet mirror)
Base Color: from palette
Subsurface: 0 (geen subsurface voor metal)
```

**Emissive voor engines:**
```
Emission Strength: 2-5
Emission Color: palette emissive
Enable Bloom in post-processing
```

**Glass cockpits:**
```
Transmission: 0.9
Roughness: 0.1
IOR: 1.45
Tint: palette cockpit color
```

## Damage state implementation

Drie benaderingen, van simpel naar complex:

**Niveau 1: Color shift only**
- Pristine: full saturation
- Damaged: desaturate 20%, warm tint
- Critical: desaturate 40%, more warm + darker

**Niveau 2: Texture blending**
- Base texture per faction
- Damage overlay texture (scratches, scorches)
- Blend factor per damage state
- Critical state: additional overlay (cracks, fire)

**Niveau 3: Geometry modifications**
- Missing pieces via boolean subtract
- Broken wings, torn panels
- Sparks particle systems
- Smoke trails

Start met niveau 1 voor quick results. Level 2 als je tijd hebt. Niveau 3 alleen voor hero ships en bosses.

## Performance optimalisaties

**Rendering tijd reduceren:**
- Eevee ipv Cycles voor sprite work
- Samples: 32 voor development, 64 voor final
- Denoising aan
- Viewport adaptive sampling

**Batch efficiency:**
- Één Blender instance per batch (avoid startup overhead)
- Pre-load materials library
- Keep scene open between ships (reset between renders)

**Disk usage:**
- PNG lossless nodig voor pixel art
- Compression level 0 in PNG (snelste read/write)
- Cleanup intermediate renders na sprite sheet assembly

## Tijdschattingen

Per ship complete render (16 angles x 3 damage states = 48 renders):

- Eevee, 32 samples, 256x256: ~5-10 minuten
- Eevee, 64 samples, 256x256: ~15-25 minuten
- Cycles, 128 samples, 256x256: ~30-60 minuten

Boss (16 angles x 5 damage states = 80 renders, 1024x1024): 1-3 uur per boss.

## Output van deze fase

Per ship:
- Folder met individual PNG renders per angle/state
- Sprite sheet PNG (assembled)
- Metadata JSON (frame coordinates, timing)
- Preview grid PNG (thumbnail overzicht)

## Quality check

Voordat naar Aseprite: visual inspection van:
- Lichting consistentie (alle angles same setup?)
- Damage progression (duidelijk slechter wordend?)
- Silhouette clarity (32x32 test)
- Color palette adherence (geen vreemde kleuren geïntroduceerd?)

NOVA v2 3D Model Jury kan dit automatisch valideren.

## Volgende stap

Renders klaar → naar 04_aseprite_polish.md voor finale pixel-level cleanup.
