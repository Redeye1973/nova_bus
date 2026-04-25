# SESSIE D4 — External Monitoring: UptimeRobot + Uptime Kuma

**Doel:** Watchdog van buitenaf die alerteert als bridge én Hetzner stuk zijn
**Tijd:** 60-90 min
**Handwerk:** UptimeRobot account (5 min)
**Afhankelijkheid:** D3 compleet

---

## HANDWERK VOORAF

**UptimeRobot account maken (5 min):**

1. Open https://uptimerobot.com
2. Klik "Sign Up Free"
3. Email + password (gebruik een email die je checkt — alerts komen hier)
4. Verify email
5. Login
6. Dashboard → rechtsboven avatar → My Settings → API
7. Noteer "Main API Key" (main-xxxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx)

**Monitor maken voor HEARTBEAT (je bridge duwt, UptimeRobot wacht):**

8. Dashboard → "+ New monitor"
9. Type: **Heartbeat**
10. Name: "NOVA Bridge Heartbeat"
11. Interval: 5 minutes
12. Save
13. Kopieer de heartbeat URL (bijv. https://heartbeat.uptimerobot.com/abcd...)

**Monitor voor Hetzner V2 (pull-based):**

14. "+ New monitor" opnieuw
15. Type: **HTTP(s)**
16. URL: http://178.104.207.194:5679
17. Name: "NOVA V2 N8n"
18. Interval: 5 minutes
19. Save

**Alert contact:**

20. My Settings → Alert Contacts → Add
21. Type: Email (bestaande)
22. Save

---

### ===SESSION D4 START===

```
SESSIE D4 — External monitoring: UptimeRobot heartbeat + Uptime Kuma.

## Context

Alex heeft UptimeRobot account + 2 monitors + heartbeat URL.
Nu: bridge pusht heartbeat elke 4 min naar UptimeRobot. Als bridge 5 min
stil is: email alert.

Plus: Uptime Kuma self-hosted op Hetzner voor detailed monitoring.

## Stap 1: vraag UptimeRobot gegevens

Stel Alex twee vragen:
1. "Plak UptimeRobot heartbeat URL"
2. "Plak UptimeRobot API key (main-...)"

Valideer beide (heartbeat URL moet beginnen met https://heartbeat.uptimerobot.com/).

## Stap 2: opslaan in secrets

Voeg toe aan L:\!Nova V2\secrets\nova_v2_passwords.txt:
UPTIMEROBOT_HEARTBEAT_URL=<url>
UPTIMEROBOT_API_KEY=<key>

## Stap 3: heartbeat pusher script

File: L:\!Nova V2\scripts\bridge_heartbeat.py

import time
import requests
import logging
import os
import sys
from pathlib import Path

LOG = Path(r"L:\!Nova V2\logs\heartbeat.log")
LOG.parent.mkdir(exist_ok=True)
logging.basicConfig(
    filename=LOG,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# Read heartbeat URL from secrets
SECRETS = Path(r"L:\!Nova V2\secrets\nova_v2_passwords.txt")
HEARTBEAT_URL = None
for line in SECRETS.read_text().splitlines():
    if line.startswith("UPTIMEROBOT_HEARTBEAT_URL="):
        HEARTBEAT_URL = line.split("=", 1)[1].strip()
        break

if not HEARTBEAT_URL:
    print("FAIL: UPTIMEROBOT_HEARTBEAT_URL not in secrets")
    sys.exit(1)

BRIDGE_URL = "http://localhost:8500/health"
INTERVAL = 240  # 4 min (UptimeRobot tolerantie 5 min)

def push_heartbeat(alive: bool):
    try:
        if alive:
            # Normal ping
            r = requests.get(HEARTBEAT_URL, timeout=10)
            logging.info(f"heartbeat sent, response={r.status_code}")
        else:
            # Some heartbeat URLs support fail status via ?status=fail
            r = requests.get(f"{HEARTBEAT_URL}?status=down", timeout=10)
            logging.warning(f"heartbeat DOWN reported, response={r.status_code}")
    except Exception as e:
        logging.error(f"failed pushing heartbeat: {e}")

def check_bridge():
    try:
        r = requests.get(BRIDGE_URL, timeout=5)
        return r.status_code == 200
    except:
        return False

def main():
    logging.info("Heartbeat pusher started")
    while True:
        alive = check_bridge()
        push_heartbeat(alive)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()

## Stap 4: heartbeat pusher als NSSM service

$nssm = "<pad_uit_session_D3>"  # lees uit state, of vraag opnieuw

& $nssm install "NOVA_Heartbeat" $pythonExe
& $nssm set "NOVA_Heartbeat" AppParameters "L:\!Nova V2\scripts\bridge_heartbeat.py"
& $nssm set "NOVA_Heartbeat" AppDirectory "L:\!Nova V2\scripts"
& $nssm set "NOVA_Heartbeat" DisplayName "NOVA Bridge Heartbeat"
& $nssm set "NOVA_Heartbeat" Start SERVICE_AUTO_START
& $nssm set "NOVA_Heartbeat" AppStdout "L:\!Nova V2\logs\heartbeat_stdout.log"
& $nssm set "NOVA_Heartbeat" AppStderr "L:\!Nova V2\logs\heartbeat_stderr.log"
& $nssm set "NOVA_Heartbeat" AppExit Default Restart

Start-Service "NOVA_Heartbeat"

Verify: 
Start-Sleep 10
Get-Content "L:\!Nova V2\logs\heartbeat.log" -Tail 5

Moet 1-2 "heartbeat sent" entries hebben.

## Stap 5: Uptime Kuma deployen op Hetzner

SSH naar prod server:

ssh root@178.104.207.194 << 'EOF'
cd /docker

# Maak uptime-kuma dir
mkdir -p uptime-kuma/data
cd uptime-kuma

# docker-compose.yml
cat > docker-compose.yml << 'YAML'
version: "3.8"
services:
  uptime-kuma:
    image: louislam/uptime-kuma:1
    container_name: uptime-kuma
    restart: unless-stopped
    ports:
      - "3001:3001"
    volumes:
      - ./data:/app/data
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      - UPTIME_KUMA_DISABLE_FRAME_SAMEORIGIN=false
YAML

# Start
docker compose up -d

# Wait for startup
sleep 15

# Verify
docker ps | grep uptime-kuma
curl -s http://localhost:3001 | head -1
EOF

## Stap 6: Uptime Kuma initial setup (handwerk door Alex VIA SSH TUNNEL)

Cursor print instructies:

"UPTIME KUMA SETUP — Alex moet dit één keer doen:

1. Open NIEUW PowerShell venster:
   ssh -L 3001:localhost:3001 root@178.104.207.194
   (laat tunnel open)

2. Open browser → http://localhost:3001

3. Admin account aanmaken (eerste keer wizard):
   - Username: nova-admin
   - Password: <kies sterke, noteer in secrets onder UPTIME_KUMA_PASSWORD=>
   - Language: Nederlands of English

4. Dashboard → Add New Monitor:

   Monitor 1: V2 N8n
   - Type: HTTP(s) - Keyword
   - Name: NOVA V2 N8n
   - URL: http://178.104.207.194:5679
   - Interval: 60 sec
   - Retries: 2
   - Save

   Monitor 2: V2 Judge
   - Type: HTTP(s)
   - Name: NOVA Judge
   - URL: http://nova-v2-judge:8000/health
   - Interval: 60 sec
   - Save

   Monitor 3: V2 Postgres
   - Type: Docker Container
   - Name: NOVA Postgres
   - Container name: nova-v2-postgres
   - Save

   Monitor 4: Heartbeat van Bridge (push)
   - Type: Push
   - Name: NOVA Bridge Heartbeat
   - Interval: 300 sec (5 min tolerance)
   - Save
   - Kopieer Push URL!

5. Plak Push URL terug in deze chat."

Wacht op Alex's Uptime Kuma Push URL.

## Stap 7: bridge heartbeat ook naar Uptime Kuma

Update bridge_heartbeat.py om TWEE URLs te pingen:

URLS = [
    os.environ.get("UPTIMEROBOT_URL"),  # external fail-safe
    os.environ.get("UPTIME_KUMA_URL"),   # internal detailed
]

Of simpeler: lees beide uit secrets, push beide in zelfde loop.

Update code zodat beide URLs elke 4 min geping worden.

Restart service:
Restart-Service NOVA_Heartbeat

Verify: beide UptimeRobot en Uptime Kuma laten binnen 5 min een successful heartbeat zien.

## Stap 8: alert contacts in Uptime Kuma

Instructie voor Alex:
"Ook in Uptime Kuma:
Settings → Notifications → Setup
- Type: Email (SMTP) OF Telegram (bot token)
- Test notificatie
- Koppel aan alle monitors"

## Stap 9: rapport

File: L:\!Nova V2\docs\session_D4_report.md
# Sessie D4 Rapport
- Timestamp
- UptimeRobot account: active
- UptimeRobot heartbeat monitor: setup, interval 5 min
- UptimeRobot HTTP monitor V2: active
- Bridge heartbeat service: installed, 4 min interval
- Uptime Kuma: deployed on Hetzner :3001
- Uptime Kuma monitors: <count>
- Both heartbeat paths: verified
- Alert contacts: email configured
- Status: SUCCESS / PARTIAL / FAILED
- Next: sessie D5 (Monitor agent integration + DR drill)

git add scripts/bridge_heartbeat.py docs/session_D4_report.md
git commit -m "day session D4: external monitoring (UptimeRobot + Uptime Kuma)"
git push origin main

Print "SESSION D4 COMPLETE — external monitoring active"

REGELS:
- UptimeRobot API key NIET in logs/commits
- Uptime Kuma admin password ook niet echoen
- Als Hetzner poort 3001 niet extern bereikbaar: dat is OK (SSH tunnel)
- Push URLs mogen in secrets file, niet in commits

Ga.
```

### ===SESSION D4 EINDE===

---

## OUTPUT

- UptimeRobot monitoring actief (external)
- Uptime Kuma op Hetzner :3001 (internal detailed)
- `NOVA_Heartbeat` service draait op PC
- Heartbeats naar beide endpoints elke 4 min
- Email alerts geconfigureerd

## VERIFIEREN

```powershell
Get-Service NOVA_Heartbeat
Get-Content "L:\!Nova V2\logs\heartbeat.log" -Tail 10
```

En in UptimeRobot dashboard: "Up" status voor beide monitors.
En in Uptime Kuma (http://localhost:3001 via SSH tunnel): groene monitors.

## BIJZONDER

Test de chain zo:
1. Stop `NOVA_Bridge_Service` handmatig
2. Wacht 5-8 minuten
3. Krijg je een email?

Als ja: pipeline werkt 100%.
Als nee: UptimeRobot tolerantie controleren, of email in spam folder.
