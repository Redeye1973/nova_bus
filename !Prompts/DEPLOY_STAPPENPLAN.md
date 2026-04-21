# NOVA v2 Deploy Stappenplan voor Cursor

Aangepast voor de platte structuur onder `L:\!Nova V2\infrastructure\` (geen extra `docker/` submap).

## Hoe gebruiken

1. Open Cursor in `L:\!Nova V2\`
2. Open Composer (Ctrl+I)
3. Kopieer de prompt hieronder
4. Plak + Enter
5. Antwoord op 2 vragen (SSH user + secrets locatie)
6. Laat Cursor 10-15 min werken

## De prompt

```
Ik ga NOVA v2 deployen op Hetzner. Lokale structuur:

L:\!Nova V2\
├── infrastructure\
│   ├── docker-compose.yml
│   ├── .env.template
│   ├── scripts\
│   │   ├── deploy.sh
│   │   └── init-postgres.sh
│   ├── config\
│   │   └── n8n-custom\.gitkeep
│   ├── .gitignore
│   ├── README.md
│   ├── README_INFRA_PACKAGE.md
│   ├── CURSOR_DEPLOY_PROMPT.md
│   ├── MASTER_DEPLOY_PROMPT.md
│   └── SIMPLE_CURSOR_PROMPT.md
├── agents\ (optioneel, uit nova_v2_agents.zip)
├── extensions\ (optioneel, uit nova_v2_extensions.zip)
└── README.md

Werk volledig autonoom. Stop alleen bij echte blockers (max 2 retry pogingen).

TARGETS:
- Hetzner: 178.104.207.194
- V1 op poort 5678 MAG NIET worden geraakt
- V2 komt op 5679 (main) + 5680 (webhook)
- Werkmap: huidige Cursor working directory = L:\!Nova V2\

== FASE 1: LOKALE VALIDATIE ==

1.1 Check dat deze bestanden bestaan (stop als één ontbreekt):
    - ./infrastructure/docker-compose.yml
    - ./infrastructure/.env.template
    - ./infrastructure/scripts/deploy.sh
    - ./infrastructure/scripts/init-postgres.sh
    - ./infrastructure/config/n8n-custom/.gitkeep

1.2 Maak werk-subfolders:
    - ./logs/ (voor deploy logs)
    - ./secrets/ (voor passwords, chmod 700 indien mogelijk)

1.3 Valideer docker-compose.yml syntax:
    Lokaal (indien Docker aanwezig): `docker compose -f ./infrastructure/docker-compose.yml config`
    Anders: parse yaml met Python en check required keys (services, volumes, networks)

== FASE 2: SSH TEST + HETZNER CHECK ==

2.1 Test SSH connectie:
    Probeer: ssh <user>@178.104.207.194 "echo OK && hostname"
    
    Als SSH user onbekend is: vraag "Welke SSH user gebruik ik voor Hetzner?"
    Wacht op antwoord, gebruik die user voor alle volgende SSH calls.
    
    Noteer gekozen user in variabele voor hergebruik.

2.2 Check Hetzner vereisten via SSH:
    - docker --version (verwacht 24+, anders vraag of installeren)
    - docker compose version (verwacht v2+)
    - df -h / | head -2 (minstens 10GB vrij)
    - free -h (minstens 2GB vrij)

2.3 Verifieer v1 werkt (oude N8n):
    curl -sI http://localhost:5678 via SSH
    
    Als response 200/401: OK, v1 werkt.
    Als geen response: vraag gebruiker of dat verwacht is voordat je doorgaat.

2.4 Check v2 poorten vrij:
    Via SSH: sudo lsof -i :5679 :5680 :9000 :9001 :6333 :6334
    
    Als een poort bezet: stop, toon welk process, vraag hoe om te lossen.

== FASE 3: GENEREER SECRETS ==

3.1 Genereer 6 sterke passwords:
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    POSTGRES_NON_ROOT_PASSWORD=$(openssl rand -base64 32)
    REDIS_PASSWORD=$(openssl rand -base64 32)
    N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)
    N8N_JWT_SECRET=$(openssl rand -hex 32)
    MINIO_ROOT_PASSWORD=$(openssl rand -base64 32)
    
    Op Windows zonder openssl: gebruik PowerShell alternatief
    [Convert]::ToBase64String((1..32 | %{Get-Random -Maximum 256}))

3.2 Vraag gebruiker waar secrets op te slaan:
    "Waar wil je NOVA v2 secrets opslaan? 
    Suggestie: ./secrets/nova_v2_passwords.txt
    (Let op: gebruiker heeft keys verplaatst van standaard locatie)"
    
    Wacht op antwoord. Bij geen antwoord: default naar ./secrets/nova_v2_passwords.txt

