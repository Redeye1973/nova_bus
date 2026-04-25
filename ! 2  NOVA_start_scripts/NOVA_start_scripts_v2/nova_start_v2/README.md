# NOVA Start Scripts v2 (PS 5.1 compatible)

## Wat is gefixt ten opzichte van v1

v1 had bash syntax (`&&`, `||`, `2>/dev/null`) die Windows PowerShell 5.1 niet parset. v2 gebruikt alleen pure PowerShell 5.1+ syntax.

## Installatie

**Belangrijk: pad mag geen uitroepteken (`!`) bevatten.**

Het `!` karakter breekt scripts in verschillende contexten (bash interpretation op remote, sommige Windows tools). Je huidige pad `C:\NOVA\! 2 nova_start\` heeft dit probleem.

Goede locaties:
- `L:\!Nova V2\scripts\nova_start\` — consistent met rest (al heeft L: ook `!`, voor lokaal gebruik geen probleem)
- `C:\NOVA\start\` — simpel, zonder speciale karakters
- `C:\Tools\NOVA\` — aanbevolen

Stappen:

1. Pak de zip uit in bijvoorbeeld `C:\Tools\NOVA\`
2. Dubbelklik `NOVA_start.bat`
3. Script detecteert zelf welke PowerShell je hebt (7.x `pwsh` of 5.1 `powershell`)

## Wat het doet

1. **Tailscale** — service + up (als geinstalleerd op default pad)
2. **Ollama** — service start of `ollama serve` background, model lijst
3. **NOVA lokale services** (NSSM) — bridge + watchdog + heartbeat
   - Fallback naar `start_bridge.ps1` als NSSM niet aanwezig
4. **Bridge health** — localhost:8500, 3 retries
5. **SSH Hetzner** — BatchMode test
6. **Hetzner containers** — `docker ps` via SSH met grep
7. **V1 + V2 endpoint health** — HTTP check
8. **Samenvatting** met URLs

## Kleuren

- **[ OK ]** groen
- **[INFO]** cyaan
- **[WARN]** geel (niet kritiek)
- **[FAIL]** rood (aandacht nodig)

## PowerShell 7 vs 5.1

Script werkt op beide, maar PS 7 is sneller:
- Download PS 7: https://github.com/PowerShell/PowerShell/releases
- Na install herkent `pwsh` commando
- .bat wrapper pakt automatisch de beste versie

## Stop script

`NOVA_stop.bat` stopt lokale services. Hetzner blijft draaien.

## Troubleshooting

**Parse errors bij start:**
- Check of je bestandspad een `!` bevat. Zo ja: verplaats naar pad zonder speciale karakters.

**"SSH niet bereikbaar":**
- `ssh-copy-id root@178.104.207.194` draaien (key-based auth vereist)

**"Bridge niet bereikbaar":**
- Day Build D3 (NSSM) nog niet gedraaid. Script gebruikt fallback.
- Of: `L:\!Nova V2\scripts\start_bridge.ps1` manueel draaien

**NSSM services ontbreken:**
- Verwacht. Day D3 installeert ze. Tot die tijd: fallback werkt.
