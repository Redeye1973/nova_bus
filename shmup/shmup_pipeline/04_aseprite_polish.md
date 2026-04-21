# 04. Aseprite Polish — Pixel-perfect Cleanup

## Doel
Blender renders zijn bijna goed, maar niet perfect. Aseprite fase doet finale touches die het verschil maken tussen "AI-render" en "echte pixel art".

## Waarom deze stap noodzakelijk is

Blender renders hebben vaak:
- Zachte pixel edges door anti-aliasing
- Tussenkleuren die buiten palette vallen
- Kleine artefacten op randen
- Inconsistente transparantie randen
- Niet-pixel-perfect kleine details

Aseprite dwingt pixel discipline af. Elke pixel is bewust geplaatst, kleur komt uit gelimiteerde palette, geen tussenwaardes.

## Aseprite workflow

**Stap 1: Import Blender renders**
- Open sprite sheet PNG in Aseprite
- Of individuele frames als animation

**Stap 2: Palette lock**
- Load master palette (uit style bible)
- File → Color Mode → Indexed
- Remap colors to palette
- Alle pixels worden geforceerd naar palette kleuren

**Stap 3: Cleanup passes**
- Edge smoothing (anti-aliasing weg of handmatig redo)
- Dithering waar nodig voor gradient illusies
- Orphan pixel removal
- Outline refinement

**Stap 4: Manual touches**
- Weapon muzzle flashes
- Cockpit highlight details
- Engine glow accents
- Hero ship portrait (cinematic close-up voor menu)

**Stap 5: Animation polish**
- Engine flicker frames (Blender kan niet alles)
- Damage animation smoothness
- Weapon charge animations
- Transition frames tussen states

**Stap 6: Export**
- Sprite sheet PNG
- Metadata JSON
- Animation definitions

## Aseprite CLI voor batch work

Aseprite heeft krachtige CLI voor scripted operations:

```bash
# Convert to indexed palette
aseprite -b --color-mode indexed --palette master_palette.ase input.png --save-as output.aseprite

# Resize with nearest neighbor
aseprite -b --scale 2 --scale-mode nearest input.png --save-as output.png

# Export sprite sheet
aseprite -b input.aseprite --sheet spritesheet.png --data metadata.json
```

NOVA v2 pipeline gebruikt deze CLI calls in batch.

## Cursor prompt: Aseprite automation

```
Bouw een Aseprite automation systeem voor shmup sprites:

1. Python script `aseprite/batch_processor.py`:
   - Input: folder met Blender render PNGs
   - Voor elke ship/frame:
     - Import in Aseprite via CLI
     - Apply master palette
     - Run cleanup scripts
     - Export pixel-perfect result
   - Progress tracking + logging

2. Aseprite scripts `aseprite/scripts/`:
   - `palette_remap.lua` - Forceer alle pixels naar master palette
   - `edge_cleanup.lua` - Remove orphan pixels, clean edges
   - `dither_gradient.lua` - Apply dithering pattern voor smooth gradients
   - `outline_refine.lua` - Ensure clean 1-pixel outline if needed

3. Python script `aseprite/sprite_sheet_exporter.py`:
   - Combine individual frames to sprite sheet
   - Generate Aseprite tag-based metadata (rotation tags, damage tags)
   - Output JSON compatible with Godot SpriteFrames

4. Python script `aseprite/animation_designer.py`:
   - CLI voor definiëren animations:
     - `add_animation --name engine_flicker --frames 8 --duration 100`
     - `add_animation --name rotation --frames 16 --loop true`
   - Updates sprite metadata

5. Python script `aseprite/palette_tools.py`:
   - Analyze image → extract colors
   - Compare tegen master palette
   - Report non-palette colors
   - Snap to nearest palette color

6. Python script `aseprite/manual_fix_queue.py`:
   - Detect automated cleanup failures
   - Queue voor handmatige Aseprite edit
   - Open file in Aseprite GUI voor user
   - Wait for save, validate again

7. Aseprite palette file `aseprite/master_palette.ase`:
   - Generated from style_bible colors
   - Named slots per faction/purpose
   - Loadable in Aseprite

8. Integration tests:
   - Test palette adherence (0 non-palette colors)
   - Test sprite sheet geometry (frames align)
   - Test animation metadata correctness

Gebruik Python 3.11, Aseprite CLI, Lua voor Aseprite scripts.
Aseprite install path configurable via env var.
```

## Aseprite Lua scripts

Aseprite ondersteunt Lua scripting. Hier de belangrijkste:

