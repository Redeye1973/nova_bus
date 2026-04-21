# NOVA Bridge - Claude.ai ↔ Cursor Handoff System

Automatische handoff tussen claude.ai (strategie/packages) en Cursor (executie) zonder eindeloos copy-paste.

## Hoe het werkt

```
claude.ai (deze chat)
    ↓ schrijft opdracht
handoff/to_cursor/[timestamp]_[name].md
    ↓ Cursor leest (via watcher script)
Cursor voert autonoom uit
    ↓ schrijft resultaat
handoff/from_cursor/[timestamp]_[name]_response.md
    ↓ jij upload naar Claude project
claude.ai leest volgende handoff
```

## Installatie

### Stap 1: Uitpakken

```powershell
Expand-Archive -Path "$HOME\Downloads\nova_bridge.zip" -DestinationPath "L:\!Nova V2\bridge\" -Force
```

### Stap 2: Cursor watcher starten

Open PowerShell in `L:\!Nova V2\bridge\nova_bridge\`:

```powershell
.\scripts\start_watcher.ps1
```

Dit start een background process dat `handoff/to_cursor/` monitort. Zodra ik een nieuwe opdracht achterlaat, verschijnt notificatie + opent Cursor met de opdracht klaar.

### Stap 3: Bij Cursor startup

Plak dit **eenmalig** in Cursor Composer als "persistent instruction":

```
Je werkt binnen NOVA V2 project L:\!Nova V2\.

Bij start van elke sessie:
1. Check L:\!Nova V2\bridge\nova_bridge\handoff\to_cursor\
2. Zoek nieuwste unprocessed opdracht (.md file zonder corresponderende _response.md)
3. Lees handoff/shared_state/ voor context (current_baseline, blockers, decisions)
4. Voer opdracht uit volgens zijn instructies
5. Schrijf resultaat naar handoff/from_cursor/[zelfde_timestamp]_response.md
6. Update handoff/shared_state/ met nieuwe baseline info

Werk autonoom. Max 3 pogingen per substap. Bij blocker: markeer in response + shared_state/blockers.md.
```

### Stap 4: Gebruik

**Ik (claude.ai)**: schrijf opdracht in outputs zip, jij pakt uit in `handoff/to_cursor/`

**Cursor**: leest automatisch, voert uit, schrijft response

**Jij**: upload `from_cursor/*.md` naar je Claude project periodiek (1-2x per dag)

## Bestandsstructuur

```
nova_bridge/
├── README.md                         # Dit bestand
├── scripts/
│   ├── start_watcher.ps1             # Start file watcher
│   ├── stop_watcher.ps1              # Stop watcher
│   ├── handoff_status.ps1            # Toon current state
│   ├── archive_old.ps1               # Archiveer oude handoffs
│   └── bridge_watcher.py             # Core watcher logic
├── handoff/
│   ├── to_cursor/                    # Ik schrijf hier
│   ├── from_cursor/                  # Cursor schrijft hier
│   ├── shared_state/                 # Beide lezen/schrijven
│   │   ├── current_baseline.md
│   │   ├── blockers.md
│   │   └── decisions.md
│   └── archive/                      # Voltooide handoffs
├── templates/
│   ├── opdracht_template.md
│   └── response_template.md
└── docs/
    ├── PROTOCOL.md                   # Hoe handoffs structureren
    ├── CURSOR_SETUP.md               # Cursor configuratie
    └── TROUBLESHOOTING.md
```

## Voordelen

- **Geen copy-paste**: ik schrijf opdracht, Cursor leest direct van disk
- **Asynchroon**: jij kan weg, Cursor werkt door, rapport klaar wanneer jij terug bent
- **Audit trail**: alle handoffs bewaard in archive/
- **Shared state**: geen "wait is het nu X of Y?" - beide Claudes kijken naar dezelfde files
- **Rollback mogelijk**: als Cursor fout doet, rollback per handoff

## Wat je moet doen

Eénmalig:
- Uitpakken
- Cursor config updaten
- Watcher starten

Per sessie:
- Upload `from_cursor/*.md` naar Claude project (drag-drop in chat of via Projects sync)
- Ik schrijf nieuwe opdracht → jij krijgt zip → uitpakken → Cursor doet rest

Dat is alles.

## Limitaties

- Niet realtime: jij moet nog steeds 1x upload per batch doen (Claude kan niet zelf files lezen van jouw PC)
- Cursor moet open staan en watcher draaien
- Conflict detectie: als jij + Cursor tegelijk in zelfde file schrijven, laatste wint

## Volgende stap na installatie

Zie `handoff/to_cursor/20260419_001_first_handoff.md` voor de eerste opdracht - dat is batch 2 (Agent 11, 17, 21) volgens het plan dat we bespraken.
