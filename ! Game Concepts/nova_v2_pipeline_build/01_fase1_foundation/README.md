# Fase 1: Foundation (10 prompts)

## Doel

Bouw de fundamentele agents die alle volgende agents nodig hebben:

- **Design Fase (20)**: Master palette, style bibles, color consistency
- **Code Jury (02)**: GDScript + Python code review (nodig voor alle volgende code)
- **Game Balance (10)**: Numerieke validatie (simpele test case voor Code Jury)
- **FreeCAD Parametric (21)**: 3D component generation
- **Blender Game Renderer (22)**: Multi-angle sprite rendering
- **Aseprite Processor (23)**: Pixel-art polish + batch
- **PyQt5 Assembly (25)**: Sprite sheet + Godot resource generation
- **Godot Import (26)**: Game engine integratie
- **Monitor (11)**: Runtime observabiliteit
- **Error (17)**: Error handling en auto-repair

## Waarom deze volgorde

1. **Design Fase eerst** - definieert palette/style voor alle rendering agents
2. **Code Jury tweede** - valideert alle gegenereerde code vanaf nu
3. **Game Balance derde** - simpele test agent om Code Jury te valideren
4. **Asset pipeline chain** (21→22→23→25→26) - shmup asset productie
5. **Monitor + Error laatst** - observability voor alles dat al draait

## Wat je krijgt na Fase 1

Een werkende asset productie pipeline:

```
Design → FreeCAD → Blender → Aseprite → PyQt5 → Godot
```

Alles met quality gates:
- Sprite Jury (01, al live) op Aseprite output
- Code Jury (02) op GDScript
- Monitor (11) op alles
- Error (17) voor crashes

## Success criteria Fase 1

- 8/10 agents active status
- Sprite pipeline end-to-end test slaagt
- Minimaal 2 van 3 hero agents (20, 22, 26) 100% functioneel
- V1 onaangetast

## Tijd

Sequentieel: 25-35 uur Cursor werk
Met 24/7 PC: 4-5 dagen doorlopend

## Per prompt

Open prompt_01 tot prompt_10 in volgorde. Elke prompt is zelfstandig uitvoerbaar.

Na elk: check status file, run validatie, commit, volgende.

## Na Fase 1

Run `FASE1_VALIDATIE.md` checklist voordat je door gaat naar Fase 2.
