# Fase 5-8 Prompt: NOVA v2 Deploy naar Hetzner

Voor Cursor uit te voeren nadat Fase 3-4 klaar is en SSH getest is met root@178.104.207.194.

## Voor gebruik

1. Verifieer dat Fase 3-4 klaar is:
   - `L:\!Nova V2\secrets\nova_v2_passwords.txt` bestaat
   - `L:\!Nova V2\infrastructure\.env` bestaat zonder CHANGE_ME
2. SSH getest: `ssh root@178.104.207.194` werkt
3. Plak prompt hieronder in Cursor Composer
4. Enter

## De prompt

Plak dit in Cursor Composer:

```
Voer NOVA v2 Fase 5-8 uit: upload naar Hetzner, deploy, validatie, rapport.

CONTEXT BEVESTIGINGEN:
- Fase 3-4 is klaar: infrastructure/.env is gevuld, secrets/ bevat passwords
- SSH user: root
- SSH target: root@178.104.207.194
- SSH authenticatie: password-based (root login werkt)
- V1 op poort 5678 MAG NIET geraakt worden
- V2 target poorten: 5679 (main), 5680 (webhook), 9000/9001 (MinIO), 6333 (Qdrant)
- Lokale structuur plat: ./infrastructure/docker-compose.yml (geen docker/ submap)
- Hetzner structuur plat: /docker/nova-v2/ met bestanden direct erin

BELANGRIJK:
- SSH is password-based, dus interactieve prompts kunnen komen
- Als scp/ssh om password vraagt: gebruik sshpass of vraag gebruiker
- Alternatief: setup SSH key nu met: ssh-copy-id root@178.104.207.194
  Dan is rest password-less. Aanbevolen voor meerdere operaties.

== PRE-CHECK ==

P.1 Verifieer Fase 3-4 output:
    - Test-Path "infrastructure\.env" moet True zijn
    - Test-Path "secrets\nova_v2_passwords.txt" moet True zijn
    - grep/Select-String "CHANGE_ME" in infrastructure/.env moet leeg zijn
    
    Als één faalt: stop, vraag gebruiker Fase 3-4 opnieuw uit te voeren.

P.2 Test SSH werkt:
    ssh -o BatchMode=no -o ConnectTimeout=10 root@178.104.207.194 "echo CONNECT_OK"
    
    Als timeout/fail: vraag gebruiker SSH handmatig te testen.

P.3 Optioneel: setup SSH key voor password-less operations:
    Vraag gebruiker: "Wil je SSH key setup doen voor password-less deploy? (ja/nee)"
    Als ja: run ssh-copy-id root@178.104.207.194
    Als nee: gebruiker typt password meerdere keren tijdens deploy

== FASE 5: UPLOAD NAAR HETZNER ==

5.1 Maak directory structuur op Hetzner:
    ssh root@178.104.207.194 "mkdir -p /docker/nova-v2/scripts /docker/nova-v2/config/n8n-custom /docker/nova-v2/logs"

5.2 Upload bestanden met scp (platte structuur):
    scp infrastructure/docker-compose.yml root@178.104.207.194:/docker/nova-v2/
    scp infrastructure/.env root@178.104.207.194:/docker/nova-v2/
    scp infrastructure/scripts/deploy.sh root@178.104.207.194:/docker/nova-v2/scripts/
    scp infrastructure/scripts/init-postgres.sh root@178.104.207.194:/docker/nova-v2/scripts/
    
    Config folder (voor n8n-custom):
    ssh root@178.104.207.194 "touch /docker/nova-v2/config/n8n-custom/.gitkeep"

5.3 Set permissies op Hetzner:
    ssh root@178.104.207.194 "chmod +x /docker/nova-v2/scripts/*.sh"
    ssh root@178.104.207.194 "chmod 600 /docker/nova-v2/.env"
    ssh root@178.104.207.194 "chmod 644 /docker/nova-v2/docker-compose.yml"

5.4 Verifieer upload:
    ssh root@178.104.207.194 "ls -la /docker/nova-v2/ && echo '---' && ls -la /docker/nova-v2/scripts/"
    
    Verwachte bestanden:
    - /docker/nova-v2/docker-compose.yml
    - /docker/nova-v2/.env (chmod 600)
    - /docker/nova-v2/scripts/deploy.sh (executable)
    - /docker/nova-v2/scripts/init-postgres.sh (executable)
    - /docker/nova-v2/config/n8n-custom/.gitkeep
    
    Als bestanden ontbreken: retry upload (max 2x), dan stop.

5.5 Valideer .env inhoud op Hetzner (zonder waardes tonen):
    ssh root@178.104.207.194 "grep -c '^[A-Z]' /docker/nova-v2/.env"
    
    Moet >= 13 zijn (aantal expected variables).

== FASE 6: DEPLOY ==

6.1 Voorcheck Hetzner vereisten:
    ssh root@178.104.207.194 "docker --version && docker compose version && df -h / | head -2 && free -h | head -2"
    
    Check:
    - Docker 24+ aanwezig
    - Docker compose v2+
    - Disk: >10GB vrij
    - RAM: >2GB vrij

6.2 Check v2 poorten nog steeds vrij:
    ssh root@178.104.207.194 "sudo lsof -i :5679 -i :5680 -i :9000 -i :9001 -i :6333 -i :6334 2>/dev/null || echo 'All free'"
    
    Als bezet: stop en rapporteer.

6.3 Verifieer v1 nog draait:
    ssh root@178.104.207.194 "curl -sI http://localhost:5678 | head -1"
    
    Moet 200 of 401 response geven.

6.4 Pull Docker images:
    ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose pull"
    
    Tijd: 2-5 min voor eerste pull.
    Bij network error: retry 1x met sleep 30.

6.5 Start services:
    ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose up -d"

6.6 Wacht voor startup:
    sleep 45 (PostgreSQL + N8n init takes time)

6.7 Status check:
    ssh root@178.104.207.194 "cd /docker/nova-v2 && docker compose ps"
    
    Verwacht 7 containers in "Up" of "healthy" state:
    - nova-v2-postgres (healthy)
    - nova-v2-redis (healthy)
    - nova-v2-n8n-main (Up)
    - nova-v2-n8n-worker-1 (Up)
    - nova-v2-n8n-webhook (Up)
    - nova-v2-minio (healthy)
    - nova-v2-qdrant (Up)
    
    Als een container failed/restarting:
    - ssh root@hetzner "docker compose logs --tail=50 <container_name>"
    - Analyseer error
    - Max 2 fix pogingen (bijv. permissies, config)
    - Bij aanhoudende fout: stop, rapporteer, toon logs

== FASE 7: HEALTH VALIDATIE ==

7.1 Lokale health checks op Hetzner:
    ssh root@178.104.207.194:
    
    # N8n main
    curl -sI http://localhost:5679 | head -1
    # Verwacht: HTTP/1.1 200 OK of 401
    
    # N8n webhook
    curl -sI http://localhost:5680 | head -1
    # Verwacht: 200 of 404
    
    # MinIO health
    curl -s http://localhost:9000/minio/health/live
    # Verwacht: empty response of "OK" (200 status)
    
    # Qdrant
    curl -s http://localhost:6333/ | head -5
    # Verwacht: JSON met title en version

7.2 Firewall openen:
    ssh root@178.104.207.194:
    
    ufw status
    
    # Als firewall aanstaat, open poorten:
    ufw allow 5679/tcp comment 'NOVA v2 N8n main'
    ufw allow 5680/tcp comment 'NOVA v2 N8n webhook'
    ufw allow 9001/tcp comment 'NOVA v2 MinIO console'
    
    # NIET publiek openen: 9000 (MinIO S3), 6333/6334 (Qdrant)

7.3 Externe bereikbaarheid vanaf lokaal:
    curl -sI http://178.104.207.194:5679 | head -1
    
    Moet 200 of 401 geven.
    
    Als niet: check ufw status op Hetzner opnieuw.

7.4 V1 onaangetast verifieren (critical):
    ssh root@178.104.207.194 "curl -sI http://localhost:5678 | head -1"
    
    Moet nog steeds 200/401 zijn.
    
    Als v1 kapot: CRITICAL, stop alles, rapporteer direct.

== FASE 8: RAPPORTAGE ==

8.1 Genereer deploy rapport:
    
    Bestand: logs/deploy_YYYY-MM-DD_HH-MM.md
    
    # NOVA v2 Deployment Rapport
    
    **Datum**: [ISO timestamp]
    **Duur**: [start tot nu]
    **Status**: Success
    
    ## Container Status
    
    ```
    [docker compose ps output]
    ```
    
    ## Health Checks
    
    - N8n main (5679): [HTTP status]
    - N8n webhook (5680): [HTTP status]
    - MinIO (9001 console): [status]
    - Qdrant (6333): [status]
    - V1 (5678): onaangetast
    
    ## Firewall
    
    - 5679/tcp: open
    - 5680/tcp: open
    - 9001/tcp: open
    - 9000/tcp: alleen intern
    - 6333/tcp: alleen intern
    
    ## Access URLs
    
    - N8n UI: http://178.104.207.194:5679
    - N8n Webhook: http://178.104.207.194:5680
    - MinIO Console: http://178.104.207.194:9001
    - Qdrant API: http://178.104.207.194:6333
    
    ## Secrets
    
    Locatie: L:\!Nova V2\secrets\nova_v2_passwords.txt
    
    MinIO credentials: lees uit secrets file (MINIO_ROOT_USER, MINIO_ROOT_PASSWORD)
    
    ## Volgende Stappen
    
    1. Open http://178.104.207.194:5679 in browser
    2. N8n vraagt bij eerste login om admin account aan te maken
    3. Admin gebruiker + password kiezen en opslaan in secrets file
    4. Settings → API → Generate API Key
    5. API key toevoegen aan secrets file als N8N_V2_API_KEY
    6. Login in MinIO console op :9001 met credentials uit secrets
    7. Maak MinIO buckets: nova-assets, nova-cache
    8. Import eerste workflows uit agents folder (apart prompt)
    
    ## Waarschuwingen
    
    [lijst indien van toepassing]

8.2 Append aan logs/deploy_log.txt alle stappen met timestamps.

8.3 Toon in chat korte summary:
    - Status: Success
    - N8n UI URL
    - Rapport locatie
    - Eerste 3 next steps

== REGELS ==

- Log elke stap, NIET secrets
- Max 2 retry per issue
- V1 is heilig, nooit raken
- Bij critical failure: docker compose down v2, rapporteer, wacht
- Alle SSH via root@178.104.207.194
- Password prompts: tonen in terminal, gebruiker typt
- Alternatief: ssh-copy-id eerst voor password-less

Ga aan de slag. Fase 5 t/m 8 doorlopen. Rapporteer tussentijds.
```

