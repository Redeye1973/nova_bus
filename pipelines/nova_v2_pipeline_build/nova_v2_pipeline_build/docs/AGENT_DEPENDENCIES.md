# Agent Dependencies

Overzicht van welke agents welke andere agents nodig hebben, welke externe tools, welke services.

## Dependency types

- **Hard dependency**: agent kan niet functioneren zonder
- **Soft dependency**: agent werkt met fallback zonder
- **Optional**: nice-to-have, geen impact op core function

## Agent → Agent dependencies

### Agent 01 Sprite Jury (bestaand)
- **Hard**: geen (standalone jury)
- **Soft**: Agent 20 Design Fase (voor palette reference)
- **Uses**: Agent 11 Monitor, 17 Error

### Agent 02 Code Jury
- **Hard**: geen
- **Soft**: Ollama voor AI review
- **Uses**: 11 Monitor, 17 Error

### Agent 03 Audio Jury
- **Hard**: geen
- **Soft**: Ollama voor context
- **Used by**: 29 ElevenLabs, 30 Audio Asset Jury

### Agent 04 3D Model Jury
- **Hard**: geen
- **Used by**: 14 Blender Baker, 22 Game Renderer, 33 Architecture

### Agent 05 GIS Jury
- **Hard**: geen
- **Used by**: 13 PDOK, 14 Baker, 15 QGIS, 31 Analysis, 32 GRASS

### Agent 06 CAD Jury
- **Hard**: geen
- **Used by**: 21 FreeCAD Parametric

### Agent 07 Narrative Jury
- **Hard**: Qdrant (voor canon search)
- **Soft**: Ollama
- **Used by**: 28 Story Text Integration

### Agent 08 Character Art Jury
- **Hard**: geen
- **Soft**: Ollama vision
- **Used by**: 27 Storyboard Visual

### Agent 09 2D Illustration Jury
- **Hard**: geen
- **Soft**: Ollama vision
- **Used by**: 35 Raster 2D Processor

### Agent 10 Game Balance Jury
- **Hard**: geen (pure numeriek)
- **Used by**: balance validation workflows

### Agent 11 Monitor Agent
- **Hard**: PostgreSQL, Redis
- **Observes**: alle agents

### Agent 12 Bake Orchestrator
- **Hard**: PostgreSQL
- **Orchestrates**: 13 PDOK → 15 QGIS → 14 Blender Baker → 04 3D Jury

### Agent 13 PDOK Downloader
- **Hard**: PDOK API access (internet)
- **Used by**: 12 Bake Orchestrator, 15 QGIS Processor

### Agent 14 Blender Baker
- **Hard**: Blender headless op host
- **Soft**: 04 3D Model Jury voor validation
- **Used by**: 12 Bake Orchestrator

### Agent 15 QGIS Processor
- **Hard**: QGIS op host
- **Soft**: 05 GIS Jury
- **Used by**: 14 Blender Baker, 12 Bake Orchestrator

### Agent 16 Cost Guard
- **Hard**: PostgreSQL
- **Observes**: ElevenLabs, Meshy, andere paid APIs

### Agent 17 Error Agent
- **Hard**: PostgreSQL (voor historie)
- **Soft**: Ollama voor intelligent diagnosis
- **Called by**: alle agents bij errors

### Agent 18 Prompt Director
- **Hard**: geen
- **Soft**: Ollama voor complex prompt generation
- **Used by**: many, voor multi-step tasks

### Agent 19 Distribution Agent
- **Hard**: MinIO
- **Used by**: build pipelines, asset delivery

### Agent 20 Design Fase
- **Hard**: geen
- **Soft**: Qdrant voor style reference search
- **Used by**: 21, 22, 23 (hele sprite pipeline)

### Agent 21 FreeCAD Parametric
- **Hard**: FreeCAD op host
- **Soft**: 06 CAD Jury
- **Used by**: 22 Blender Game Renderer

### Agent 22 Blender Game Renderer
- **Hard**: Blender op host
- **Soft**: 04 3D Jury, 20 Design Fase
- **Used by**: 23 Aseprite Processor

### Agent 23 Aseprite Processor
- **Hard**: Aseprite op host (of pixelart alternative)
- **Soft**: 01 Sprite Jury, 20 Design Fase
- **Used by**: 25 PyQt Assembly

### Agent 24 Aseprite Animation Jury
- **Hard**: Pillow, numpy (Python libs)
- **Uses**: 01 Sprite Jury pattern

