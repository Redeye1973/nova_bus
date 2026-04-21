# NOVA v2 Agent Extensions — Complete Tool-Specific Jury-Judge Set

Uitbreiding op basis NOVA v2 catalogus (agents 01-19) met tool-specifieke jury-judge agents voor alle tools in de NOVA stack.

## Nieuwe agents (20-35)

**Game Asset Production:**
- 20. Design Fase Agent — Style bible, palette, concept validatie
- 21. FreeCAD Parametric Agent — Parametric model generator + varianten
- 22. Blender Game Renderer Agent — Multi-angle sprite rendering
- 23. Aseprite Processor Agent — CLI automation, batch processing
- 24. Aseprite Animation Jury — Animation-specific quality checks
- 25. PyQt5 Assembly Agent — Sprite sheet assembly, atlasing
- 26. Godot Import Agent — Scene generation, asset import

**Story Production:**
- 27. Storyboard Visual Agent — Panel generation, layout, consistency
- 28. Story Text Integration Agent — Surilians canon + narrative implementation

**Audio Production:**
- 29. ElevenLabs Audio Agent — Voice + SFX generation
- 30. Audio Asset Jury — Game audio integration validation

**GIS Production:**
- 31. QGIS Analysis Agent — Geo-analyse workflows, cartografie
- 32. GRASS GIS Analysis Agent — Advanced geo-processing

**Architecture Visualisation:**
- 33. Blender Architecture Walkthrough Agent — Archviz walkthroughs, VR prep
- 34. Unreal Engine Import Agent — UE5 asset import, cinematic setup

**2D Raster Production:**
- 35. GIMP/Krita/Inkscape Processor Agent — Universele 2D tool orchestrator

## Jury complexity per agent

**Zware jury (4-5 leden, productie-kritiek):**
- Storyboard Visual (consistency over panels)
- Story Text Integration (canon complexity)
- Aseprite Animation (pixel-perfect animation)
- Blender Architecture Walkthrough (visual quality + VR performance)
- Unreal Engine Import (complex integration)

**Medium jury (3 leden):**
- Design Fase
- FreeCAD Parametric
- Blender Game Renderer
- Aseprite Processor
- Godot Import
- ElevenLabs Audio
- QGIS Analysis
- GRASS GIS Analysis
- GIMP/Krita/Inkscape Processor

**Lichte jury (2 leden, mostly technisch):**
- PyQt5 Assembly
- Audio Asset Jury

## Integratie met bestaande NOVA v2 (agents 01-19)

Deze extensions werken samen met:

| Nieuwe Agent | Werkt met bestaande |
|--------------|---------------------|
| 20 Design Fase | 01 Sprite Jury, 09 2D Illustration Jury |
| 21 FreeCAD Parametric | 06 CAD Jury |
| 22 Blender Game Renderer | 04 3D Model Jury |
| 23 Aseprite Processor | 01 Sprite Jury |
| 24 Aseprite Animation Jury | 01 Sprite Jury |
| 25 PyQt5 Assembly | 01 Sprite Jury |
| 26 Godot Import | 02 Code Jury |
| 27 Storyboard Visual | 08 Character Art Jury, 09 2D Illustration |
| 28 Story Text Integration | 07 Narrative Jury |
| 29 ElevenLabs Audio | 03 Audio Jury |
| 30 Audio Asset Jury | 03 Audio Jury |
| 31 QGIS Analysis | 05 GIS Jury |
| 32 GRASS GIS Analysis | 05 GIS Jury |
| 33 Blender Architecture | 04 3D Model Jury |
| 34 Unreal Engine Import | 02 Code Jury, 04 3D Model Jury |
| 35 GIMP/Krita/Inkscape | 09 2D Illustration Jury |

## Complete pipeline views

**Shmup Game Production (Black Ledger):**
```
20 Design Fase
    ↓
21 FreeCAD Parametric
    ↓ 06 CAD Jury validation
22 Blender Game Renderer
    ↓ 04 3D Model Jury
23 Aseprite Processor → 24 Aseprite Animation Jury
    ↓ 01 Sprite Jury
25 PyQt5 Assembly
    ↓
26 Godot Import
    ↓ 02 Code Jury
Gameplay
```

