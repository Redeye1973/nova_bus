# NOVA v2 Master Auto-Deploy Prompt voor Cursor

Deze prompt laat Cursor alles in de juiste volgorde doen: van uitpakken tot volledig werkende NOVA v2 infrastructure.

## Hoe gebruiken

1. Plaats de zip bestanden in één werkmap:
   - `nova_v2_infrastructure.zip`
   - `nova_v2_agents.zip` (van eerdere sessie)
   - `nova_v2_extensions.zip`
2. Open Cursor in die werkmap
3. Open Composer (Ctrl+I)
4. Kopieer onderstaande prompt
5. Plak + Enter
6. Cursor werkt autonoom

Geschatte tijd: 15-30 minuten (afhankelijk van Hetzner snelheid).

## De prompt

```
Ik ga NOVA v2 volledig uitrollen. Werk volledig autonoom in onderstaande volgorde.
Stop alleen bij echte blockers die niet auto-fixable zijn (max 2 pogingen per probleem).

== BELANGRIJKE UITGANGSPUNTEN ==

- Target server: 178.104.207.194 (Hetzner)
- Lokale werkmap: L:\!Nova V2\ (maak aan als niet bestaat)
- Oude NOVA v1 op Hetzner poort 5678 MAG NIET worden geraakt
- Nieuwe NOVA v2 op poorten 5679 (main), 5680 (webhook)
- SSH key moet werken (test eerst)
- Keys/secrets locatie: vraag gebruiker als onduidelijk - niet gebruikelijke locatie meer gebruikt
- Werk stap-voor-stap, log voortgang naar deploy_log.txt

== FASE 1: VOORBEREIDING LOKAAL ==

STAP 1.1: Check werkmap
- Maak L:\!Nova V2\ aan als niet bestaat
- Maak subfolders: unzipped/, logs/, secrets/

STAP 1.2: Controleer aanwezigheid zip bestanden in huidige Cursor werkmap
Vereist aanwezig:
- nova_v2_infrastructure.zip
- nova_v2_agents.zip  
- nova_v2_extensions.zip

Als één ontbreekt: rapporteer en stop.

STAP 1.3: Uitpakken naar L:\!Nova V2\unzipped\
- Gebruik PowerShell Expand-Archive of 7zip
- nova_v2_infrastructure.zip → L:\!Nova V2\unzipped\infrastructure\
- nova_v2_agents.zip → L:\!Nova V2\unzipped\agents\
- nova_v2_extensions.zip → L:\!Nova V2\unzipped\extensions\

STAP 1.4: Valideer inhoud uitgepakt
- L:\!Nova V2\unzipped\infrastructure\nova_v2_infrastructure\docker\docker-compose.yml moet bestaan
- L:\!Nova V2\unzipped\agents\nova_v2_agents\README.md moet bestaan
- L:\!Nova V2\unzipped\extensions\nova_v2_extensions\README.md moet bestaan

Als niet: stop en rapporteer.

== FASE 2: SSH EN HETZNER CHECK ==

STAP 2.1: Test SSH connectie
- Run: ssh user@178.104.207.194 "echo OK"
- Als user onbekend is: vraag welke SSH user je moet gebruiken
- Als SSH key niet werkt: vraag gebruiker setup te controleren
- Als succesvol: noteer SSH user voor later gebruik

STAP 2.2: Check Hetzner vereisten via SSH
Run via SSH:
- docker --version (Docker aanwezig?)
- docker compose version (Compose v2 aanwezig?)
- df -h / (genoeg disk space? minstens 10GB vrij)
- free -h (genoeg RAM? minstens 2GB vrij)

Als Docker ontbreekt: stop en vraag toestemming om te installeren.

STAP 2.3: Check of NOVA v1 draait op 5678
Run via SSH: curl -I http://localhost:5678

Als v1 niet reageert: WAARSCHUWING - gebruiker weet dit mogelijk niet. 
Vraag of het verwacht is voor doorgaan.

STAP 2.4: Check poorten vrij op Hetzner
Run via SSH voor elke poort:
- sudo lsof -i :5679
- sudo lsof -i :5680  
- sudo lsof -i :9000
- sudo lsof -i :9001
- sudo lsof -i :6333
- sudo lsof -i :6334

Als één bezet: stop en vraag gebruiker om conflict op te lossen.

== FASE 3: GENEREER SECRETS ==

STAP 3.1: Genereer strong passwords
Run lokaal (PowerShell of WSL):
- POSTGRES_PASSWORD = openssl rand -base64 32
- POSTGRES_NON_ROOT_PASSWORD = openssl rand -base64 32
- REDIS_PASSWORD = openssl rand -base64 32
- N8N_ENCRYPTION_KEY = openssl rand -hex 32
- N8N_JWT_SECRET = openssl rand -hex 32
- MINIO_ROOT_PASSWORD = openssl rand -base64 32

Als openssl niet beschikbaar: gebruik PowerShell alternatief:
[Convert]::ToBase64String((1..24 | %{Get-Random -Maximum 256}))

STAP 3.2: Vraag locatie voor secrets opslaan
- Gebruiker heeft keys verplaatst, niet meer in C:\NOVA\Key Backup
- Vraag: "Waar moeten de NOVA v2 secrets worden opgeslagen?"
- Wacht op antwoord
- Standaard suggestie als geen antwoord: L:\!Nova V2\secrets\nova_v2_passwords.txt

STAP 3.3: Schrijf secrets bestand
Op gekozen locatie, write met permissies 600 (user-only):
```
# NOVA v2 Secrets - Gegenereerd: [timestamp]
# NIET committen naar git, NIET delen

