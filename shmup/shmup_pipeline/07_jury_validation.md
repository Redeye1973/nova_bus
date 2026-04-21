# 07. NOVA v2 Jury Validation voor Shmup Assets

## Doel
Finaal kwaliteitsnet via NOVA v2 agent systeem. Automatische detectie van visuele, technische en design issues voor assets production gaan.

## Jury orchestratie voor shmup assets

Elk asset (ship, projectile, effect) passeert meerdere juries:

```
Asset klaar
    ↓
Sprite Jury (agent 01) — pixel quality, silhouette, palette
    ↓
3D Model Jury (agent 04) — voor source Blender models
    ↓
Game Balance Jury (agent 10) — stats en balance
    ↓
Alle approved?
    ├─ Yes → Asset production ready
    └─ No → Back to relevant pipeline stap
```

## Specifieke shmup asset checks

**Sprite Jury uitbreidingen voor shmup:**
- Rotation frame consistency (16 angles same ship)
- Damage state progression (duidelijk slechter)
- Engine animation smoothness
- Muzzle flash alignment met weapon mount

**Nieuwe "Shmup Jury" specialists (extension):**

1. **Gameplay Visibility Specialist**
   - Test sprite op 32x32 (typical gameplay size)
   - Contrast tegen achtergronden
   - Silhouette onderscheidbaarheid van andere enemies

2. **Animation Frame Count Validator**
   - Rotation: exact 16 frames
   - Engine: 8 frame loop
   - Damage: 3-5 states
   - Consistency check

3. **Weapon Mount Point Accuracy**
   - Muzzle flash position matched met ship sprite
   - Projectile spawn point aligned
   - Bij rotation: frame-by-frame tracking

4. **Collision Shape Sanity**
   - Collision matches visual bounds
   - Geen gaps of overreach
   - Per-frame consistent bij rotation

## Cursor prompt: Shmup Jury extension

```
Breid NOVA v2 Sprite Jury uit met shmup-specifieke checks:

1. Python service `shmup_jury/visibility_specialist.py`:
   - Input: sprite sheet + rotation frames
   - Render op 32x32 (game resolution)
   - Check silhouette clarity
   - Contrast analysis tegen common backgrounds (space, planet, nebula)
   - Output: {visibility_score, weak_angles: [], bg_conflicts: []}

2. Python service `shmup_jury/rotation_consistency.py`:
   - Parse 16 rotation frames
   - Extract ship center point per frame
   - Check: center consistent (geen drift)
   - Check: size consistent
   - Check: key features visible per angle
   - Output: {consistent, drift_pixels, missing_features_at_angles: []}

3. Python service `shmup_jury/animation_validator.py`:
   - Check frame counts per animation type
   - Validate timing metadata
   - Detect stuttering (too-similar consecutive frames)
   - Check loop points (last frame matches first voor seamless)
   - Output: {valid, issues_per_animation: {}}

4. Python service `shmup_jury/weapon_alignment.py`:
   - Input: ship sprite + weapon mount metadata + muzzle flash sprite
   - Per rotation frame check alignment
   - Validate spawn point coordinates
   - Output: {aligned, misaligned_angles: []}

5. Python service `shmup_jury/collision_generator.py`:
   - Generate suggested collision shape from sprite
   - Use OpenCV contour detection
   - Output multiple options (tight polygon, bounding circle, capsule)
   - Flag if manual tweak needed

6. Python service `shmup_jury/gameplay_sim.py`:
   - Simulate sprite in typical shmup context:
     - Against star field background
     - With 10+ similar enemies on screen
     - With player projectiles
   - Screenshot test scenarios
   - Ollama vision check: "Is this ship distinguishable?"
   - Output: {distinguishable, confusion_cases: []}

7. Extend Sprite Judge to include shmup verdict:
   - Weight gameplay visibility heavily
   - Animation issues block approval
   - Weapon misalignment requires revise (auto-fixable)
   - Include shmup-specific recommendations

8. N8n workflow extension voor shmup asset pipeline:
   - Standard Sprite Jury first
   - Als pass: run Shmup Jury specialists
   - Judge final verdict
   - Routing: production / tuning / reject

Gebruik Python 3.11, OpenCV, PIL, Ollama Qwen VL,
FastAPI voor services.
```

## Balance Jury voor shmup stats

De Game Balance Jury (agent 10) wordt specifiek toegepast op:

**Enemy stats validation:**
```yaml
# Voor elke enemy variant
stats:
  health: 100
  speed: 80
  damage: 15
  score_value: 100
  loot_table:
    credits: [5, 15]
    powerup_chance: 0.1
```