**Architecture Visualisation (Werk pitch):**
```
13 PDOK Downloader
    ↓
15 QGIS Processor + 31 QGIS Analysis + 32 GRASS GIS
    ↓ 05 GIS Jury
14 Blender Baker
    ↓ 04 3D Model Jury
33 Blender Architecture Walkthrough
    ↓
34 Unreal Engine Import
    ↓ 02 Code Jury
VR Walkthrough deliverable
```

**Story + Game Integration (Surilians/Black Ledger):**
```
28 Story Text Integration (canon check)
    ↓ 07 Narrative Jury
27 Storyboard Visual (panels)
    ↓ 08 Character Art Jury
35 GIMP/Krita/Inkscape (illustration polish)
    ↓ 09 2D Illustration Jury
Final storyboard assets
```

**Audio Production (Voor alle producten):**
```
29 ElevenLabs Audio (voice + SFX generation)
    ↓ 03 Audio Jury (technical)
30 Audio Asset Jury (integration)
    ↓
Game/Product audio ready
```

## Folder structuur

```
nova_v2_extensions/
├── README.md (dit bestand)
├── design/20_design_fase_agent.md
├── freecad/21_freecad_parametric_agent.md
├── blender_game/22_blender_game_renderer_agent.md
├── aseprite/
│   ├── 23_aseprite_processor_agent.md
│   └── 24_aseprite_animation_jury.md
├── pyqt/25_pyqt_assembly_agent.md
├── godot/26_godot_import_agent.md
├── storyboard/27_storyboard_visual_agent.md
├── story/28_story_text_integration_agent.md
├── audio/
│   ├── 29_elevenlabs_audio_agent.md
│   └── 30_audio_asset_jury.md
├── qgis/31_qgis_analysis_agent.md
├── grass/32_grass_gis_analysis_agent.md
├── blender_arch/33_blender_architecture_walkthrough_agent.md
├── unreal/34_unreal_engine_import_agent.md
├── raster2d/35_raster_2d_processor_agent.md
├── templates/
│   └── extension_workflows.json
└── stappenplan/
    ├── implementation_order.md
    └── integration_guide.md
```

## Implementatie volgorde (na basis agents 01-19)

**Fase A: Game Asset Chain (4 weken)**
- Week 13: Design Fase (20) + FreeCAD Parametric (21)
- Week 14: Blender Game Renderer (22)
- Week 15: Aseprite Processor + Animation Jury (23, 24)
- Week 16: PyQt5 Assembly (25) + Godot Import (26)

**Fase B: Architecture/GIS Chain (3 weken)**
- Week 17: QGIS Analysis + GRASS GIS (31, 32)
- Week 18: Blender Architecture Walkthrough (33)
- Week 19: Unreal Engine Import (34)

**Fase C: Story Production (2 weken)**
- Week 20: Story Text Integration (28)
- Week 21: Storyboard Visual (27)

**Fase D: Audio + 2D (2 weken)**
- Week 22: ElevenLabs + Audio Asset Jury (29, 30)
- Week 23: GIMP/Krita/Inkscape Processor (35)

Totaal: 11 weken bovenop 12 weken basis = 23 weken fulltime voor complete NOVA v2.

## Hoe te gebruiken

Per agent: open .md bestand, lees scope, kopieer Cursor prompt uit het bestand, bouw de service. Elk bestand bevat:
- Doel en scope
- Jury configuratie (aantal leden + specialisaties)
- N8n workflow structuur
- Complete Cursor prompt
- Test scenario's
- Integratie punten
- Success metrics

## Opmerkingen

**Over prioritering:**
Bouw eerst de agents die direct impact hebben op jouw volgende mijlpaal. Als dat werk-pitch is → QGIS + Blender Arch + Unreal Import eerst. Als dat Black Ledger upgrade is → Game asset chain eerst.

**Over schalen:**
Niet alle 35 agents hoeven tegelijk. Werk met MVP (minimum viable pipeline) voor eerste product. Voeg later agents toe als producten groeien.

**Over onderhoud:**
Meer agents = meer onderhoud. Elke nieuwe agent voegt complexiteit toe. Bouw alleen als waarde duidelijk is.