3.3 Schrijf secrets bestand met permissies 600 op gekozen locatie:
    
    # NOVA v2 Secrets - Gegenereerd: [timestamp]
    # NIET committen, NIET delen
    
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=<generated>
    POSTGRES_DB=n8n_v2
    POSTGRES_NON_ROOT_USER=n8n_user
    POSTGRES_NON_ROOT_PASSWORD=<generated>
    
    REDIS_PASSWORD=<generated>
    
    N8N_HOST=178.104.207.194
    N8N_PORT=5679
    N8N_PROTOCOL=http
    WEBHOOK_URL=http://178.104.207.194:5680/
    N8N_ENCRYPTION_KEY=<generated>
    N8N_JWT_SECRET=<generated>
    
    MINIO_ROOT_USER=nova_admin
    MINIO_ROOT_PASSWORD=<generated>
    
    # URLs na deploy
    N8N_MAIN_URL=http://178.104.207.194:5679
    N8N_WEBHOOK_URL=http://178.104.207.194:5680
    MINIO_CONSOLE=http://178.104.207.194:9001
    QDRANT_URL=http://178.104.207.194:6333

== FASE 4: BOUW LOKALE .env ==

4.1 Kopieer ./infrastructure/.env.template naar ./infrastructure/.env

4.2 Vervang alle CHANGE_ME placeholders met de gegenereerde waardes uit secrets file.

4.3 Valideer .env heeft geen CHANGE_ME meer:
    grep CHANGE_ME ./infrastructure/.env moet leeg zijn.

4.4 Set permissies .env naar 600 indien mogelijk.

== FASE 5: UPLOAD NAAR HETZNER ==

5.1 Maak directory structuur op Hetzner:
    ssh user@178.104.207.194 "mkdir -p /docker/nova-v2/scripts /docker/nova-v2/config/n8n-custom /docker/nova-v2/logs"
    ssh user@178.104.207.194 "sudo chown -R \$USER:\$USER /docker/nova-v2/"

5.2 Upload platte structuur (LET OP: geen docker/ subfolder!):
    
    scp ./infrastructure/docker-compose.yml user@hetzner:/docker/nova-v2/
    scp ./infrastructure/.env user@hetzner:/docker/nova-v2/
    scp ./infrastructure/scripts/deploy.sh user@hetzner:/docker/nova-v2/scripts/
    scp ./infrastructure/scripts/init-postgres.sh user@hetzner:/docker/nova-v2/scripts/
    scp ./infrastructure/config/n8n-custom/.gitkeep user@hetzner:/docker/nova-v2/config/n8n-custom/
    
    Vervang "user@hetzner" met juiste user@178.104.207.194

5.3 Set permissies op Hetzner:
    ssh user@hetzner "chmod +x /docker/nova-v2/scripts/*.sh"
    ssh user@hetzner "chmod 600 /docker/nova-v2/.env"

5.4 Verifieer upload:
    ssh user@hetzner "ls -la /docker/nova-v2/ /docker/nova-v2/scripts/ /docker/nova-v2/config/n8n-custom/"
    
    Verwacht: docker-compose.yml, .env, scripts/ met 2 .sh, config/n8n-custom/ met .gitkeep

== FASE 6: DEPLOY ==

6.1 Pull Docker images:
    ssh user@hetzner "cd /docker/nova-v2 && docker compose pull"
    
    Als pull faalt (network): retry 1x, dan stop en rapporteer.

6.2 Start services:
    ssh user@hetzner "cd /docker/nova-v2 && docker compose up -d"

6.3 Wacht voor startup:
    sleep 30

6.4 Check container status:
    ssh user@hetzner "cd /docker/nova-v2 && docker compose ps"
    
    Verwacht 7 containers running/healthy:
    - nova-v2-postgres
    - nova-v2-redis
    - nova-v2-n8n-main
    - nova-v2-n8n-worker-1
    - nova-v2-n8n-webhook
    - nova-v2-minio
    - nova-v2-qdrant
    
    Voor elk container dat niet running is:
    - docker compose logs <container_name>
    - Diagnose probleem
    - Max 2 fix pogingen
    - Bij aanhoudende fout: rapporteer en stop

== FASE 7: HEALTH VALIDATIE ==

7.1 Interne health checks via SSH:
    ssh user@hetzner:
    - curl -sI http://localhost:5679 (verwacht 200 of 401)
    - curl -sI http://localhost:5680 (verwacht 200 of 404)
    - curl -s http://localhost:9000/minio/health/live (verwacht "live")
    - curl -s http://localhost:6333/ | grep qdrant (verwacht qdrant info)

7.2 Externe bereikbaarheid vanaf lokaal:
    curl -sI http://178.104.207.194:5679
    
    Als niet bereikbaar: check Hetzner firewall (stap 7.3)