## Tijdens deploy

Cursor zal mogelijk om root password vragen (meerdere keren bij elke ssh/scp). Twee opties:

**Optie A: Typ elke keer password**
Minder ideaal bij veel commandos (7+ ssh calls).

**Optie B: SSH key setup eerst (aanbevolen)**

In een PowerShell terminal:
```
ssh-copy-id root@178.104.207.194
```

Typ password één keer. Daarna zijn alle SSH/SCP calls password-less.

Als `ssh-copy-id` niet bestaat in PowerShell:
```
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh root@178.104.207.194 "cat >> ~/.ssh/authorized_keys"
```

Of als je geen SSH key hebt:
```
ssh-keygen -t ed25519
ssh-copy-id root@178.104.207.194
```

## Na succesvolle deploy

Open browser: http://178.104.207.194:5679

N8n vraagt bij eerste bezoek:
- Email voor admin
- Password voor admin
- Personal info (skip kan)

Bewaar admin credentials in `L:\!Nova V2\secrets\nova_v2_passwords.txt`:
```
# N8n v2 Admin (handmatig ingevuld na eerste login)
N8N_V2_ADMIN_EMAIL=jouw@email.com
N8N_V2_ADMIN_PASSWORD=<gekozen password>
```

Daarna: Settings → n8n API → Create API Key → kopieer → toevoegen aan secrets file.

Ready voor eerste workflow imports uit `agents/nova_v2_agents/templates/`.