### Agent 25 PyQt5 Assembly
- **Hard**: PyQt5
- **Used by**: 26 Godot Import

### Agent 26 Godot Import
- **Hard**: Godot 4.x op host (voor validation)
- **Soft**: 02 Code Jury voor generated GDScript

### Agent 27 Storyboard Visual
- **Hard**: Pillow
- **Soft**: Ollama vision, 08 Character Art Jury

### Agent 28 Story Text Integration
- **Hard**: Qdrant, 07 Narrative Jury
- **Soft**: Ollama

### Agent 29 ElevenLabs Audio
- **Hard**: ElevenLabs API key
- **Soft**: 03 Audio Jury, 30 Audio Asset Jury

### Agent 30 Audio Asset Jury
- **Hard**: librosa, pydub
- **Uses**: 03 Audio Jury

### Agent 31 QGIS Analysis
- **Hard**: QGIS op host
- **Soft**: 05 GIS Jury

### Agent 32 GRASS GIS Analysis
- **Hard**: GRASS GIS op host
- **Soft**: 05 GIS Jury

### Agent 35 Raster 2D Processor
- **Hard**: GIMP, Krita, of Inkscape op host (minstens 1)
- **Soft**: 09 2D Illustration Jury

## Agent → Externe tools

| Agent | Tool | Versie | Install locatie |
|-------|------|--------|-----------------|
| 14 | Blender | 4.x | PC |
| 15 | QGIS | 3.x | PC |
| 21 | FreeCAD | 1.x | PC |
| 22 | Blender | 4.x | PC |
| 23 | Aseprite | latest | PC |
| 26 | Godot | 4.6+ | PC |
| 31 | QGIS | 3.x | PC |
| 32 | GRASS GIS | 8.x | PC |
| 35 | GIMP/Krita/Inkscape | latest | PC |

Alle desktop tools draaien op PC, niet in Hetzner containers. Agents roepen ze aan via:
- SSH + Tailscale
- Of lokaal subprocess indien agent container op PC draait

## Agent → Infrastructure services

| Service | Agents die gebruiken |
|---------|---------------------|
| PostgreSQL | 11, 12, 16, 17, 28 (canon), N8n backend |
| Redis | 11 (queue metrics), 12 (job queue), N8n workers |
| MinIO | 19, 26 (asset output), 22 (rendered sprites) |
| Qdrant | 07, 20, 28 (canon search) |
| Ollama | 02, 03, 04, 05, 06, 07, 08, 09, 17, 18, 20, 27, 28 (via tailscale) |
| ElevenLabs API | 29 |

## Agent → N8n workflows

Elke agent heeft 1 eigen workflow voor webhook handling. Sommige agents hebben additionele orchestratie-workflows:

- Agent 12 Bake Orchestrator: 1 main workflow + sub-workflows per bake type
- Agent 17 Error Agent: 1 webhook + scheduled heartbeat workflow
- Agent 18 Prompt Director: 1 webhook + template library workflow

## Dependency resolution bij build

Pipeline build volgt deze regels:

1. **Infrastructure eerst**: PostgreSQL, Redis, MinIO, Qdrant moeten UP zijn
2. **Operational agents vroeg**: Monitor (11), Error (17) in fase 1
3. **Jury agents voor producers**: Code Jury (02) voor GDScript agents
4. **Design agent eerst in chain**: Design Fase (20) voor sprite pipeline
5. **Orchestrators als laatste**: Bake (12), Prompt Director (18) als dependencies beschikbaar zijn

## Circular dependencies

Mogelijk probleem:
- Monitor (11) observeert Error (17)
- Error (17) rapporteert naar Monitor (11)

Oplossing: beide agents bootstrap parallel, niet in chain. Elk agent heeft lokale fallback log zodat geen strict cycle nodig is.

## Dependency health check

Voor elke agent start:
```python
def check_dependencies(agent_config):
    for dep in agent_config.dependencies:
        if dep.type == "agent":
            status = check_agent_health(dep.agent_id)
            if not status.healthy and dep.required:
                raise DependencyFailure(f"Required agent {dep.agent_id} unhealthy")
        elif dep.type == "service":
            status = check_service_health(dep.service_name)
            if not status.healthy:
                if dep.required:
                    raise DependencyFailure(...)
                else:
                    enable_fallback_mode(dep.fallback_strategy)
        elif dep.type == "external_tool":
            path = find_tool(dep.tool_name)
            if not path:
                enable_fallback_mode(dep.fallback_strategy)
```

Elke agent start met dependency check. Output in status file onder `dependencies`.
