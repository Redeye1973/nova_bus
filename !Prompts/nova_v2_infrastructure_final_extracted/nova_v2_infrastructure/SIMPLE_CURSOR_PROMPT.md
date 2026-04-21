# NOVA v2 Simple Auto-Deploy Prompt

Versimpelde workflow omdat Cursor zelf zips uitpakt als je ze in de chat sleept.

## Gebruik

1. Open Cursor in L:\!Nova V2\ (maak aan als niet bestaat)
2. Sleep deze drie zips in de Cursor chat balk:
   - nova_v2_infrastructure.zip
   - nova_v2_agents.zip
   - nova_v2_extensions.zip
3. Plak onderstaande prompt
4. Enter

Cursor pakt zelf uit en deployt.

## De prompt

```
Ik heb 3 zip files gedeeld:
- nova_v2_infrastructure.zip (Docker setup voor Hetzner)
- nova_v2_agents.zip (19 basis agents met documentatie)
- nova_v2_extensions.zip (16 extensie agents)

Ik wil dat je NOVA v2 volledig autonoom uitrolt. Werk door onderstaande fases 
in volgorde. Stop alleen bij echte blockers (max 2 retry pogingen per probleem).

TARGETS:
- Hetzner server: 178.104.207.194
- Lokale werkmap: huidige Cursor working directory (L:\!Nova V2\)
- V1 op Hetzner poort 5678 MAG NIET worden geraakt
- V2 komt op poorten 5679 (main) + 5680 (webhook)

== FASE 1: UITPAKKEN EN STRUCTUREREN ==

1.1 Pak de drie zips uit in werkmap:
    - nova_v2_infrastructure.zip → ./infrastructure/
    - nova_v2_agents.zip → ./agents/
    - nova_v2_extensions.zip → ./extensions/

1.2 Valideer dat key files bestaan:
    - ./infrastructure/nova_v2_infrastructure/docker/docker-compose.yml
    - ./agents/nova_v2_agents/README.md
    - ./extensions/nova_v2_extensions/README.md

Als één ontbreekt: stop en rapporteer.

1.3 Maak werkmap structuur:
    - ./logs/
    - ./secrets/ (chmod 700 - alleen user access)

== FASE 2: SSH EN HETZNER VOORBEREIDING ==

2.1 Test SSH naar 178.104.207.194:
    ssh <user>@178.104.207.194 "echo OK && hostname"
    
    Als SSH user niet bekend: vraag me "Welke SSH user moet ik gebruiken voor 
    Hetzner?" en wacht op antwoord.

2.2 Check Hetzner vereisten via SSH:
    - docker --version (verwacht 24+)
    - docker compose version (verwacht 2+)
    - df -h / (minstens 10GB vrij)
    - free -h (minstens 2GB vrij)
    
    Als Docker ontbreekt: vraag toestemming om installeren.

2.3 Verifieer v1 werkt:
    curl -I http://localhost:5678 (via SSH)
    
    Als v1 down: waarschuw me, vraag of doorgaan OK is.

2.4 Check v2 poorten vrij:
    sudo lsof -i :5679, :5680, :9000, :9001, :6333, :6334
    
    Als bezet: stop en rapporteer conflict.

== FASE 3: SECRETS GENEREREN ==

3.1 Genereer 6 strong passwords:
    - POSTGRES_PASSWORD: openssl rand -base64 32
    - POSTGRES_NON_ROOT_PASSWORD: openssl rand -base64 32
    - REDIS_PASSWORD: openssl rand -base64 32
    - N8N_ENCRYPTION_KEY: openssl rand -hex 32
    - N8N_JWT_SECRET: openssl rand -hex 32
    - MINIO_ROOT_PASSWORD: openssl rand -base64 32

3.2 Vraag me: "Waar wil je NOVA v2 secrets opslaan? 
    Suggestie: ./secrets/nova_v2_passwords.txt
    (Gebruiker heeft keys verplaatst van standaard locatie)"
    
    Wacht op antwoord.

3.3 Schrijf secrets file op gekozen locatie met header:
    # NOVA v2 Secrets - [timestamp]
    # NIET committen, NIET delen
    
    [alle passwords]
    
    # URLs
    N8N_MAIN_URL=http://178.104.207.194:5679
    N8N_WEBHOOK_URL=http://178.104.207.194:5680
    MINIO_CONSOLE=http://178.104.207.194:9001
    QDRANT_URL=http://178.104.207.194:6333
    
    Set permissies: chmod 600

== FASE 4: UPLOAD NAAR HETZNER ==

4.1 Maak directory op Hetzner:
    ssh user@178.104.207.194 "mkdir -p /docker/nova-v2/scripts /docker/nova-v2/config/n8n-custom /docker/nova-v2/logs"
    ssh user@178.104.207.194 "sudo chown -R \$USER:\$USER /docker/nova-v2"

4.2 Upload bestanden via scp:
    scp ./infrastructure/nova_v2_infrastructure/docker/docker-compose.yml user@hetzner:/docker/nova-v2/
    scp ./infrastructure/nova_v2_infrastructure/docker/.env.template user@hetzner:/docker/nova-v2/
    scp ./infrastructure/nova_v2_infrastructure/scripts/*.sh user@hetzner:/docker/nova-v2/scripts/

4.3 Maak scripts executable:
    ssh user@hetzner "chmod +x /docker/nova-v2/scripts/*.sh"

4.4 Bouw .env met gegenereerde passwords:
    Lokaal maak .env op basis van .env.template met substituties.
    Upload naar Hetzner: scp .env user@hetzner:/docker/nova-v2/
    Set permissies: ssh user@hetzner "chmod 600 /docker/nova-v2/.env"

== FASE 5: DEPLOY ==

5.1 Pull images:
    ssh user@hetzner "cd /docker/nova-v2 && docker compose pull"

5.2 Start services:
    ssh user@hetzner "cd /docker/nova-v2 && docker compose up -d"

5.3 Wacht 30 seconden.

5.4 Check status:
    ssh user@hetzner "cd /docker/nova-v2 && docker compose ps"
    
    Verwacht 7 containers running/healthy:
    - nova-v2-postgres
    - nova-v2-redis
    - nova-v2-n8n-main
    - nova-v2-n8n-worker-1
    - nova-v2-n8n-webhook
    - nova-v2-minio
    - nova-v2-qdrant

Als één niet running:
    docker compose logs <service>
    Diagnose, fix (max 2 pogingen), of stop en rapporteer.

== FASE 6: VALIDATIE ==

6.1 Health checks lokaal op Hetzner (via SSH):
    curl -I http://localhost:5679 → 200 of 401
    curl -I http://localhost:5680 → 200 of 404
    curl http://localhost:9000/minio/health/live → live
    curl http://localhost:6333/ → qdrant info

6.2 Externe bereikbaarheid vanaf lokaal:
    curl -I http://178.104.207.194:5679 → 200 of 401

6.3 Firewall (indien extern niet bereikbaar):
    ssh user@hetzner "sudo ufw allow 5679/tcp && sudo ufw allow 5680/tcp && sudo ufw allow 9001/tcp"
    
    NIET openen publiek: 9000, 6333, 6334

6.4 Verifieer v1 nog werkt:
    ssh user@hetzner "curl -I http://localhost:5678"
    
    Als v1 kapot: CRITICAL, rapporteer direct.

== FASE 7: RAPPORTAGE ==

7.1 Schrijf rapport naar ./logs/deploy_YYYY-MM-DD_HH-MM.md:

```
# NOVA v2 Deployment Rapport