POSTGRES_PASSWORD=<generated>
POSTGRES_NON_ROOT_PASSWORD=<generated>
REDIS_PASSWORD=<generated>
N8N_ENCRYPTION_KEY=<generated>
N8N_JWT_SECRET=<generated>
MINIO_ROOT_PASSWORD=<generated>

# Toegang URLs na deploy
N8N_MAIN_URL=http://178.104.207.194:5679
N8N_WEBHOOK_URL=http://178.104.207.194:5680
MINIO_CONSOLE=http://178.104.207.194:9001
QDRANT_URL=http://178.104.207.194:6333
```

== FASE 4: UPLOAD NAAR HETZNER ==

STAP 4.1: Maak directory structuur op Hetzner
Via SSH:
- mkdir -p /docker/nova-v2/scripts
- mkdir -p /docker/nova-v2/config/n8n-custom
- mkdir -p /docker/nova-v2/logs
- sudo chown -R $(whoami):$(whoami) /docker/nova-v2/

STAP 4.2: Upload bestanden via scp of rsync
Van L:\!Nova V2\unzipped\infrastructure\nova_v2_infrastructure\:
- docker/docker-compose.yml → user@hetzner:/docker/nova-v2/
- docker/.env.template → user@hetzner:/docker/nova-v2/
- scripts/init-postgres.sh → user@hetzner:/docker/nova-v2/scripts/
- scripts/deploy.sh → user@hetzner:/docker/nova-v2/scripts/

STAP 4.3: Maak scripts executable
Via SSH: 
- chmod +x /docker/nova-v2/scripts/*.sh

STAP 4.4: Maak .env file op Hetzner
Gebruik secrets uit Fase 3.3:
- Upload .env naar /docker/nova-v2/.env
- Vul in: alle POSTGRES_*, REDIS_*, N8N_*, MINIO_* waardes
- Ook: N8N_HOST=178.104.207.194, N8N_PORT=5679, etc
- Chmod 600 op .env

== FASE 5: DEPLOY ==

STAP 5.1: Pull Docker images
Via SSH:
- cd /docker/nova-v2
- docker compose pull

Als pull faalt: check internet, retry 1x.

STAP 5.2: Start services
Via SSH:
- docker compose up -d

STAP 5.3: Wacht op startup
Via SSH: sleep 30 (services hebben tijd nodig)

STAP 5.4: Check container status
Via SSH: docker compose ps

Verwacht: alle 7 containers "healthy" of "running":
- nova-v2-postgres
- nova-v2-redis
- nova-v2-n8n-main
- nova-v2-n8n-worker-1
- nova-v2-n8n-webhook
- nova-v2-minio
- nova-v2-qdrant

Als één niet draait: 
- docker compose logs <service_name>
- Diagnoseer issue
- Max 2 fix pogingen
- Bij falen: rapporteer en stop

== FASE 6: HEALTH VALIDATIE ==

STAP 6.1: Lokale health checks op Hetzner
Via SSH:
- curl -I http://localhost:5679 → verwacht 200 of 401
- curl -I http://localhost:5680 → verwacht 200 of 404
- curl http://localhost:9000/minio/health/live → verwacht live
- curl http://localhost:6333/ → verwacht qdrant info

STAP 6.2: Externe bereikbaarheid
Vanaf lokale machine:
- curl -I http://178.104.207.194:5679 → moet werken

Als extern niet: check Hetzner firewall.

STAP 6.3: Firewall configureren indien nodig
Via SSH:
- sudo ufw status
- sudo ufw allow 5679/tcp
- sudo ufw allow 5680/tcp
- sudo ufw allow 9001/tcp
- NIET openen: 9000, 6333, 6334 (alleen intern)

STAP 6.4: Verifieer v1 onaangetast
Via SSH: curl -I http://localhost:5678

Als v1 kapot: CRITICAL - rapporteer direct, rollback v2 als nodig.

== FASE 7: INTEGRATIE MET LOKALE PC ==

STAP 7.1: Update nova_config.yaml (indien bestaand)
Als L:\!Nova V2\nova_config.yaml bestaat:
- Voeg infrastructure sectie toe met URLs
- Voeg n8n_v2_api_key placeholder toe

Als niet bestaat:
- Maak basic nova_config.yaml aan
- Voeg infrastructure sectie toe

STAP 7.2: Test webhook vanaf lokaal
Run lokaal:
curl -X POST http://178.104.207.194:5680/webhook-test/placeholder

Response is 404 ok (geen workflow met die path), maar betekent webhook-listener werkt.

STAP 7.3: Check of MCP server connectie kan werken
Via SSH naar Hetzner: controleer dat 178.104.207.194:5679 bereikbaar is van buitenaf.

== FASE 8: RAPPORTAGE ==

STAP 8.1: Schrijf deploy rapport
Naar L:\!Nova V2\logs\deploy_YYYY-MM-DD_HH-MM.md:

```
# NOVA v2 Deployment Rapport

