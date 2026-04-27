# Nova Reference Layer — Cursor Prompts, fase 7

**Voor:** A. Meter, Nova Platform  
**Datum:** April 2026  
**Doel:** Windows-specifieke hardening, alert-irritatie oplossen, foundations stabieler maken, plus geoptimaliseerde patches voor de bestaande Stap1 en Fase6 prompts.

**Werkdirectory:** `L:\!Nova V2\!2 Cursor ToDo\27-04-2026 1251`

**Aannames** (corrigeer in dit document vóór uitvoering als ze niet kloppen):
- Nova draait op Windows 11 Pro desktop, native Docker (geen WSL2 backend nog)
- Monitoring = Uptime Kuma op dezelfde pc
- "Bridge" = Discord↔Telegram koppeling, draait als N8n workflow of losse bot
- Nova-pc is privé en wordt 's avonds soms uitgezet voor gaming of bedtijd
- Geen UPS aanwezig — stroomverlies is gewoon uitval

---

## INSTRUCTIES AAN CURSOR — LEES EERST

Dit document bevat **9 nieuwe prompts** plus **2 optimalisatie-patches** voor bestaande bestanden. Twee uitvoeringsmodi — kies één:

**Modus A — In één keer geplakt:**
Werk de prompts sequentieel af in de volgorde 01 → 11. Per prompt: schrijf code → run tests → commit → smoke check → DAARNA pas door naar volgende. Vraag mij om akkoord NA elke commit, tenzij ik in de openingsboodschap "voer alles achter elkaar uit zonder check-ins" zeg.

**Modus B — Als losse bestanden in directory:**
Splits dit document in `L:\!Nova V2\!2 Cursor ToDo\27-04-2026 1251\` op in genummerde bestanden:
- `01_shutdown_alerts_fix.md`
- `02_disk_log_rotation.md`
- `03_connection_pool_limits.md`
- `04_timezone_utc_forcing.md`
- `05_secrets_safety.md`
- `06_wsl2_migration.md`
- `07_per_build_rate_limiting.md`
- `08_telegram_snooze_command.md`
- `09_weekly_self_check_report.md`
- `10_optimization_patch_stap1.md`
- `11_optimization_patch_fase6.md`

Werk ze daarna in deze volgorde af, één voor één.

**Universele regels:**
- Vastlopen na 3 pogingen op zelfde technisch probleem → STOP, zoek alternatief via web/docs, ga geen circles draaien
- Bij elke "NIET DOEN"-clausule: lees, begrijp, respecteer
- Geen scope creep — als een prompt een bestand niet noemt, raak het niet aan
- Bestaande tests moeten groen blijven na elke prompt

---

# 01 — Shutdown/startup alerts oplossen

```
PROBLEEM:
Bij elke pc-shutdown krijg ik via Telegram en Discord alerts dat Nova en/of de
bridge "down" zijn. Dit is geen crash, dit is gepland gedrag. De alerts zijn
nu zo veel ruis dat ik echte alerts ga missen.

OPLOSSING:
Twee dingen tegelijk: (a) Windows vertelt het monitoringsysteem dat het pc 
shutdown is — niet een crash, en (b) een tijdelijke "stille modus" wordt
geactiveerd zodat eventuele alerts in de eerste 5 minuten na boot ook
gesuppressed worden.

NIEUWE BESTANDEN:

1. infrastructure/scripts/windows/nova_shutdown_notify.ps1
   PowerShell script dat:
   - Een webhook fired naar de centrale alert-suppressor (zie punt 3)
   - Body: {"event": "shutdown", "host": "nova-desktop", "timestamp": "<ISO>"}
   - Timeout 5 seconden — mag de shutdown NIET vertragen
   - Schrijft logregel naar C:\nova\logs\lifecycle.log
   - Bij webhook-fail: alleen log, geen blocking
   
   IMPORTANT: dit script moet draaien NIET-blocking en in maximaal 5 seconden
   klaar zijn, anders blokkeert het Windows shutdown.

2. infrastructure/scripts/windows/nova_startup_notify.ps1
   Vergelijkbaar maar met event "startup". Plus:
   - Kort wachten (30s) op netwerk en docker daemon ready
   - Webhook stuurt event "startup" + activeert quiet_mode voor 5 min

3. nova-bridge/src/alert_suppressor.py (nieuwe module in bestaande bridge)
   FastAPI service die:
   
   POST /lifecycle
   Body: {"event": "shutdown"|"startup"|"snooze", "host": str, "duration_minutes": int?}
   
   Logica:
   - shutdown event → set Redis key "nova:quiet_mode" met TTL 7200s (2 uur, ruim
     genoeg voor reboot of bedtijd)
   - startup event → set Redis key "nova:quiet_mode" met TTL 300s (5 min) zodat
     na boot eerst alles stabiel kan starten zonder false-positive alerts
   - snooze event → set Redis key met TTL = duration_minutes * 60
   
   GET /lifecycle/status
   Return current quiet_mode state + remaining seconds
   
   Mount op de bestaande bridge service — geen nieuw container nodig.

4. nova-bridge/src/middleware.py — alert filter
   Voor elke uitgaande alert (Telegram, Discord):
   - Check Redis "nova:quiet_mode"
   - Als gezet: log de gesupprimeerde alert naar Postgres tabel "suppressed_alerts"
     maar verstuur NIET
   - Als niet gezet: verstuur normaal
   
   CRITICAL: alleen INFRASTRUCTURE alerts filteren ("X is down", "container exit").
   ECHTE messages naar gebruikers (Telegram chat met Alex, Discord commando 
   responses) ALTIJD doorlaten. Dit is geen mute-knop voor jou, dit is een 
   filter voor monitoring-noise.

5. infrastructure/scripts/install_windows_lifecycle_hooks.ps1
   Installer-script dat draait als Administrator:
   - Kopieert nova_shutdown_notify.ps1 naar C:\nova\scripts\
   - Registreert het via Group Policy: Computer Configuration > Windows Settings 
     > Scripts > Shutdown
   - Idem voor startup script
   - Test webhook bereikbaarheid voordat installatie compleet is
   
   Documentatie in scripts/README_WINDOWS_HOOKS.md met manual installation
   instructies als alternatief, want gpedit kan finicky zijn.

DATABASE WIJZIGING:

