# Cursor Setup voor NOVA Bridge

Hoe Cursor configureren om het handoff system te gebruiken.

## Eenmalig: Persistent Instruction

Cursor heeft geen "system prompt" maar wel Rules voor projects en AI. Voeg dit toe:

### Optie A: Via Cursor Settings (Rules)

1. Open Cursor
2. Ctrl+, voor Settings
3. Ga naar **General** → **Rules for AI**
4. Voeg toe:

```
NOVA V2 Bridge Protocol:

Je werkt binnen L:\!Nova V2\ project.

Bij start van elke sessie (of bij mijn vraag):
1. Check L:\!Nova V2\bridge\nova_bridge\handoff\to_cursor\
2. Vind oudste unprocessed opdracht (.md file zonder corresponderende 
   _response.md in from_cursor/)
3. Lees shared_state/ voor huidige context:
   - current_baseline.md (wat werkt)
   - blockers.md (wat is vast)
   - decisions.md (waarom keuzes zijn gemaakt)
4. Voer opdracht uit volgens zijn instructies
5. Schrijf response naar from_cursor/[zelfde_timestamp]_response.md
6. Update shared_state/ met nieuwe baseline info
7. Commit wijzigingen naar L:\!Nova V2\ git repo

Werk autonoom. Max 3 pogingen per substap. Bij blocker:
- Documenteer in response
- Update blockers.md  
- Ga door naar volgende substap of rapporteer klaar

Regels:
- V1 N8n (poort 5678) NOOIT aanraken
- Sprite Jury agent 01 POC NOOIT aanraken
- Status JSONs moeten webhook_url schema gebruiken (zie agent_20_status.json)
- Geen secrets in git commits of response files
```

### Optie B: Per-project `.cursor-rules` file

Maak `L:\!Nova V2\.cursor-rules` met zelfde inhoud. Cursor laadt project rules automatisch.

## Workflow

### Sessie starten

Open Cursor in `L:\!Nova V2\`. Open Composer (Ctrl+I of Ctrl+L). Zeg:

```
Check nieuwe handoff opdracht en voer uit
```

Cursor volgt dan de rules: leest `to_cursor/`, vindt oudste unprocessed, leest shared state, voert uit, schrijft response.

### Mid-sessie

Als je tussendoor wilt ingrijpen (bijv. "stop, doe X eerst"):
- Cursor Composer blijft context behouden
- Manual instructie kan opdracht overrulen
- Na ingreep: "ga verder met handoff opdracht"

### Sessie afsluiten

Cursor schrijft response + updates shared state. Dan kan je vragen:

```
Run sync_to_claude.ps1 om upload bundle te maken
```

Dat maakt `$HOME\Desktop\nova_bridge_upload\` klaar voor upload naar Claude project.

## MCP integratie (optioneel)

Als je wilt dat Cursor ook direct met N8n V2 praat tijdens handoffs:

1. Voeg V2 toe aan Cursor MCP config (zie eerdere bericht over `mcp.json`)
2. Cursor kan dan workflows lezen/schrijven in V2 direct
3. Nuttig voor "importeer deze workflow JSON in V2" taken

## Performance tips

### Grote opdrachten

Als een handoff te groot is voor 1 Cursor sessie (>4 uur scope):
- Knip in deel-opdrachten
- Elke deel-opdracht = aparte handoff file
- Zelfde dag volgnummer oplopend: 001, 002, 003

### Context window

Bij lange sessies: start nieuwe Cursor sessie en zeg "lees from_cursor/*.md van vandaag om bij te lezen, dan check to_cursor/ voor actieve". Cursor kan dan context reconstrueren.

### Snelle iteraties

Voor snelle wijzigingen niet via handoff maar direct:
- Manual prompt in Cursor Composer
- Geen formeel handoff nodig voor 5-min fixes
- Handoffs voor substantiele taken (1+ uur)

## Debugging

### Cursor volgt rules niet

Check:
1. Zijn rules opgeslagen? Settings → Rules for AI → zie je tekst?
2. Herstart Cursor
3. In nieuwe sessie: "wat zijn jouw huidige rules?" - Cursor zou moeten kunnen citeren
4. Als niet: `.cursor-rules` file in project root expliciet aanmaken

### Handoff niet gedetecteerd

Check:
1. Watcher running? `.\scripts\handoff_status.ps1`
2. File in juiste locatie? `handoff/to_cursor/YYYYMMDD_NNN_*.md`
3. Bestand readable voor Python? (permissions)

### Response incomplete

Als Cursor stopt midden in een handoff:
- Check `from_cursor/` voor partial response
- Handmatig in Cursor: "continue waar je stopte met handoff XXX"
- Of nieuwe handoff: "rescue handoff YYY" met verwijzing