**Datum**: [timestamp]
**Duur**: [start tot end]

## Status

**Services**: 
- [x] PostgreSQL running
- [x] Redis running  
- [x] N8n main (5679) - [URL]
- [x] N8n worker
- [x] N8n webhook (5680) - [URL]
- [x] MinIO (9001) - [URL]
- [x] Qdrant (6333) - [URL]

**V1 Status**: [onaangetast/issues]

## Toegang

- N8n UI: http://178.104.207.194:5679
- N8n Webhook: http://178.104.207.194:5680
- MinIO Console: http://178.104.207.194:9001
- Qdrant: http://178.104.207.194:6333

## Secrets locatie

[locatie waar gebruiker aangaf]

## Volgende Stappen

1. Open http://178.104.207.194:5679 in browser
2. Maak N8n admin account aan
3. Genereer API key: Settings → API
4. Sla API key op in secrets locatie
5. Importeer eerste workflow uit L:\!Nova V2\unzipped\agents\nova_v2_agents\templates\
6. Configure MinIO buckets: nova-assets, nova-cache
7. Configure Qdrant collection: surilians_bible

## Waarschuwingen

[lijst van eventuele waarschuwingen tijdens deploy]
```

STAP 8.2: Laat gebruiker weten
Print concise summary:
- Success/failure
- Access URLs
- Secrets locatie
- Rapport locatie
- 3 concrete volgende stappen

== FALLBACK PROCEDURES ==

BIJ CRITICAL FAILURE:
1. docker compose down (stop alles zonder data te verliezen)
2. Rapporteer in rapport wat mis ging
3. NIET proberen v1 te fixen (oud blijft apart)
4. Geef gebruiker handmatige stappen voor recovery

BIJ SSH FAILURE:
1. Test verschillende SSH users (root, admin, user)
2. Vraag naar SSH config
3. Stop als niet oplosbaar

BIJ NETWORK FAILURE TIJDENS UPLOAD:
1. Retry 2x met sleep ertussen
2. Als blijvend: rapporteer netwerk issue
3. Biedt optie: handmatige upload instructions

== LOGGING ==

Log elke stap naar L:\!Nova V2\logs\deploy_log.txt:
Format: [timestamp] | FASE.STAP | action | result

Voorbeeld:
[2026-04-19 11:00:15] | 1.1 | Directory L:\!Nova V2 created | SUCCESS
[2026-04-19 11:00:23] | 2.1 | SSH test | SUCCESS (user: admin)
[2026-04-19 11:03:45] | 5.2 | Docker compose up -d | SUCCESS
[2026-04-19 11:04:15] | 6.1 | Health check n8n-main:5679 | SUCCESS (200 OK)

Ga nu autonoom aan de slag. Werk door alle fases in volgorde. 
Stop alleen bij echte blockers. Rapporteer duidelijk wat klaar is en wat niet.
```