6. nova-bridge/sql/004_suppressed_alerts.sql
   
   CREATE TABLE IF NOT EXISTS suppressed_alerts (
       id              BIGSERIAL PRIMARY KEY,
       suppressed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       channel         TEXT NOT NULL,         -- 'telegram', 'discord'
       alert_text      TEXT NOT NULL,
       reason          TEXT NOT NULL,         -- 'quiet_mode_active', etc.
       quiet_mode_ttl  INT
   );
   
   CREATE INDEX idx_suppressed_recent ON suppressed_alerts(suppressed_at DESC);
   
   Retention: keep laatste 7 dagen, drop daarvoor (cron job, prompt 02 doet dit).

UPTIME KUMA INTEGRATIE:

7. infrastructure/uptime_kuma/maintenance_setup.md
   Documentatie (geen code) met instructie hoe in Uptime Kuma:
   - Een "Maintenance Window" toe te voegen voor recurring 23:00-07:00 als
     extra vangnet (defense in depth bovenop het lifecycle hook)
   - Hoe een "Push monitor" te configureren voor Nova-services zodat 
     monitoring push-based wordt ipv polling-based — push stopt natuurlijk 
     als pc uit gaat, geen alert
   
   Belangrijk: dit is configuratie via UI, geen code. Beschrijf het zo dat 
   ik het in 5 minuten zelf kan klikken.

TESTS:

In nova-bridge/tests/test_alert_suppressor.py:

- test_shutdown_event_sets_quiet_mode_2h: POST /lifecycle event=shutdown,
  GET /status returnt remaining ~7200s
- test_startup_event_sets_quiet_mode_5min: idem maar 300s
- test_alert_during_quiet_mode_logged_not_sent: trigger fake alert, 
  verifieer Postgres rij in suppressed_alerts EN geen webhook call
- test_alert_outside_quiet_mode_sent_normally: idem maar zonder quiet mode,
  verifieer webhook wel aangeroepen
- test_user_messages_bypass_filter: Telegram chat message naar Alex moet 
  ALTIJD door, ook bij quiet_mode actief
- test_lifecycle_endpoint_returns_503_if_redis_down: graceful degradation

VALIDATIE (handmatig):

1. Run install_windows_lifecycle_hooks.ps1 als Administrator
2. Reboot pc
3. Telegram bericht na boot: "Nova-host startup, quiet mode 5 min"
4. Verifieer in Uptime Kuma dat geen down-alert binnen die 5 min is verstuurd
5. Shutdown pc om bedtijd
6. GEEN alerts in de daaropvolgende 2 uur
7. Daarna pas zou een echt offline-alert komen (als pc nog uit is)

COMMIT MESSAGE:
"feat(bridge): Windows lifecycle hooks with quiet mode for graceful shutdown"

NIET DOEN:
- Geen alert-suppression voor user-facing messages (Telegram chat, bot replies)
- Geen permanente "altijd suppressed" mode — quiet mode heeft altijd TTL
- Geen alert-suppression op fouten in Nova services zelf (errors die NIET via
  monitoring komen, maar via try/except in code) — die zijn bug signals
```

---

# 02 — Disk fill-up bescherming

```
PROBLEEM:
Een runaway log-loop, een crashende container, of accumulating Postgres data
kan binnen uren je systeem vol laten lopen. Alle services down, ook Uptime
Kuma, dus geen alert. Stille killer.

OPLOSSING:
Drie lagen: (a) Docker logs gebound aan grootte, (b) actieve disk monitoring 
naar Telegram, (c) automatic cleanup van predictable cruft.

WIJZIGINGEN:

1. infrastructure/docker-compose.yml — voor ALLE services
   Voeg toe aan elk service block:
   
   logging:
     driver: "json-file"
     options:
       max-size: "100m"
       max-file: "3"
   
   Dit beperkt elk container tot 300MB aan logs total. Bestaande grote logs 
   moeten handmatig opgeschoond worden — log een TODO in commit message.

2. infrastructure/scripts/windows/nova_disk_check.ps1
   PowerShell script dat:
   - Disk usage controleert van: C:\, drive met Docker volumes (vermoedelijk 
     L: gezien werkdir), drive met backups
   - Postgres data dir grootte checkt (via docker exec + du)
   - Bij >80% disk usage: webhook naar bridge met severity "warning"
   - Bij >90% disk usage: webhook met severity "critical" (wordt NIET gesuppressed,
     ook tijdens quiet mode)
   - Bij >95%: triggers automatic cleanup van docker logs en oudste backups
   
   Output ook naar C:\nova\logs\disk_check.log voor history.

3. infrastructure/scripts/windows/nova_cleanup.ps1
   Cleanup script (idempotent, safe to run vaak):
   - docker system prune -f --filter "until=168h" (>7 dagen oud)
   - Verwijder backups ouder dan 30 dagen uit backup dir
   - Verwijder suppressed_alerts ouder dan 7 dagen via SQL
   - Verwijder Uptime Kuma history ouder dan 90 dagen (via SQL als mogelijk)
   - Output: hoeveelheid GB vrijgemaakt

4. Windows Task Scheduler entries (lever instructies in 
   infrastructure/scripts/README_TASKSCHEDULER.md):
   - nova_disk_check.ps1 elke 30 minuten
   - nova_cleanup.ps1 elke zondag 02:00
   - Beide moeten draaien als Administrator (anders kan docker exec niet)
   - Trigger: At Logon + every 30min repeat (voor disk_check)

5. nova-bridge — nieuwe alert kanaal:
   Voeg "critical_alert" type toe aan alert_suppressor middleware.
   Critical alerts BYPASS quiet mode. Reden: disk-full bij 95% kan jouw 
   bedtijd zijn maar je wilt het wél weten.
   
   Format Telegram message:
   "🚨 CRITICAL Nova disk fill: L: 95% (Postgres data 2.3GB). Cleanup running."

TESTS:

In infrastructure/tests/test_disk_check.ps1 (PowerShell Pester):
- test_normal_disk_usage_no_alert: mock 50% usage → no webhook
- test_high_usage_warning_alert: mock 85% → severity warning
- test_critical_usage_alert_and_cleanup: mock 96% → severity critical + 
  cleanup script triggered
- test_cleanup_dry_run_calculates_freeable_space

VALIDATIE:
- Vul handmatig L: tot 85% (e.g. dummy file `fsutil file createnew dummy.bin 100GB`)
- Verifieer dat binnen 30 min een Telegram warning komt
- Cleanup dummy file
- Verifieer geen valse alerts daarna

COMMIT MESSAGE:
"feat(infra): disk monitoring with auto-cleanup and bypass-quiet-mode for critical alerts"