**palette_remap.lua:**
```lua
-- Remap alle kleuren naar dichtstbij palette kleur
local spr = app.activeSprite
if not spr then return end

app.command.ChangePixelFormat {
    format = "indexed",
    dithering = "none",  -- No dithering in remap
    toGray = "default"
}

app.command.LoadPalette { preset = "master_palette" }
app.command.ApplyPalette()

app.refresh()
```

**edge_cleanup.lua:**
```lua
-- Remove orphan pixels (1 pixel in sea of transparent)
local spr = app.activeSprite
local img = spr.cels[1].image
local cleaned = Image(img.width, img.height, img.colorMode)

for y = 0, img.height - 1 do
    for x = 0, img.width - 1 do
        local pixel = img:getPixel(x, y)
        if pixel ~= 0 then  -- Not transparent
            -- Check 8 neighbors
            local neighbor_count = 0
            for dy = -1, 1 do
                for dx = -1, 1 do
                    if dx ~= 0 or dy ~= 0 then
                        local nx, ny = x + dx, y + dy
                        if nx >= 0 and nx < img.width and 
                           ny >= 0 and ny < img.height then
                            if img:getPixel(nx, ny) ~= 0 then
                                neighbor_count = neighbor_count + 1
                            end
                        end
                    end
                end
            end
            
            -- Keep pixel only if >= 2 neighbors
            if neighbor_count >= 2 then
                cleaned:drawPixel(x, y, pixel)
            end
        end
    end
end

spr.cels[1].image = cleaned
app.refresh()
```

## Manual vs automatic werk

**Automatiseer:**
- Palette enforcement (100% automated)
- Basic edge cleanup (90% automated)
- Sprite sheet assembly (100% automated)
- Metadata generation (100% automated)

**Manual touch up nodig voor:**
- Hero ships (player + boss)
- Unique detail elements (weapon effects)
- Animations met character (engine flicker timing)
- Face/character portraits indien van toepassing
- Stylistic flourishes (faction insignia, pilot visible)

Accepteer dat 20% van assets handwerk blijft vragen. Dat is wat AAA indie art van AI slop onderscheidt.

## Visual quality checklist

Voor elke ship na Aseprite stap:

- [ ] Alle pixels zijn uit master palette (exact)
- [ ] Silhouette leesbaar op 32x32
- [ ] Transparantie edges schoon (geen halo)
- [ ] Damage states duidelijk progressief
- [ ] Rotation frames coherent (zelfde ship, verschillende hoek)
- [ ] Animation loops zonder haperingen
- [ ] Scale consistent met andere assets
- [ ] Kleuren passen faction context

Als iets niet pass, terug naar stap.

## Aseprite file organization

```
aseprite_work/
├── sources/                  # Input from Blender
│   └── ship_name/
│       ├── pristine_00.png
│       ├── pristine_01.png
│       └── ...
├── aseprite_files/           # .aseprite bewerking files
│   └── ship_name.aseprite
├── exports/                  # Finale outputs
│   ├── sprite_sheets/
│   │   └── ship_name_sheet.png
│   └── metadata/
│       └── ship_name_data.json
└── manual_queue/             # Needs human attention
    └── ship_name/
```

## Tool setup tips

**Aseprite preferences voor shmup werk:**
- Pixel grid visible
- Snap to pixel grid
- Tiles of 16x16 or 32x32 (guides)
- Onion skin voor animations (2 frames back, 1 forward)

**Keybindings worth setting:**
- Cycle palette colors: comma, period
- Flip horizontal for symmetric checks
- Quick color pick: alt+click
- Animation preview play/pause

## Time estimates

Per ship Aseprite stap:
- Automated processing: 1-2 minuten
- Minor manual cleanup: 10-15 minuten
- Hero ship polish: 1-3 uur
- Boss detail work: 3-6 uur
- Animation tuning: 30-60 min per anim

Budget 15-30 min gemiddeld per ship voor professionele kwaliteit.

## Alternative: no Aseprite workflow

Als je zonder Aseprite wilt werken:

**PyQt5 + PIL alternative:**
- Use PIL voor palette enforcement
- ImageMagick voor batch operations
- Custom Python scripts voor edge cleanup
- Geen interactive polish (pure algorithmic)

Nadeel: kwaliteit lager, geen menselijke judgement voor details.
Voordeel: 100% automatable, faster, geen Aseprite license.

Voor Black Ledger-kwaliteit: Aseprite loont. Voor bulk enemy varianten: PyQt5 pipeline prima.

## Output van deze fase

Per ship:
- Polished sprite sheet PNG
- Animation metadata JSON
- Aseprite source file (voor later editing)
- Quality approved flag

Klaar voor PyQt5 assembly stap of directe Godot import.

## Volgende stap

Polished sprites → 05_pyqt_assembly.md voor batch assembly en final packaging.