## Wat Cursor gaat doen

Als je deze prompt plakt, gaat Cursor:

1. Lokaal werkmap L:\!Nova V2\ klaarmaken
2. De drie zips uitpakken
3. SSH naar Hetzner testen
4. Docker check op Hetzner
5. Wachtwoorden genereren
6. Vraagt jou waar secrets op te slaan
7. Upload naar /docker/nova-v2/
8. .env invullen met gegenereerde passwords
9. Docker compose up -d
10. Health checks draaien
11. Firewall configureren
12. Test of v1 nog werkt
13. Rapport schrijven
14. Samenvatting tonen

## Wat je moet doen als gebruiker

**Voor je de prompt plakt:**
- Zorg dat SSH werkt naar 178.104.207.194
- Zorg dat de drie zip bestanden in je werkmap staan:
  - nova_v2_infrastructure.zip
  - nova_v2_agents.zip
  - nova_v2_extensions.zip
- Bedenk waar je de secrets wilt opslaan (Cursor vraagt het)

**Tijdens Cursor werkt:**
- Antwoord op SSH user vraag (bv. 'admin' of 'root')
- Antwoord op secrets locatie vraag
- Niks anders, laat Cursor werken

**Na Cursor klaar is:**
- Open http://178.104.207.194:5679 in browser
- Maak N8n admin account
- Genereer API key
- Sla API key op naast andere secrets

## Time budget

Realistisch:
- Fase 1-2 (lokaal + SSH): 1-2 min
- Fase 3-4 (secrets + upload): 2-3 min
- Fase 5 (docker pull + up): 5-10 min (afhankelijk van internet)
- Fase 6-7 (validatie + integratie): 2-3 min
- Fase 8 (rapportage): 1 min

**Totaal: 15-20 minuten gemiddeld.**

Als iets crasht: kan langer duren door retries.

## Success criteria

Deploy is succesvol als:
- [ ] Alle 7 containers draaien
- [ ] N8n UI bereikbaar op http://178.104.207.194:5679
- [ ] Webhooks werken op poort 5680
- [ ] V1 op poort 5678 nog steeds werkt
- [ ] Secrets opgeslagen op veilige plek
- [ ] Rapport geschreven in logs folder

## Na succesvolle deploy

Gebruik volgende Cursor prompt voor eerste workflow import:

```
Import de NOVA v2 basis workflows in N8n v2:
- L:\!Nova V2\unzipped\agents\nova_v2_agents\templates\jury_judge_subworkflow.json
- L:\!Nova V2\unzipped\agents\nova_v2_agents\templates\bake_workflow.json
- L:\!Nova V2\unzipped\agents\nova_v2_agents\templates\monitor_workflow.json

Gebruik N8n API op http://178.104.207.194:5679/api/v1/workflows.
API key zit in [secrets locatie] onder N8N_V2_API_KEY.
```

Maar dat is voor daarna, niet in deze deploy.