NIET DOEN:
- Geen ALTER van Postgres autovacuum nu — pgsql doet dat zelf prima
- Geen automatic Postgres dump-and-clear bij high disk — risico op dataverlies
- Geen Docker prune zonder --filter "until=" — verwijdert anders draaiende
  resources
```

---

# 03 — Connection pool limits

```
PROBLEEM:
Postgres staat default op max_connections=100. Een bug die connections lekt
in nova-ref of nova-learn kan binnen een uur alle 100 dichttrekken. Dan kan
zelfs Uptime Kuma er niet meer bij om te alerten dat het stuk is.

OPLOSSING:
Expliciete pool limits per service + proactive monitoring van actieve 
connections + alert vóór exhaustion.

WIJZIGINGEN:

1. nova-ref/src/nova_ref/core/db.py
   
   Configureer asyncpg pool met expliciete limits:
   
   pool = await asyncpg.create_pool(
       dsn=DATABASE_URL,
       min_size=2,
       max_size=10,                       # CONFIGURABLE via env
       max_inactive_connection_lifetime=300.0,
       command_timeout=30.0,
   )
   
   Env vars:
   NOVA_REF_DB_POOL_MIN=2
   NOVA_REF_DB_POOL_MAX=10
   NOVA_REF_DB_POOL_IDLE_TIMEOUT=300

2. nova-learn/src/nova_learn/core/db.py
   Idem maar:
   NOVA_LEARN_DB_POOL_MIN=1
   NOVA_LEARN_DB_POOL_MAX=5    (kleiner — minder hot path)

3. nova-bridge — als die ook Postgres gebruikt, idem.

4. Postgres config tweak (postgres-ref container):
   In docker-compose, voeg toe:
   command: ["postgres",
             "-c", "max_connections=50",
             "-c", "log_connections=on",
             "-c", "log_disconnections=on",
             "-c", "log_min_duration_statement=1000"]
   
   Reden: 50 max is genoeg voor jouw 3 services met pool 10+5+5=20, plus 
   ruimte voor admin connections, plus monitoring. Lager dan default 100 
   forceert je om bij groei expliciet te denken over connection budget.

5. Health check uitbreiding in nova-ref/src/nova_ref/api/health.py:
   GET /health endpoint returnt nu ook:
   {
     "db_connections_active": int,
     "db_connections_idle": int,  
     "db_pool_max": int,
     "db_pool_utilization_percent": float
   }
   
   Bij utilization >80%: log structlog warning per request.
   Bij utilization >95%: /ready endpoint returnt 503 (load balancer fail-over)

6. Prometheus metrics:
   nova_ref_db_pool_active{service}
   nova_ref_db_pool_idle{service}  
   nova_ref_db_pool_size_max{service}
   
   Update elke 30 seconden via background task.

7. infrastructure/scripts/check_connection_leak.ps1
   Diagnostic script (manual run):
   - psql query: SELECT pid, application_name, state, query_start, query 
     FROM pg_stat_activity WHERE state != 'idle' ORDER BY query_start;
   - Output: lijst van actieve connections > 60s oud
   - Hint message bij findings: "Possible connection leak in {app_name}, 
     query started {seconds}s ago"

TESTS:

- test_pool_respects_max_size: open 11 concurrent connections, 11e moet 
  wachten of timeout
- test_health_endpoint_reports_pool_stats
- test_ready_returns_503_at_high_utilization
- test_long_running_query_logged_to_postgres_log

VALIDATIE:
- Start nova-ref, doe `docker exec postgres-ref psql -c "SHOW max_connections;"` 
  → moet 50 zijn
- GET /health, bekijk db_pool_utilization_percent (rust: <30%)
- Run load test: 100 parallel /lookup calls
- Verifieer geen errors, utilization piekt onder 100%

COMMIT MESSAGE:
"feat(db): explicit pool limits, connection monitoring, leak detection"

NIET DOEN:
- Geen connection pooler zoals PgBouncer nu — overkill voor jouw schaal
- Geen retry op pool exhaustion in app code — laat de error propageren, 
  dat is je signaal dat er een leak is
- Geen automatic connection-killing van long-running queries — kan productie
  workflows breken
```

---

# 04 — Tijdzones forceren UTC

```
PROBLEEM:
Postgres staat op UTC default, Windows op Europe/Amsterdam, Docker containers
varieren. Eerste keer dat audit-log entries een uur in de toekomst staan, 
weet je niet meer wat klopt. Plus zomertijd-overgang in maart en oktober 
breekt cron-schedules subtiel.

OPLOSSING:
Forceer UTC OVERAL behalve aan de display-rand (Telegram berichten, dashboards).
Standaardiseer datetime handling in code.

WIJZIGINGEN:

1. docker-compose.yml — voor ELKE service:
   environment:
     - TZ=UTC
   
   Inclusief postgres, nova-ref, nova-learn, nova-bridge, redis, uptime-kuma.

2. Postgres config (al deels in prompt 03):
   command: [..., "-c", "timezone=UTC"]
   
   Verifieer met: `docker exec postgres-ref psql -c "SHOW timezone;"` → UTC

3. Codebase audit — Cursor moet onderstaande regex ZOEKEN en patches voorstellen:
   
   PATTERN A: datetime.now() zonder timezone arg
   FIND:    datetime.now()
   REPLACE: datetime.now(timezone.utc)
   FILES:   alle *.py in nova-ref/, nova-learn/, nova-bridge/
   
   PATTERN B: datetime.utcnow() (deprecated in Python 3.12+)
   FIND:    datetime.utcnow()
   REPLACE: datetime.now(timezone.utc)
   
   PATTERN C: TIMESTAMP zonder TZ in SQL
   FIND:    TIMESTAMP NOT NULL
   REPLACE: TIMESTAMPTZ NOT NULL
   FILES:   alle *.sql migraties
   
   Voor elke match: laat me eerst de wijzigingen zien voordat je ze toepast.
   Niet auto-applyen — sommige TIMESTAMP zonder TZ kunnen bewust zo zijn.

4. nova-ref/src/nova_ref/core/timeutils.py (nieuwe module):
   
   from datetime import datetime, timezone
   from zoneinfo import ZoneInfo
   
   def now_utc() -> datetime:
       """Canonieke UTC timestamp factory. Use deze ipv datetime.now()."""
       return datetime.now(timezone.utc)
   
   def to_local(dt: datetime, tz: str = "Europe/Amsterdam") -> datetime:
       """ALLEEN gebruiken voor display, nooit voor opslag."""
       return dt.astimezone(ZoneInfo(tz))
   
   def format_for_user(dt: datetime, tz: str = "Europe/Amsterdam") -> str:
       """Friendly format voor Telegram/Discord messages."""
       local = to_local(dt, tz)
       return local.strftime("%d-%m-%Y %H:%M")
   
   Update bestaande code om now_utc() te gebruiken ipv datetime.now().

