# NOVA v2 Infrastructure Auto-Deploy Prompt voor Cursor

Deze prompt laat Cursor autonoom NOVA v2 N8n infrastructure deployen op jouw Hetzner server.

## Wat Cursor gaat doen

1. SSH verbinden met Hetzner server (178.104.207.194)
2. Docker + Docker Compose controleren (installeren indien nodig)
3. Directory structuur aanmaken op /docker/nova-v2/
4. Docker compose files uploaden
5. .env genereren met sterke random passwords
6. Services deployen
7. Health checks valideren
8. Resultaten terugrapporteren

## Voorwaarden

Voordat je deze prompt gebruikt:
- SSH toegang tot Hetzner is geconfigureerd op jouw lokale machine
- SSH key is actief (ssh-agent running)
- Je hebt root of sudo rechten op Hetzner
- NOVA v1 op poort 5678 blijft ongemoeid

## De prompt voor Cursor

Plak dit in Cursor Composer (Ctrl+I):

```
Ik wil NOVA v2 N8n infrastructure deployen op mijn Hetzner server (178.104.207.194).
Oude N8n v1 draait op poort 5678 en moet ongewijzigd blijven.
Nieuwe v2 gaat op poort 5679 (main) en 5680 (webhooks).

Voer de volgende stappen autonoom uit:

STAP 1: SSH VERBINDING CHECKEN
- Test of SSH naar 178.104.207.194 werkt
- Als niet: meld exact welk SSH commando faalt, stop en vraag om hulp
- Als wel: ga door

STAP 2: VEREISTEN CHECKEN OP HETZNER
- Run via SSH: `docker --version`
- Run via SSH: `docker compose version`
- Als één ontbreekt: rapporteer en vraag toestemming om te installeren
- Check of poorten 5679, 5680, 9000, 9001, 6333, 6334 vrij zijn met `lsof -i :POORT`

STAP 3: DIRECTORY STRUCTUUR
- Maak op Hetzner: `/docker/nova-v2/`
- Submappen: `scripts/`, `config/n8n-custom/`, `logs/`
- Zet eigenaar op gebruiker (niet root)

STAP 4: BESTANDEN UPLOADEN
Upload naar /docker/nova-v2/:
- docker-compose.yml (uit deze package, content bijgevoegd)
- .env.template
- scripts/init-postgres.sh (maak executable: chmod +x)
- scripts/deploy.sh (maak executable)

Gebruik scp of rsync voor upload.

STAP 5: SECRETS GENEREREN
Genereer strong passwords en maak .env file:
- POSTGRES_PASSWORD: openssl rand -base64 32
- POSTGRES_NON_ROOT_PASSWORD: openssl rand -base64 32  
- REDIS_PASSWORD: openssl rand -base64 32
- N8N_ENCRYPTION_KEY: openssl rand -hex 32
- N8N_JWT_SECRET: openssl rand -hex 32
- MINIO_ROOT_PASSWORD: openssl rand -base64 32

Vul deze in .env in (copy van template + substituties).
BELANGRIJK: Bewaar de gegenereerde passwords lokaal in een veilige plek
(bv. C:/Users/awsme/nova_v2_secrets.txt - of nieuwe key locatie waar gebruiker
aangegeven heeft). Vraag waar ze opgeslagen moeten worden als onduidelijk.

STAP 6: DEPLOY
Run op Hetzner:
- cd /docker/nova-v2/
- docker compose pull (trekt laatste images)
- docker compose up -d (start alles detached)
- Wacht 30 seconden voor services om te starten
- docker compose ps (check status)

STAP 7: HEALTH VALIDATIE
Test vanaf Hetzner lokaal:
- curl -I http://localhost:5679 (N8n main moet 200 of 401 geven)
- curl -I http://localhost:5680 (N8n webhook moet respond)
- curl http://localhost:9000/minio/health/live (MinIO health)
- curl http://localhost:6333/ (Qdrant info)

Test vanaf lokale machine:
- curl -I http://178.104.207.194:5679 (extern bereikbaar)

Als één health check faalt:
- Toon docker compose logs van die service
- Identificeer issue
- Probeer fix (maximaal 2 keer)
- Als nog steeds faalt: rapporteer duidelijk en stop

STAP 8: FIREWALL CHECK
Check of Hetzner firewall (UFW) de nieuwe poorten toestaat:
- sudo ufw status
- Indien niet: sudo ufw allow 5679/tcp, 5680/tcp, 9001/tcp, 6333/tcp
(9000 en 6334 NIET openen publiek - alleen intern gebruiken)

STAP 9: V1 VERIFICATIE
Check of oude N8n v1 nog steeds werkt:
- curl -I http://localhost:5678 op Hetzner
- Als niet meer: CRITICAL - undo deployment en rapporteer
- Als wel: continue

STAP 10: RAPPORTAGE
Output een complete deployment report:
- Welke services draaien
- Welke poorten open
- Access URLs
- Gegenereerde secrets locatie (niet de passwords zelf!)
- Eventuele warnings
- Next steps voor gebruiker (admin account aanmaken, etc)

TERUGROLLING BIJ PROBLEMEN:
Als iets halverwege misgaat, voer terugrol uit:
- docker compose down
- Backup .env naar safekeeping
- Rapporteer exact waar het misging
- NIET v1 op 5678 raken

AUTONOOM WERKEN:
- Werk door zonder bevestiging te vragen voor elke stap
- Stop alleen bij echte fouten die niet auto-fixable zijn
- Max 2 pogingen zelfde aanpak (per NOVA architectuur regel)
- Bij 3e fout: stop en rapporteer

LOGS:
Log alles wat je doet naar /docker/nova-v2/logs/deploy_YYYY-MM-DD.log
Formaat: timestamp | step | action | result

De bestanden die je moet uploaden zijn in: [pad waar zip is uitgepakt]/docker/
Werk met deze content, niet eigen versies maken.

Ga nu autonoom aan de slag. Rapporteer als je klaar bent.
```

