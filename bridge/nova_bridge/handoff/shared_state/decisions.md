# Decisions Log - NOVA V2

Alle architecturele en strategische beslissingen, met reasoning.

## 2026-04-19: Bridge system tussen claude.ai en Cursor

**Decision**: Handoff folder system (`handoff/to_cursor/`, `handoff/from_cursor/`, `handoff/shared_state/`) voor async communicatie.

**Context**: Copy-paste tussen claude.ai en Cursor werd bottleneck, jij vroeg om automatisering.

**Reasoning**: 
- Claude instances kunnen niet direct met elkaar praten (geen API)
- Shared filesystem met gestructureerde formats werkt als brug
- File watcher notificeert bij nieuwe handoffs
- Upload naar Claude project automatiseert de claude.ai kant

**Alternatieven overwogen**:
- MCP Claude-to-Claude bridge: niet publiek beschikbaar
- Chrome extensie: onderhouden versies niet bekend
- Manual copy-paste: huidige pijn

**Implementation**: Python watcher + PowerShell helpers + markdown templates.

---

## 2026-04-19: V2 Docker stubs-first deployment

**Decision**: Cursor deployde 29 agent stubs + 3 echte agents in één operatie, in plaats van agent-per-agent volle implementatie.

**Reasoning**:
- Infrastructure sneller staan
- Stubs verifiëren container/network/n8n setup
- Volle logica vullen is daarna puur code werk, geen infra werk

**Consequence**: Baseline heeft 4 echte agents (01, 02, 10, 20) + 29 stubs. Batches vullen stubs met echte logica.

---

## 2026-04-19: Batches van 3 agents per Cursor sessie

**Decision**: Niet alle 36 prompts in één Cursor run, maar batches van 3.

**Reasoning**:
- Context window management
- Quality degradatie in lange sessies
- Duidelijke stopmomenten voor review

**Risico**: trager totaal. **Mitigation**: meerdere batches per dag mogelijk als tijd/energie.

---

## 2026-04-19: NOVA Host Bridge voor host-only tools (FreeCAD, QGIS, later Blender)

**Decision**: Eén unified FastAPI service `nova_host_bridge` op de PC (port 8500, bind 0.0.0.0), bereikbaar voor Hetzner agents over het bestaande Tailscale tailnet (`http://100.64.0.2:8500` of `http://alex-main-1:8500`). Alle host-dependent tools (FreeCAD CLI, QGIS process, eventueel Blender) krijgen een adapter in dezelfde service.

**Context**: Agent 21 had FreeCAD nodig maar Hetzner heeft geen GUI/FreeCAD. Initial deploy gebruikte trimesh fallback (geen STEP). Voor full BOM (Blender, QGIS) is hetzelfde patroon nodig.

**Reasoning**:
- FreeCAD/QGIS/Blender installs op Linux servers zijn duur (GUI deps, licenties, GPU). PC heeft alles al.
- Bestaande Tailscale mesh (PC `alex-main-1` ↔ `nova-hetzner`) elimineert tunnel/firewall werk.
- Eén proces = één codebase, één auth, één set logs. Geen versnippering per tool.
- Agent 21 kan zonder PC nog steeds draaien: trimesh fallback blijft pad.

**Alternatieven overwogen**:
- FreeCAD in Docker op Hetzner: werkt maar zwaar, en geen Aseprite/Blender licenties op server.
- Cloudflare tunnel: extra dependency, niet nodig met Tailscale.
- Aparte service per tool: meer onderhoud, geen winst.

**Consequence**:
- Agent 21 v0.2.0: bridge-first met trimesh fallback. Real STEP files via downloadable bridge URLs.
- Bridge moet draaien op PC; auto-start (Task Scheduler) wordt aangeraden.
- Filename URLs gebruiken `PureWindowsPath` (Windows paden vanuit Linux containers).
- Toekomst: Agent 22 (Blender), Agent 28 (QGIS terrain) kunnen hetzelfde patroon volgen.

**Revisit trigger**: PC vaak offline → migreren naar Hetzner-side install of cloud renderfarm.

---

## 2026-04-19: freecadcmd.exe loadt scripts als module, niet als __main__

**Decision**: Onze `scripts/freecad_parametric.py` roept `main()` aan op module-load level (geen `if __name__ == "__main__"` guard).

**Context**: `freecadcmd.exe script.py` zet `__name__` op de module-stem (`'freecad_parametric'`), niet op `'__main__'`. Standaard Python idiom faalt silent.

**Reasoning**: Compatibel met FreeCAD's runner. Documenteren in script docstring zodat copy-paste-bugs voorkomen worden.

**Consequence**: Param doorgeven via env vars (`FC_SPEC`, `FC_RESULT`, `FC_WORKDIR`) ipv argparse, want freecadcmd interpreteert trailing CLI args als files-to-open.

---

## Format voor nieuwe decisions

```
## [Date]: [Title]

**Decision**: [Wat is besloten]

**Context**: [Waar kwam deze vraag vandaan]

**Reasoning**: [Waarom deze keuze]

**Alternatieven overwogen**: [Wat was afgewezen en waarom]

**Consequence**: [Wat betekent dit voor komende werk]

**Revisit trigger**: [Wanneer deze beslissing herzien als X gebeurt]
```