5. nova-bridge — Telegram message formatting:
   Alle uitgaande messages die timestamps bevatten, gebruik format_for_user().
   Voorbeeld: "Backup voltooid om {format_for_user(backup.completed_at)}"

6. Pre-commit hook (in .git/hooks/pre-commit):
   Bash script dat blokkeert op:
   - datetime.now() zonder tz argument
   - datetime.utcnow()  
   - 'TIMESTAMP NOT NULL' in *.sql (alleen TIMESTAMPTZ toegestaan, met
     uitzondering van expliciete /* TIMESTAMP-OK */ comment)

TESTS:

- test_now_utc_returns_aware_datetime: now_utc().tzinfo is timezone.utc
- test_to_local_converts_correctly: 12:00 UTC → 13:00 Europe/Amsterdam in 
  winter, 14:00 in zomer
- test_audit_log_uses_utc: doe een audit insert, query DB direct, 
  verifieer changed_at heeft UTC offset
- test_telegram_messages_show_local_time: mock het formatteren, verwacht 
  CET/CEST output
- test_dst_transition_doesnt_break_cron: simulate 25 maart 03:00 → moet 
  geen duplicate or skipped jobs

VALIDATIE:
- docker exec postgres-ref date → moet UTC tonen
- docker exec nova-ref date → moet UTC tonen
- Insert handmatig een audit row, query: 
  SELECT changed_at, changed_at AT TIME ZONE 'Europe/Amsterdam' 
  → kolom 1 in UTC, kolom 2 in lokaal
- Telegram bericht over recent gebeurtenis: tijdstempel klopt met klok aan muur

COMMIT MESSAGE:
"refactor(time): force UTC across stack, local time only at display edges"

NIET DOEN:
- Geen UTC tonen in user-facing messages — verwarrend, geen UX-winst
- Geen migratie van bestaande TIMESTAMP NULL kolommen ZONDER mij eerst 
  consulteren — kan rare ALTER TABLE issues geven
- Geen pytz library — gebruik built-in zoneinfo (Python 3.9+)
```

---

# 05 — Secrets veiligheid

```
PROBLEEM:
.env bestanden met API keys, Postgres passwords, Telegram bot tokens, etc.
Eén git commit waarbij .env per ongeluk wordt meegezet en alles is publiek
op GitHub. Dit is niet hypothetisch — gebeurt elke week aan iemand.

OPLOSSING:
Defense in depth: global gitignore, gitleaks pre-commit hook, secrets in 
een aparte locatie buiten de repo, en een audit van wat er nu al in git 
zit aan vermoedelijke secrets.

WIJZIGINGEN:

1. ~/.config/git/ignore (Windows: %USERPROFILE%\.gitignore_global):
   Maak/update met content:
   
   # Secrets
   .env
   .env.*
   !.env.example
   *.key
   *.pem
   *secrets*
   *credentials*
   *_token.txt
   
   # Backups en dumps  
   *.dump
   *.dump.gz
   *.sql.gz
   
   Configureer git om dit te gebruiken:
   git config --global core.excludesFile ~/.config/git/ignore
   
   (Op Windows: git config --global core.excludesFile "%USERPROFILE%/.gitignore_global")

2. Per-project .gitignore audit
   Verifieer dat ELKE Nova-repo (.gitignore in root) bevat:
   - .env
   - .env.*  
   - !.env.example
   
   Als deze ontbreken: voeg toe en commit.

3. Pre-commit hook met gitleaks:
   
   Maak .pre-commit-config.yaml in elke repo:
   repos:
     - repo: https://github.com/gitleaks/gitleaks
       rev: v8.18.0
       hooks:
         - id: gitleaks
   
   Setup:
   - pip install pre-commit
   - pre-commit install
   
   Test: probeer een commit met "AWS_KEY=AKIA..." string → moet geblokkeerd
   worden. Documenteer dit in repo README als verplichte setup-stap.

4. Audit bestaande git history:
   Run vanuit elke Nova-repo:
   
   git log --all --full-history -p | gitleaks detect --pipe -v --no-banner
   
   Als gitleaks vondsten doet:
   STOP en informeer mij — vondsten in history vereisen filter-repo of 
   BFG cleanup, dat is geen automatic fix.

5. Secrets locatie standaardiseren:
   Verplaats .env files naar buiten de repo:
   
   Van: L:\!Nova V2\nova-ref\.env
   Naar: C:\nova\secrets\nova-ref.env
   
   Update docker-compose:
   env_file:
     - C:/nova/secrets/nova-ref.env
   
   Permissions op C:\nova\secrets\: alleen jouw user, geen "Everyone" of 
   "Users". PowerShell:
   icacls "C:\nova\secrets" /inheritance:r /grant:r "$($env:USERNAME):(OI)(CI)F"

6. Nieuwe .env.example bestanden:
   Voor elke service een .env.example MET alle keys MAAR met dummy values:
   
   # nova-ref/.env.example
   NOVA_REF_DB_PASS=changeme_in_actual_env
   SMITHSONIAN_API_KEY=your_smithsonian_key_here
   ...
   
   .env.example MAG in git, .env MAG NIET.

7. Documentatie SECRETS_SETUP.md in nova-ref:
   Korte runbook hoe een nieuwe ontwikkelaar (of toekomstige Alex die 
   restoret) de secrets opnieuw inricht na bare-metal install.

VALIDATIE:

- Run gitleaks tegen elke repo: clean
- Probeer test-commit met fake secret: geblokkeerd  
- Verifieer .env in C:\nova\secrets\ leesbaar voor service maar niet 
  voor andere users (test met `runas /user:guest`)
- Containers starten correct met de nieuwe env_file pad

COMMIT MESSAGE:
"chore(security): global gitignore, gitleaks pre-commit, secrets relocation"

NIET DOEN:
- Geen Hashicorp Vault, AWS Secrets Manager, etc — overkill voor solo project
- Geen secrets in environment van Docker Compose itself (zichtbaar via 
  `docker inspect`) — env_file is veiliger
