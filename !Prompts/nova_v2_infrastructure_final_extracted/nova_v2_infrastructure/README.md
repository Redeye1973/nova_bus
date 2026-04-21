# NOVA v2 Infrastructure

Complete Docker infrastructure voor NOVA v2 N8n deployment naast bestaande v1.

## Inhoud

```
nova_v2_infrastructure/
├── README.md (dit bestand)
├── CURSOR_DEPLOY_PROMPT.md (voor automatische deploy via Cursor)
├── docker/
│   ├── docker-compose.yml (complete stack)
│   └── .env.template (secrets template)
├── scripts/
│   ├── deploy.sh (handmatig deploy script)
│   └── init-postgres.sh (PostgreSQL init)
├── config/
│   └── (custom N8n config indien nodig)
└── docs/
    └── (extra documentatie)
```

## Wat er gedeployed wordt

**Services:**
- N8n main (poort 5679) - UI + orchestratie
- N8n worker (1x, kan meer) - queue job processor
- N8n webhook (poort 5680) - dedicated webhook ontvangst
- PostgreSQL 16 - N8n database
- Redis 7 - queue + cache
- MinIO (poort 9000/9001) - S3-compatible asset storage
- Qdrant (poort 6333) - vector search voor Surilians bible + asset similarity

**Geen impact op:**
- NOVA v1 op poort 5678 blijft volledig werken
- Bestaande workflows blijven draaien
- v1 data en credentials onaangetast

## Quick Start

### Optie 1: Automatisch via Cursor (aanbevolen)

1. Open Cursor in deze map
2. Open CURSOR_DEPLOY_PROMPT.md
3. Kopieer de prompt
4. Plak in Cursor Composer (Ctrl+I)
5. Cursor deployt autonoom op Hetzner

### Optie 2: Handmatig

```bash
# Op je lokale machine
# 1. Kopieer naar Hetzner
scp -r nova_v2_infrastructure/ user@178.104.207.194:/docker/nova-v2/

# 2. SSH naar Hetzner
ssh user@178.104.207.194

# 3. Configureer secrets
cd /docker/nova-v2/docker
cp .env.template .env
nano .env  # Vul passwords in

# Genereer sterke passwords:
openssl rand -base64 32  # voor wachtwoorden
openssl rand -hex 32     # voor N8N_ENCRYPTION_KEY en JWT_SECRET

# 4. Maak scripts executable
chmod +x ../scripts/deploy.sh
chmod +x ../scripts/init-postgres.sh

# 5. Deploy
../scripts/deploy.sh
```

## Poorten overzicht

| Poort | Service | Doel |
|-------|---------|------|
| 5678 | N8n v1 | **Bestaand**, niet aanraken |
| 5679 | N8n v2 main | UI, workflow management |
| 5680 | N8n v2 webhook | Webhook endpoint |
| 9000 | MinIO S3 API | Asset storage API |
| 9001 | MinIO Console | Web UI voor MinIO |
| 6333 | Qdrant HTTP | Vector search API |
| 6334 | Qdrant gRPC | Vector search gRPC |

## Hetzner firewall

Open deze poorten in UFW:
```bash
sudo ufw allow 5679/tcp  # N8n v2 UI
sudo ufw allow 5680/tcp  # N8n v2 webhooks
sudo ufw allow 9001/tcp  # MinIO console (alleen voor jou, overweeg VPN)
# NIET publiek openen:
# 9000 - MinIO S3 (alleen intern gebruiken)
# 6333/6334 - Qdrant (alleen intern)
# PostgreSQL, Redis (intern Docker network only)
```

## Resources verbruik

**Idle:**
- Memory: ~1.5GB RAM
- CPU: < 5%
- Disk: ~500MB containers + data groeiend

**Active (workflows runnen):**
- Memory: 2-4GB RAM
- CPU: 20-60% depending op load
- Network: afhankelijk van jobs

Op Hetzner €8/maand server: passend voor development en moderate productie.

## Migration van v1 naar v2

**Phase 1: Parallel running (maand 1-3)**
- v1 op 5678 blijft doen wat het doet
- v2 op 5679 krijgt opgebouwd
- Nieuwe workflows bouwen in v2
- Test parallel