**Datum**: [timestamp]
**Duur**: [start - end]
**Status**: [Success / Partial / Failed]

## Services

Alle containers status + URLs

## V1 Status  
[onaangetast]

## Secrets
Locatie: [waar gebruiker aangaf]

## Volgende Stappen
1. Open http://178.104.207.194:5679
2. Maak N8n admin account aan (eerste login vraagt dit)
3. Settings → API → Generate API Key
4. Sla API key toe aan secrets file
5. Volgende prompt: import workflows uit ./agents/nova_v2_agents/templates/

## Waarschuwingen
[eventueel]
```

7.2 Toon korte summary in chat:
    - Success/Failed
    - Main URLs
    - Secrets locatie
    - 3 concrete next steps

== REGELS ==

- Max 2 retry pogingen per probleem, dan escaleer naar mij
- Log elke belangrijke actie naar ./logs/deploy_log.txt
- Formaat: [timestamp] | FASE.STAP | actie | result
- Bij kritieke fout: STOP, rapporteer, wacht op instructies
- V1 op 5678 mag nooit geraakt worden
- Secrets nooit in logs of chat display (alleen in secrets file)

Ga nu autonoom aan de slag. Werk door fases 1-7. 
Rapporteer bij elke fase voltooid. Stop bij blockers.
```

## Na deploy: Eerste workflows importeren

Tweede prompt (als deploy klaar is):

```
NOVA v2 draait. Nu wil ik de basis workflows importeren.

Vereisten:
- N8n API key moet in secrets file staan als N8N_V2_API_KEY
- Workflows staan in ./agents/nova_v2_agents/templates/

Taken:
1. Lees API key uit [secrets file locatie]
2. Import via N8n API naar http://178.104.207.194:5679/api/v1/workflows:
   - jury_judge_subworkflow.json (als reusable subworkflow)
   - bake_workflow.json
   - monitor_workflow.json
3. Zet workflows op "active" als ze valid zijn
4. Test webhook van jury-judge met dummy call
5. Rapporteer workflow IDs en status

Gebruik curl met header X-N8N-API-KEY.
```

## Eventuele problemen

**Cursor pakt zip niet uit bij drag-drop:**
Manueel uitpakken: rechtsklik → Alles uitpakken → in Cursor werkmap

**SSH werkt niet:**
Test eerst handmatig in terminal:
```
ssh user@178.104.207.194
```
Als dat faalt: SSH key setup controleren.

**Permissions denied bij scp/ssh:**
Mogelijk gebruiker heeft geen toegang tot /docker/. Run dan eerst:
```
ssh user@hetzner "sudo mkdir -p /docker && sudo chown \$USER:\$USER /docker"
```

## Tijd budget

Simpelere workflow, zelfde tijd:
- Uitpakken: enkele seconden
- SSH check: 30 sec
- Secrets + upload: 2-3 min
- Docker pull + start: 5-10 min
- Validatie: 1-2 min
- Rapport: 30 sec

**Totaal: 10-15 min.**