- Geen automatische rotatie nu — handmatig bij vermoeden van leak is genoeg
- Geen Cleanup van git history zonder mijn akkoord — destructive operation
```

---

# 06 — WSL2 migratie van native Windows Docker

```
PROBLEEM:
Native Windows Docker (Hyper-V backend) heeft 3-10× slechtere file IO 
performance via volume mounts. Bash scripts werken niet zonder WSL. Cron 
ontbreekt op host. Toekomstige scaling pijnpunt.

OPLOSSING:
Migreer naar Docker Desktop met WSL2 backend + Ubuntu distro. Geen feature 
loss, dramatische performance gain, alle eerdere prompts werken zonder 
aanpassing.

DIT IS DE ENIGE PROMPT DIE EEN SERVICE-DOWNTIME VEREIST. Plan ervoor — 
duur ~45-60 min met tests. Doe dit NIET op een moment waarop je Nova
nodig hebt.

PRE-FLIGHT (Cursor: vraag eerst akkoord op deze checklist voordat je begint):
- [ ] Lopende processen geen lookup-load: stop sprite-pipeline, n8n workflows
- [ ] Backup gemaakt EN gevalideerd: pg_dump van nova_ref_db naar C:\nova\backups\
- [ ] Diskspace vrij op WSL2-target: minimaal 50GB op C: of andere SSD
- [ ] Windows versie minimaal 10 build 19041 (WSL2 vereist) — check via winver
- [ ] Hyper-V feature beschikbaar (vereist voor WSL2) — Pro versie heeft dit

STAPPENPLAN:

FASE A: WSL2 installatie (Cursor: handmatig executen, niet automatiseerbaar)

1. PowerShell als Administrator:
   wsl --install -d Ubuntu-22.04
   (reboot indien gevraagd)

2. Setup Ubuntu user (matched aan Windows username waar mogelijk):
   Run "Ubuntu" vanuit Start, eerste boot maakt user aan.

3. Update Ubuntu:
   wsl -d Ubuntu-22.04
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y curl git build-essential

FASE B: Docker Desktop reconfiguratie

4. Open Docker Desktop → Settings → General
5. Vink aan: "Use the WSL 2 based engine"  
6. Settings → Resources → WSL Integration:
   - Enable integration with my default WSL distro
   - Enable integration with Ubuntu-22.04
7. Apply & Restart

8. Verify: in PowerShell
   docker info | findstr "Server Version"
   docker info | findstr "OSType"
   → moet "linux" tonen, niet "windows"

FASE C: Project migratie (CRITICAL — paths moeten correct)

9. Stop alle Nova-containers:
   docker compose -f L:\!Nova V2\... down

10. Maak Postgres backup (verifieer met pg_restore --list):
    docker exec postgres-ref pg_dump -U nova_ref nova_ref_db -Fc > 
      C:\nova\backups\pre_wsl2_migration.dump

11. Verplaats Nova-projectmap NAAR WSL2 filesystem (NIET op /mnt/l/...):
    
    In WSL2 (wsl -d Ubuntu-22.04):
    mkdir -p ~/projects
    cp -r /mnt/l/!Nova\ V2 ~/projects/nova
    cd ~/projects/nova
    
    BELANGRIJK: data MOET op ~/projects (Linux fs) staan, NIET op 
    /mnt/l/... (Windows fs via 9P bridge). Performance staat of valt 
    hiermee.

12. Update .env paths:
    Secrets blijven op Windows side voor cross-platform compatibility:
    Verander env_file in compose naar:
    env_file: /mnt/c/nova/secrets/nova-ref.env

13. Volumes naming check:
    Open docker-compose.yml — volumes mogen NIET naar /mnt/l/ of L:/ 
    paden wijzen. Gebruik named volumes:
    
    volumes:
      postgres_ref_data:
    
    services:
      postgres-ref:
        volumes:
          - postgres_ref_data:/var/lib/postgresql/data
    
    Named volumes draaien op WSL2 native fs en zijn fast.

FASE D: Restart en verify

14. Start vanuit WSL2:
    cd ~/projects/nova/infrastructure
    docker compose up -d

15. Restore Postgres data:
    docker exec -i postgres-ref pg_restore -U nova_ref -d nova_ref_db 
      --clean --create < /mnt/c/nova/backups/pre_wsl2_migration.dump

16. Verify services:
    curl http://localhost:8400/health
    curl http://localhost:8401/health
    curl http://localhost:3001/  (Uptime Kuma)

17. Performance check (de hele reden voor deze migratie):
    docker exec postgres-ref pgbench -i -s 10 nova_ref_db
    docker exec postgres-ref pgbench -c 4 -t 1000 nova_ref_db
    
    Resultaat noteren in migration_log.md. Verwacht: minimaal 3× hogere 
    transactions/sec dan voor migratie.

FASE E: Rollback path documenteren

18. Schrijf infrastructure/docs/WSL2_ROLLBACK.md met EXACTE stappen om
    terug te gaan naar native Windows Docker als iets fundamenteel breekt:
    - Stop containers in WSL2
    - Restore /mnt/l/!Nova V2 vanuit backup of git checkout
    - Docker Desktop Settings → uncheck WSL2
    - docker compose up -d vanuit Windows
    
    Test deze rollback NIET nu (kost extra uur), maar zorg dat het 
    document accuraat is.

TESTS NA MIGRATIE:

- pytest in nova-ref vanuit WSL2 — alle bestaande tests groen
- pytest in nova-learn — idem
- Smoke test: 50 lookup calls in een loop, geen errors
- Verify Telegram bridge werkt
- Verify Discord bridge werkt
- Verify Uptime Kuma alerts naar correcte channels

COMMIT MESSAGE:
"refactor(infra): migrate from native Windows Docker to WSL2 backend with named volumes"

NIET DOEN:
- Niet verschillende delen op verschillende fs (Postgres op WSL, services op
  /mnt/l/) — kies één: alles op WSL2
- Geen volumes via /mnt/c/ binnen Linux containers — performance killer
- Geen migratie tijdens het draaien van builds — eerst alles stoppen
- Geen WSL1 (alleen WSL2) — WSL1 heeft eigen perf issues met Docker
```

---

# 07 — Per-build rate limiting

```
PROBLEEM:
Een bug in sprite-pipeline kan in een loop /lookup blijven hameren. Binnen 
een minuut: Wikidata IP-ban, Postgres onder vuur, alle services traag.

OPLOSSING:
Rate limit per build_name in nova-ref. Niet als security-feature, als 
beveiliging tegen je eigen toekomstige bugs.

WIJZIGINGEN:

1. nova-ref/src/nova_ref/core/rate_limit.py (nieuwe module):
   
   Implementatie via slowapi (aanvulling op FastAPI):
   - Limit per (build_name, endpoint)
   - Default limits per endpoint:
     - /lookup:    60/minute per build
     - /search:    30/minute per build
     - /ingest:    10/minute per build
     - /feedback:  120/minute per build (kan veel zijn bij batch processing)
   
   Storage backend: Redis (al draaiend voor events).
   
   Override per build via cache.adapter_status-achtige tabel zodat je 
   handmatig limits kunt verhogen voor specifieke builds zonder code-deploy.

2. Nieuw schema:
   CREATE TABLE cache.rate_limits (
       build_name      TEXT NOT NULL,
       endpoint        TEXT NOT NULL,
       limit_per_min   INT NOT NULL,
       updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       PRIMARY KEY (build_name, endpoint)
   );

3. Middleware in nova-ref/src/nova_ref/api/middleware.py:
   
   Bij elke request, BEFORE handler:
   - Extract build_name uit request body of X-Build-Name header
   - Check Redis counter: ratelimit:{build}:{endpoint}:{minute_window}
   - Increment, vergelijk met limit (db lookup, gecached 5min)
   - Bij overschrijding: return 429 met:
     Headers: Retry-After: <seconds_until_window_resets>
     Body: {"error": "rate_limit_exceeded", "limit": 60, "window": "1min"}

4. Logging bij rate limit hits:
   Structlog warning met build_name, endpoint, current_rate
   Increment Prometheus counter: nova_ref_rate_limit_hits_total{build, endpoint}

5. Self-protection (anti-amplification):
   Als zelfde build 5x rate_limit_exceeded raakt binnen 5 minuten:
   - Log structlog ERROR (niet warning) met "build runaway suspected"
   - Stuur Telegram alert met severity warning (NIET critical, kan loop zijn)
   - Verhoog effective limit niet automatisch — manual intervention required

6. API endpoint voor live overrides:
   PUT /admin/rate_limits/{build_name}/{endpoint}
   Body: {"limit_per_min": 120, "reason": "batch import voor Surilians"}
   Vereist localhost-only middleware (bestaande, uit Fase6).

TESTS:

- test_rate_limit_allows_under_threshold: 50 calls in 60s → all 200
- test_rate_limit_blocks_at_threshold: 61 calls → 61e is 429
- test_429_includes_retry_after: header bevat correcte seconds
- test_rate_limit_resets_after_window: 60 calls → wait 65s → call 61 OK
- test_per_build_isolation: build_a hits limit, build_b nog OK
- test_admin_override_increases_limit: PUT, daarna hogere limit actief 
  binnen 5 minuten
- test_runaway_detection_alerts: simuleer 5x limit-hits in 5min, verifieer 
  Telegram alert

OBSERVABILITY:
nova_ref_rate_limit_hits_total{build, endpoint}     # counter
nova_ref_rate_limit_active_keys                     # gauge
nova_ref_rate_limit_overrides_total                 # counter

VALIDATIE:
- Schrijf scriptje dat 100 lookups in 30s probeert
- Verifieer eerste 60 OK, daarna 429
- Bekijk Redis: keys ratelimit:* (allemaal TTL ~60s)
- Bekijk Postgres bij overrides: rate_limits row verschijnt

COMMIT MESSAGE:
"feat(rate-limit): per-build rate limiting with admin overrides and runaway detection"

NIET DOEN:
- Geen IP-based limiting (alle calls komen van localhost)
- Geen distributed counter buiten Redis (overkill)
- Geen automatic limit lowering bij vermoeden van bug — manual check first
```

---

# 08 — Telegram snooze-commando

```
PROBLEEM:
Soms wil ik gewoon rust hebben — gaming, slapen, klusje doen — zonder pc 
uit te zetten. Lifecycle hooks zijn voor pc-shutdown, maar wat als pc aan 
blijft maar ik wil 4 uur stilte?

OPLOSSING:
Telegram bot commando dat de quiet_mode (uit prompt 01) handmatig 
activeert voor X uur.

WIJZIGINGEN:

1. nova-bridge — voeg commando handlers toe:
   
   /nova snooze <duration>
   Voorbeelden:
   - /nova snooze 4h     → 4 uur stilte
   - /nova snooze 30m    → 30 min stilte
   - /nova snooze night  → tot 08:00 lokale tijd (max 12h cap)
   
   Implementatie:
   - Parse duration: "4h", "30m", "1h30m", "night"
   - "night" = bereken seconds tot volgende 08:00 Europe/Amsterdam, max 12h
   - Auth check: alleen mijn Telegram chat_id (hardcode, geen rolesystem)
   - POST naar /lifecycle endpoint met event=snooze, duration_minutes=X
   - Reply naar mij: "🌙 Snooze actief tot {format_for_user(end_time)}"

2. /nova wake commando — opheffen van snooze
   - DELETE Redis key nova:quiet_mode
   - Reply: "👁️ Monitoring weer actief"

3. /nova status commando — check huidige staat
   Reply format:
   ```
   Nova-status:
   - Monitoring: actief / snoozed (nog 2h 14m)
   - Services up: nova-ref, nova-learn, bridge
   - Services down: (geen)
   - Disk usage L:: 67%
   - Last backup: 03:30 vandaag (succes)
   ```

4. Auth via chat_id whitelist:
   Env var: NOVA_TELEGRAM_ADMIN_CHATIDS=123456789,987654321
   Alleen deze IDs mogen /nova-commando's gebruiken.
   Andere chat: stille decline (geen response, log warning).

5. Bot help message update:
   /start of /help reply moet snooze-commando vermelden. Geen lange 
   handleiding — twee regels en klaar.

TESTS:

- test_snooze_sets_quiet_mode_correct_duration
- test_snooze_night_calculates_correctly_in_winter (zomertijd-edge case)
- test_snooze_unauthorized_chatid_silently_declines
- test_wake_clears_quiet_mode
- test_status_command_returns_correct_state
- test_invalid_duration_format_returns_helpful_error: "/nova snooze banaan" 
  → "Usage: /nova snooze 4h | 30m | night"

VALIDATIE:
- Vanaf jouw Telegram: /nova status → ziet huidige staat
- /nova snooze 5m → krijgt confirm message
- Trigger fake alert binnen 5 min: ziet niet binnenkomen, ZIET wel in 
  suppressed_alerts table
- /nova wake → zou nu wel binnenkomen
- /nova snooze 5m via tweede (niet-whitelisted) telegram account: geen 
  response, log warning visible