**Phase 2: Graduele transitie (maand 3-6)**
- Nieuwe klanten/projecten alleen via v2
- v1 workflows niet meer uitbreiden
- Bij kritieke bugs v1 patchen

**Phase 3: V2 promoveren (maand 6+)**
- V1 workflows migreren naar v2 (1 voor 1, getest)
- v1 in read-only mode
- Eventueel v1 shutdown, v2 krijgt poort 5678

## Volgende stappen na deploy

1. **Open N8n UI**: http://178.104.207.194:5679
2. **Admin account**: Eerste login vraagt om gebruiker/wachtwoord aan te maken
3. **API key**: Settings → API → Generate (bewaar in key store)
4. **Importeer NOVA v2 workflows**: Uit `nova_v2_agents/templates/` folder
5. **Configureer Ollama credentials**: In N8n credentials, point naar lokale PC
6. **Configureer MinIO buckets**: via Console op :9001 of mc CLI
7. **Setup Qdrant collections**: via API voor Surilians bible + asset library

## Backup

Pas backup strategie toe vanaf eerste week:

```bash
# Cron job voor dagelijkse backup
# Op Hetzner: crontab -e
0 3 * * * cd /docker/nova-v2 && docker compose exec -T postgres-v2 pg_dump -U $(grep POSTGRES_NON_ROOT_USER docker/.env | cut -d= -f2) -d n8n_v2 | gzip > /backup/n8n_v2_$(date +\%Y\%m\%d).sql.gz

# MinIO backup
0 4 * * * docker run --rm -v nova-v2-minio-data:/data:ro -v /backup:/backup alpine tar czf /backup/minio_$(date +\%Y\%m\%d).tar.gz /data

# Keep laatste 30 dagen, cleanup ouder
0 5 * * 0 find /backup -name "*.gz" -mtime +30 -delete
```

## Troubleshooting

**Containers starten niet:**
```bash
cd /docker/nova-v2/docker
docker compose ps
docker compose logs
```

**N8n UI niet bereikbaar:**
```bash
# Check specifiek logs
docker compose logs n8n-v2-main

# Check postgres health
docker compose ps postgres-v2
docker compose exec postgres-v2 pg_isready -U $POSTGRES_USER

# Check netwerk
docker compose exec n8n-v2-main ping postgres-v2
```

**Webhook geeft 404:**
```bash
# Webhook container apart checken
docker compose logs n8n-v2-webhook
curl -I http://localhost:5680/webhook/test
```

**Reset alles (data behouden):**
```bash
docker compose down
docker compose up -d
```

**Complete reset (DATA VERLIES):**
```bash
docker compose down -v  # -v verwijdert volumes!
# Data weg, begin opnieuw
```

## Veiligheid notes

**Voor development/personal use** (huidige fase):
- HTTP is ok
- Port exposure is ok (private IP anyway)
- Passwords in .env lokaal

**Voor productie met klanten** (later):
- HTTPS verplicht (reverse proxy met Caddy of Traefik)
- Rate limiting
- IP whitelisting waar mogelijk
- Secrets in Vault of vergelijkbaar
- Regular security audits

## Integratie met nova_config.yaml

Na deploy, update `nova_config.yaml` met:

```yaml
nova_config:
  infrastructure:
    n8n_v2:
      main_url: "http://178.104.207.194:5679"
      webhook_url: "http://178.104.207.194:5680"
      api_key: "<from settings>"
    minio:
      endpoint: "http://178.104.207.194:9000"
      console: "http://178.104.207.194:9001"
      access_key: "<from .env>"
      secret_key: "<from .env>"
    qdrant:
      url: "http://178.104.207.194:6333"
    postgres_v2:
      host: "178.104.207.194"
      port: 5432  # niet publiek toegankelijk
    redis_v2:
      host: "178.104.207.194"
      port: 6379  # niet publiek toegankelijk
```

Alle NOVA v2 agents (01-35) lezen dit bij startup.

## Support

Bij problemen:
1. Check deze README eerst
2. docker compose logs van relevante service
3. Memory of git commit waar stap-voor-stap gefaalde
4. Vraag in nieuwe Claude sessie met logs meegestuurd
