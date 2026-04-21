# NOVA Chat Starter — 21 april 2026

Plak dit als eerste bericht in een nieuwe Claude chat.

---

## Context van vorige sessie

Ik ben Alex Meter, Hoogeveen. Ik bouw het NOVA Platform — een multi-product ecosysteem voor geautomatiseerde content productie (games, GIS, narratief). Alles op open-source tooling, IP blijft van mij.

### Wat we vandaag besproken hebben

**Software inventory bridge (bevestigd):**
- FreeCAD 1.0.2 ✅ bridge actief, E2E verified
- QGIS 3.40.13 LTR ✅ bridge actief
- Blender ✅ geïnstalleerd, adapter nog te bouwen (handoff 003)
- Aseprite ✅ geïnstalleerd, adapter nog te bouwen
- Godot 4.6.2 ✅ geïnstalleerd, adapter nog te bouwen (handoff 004)
- Krita ✅ geïnstalleerd, adapter nog te bouwen (handoff 005)
- GIMP ❌ nog installeren
- Inkscape ❌ nog installeren
- GRASS GIS ❌ nog installeren

Bridge_expansion.zip met handoffs 003-005 staat klaar maar is nog NIET door Cursor uitgevoerd.

**Recovery na stroomuitval (gisternacht):**
- Bridge draaide foreground → nu DOWN
- Eerste checks bij sessiestart: `curl http://localhost:8500/tools`, `git log --oneline -10`, `docker compose ps` op Hetzner
- TB-001 (Task Scheduler voor bridge) is HOOG prioriteit

**Humble Bundles gekocht:**
- Bugrimov Maksim asset pack (Epic Games keys, Unreal .uasset formaat → conversie naar Godot nodig)
- Audio + Visual FX bundle (Unity Asset Store keys, grotendeels direct bruikbaar in Godot als PNG/WAV/FBX)
- Keys verlopen april 2027

**NOVA handoff document gemaakt:**
- `NOVA_V1_V2_Handoff_Document.docx` — volledig overzicht voor andere AI
- Opslaan in `L:\!Nova V2\bridge\nova_bridge\handoff\shared_state\`

---

## Huidige staat NOVA

### V1 (poort 5678, Hetzner)
- 68 productie-workflows actief
- Sprites, audio, Unreal pipeline, error/rollback agents
- NIET aanraken tijdens V2 werk

### V2 (poort 5679/5680, Hetzner)
Actieve agents (E2E verified):
- Agent 01 Sprite Jury POC — /webhook/sprite-review-poc
- Agent 02 Code Jury — /webhook/code-review
- Agent 10 Game Balance Jury — /webhook/balance-review
- Agent 20 Design Fase — /webhook/design-fase
- Agent 21 FreeCAD Parametric v0.2.0 — /webhook/freecad-parametric (via bridge)
- 29 stubs — containers healthy, logica leeg

### Bridge (PC, poort 8500)
- nova_host_bridge FastAPI service
- Tailscale mesh PC ↔ Hetzner (100.64.0.2 ↔ 100.64.0.1), 119ms latency
- Na stroomuitval: handmatig herstarten via `python -m uvicorn app.main:app --host 0.0.0.0 --port 8500`
- Werkdirectory: `L:\!Nova V2\bridge\nova_host_bridge\`

---

## Directe prioriteiten (in volgorde)

1. **Recovery checks** (5 min):
   ```powershell
   curl http://localhost:8500/tools
   ssh root@178.104.207.194 "curl -s http://alex-main-1:8500/tools"
   cd "L:\!Nova V2" && git log --oneline -10 && git status
   ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose ps"
   Get-ChildItem "L:\!Nova V2\bridge\nova_bridge\handoff\from_cursor\*.md" | Sort-Object LastWriteTime -Descending | Select -First 5 Name, LastWriteTime
   ```

2. **TB-001 Bridge Task Scheduler** (60 min Cursor werk):
   Bridge als Windows Task Scheduler entry zodat hij automatisch start bij reboot.

3. **Bridge expansion handoffs uitvoeren** (Cursor):
   Handoffs 003-005 uit `bridge_expansion.zip` deployen:
   - 003: Blender + Aseprite + PyQt5 adapters
   - 004: Godot adapter
   - 005: GRASS + GIMP + Krita + Inkscape adapters (GIMP/Inkscape/GRASS eerst installeren)

4. **Batch 2 valideren**:
   Waren Agent 11 Monitor en 17 Error al afgerond voor de stroomuitval?

---

## Kritieke regels

- V1 op poort 5678 NOOIT aanraken
- Sprite Jury Agent 01 POC NIET aanraken
- Secrets lezen uit `L:\!Nova V2\secrets\nova_v2_passwords.txt` — NOOIT in code/chat/logs
- Max 2 pogingen zelfde aanpak, dan docs lezen en alternatief zoeken
- Krita CLI (--script) werkt NIET — gebruik PyQt5 QImage/QPainter direct
- Geen Cloudflare tunnel — pull model: PC belt Hetzner, nooit andersom
- Alex bepaalt wanneer gesprek klaar is — nooit afsluiten met "Tot straks" enz.

---

## Paden

| Pad | Inhoud |
|-----|--------|
| `L:\!Nova V2\` | Root V2 development |
| `L:\!Nova V2\secrets\nova_v2_passwords.txt` | API keys + credentials |
| `L:\!Nova V2\bridge\nova_host_bridge\` | Bridge service |
| `L:\!Nova V2\bridge\nova_bridge\handoff\to_cursor\` | Opdrachten voor Cursor |
| `L:\!Nova V2\bridge\nova_bridge\handoff\from_cursor\` | Cursor responses |
| `L:\!Nova V2\bridge\nova_bridge\handoff\shared_state\` | current_baseline.md, decisions.md, to_build.md |
| `L:\!Nova V2\status\` | Agent status JSON bestanden |
| `L:\!Nova V2\pipelines\nova_v2_pipeline_build\` | 36 Cursor prompts |
| `L:\Nova\SpaceShooter\` | Black Ledger (Godot 4) |
| `C:\GODOT_PROJECTS\TyrianKloon\` | TyrianKloon project |
| `L:\Nova\Key's\` | API key backups |

---

## Hetzner

- IP: 178.104.207.194
- V1 N8n: poort 5678
- V2 N8n main: poort 5679
- V2 N8n webhook: poort 5680
- SSH: `ssh root@178.104.207.194`
- Docker compose V2: `/docker/nova-v2/`

---

## Hardware

- Huidige GPU: Arc A770 8GB (Vulkan werkt NIET met Ollama → CPU inference)
- Incoming: RTX 5060 Ti 16GB (Blackwell) → ontgrendelt Qwen 2.5 Coder 9B + Nemotron Nano 4B + FLUX lokaal + Whisper
- Na RTX: vervang llama3.2:3b door Nemotron Nano 4B, Codestral door Qwen 2.5 Coder 9B

---

## Maandelijkse kosten

Cursor Pro €20 + Claude Max ~€95 + Hetzner vast €8 = ~€123/maand

---

## Actieve projecten

- **Black Ledger** — top-down space shooter, Rex Varn protagonist (Riddick archetype), 3 eindes, L:\Nova\SpaceShooter
- **Surilians** — sci-fi roman, Cathleen van Buren / GLITCH / THAEL, Venus setting, 9+ hoofdstukken
- **TyrianKloon** — Godot 4 shooter in Hoogeveen met PDOK 3D tiles, Von Neumann vijanden
- **HeliosMeter / 45Route** — routeplanner bromfiets, geparkeerd tot V2 stabiel