COMMIT MESSAGE:
"feat(bridge): /nova snooze, wake, status commands with chat_id auth"

NIET DOEN:
- Geen complex permission system — chat_id whitelist is genoeg
- Geen scheduled snoozes ("snooze elke avond 23:00") — Windows lifecycle 
  hooks doen dat al via shutdown event
- Geen snooze van langer dan 12h via één commando — manual reactivation 
  forceren als safety
```

---

# 09 — Wekelijks self-check rapport

```
PROBLEEM:
Solo developer = niemand kijkt over je schouder mee. Nova kan langzaam 
"verrotten" zonder dat je het door hebt: een metric die wegvalt, een 
adapter die stilletjes faalt, een groei in latency die je gewend raakt 
aan totdat het echt erg is.

OPLOSSING:
Elke zondagavond 20:00 een markdown-rapport via Telegram. Geen alerts, 
geen actie nodig — passieve gezondheidscheck. Doel is dat je af en toe 
"hé, dat is gek" denkt en dan onderzoekt.

WIJZIGINGEN:

1. nova-bridge/src/weekly_report.py
   
   Markdown generator die een rapport opstelt met:
   
   ## Nova Weekrapport — {week_iso}
   Periode: {start_date} t/m {end_date}
   
   ### Volume
   - Lookups deze week: {count} ({delta_vs_prev}%)
   - Cache hit rate: {percent}% (target: >70%)
   - Top builds:
     1. {build}: {count} lookups, {success_rate}% success
     2. ...
   
   ### Adapters  
   | Adapter | Calls | Success | Avg latency |
   |---------|-------|---------|-------------|
   | wikidata | ... | ... | ... |
   
   ### Drie willekeurige entities (visuele check)
   - {entity_id}: {canonical_name} ({category}, fetched {age} ago)
   - ...
   
   ### Audit
   - Nieuwe entries via /ingest: {count}
   - Top actor: {actor}
   
   ### Disk & resources
   - Postgres data: {size_gb}GB ({delta}% growth)
   - Backups: {count} (oudste {age} dagen)
   - Disk L:: {percent}% used
   
   ### Open TODOs
   - {count} TODO/FIXME in codebase
   
   ### Aandachtspunten
   - {auto-flagged anomalies based on rules below}

2. Anomalie-detectie regels (simpel, geen ML):
   - Adapter avg_latency > 2x vorige week → flag
   - Cache hit rate gedaald >10pt week-over-week → flag
   - Build volume gedaald >50% week-over-week → flag
   - Postgres groei > 1GB in een week → flag (mogelijk runaway data)
   - Entity fetched_at > 60 dagen geleden voor non-fictional → flag

3. SQL queries als materialized views (efficient query op grote tabellen):
   
   CREATE MATERIALIZED VIEW IF NOT EXISTS reports.weekly_lookup_stats AS
   SELECT 
       date_trunc('week', created_at) AS week,
       category_hint,
       used_adapters[1] as primary_adapter,
       COUNT(*) as count,
       AVG(duration_ms) as avg_latency,
       AVG(CASE WHEN matched_entity IS NOT NULL THEN 1 ELSE 0 END) as hit_rate
   FROM cache.queries
   GROUP BY 1, 2, 3;
   
   REFRESH zondag 19:00 via scheduled job, voor het rapport om 20:00.

4. Schedule:
   Cron-equivalent (binnen Linux container — werkt ook op WSL2):
   30 19 * * 0    /usr/local/bin/refresh_views.sh   # vrijdag 19:30 view refresh
   0  20 * * 0    /usr/local/bin/send_weekly.sh     # zondag 20:00 verzenden
   
   Op Windows zonder WSL2: Task Scheduler entries.

5. Verzending:
   Niet één lange message — splits in chunks als markdown >4000 chars 
   (Telegram limit). Eerste chunk heeft "1/3" suffix etc.
   
   Discord-versie ook: zelfde markdown, naar dedicated #nova-reports kanaal.

6. Archief:
   Sla elke rapport op in /opt/nova/reports/{week_iso}.md voor history.
   Niet in DB — git repo "nova-reports" committen werkt mooier voor 
   historische analyse.

TESTS:

- test_report_generation_with_data: seed 100 fake build_runs, generate, 
  parse markdown, verifieer volume sectie correct  
- test_anomaly_detection_latency_spike: adapter latency 100ms vorig week, 
  300ms deze week → flagged
- test_telegram_chunking: rapport van 6000 chars → 2 messages
- test_empty_week_no_crash: geen data deze week → rapport zegt "weinig 
  activiteit"
- test_random_entity_sampling: zelfde week → andere entities elke run

VALIDATIE:
- Trigger handmatig: docker exec nova-bridge python -m send_weekly
- Zou Telegram message moeten leveren binnen 30s
- Bekijk: bevat alle secties? Klopt data met handmatige queries?
- Sla rapport op, vergelijk volgende week voor delta-berekening

COMMIT MESSAGE:
"feat(bridge): weekly self-check report via Telegram with anomaly flags"

NIET DOEN:
- Geen "actionable" wording in het rapport — passief, niet opdringerig
- Geen email — Telegram is genoeg
- Geen aanpasbare frequentie nu — wekelijks zondag is een Schelling point
- Geen email/SMS escalation als rapport niet verzonden wordt — gewoon log 
  error, volgende week opnieuw proberen
```

---

# 10 — Optimalisatie-patch voor Nova_Cursor_Prompts_Stap1.md

```
DOEL: 
Stap1 prompts geschreven voor Linux/Hetzner setup. Nu draaien we Windows 
desktop privé. Patch de prompts (in dat bestand of in de werkende code 
afhankelijk van wat al uitgevoerd is) zodat ze kloppen met huidige reality.

CURSOR ACTIE-PATTERN:
Voor elk punt hieronder:
1. Check via git log: is deze prompt al uitgevoerd? (zoek commit met 
   genoemde commit message)
2a. Ja, uitgevoerd → patch de werkende code
2b. Nee, nog niet → patch alleen de promptdefinitie in 
    Nova_Cursor_Prompts_Stap1.md zelf
3. Commit met "fix(stap1): patch X for Windows/local setup"

PATCHES:

PATCH 1: Wikidata adapter User-Agent
- Vervang in adapter en .env.example: alex@buro-hollema.nl
  Door: NOVA_CONTACT_EMAIL (expliciet invullen na bevestiging van Alex).
  Gebruik nooit automatisch een oude werk-email.