## Bijgevoegde bestanden

Cursor heeft deze nodig, zorg dat ze toegankelijk zijn:
- `docker/docker-compose.yml`
- `docker/.env.template`
- `scripts/init-postgres.sh`
- `scripts/deploy.sh`

## Hoe Cursor de SSH doet

Cursor zal waarschijnlijk gebruiken:

**Voor SSH commando's:**
```bash
ssh user@178.104.207.194 "command_here"
```

**Voor bestand upload:**
```bash
scp file user@178.104.207.194:/docker/nova-v2/
# of
rsync -avz file user@178.104.207.194:/docker/nova-v2/
```

**Voor multi-regel scripts:**
```bash
ssh user@178.104.207.194 << 'EOF'
cd /docker/nova-v2
docker compose up -d
EOF
```

Als Cursor SSH gebruikersnaam of specifieke key path nodig heeft: vul dat zelf aan in het commando of in `~/.ssh/config` op jouw PC.

## Na Cursor klaar is

**Verwachte output:**
- Alle 6 containers draaien (postgres, redis, n8n-main, n8n-worker, n8n-webhook, minio, qdrant)
- V1 N8n op poort 5678 werkt nog
- V2 N8n op poort 5679 bereikbaar vanaf je browser
- Secrets opgeslagen op veilige locatie (niet in git!)

**Eerste manuele stappen daarna:**
1. Open http://178.104.207.194:5679 in browser
2. N8n vraagt om admin account aan te maken (eerste login)
3. Na login: Settings → API → generate API key
4. Bewaar API key in key storage (niet in git)
5. Importeer NOVA v2 workflows uit agent catalogus

## Troubleshooting

**SSH werkt niet:**
```bash
# Test handmatig eerst
ssh -v user@178.104.207.194
```

**Port 5679 al in gebruik:**
```bash
# Op Hetzner
sudo lsof -i :5679
# Zie welk process, beslis of stoppen of andere port kiezen
```

**Docker compose faalt:**
```bash
# Logs bekijken
cd /docker/nova-v2
docker compose logs n8n-v2-main
# Of specifieke service
docker compose logs postgres-v2
```

**N8n start niet (database niet ready):**
```bash
# Wacht langer en check postgres
docker compose ps postgres-v2
docker compose logs postgres-v2
```

**Externe bereikbaarheid niet:**
```bash
# Hetzner firewall
sudo ufw status
sudo ufw allow 5679/tcp
```

## Integratie met NOVA v2 agents

Na succesvolle deploy:
- Elke NOVA v2 agent (01-35) lezen de Hetzner URL: http://178.104.207.194:5679
- Webhooks naar: http://178.104.207.194:5680/webhook/...
- MinIO voor asset storage: http://178.104.207.194:9000 (S3 API)
- Qdrant voor vector search: http://178.104.207.194:6333

Deze URLs automatisch in nova_config.yaml (van software discovery).

## Backup strategie

Na deploy, setup automatische backups:
```bash
# Dagelijkse backup van PostgreSQL
0 3 * * * docker exec nova-v2-postgres pg_dump -U postgres n8n_v2 > /backup/n8n_v2_$(date +\%Y\%m\%d).sql

# Backup MinIO data
0 4 * * * docker run --rm -v nova-v2-minio-data:/data -v /backup:/backup alpine tar czf /backup/minio_$(date +\%Y\%m\%d).tar.gz /data
```

## Veiligheid checklist

Voor productie:
- [ ] .env file permissies 600 (alleen owner)
- [ ] .env in .gitignore
- [ ] Hetzner firewall actief (UFW)
- [ ] Fail2ban op SSH
- [ ] Docker socket niet exposed
- [ ] MinIO ingesteld met HTTPS (later)
- [ ] N8n behind reverse proxy met SSL (later, via Caddy of Traefik)

Voor nu (development): HTTP ok, port exposed ok, maar vooruit plannen.
