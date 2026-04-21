# NOVA Bridge Troubleshooting

## Python script fails met ImportError: plyer

```
pip install plyer
```

Als je dat niet wilt, toast notifications vallen silent terug op PowerShell method (werkt op Windows 10+).

## Watcher draait maar detecteert niks

Check 1: is het proces echt running?
```powershell
.\scripts\handoff_status.ps1
```

Check 2: test handmatig
```powershell
python scripts\bridge_watcher.py --once
```

Dit doet één scan en reports. Als hij niks vindt maar er is wel een nieuwe opdracht:
- Check bestandsnaam format (moet `.md` extensie hebben)
- Check of response file al bestaat (dan wordt opdracht als "afgehandeld" beschouwd)

Check 3: status file reset
```powershell
Remove-Item bridge_state.json -Force
python scripts\bridge_watcher.py --once
```

## Toast notifications werken niet

Oorzaak 1: Windows Focus Assist staat aan (muted notifications)
- Windows Settings → System → Notifications → Focus assist → Off

Oorzaak 2: plyer niet geïnstalleerd + PowerShell fallback faalt
- `pip install plyer`
- Of gewoon accepteren - zonder toast moet je zelf `handoff_status.ps1` runnen periodiek

## Cursor leest opdrachten niet

Oorzaak 1: Rules niet actief
- Settings → Rules for AI → verify text
- Herstart Cursor

Oorzaak 2: Cursor weet pad niet
- Expliciet: "check L:\\!Nova V2\\bridge\\nova_bridge\\handoff\\to_cursor\\ op nieuwe opdrachten"

Oorzaak 3: Bestandsnaam collision
- Twee opdrachten met zelfde timestamp (onwaarschijnlijk maar mogelijk)
- Hernoem één met volgnummer +1

## Cursor schrijft response maar format is fout

Oorzaak: Cursor volgt template niet strict
- Verwijs expliciet: "gebruik templates/response_template.md structuur"
- Of bouw in je opdracht de exacte headers in

## Shared state conflict

Als beide (jij handmatig + Cursor) tegelijk in `current_baseline.md` schrijven:
- Git `L:\!Nova V2\bridge\nova_bridge\` helpt: commits maken
- Als conflict: merge handmatig
- Preventie: commit na elke shared state wijziging

## Watcher crash

Check log:
```powershell
Get-Content bridge_watcher.log -Tail 50
```

Common crashes:
- Permission denied op `from_cursor/` - fix file permissions
- Path te lang (Windows 260 char limit) - verplaats naar kortere parent

Restart:
```powershell
.\scripts\stop_watcher.ps1
.\scripts\start_watcher.ps1
```

## Upload naar Claude project faalt

Oorzaak 1: File te groot
- Claude project files max 30MB per file
- Splits grote responses

Oorzaak 2: Te veel files tegelijk
- Upload in batches van 10-20

Oorzaak 3: Format niet ondersteund
- Claude accepteert .md, .txt, .pdf, .json - alle default formats OK
- .log files hernoem naar .txt

## Disk space

Archive groeit na tijd. Cleanup:
```powershell
python scripts\bridge_watcher.py --cleanup
```

Dat verplaatst handoffs ouder dan 30 dagen naar archive. Voor harde delete:
```powershell
# Archive ouder dan 90 dagen verwijderen
Get-ChildItem handoff\archive -Directory | 
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-90) } | 
    Remove-Item -Recurse -Force
```

## Bridge werkt niet meer na Windows update

Check:
1. Python nog installed? `python --version`
2. PATH nog correct? `$env:PATH -split ';' | Where-Object { $_ -like '*Python*' }`
3. plyer nog geinstalleerd? `pip show plyer`
4. PowerShell execution policy? `Get-ExecutionPolicy` - moet RemoteSigned of ruimer zijn

## Emergency stop

Alles stoppen en state reset:
```powershell
.\scripts\stop_watcher.ps1
Remove-Item bridge_state.json -Force
Remove-Item watcher.pid -Force -ErrorAction SilentlyContinue
```

Bridge files op disk blijven intact. Herstart met:
```powershell
.\scripts\start_watcher.ps1
```