PATCH 2: PDOK BAG TIMEZONES
- Postgres timestamps in /ingest van BAG data: vorige prompt forceerde 
  geen UTC. Nu wel via prompt 04. Verifieer dat de PDOK adapter 
  fetched_at correct in UTC schrijft (`datetime.now(timezone.utc)` of `now_utc()`).

PATCH 3: Pilot integration sprite-pipeline 
- Bestaande prompt 5 in Stap1.md verwijst naar Hetzner pad. Vervang:
  Van: http://nova-ref:8400/lookup
  Naar: behoud (interne docker network) — geen actie nodig
  
- Maar: de feature flag SPRITE_PIPELINE_USE_REFERENCE_LAYER moet nu via 
  het feature flag systeem uit Fase6 prompt 5 lopen, niet via .env als
  primaire bron.
  Patch de pipeline volgorde:
  1) check centrale flag client,
  2) bij onbeschikbaar flag-systeem fallback naar env var,
  3) log expliciet welke bron beslissend was.

PATCH 4: Health checks
- Bestaande /health endpoint moet nu ook db_pool stats meeleveren 
  (uit prompt 03): active, idle, pool_max, utilization_percent.
  Cross-check dat health + readiness + metrics implementaties consistent
  dezelfde pool-waarden gebruiken.

PATCH 5: Test markers  
- Bestaande tests in Stap1 gebruikten @pytest.mark.integration voor echte 
  Wikidata calls. Voeg aan pyproject.toml toe:
  [tool.pytest.ini_options]
  markers = [
      "integration: tests die echte externe calls doen, exclude via -m 'not integration'"
  ]
  
  Anders waarschuwt pytest over unknown markers.
  Als er nog geen pyproject.toml bestaat in de target service, maak die eerst
  minimaal aan met alleen deze pytest-sectie.

NIET DOEN:
- Geen hele Stap1 prompts herschrijven — alleen de specifieke patches
- Geen scope-uitbreiding ("bij deze patch ook nog X verbeteren") — 
  alleen de hier genoemde wijzigingen
```

---

# 11 — Optimalisatie-patch voor Nova_Cursor_Prompts_Fase6_Hardening.md

```
DOEL:
Fase6 prompts geschreven voor Linux + Hetzner. Nu Windows + lokaal. Patch.

CURSOR ACTIE-PATTERN: idem als prompt 10.

PATCHES:

PATCH 1 — prompt 1 (Backup):
- Vervang bash scripts door PowerShell equivalenten:
  - nova_ref_backup.sh → nova_ref_backup.ps1
  - nova_ref_restore.sh → nova_ref_restore.ps1
  - nova_ref_offsite_sync.sh → nova_ref_offsite_sync.ps1 (optional, 
    placeholder met TODO)
  
- Vervang Hetzner Storage Box rsync door:
  Lokale rsync (of robocopy op Windows native): 
  Source: C:\nova\backups\
  Target: Toshiba HDD path, vermoedelijk D: of T: 
  (vraag mij eerst exact welke drive letter)

- Cron entry → Windows Task Scheduler:
  infrastructure/scripts/install_backup_tasks.ps1 die de scheduled task 
  registreert via schtasks command of New-ScheduledTask cmdlet.
  Daily 03:30 lokaal. Action: PowerShell -File C:\nova\scripts\nova_ref_backup.ps1

- RESTORE_RUNBOOK.md update naar Windows commands.

PATCH 2 — prompt 2 (DLQ):
- Geen wijzigingen nodig — DLQ logica is platform-agnostic Python code.
- Verifieer alleen dat Redis Stream commando's werken op je Redis versie.

PATCH 3 — prompt 3 (Schema versioning + idempotency):
- Geen platform-specifieke wijzigingen.
- Kleine toevoeging: idempotency_key TTL configuratie via env, default 
  60s, maximum 600s (om misbruik te voorkomen).

PATCH 4 — prompt 4 (Audit log):
- REVOKE UPDATE/DELETE syntax: dezelfde, Postgres syntax is niet 
  platform-afhankelijk.
- Update X-Actor header voorbeeld values: gebruik realistische Nova-context
  ("agent:sprite_pipeline", "human:alex_telegram", etc.)

PATCH 5 — prompt 5 (Feature flags + Telegram):
- Verwijder Bearer token auth voor /flags admin endpoints.
- Vervang door localhost-only middleware (zelfde patroon als bestaande 
  /admin paths uit deze prompt-set).
- Telegram /flag commando's: alleen jouw chat_id whitelist (zie prompt 08)

PATCH 6 — prompt 6 (Observability):
- Uptime Kuma monitors: gebruik PUSH monitors waar mogelijk (niet poll), 
  combineer met lifecycle hooks uit prompt 01.
- Grafana dashboard JSON: geen wijzigingen nodig, panel queries zijn 
  Prometheus-standaard.
- Loki/Elasticsearch sectie in NIET-DOEN blijft staan.

NIEUWE TOEVOEGINGEN AAN FASE6:

PATCH 7 — Operational README:
Maak C:\nova\OPERATIONAL_README.md met:
- Locatie van alle credentials  
- Hoe services starten/stoppen
- Hoe een restore te draaien
- Welke monitors te checken bij vermoeden van probleem
- Contact (jij)
- Disaster recovery scenario's

Dit document leest jij over 6 maanden als je vergeten bent hoe iets werkt, 
of een vriend/familielid leest het in een noodgeval. Schrijf het zo 
duidelijk dat een technisch onderlegd persoon zonder Nova-kennis jouw 
spullen kan beheren.

NIET DOEN:
- Geen volledige rewrite — alleen de patches hierboven
- Geen Linux-specifieke commando's vervangen waar Windows-equivalent 
  niet schoon is — gebruik Python cross-platform script als alternatief
```

---

## Slot

11 onderdelen, 11 commits, 11 groene CI-runs. In deze volgorde:

1. **Acuut**: shutdown alerts (irritatie weg)
2. **Foundations**: disk monitoring, connection pools, UTC, secrets
3. **Big move**: WSL2 migratie (~uur, plan in)
4. **Polish**: rate limiting, snooze, weekrapport
5. **Maintenance**: patches op bestaande Stap1 + Fase6 prompts

**Plak dit hele document in Cursor** óf laat hem het splitsen in losse bestanden in `L:\!Nova V2\!2 Cursor ToDo\27-04-2026 1251\` — beide werken.

Tussen elke prompt: smoke test, commit, akkoord vragen vóór je doorgaat (tenzij ik expliciet "alles achter elkaar" zeg).

Bij twijfel: stop, vraag.