7.3 Firewall openen (indien nodig):
    ssh user@hetzner:
    - sudo ufw status
    - sudo ufw allow 5679/tcp
    - sudo ufw allow 5680/tcp
    - sudo ufw allow 9001/tcp
    
    NIET publiek openen: 9000, 6333, 6334 (alleen intern Docker)

7.4 Verifieer v1 onaangetast:
    ssh user@hetzner "curl -sI http://localhost:5678"
    
    Als v1 kapot: CRITICAL, stop direct en rapporteer.

== FASE 8: RAPPORTAGE ==

8.1 Schrijf deploy rapport naar ./logs/deploy_YYYY-MM-DD_HH-MM.md:
    
    # NOVA v2 Deployment Rapport
    
    **Datum**: [ISO timestamp]
    **Duur**: [minuten]
    **Status**: Success / Partial / Failed
    
    ## Containers Status
    [docker compose ps output]
    
    ## Health Checks
    - N8n main (5679): [status]
    - N8n webhook (5680): [status]
    - MinIO (9001): [status]
    - Qdrant (6333): [status]
    - V1 (5678): onaangetast
    
    ## Access URLs
    - N8n UI: http://178.104.207.194:5679
    - N8n Webhook: http://178.104.207.194:5680
    - MinIO Console: http://178.104.207.194:9001
    - Qdrant: http://178.104.207.194:6333
    
    ## Secrets
    Opgeslagen in: [locatie van gebruiker]
    
    ## Next Steps Voor Gebruiker
    1. Open http://178.104.207.194:5679 in browser
    2. Maak N8n admin account aan (eerste login vraagt dit)
    3. Settings → API → Generate API Key
    4. Voeg API key toe aan secrets file
    5. Import workflows uit ./agents/nova_v2_agents/templates/
    
    ## Waarschuwingen
    [eventuele waarschuwingen tijdens deploy]

8.2 Toon korte summary in chat:
    - Status: Success / Failed
    - Main URL: http://178.104.207.194:5679
    - Secrets locatie
    - 3 concrete next steps
    - Rapport locatie

== REGELS ==

- Log elke fase naar ./logs/deploy_log.txt
- Formaat: [timestamp] | fase.stap | actie | result
- Max 2 retry pogingen per probleem
- V1 (poort 5678) mag NOOIT worden geraakt
- Secrets nooit in chat displayen, alleen in secrets file
- Bij SSH/Docker failure: stop, rapporteer, wacht op instructies
- Bestands-paden zijn plat (./infrastructure/docker-compose.yml), NIET ./infrastructure/docker/

Ga nu autonoom aan de slag. Werk door fases 1-8 in volgorde.
Rapporteer wanneer elke fase compleet is. Stop bij blockers.
```

## Wat je moet doen

**Voor plakken:**
- Zorg dat SSH werkt naar 178.104.207.194 (test eerst handmatig: `ssh user@178.104.207.194`)
- Bedenk waar secrets moeten (Cursor vraagt)

**Tijdens Cursor werkt:**
- Antwoord 2 vragen: SSH user + secrets locatie
- Laat rest gaan

**Na deploy:**
- Open http://178.104.207.194:5679
- Maak N8n admin account
- Genereer API key
- Sla toe aan secrets file

## Geschatte tijd

- Fase 1-2: 1-2 min (validatie + SSH check)
- Fase 3-4: 1 min (secrets genereren + .env bouwen)
- Fase 5: 2-3 min (upload naar Hetzner)
- Fase 6: 5-10 min (docker pull + up)
- Fase 7-8: 2-3 min (validatie + rapport)

**Totaal: 10-15 minuten**

## Fallback bij problemen

**Cursor kan niet SSHen:**
Test eerst lokaal: open terminal, run `ssh user@178.104.207.194`. Als dat faalt, eerst SSH config fixen voordat deploy.

**Docker compose fout:**
```bash
# Via SSH
cd /docker/nova-v2
docker compose logs n8n-v2-main
# Kijk naar specifieke error
```

**Container start niet (postgres):**
Meestal permissies probleem. Check:
```bash
ls -la /docker/nova-v2/scripts/init-postgres.sh
# Moet executable zijn (+x)
```

**V1 breekt onverwacht:**
```bash
cd /docker/nova-v2
docker compose down  # Stop v2
# V1 zou weer werken; als niet: docker ps voor andere containers check
```

## Bij succesvolle deploy: vervolg prompt

Na deploy klaar, eerste workflow importeren:

```
NOVA v2 draait. N8n op http://178.104.207.194:5679.
Importeer de basis workflows uit ./agents/nova_v2_agents/templates/:
- jury_judge_subworkflow.json
- bake_workflow.json  
- monitor_workflow.json

Lees N8n API key uit [secrets file locatie] (N8N_V2_API_KEY key).
Gebruik curl met X-N8N-API-KEY header naar /api/v1/workflows.
Rapporteer workflow IDs en activatie status.
```

Maar dit is voor nadat deploy succesvol is.