Balance Jury checkt:
- DPS ratio past bij tier (standard, heavy, elite, boss)
- Score value matches difficulty
- Loot proportional to effort
- Speed/health combination zinnig

**Player weapon validation:**
- Damage scaling over tiers
- Fire rate progression
- Credit cost vs power
- No overpowered combinations

## Complete pipeline validation flow

Voor nieuwe Corporate Fighter Mk.II ship:

```
1. Asset created (Blender → Aseprite → PyQt5 → Godot)
   ↓
2. Standard Sprite Jury run
   - Pixel integrity: ok
   - Silhouette: ok
   - Style consistency: ok
   ↓
3. Shmup Jury run
   - Visibility: ok (distinguishable on 32x32)
   - Rotation consistency: ok
   - Animation: 16 frames correct
   - Weapon alignment: ok per frame
   ↓
4. Game Balance Jury
   - Stats fit tier: ok
   - Score appropriate: ok
   ↓
5. All approved → Production bucket
   - Upload via Distribution Agent
   - Update game build manifest
   - Notify dev team
```

Bij elke fail: specific feedback naar relevante pipeline stap.

## Integration test suite

Voor complete asset package test:

```python
# tests/shmup_integration_test.py
def test_complete_asset():
    """Test that a complete ship asset passes all juries."""
    
    ship_name = "corp_fighter_mk2"
    asset_path = f"assets_final/ships/enemies/corporate/{ship_name}/"
    
    # Run through all validations
    sprite_result = run_sprite_jury(asset_path)
    assert sprite_result.verdict == "accept"
    
    shmup_result = run_shmup_jury(asset_path)
    assert shmup_result.verdict == "accept"
    
    balance_result = run_balance_jury(
        stats=load_enemy_stats(ship_name),
        tier="standard_enemy"
    )
    assert balance_result.verdict == "accept"
    
    # Integration test: load in Godot headless
    godot_result = run_godot_import_test(asset_path)
    assert godot_result.success
    assert godot_result.fps_estimate > 60
```

## Kwaliteit benchmarks

Voor Raptor-style kwaliteit streef naar:

**Technische kwaliteit:**
- 100% palette adherence (geen niet-palette pixels)
- 99%+ silhouette leesbaarheid op 32x32
- 0% animation hiccups
- 100% collision accuracy

**Visuele kwaliteit (subjectief):**
- Rotation voelt vloeiend
- Damage states zijn betekenisvol zichtbaar
- Lighting consistent tussen assets
- Color choices ondersteunen faction identity

**Game feel kwaliteit:**
- Enemies onderscheidbaar van elkaar
- Projectiles duidelijk vijand vs speler
- Power-ups zichtbaar in chaotic gameplay
- Boss phases visueel gecommuniceerd

## Continuous monitoring

Na release:
- Player feedback op sprite leesbaarheid
- Analytics op "confusion" moments (players die foute enemies raken)
- Performance metrics in game (FPS drops gerelateerd aan specific sprites?)
- Update juries op basis van leerdata

## Wanneer bypass van jury toegestaan

Soms heb je "imperfect" art nodig:
- Experimental variants (retro-intentional ugly)
- Time-constrained releases
- Creative keuzes die juries niet begrijpen

Voor deze gevallen: experimental bucket, clear labeling, explicit user override.

## Output van deze fase

Per asset: officiële "production-ready" stamp met:
- All jury verdicts documented
- Quality scores logged
- Ready voor release build

## Complete pipeline resumé

Terugblik op wat we hebben gebouwd:

1. **Design fase** → Style bible + ship concepten
2. **FreeCAD** → Parametric base models
3. **Blender** → Multi-angle 3D renders
4. **Aseprite** → Pixel perfect polish
5. **PyQt5** → Batch assembly + packaging
6. **Godot** → Game engine integratie
7. **Jury** → Quality validation (deze fase)

Van concept tot production-ready shmup asset in gedocumenteerde, herbruikbare, automatiseerbare stappen.

## Volgende stappen (buiten pipeline)

**Level design** — Waves, patronen, boss encounters
**Audio** — Muziek + SFX (Audiocraft via NOVA v2 pipeline)
**Menu/UI** — Bewust niet pixel art, liever clean vector
**Story integration** — Surilians/Rex Varn narrative integratie
**Publishing** — Steam setup, trailer, marketing

Elk daarvan kan aparte NOVA v2 pipeline krijgen.

## Success definitie

Na deze pipeline heb je een shmup dat:
- Visueel concurreert met Raptor Call of the Shadows
- Efficiënte productie-pipeline voor uitbreiding
- Automatische kwaliteitsborging
- Schaalbaar naar honderden assets
- Onderhoudbaar over jaren

Dat is de belofte van NOVA v2 voor game productie.
