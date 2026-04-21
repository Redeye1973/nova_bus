# NOVA v2 Architecture

## Overzicht

NOVA v2 is een multi-agent orchestration platform dat content production pipelines automatiseert via jury-judge kwaliteitsgates. Gebouwd met Docker containers op Hetzner + jouw lokale PC voor GPU-intensive tasks.

## Componenten

### Server layer (Hetzner)

**N8n v2 main (port 5679)**
- Workflow orchestratie
- API endpoint voor agents
- UI voor monitoring

**N8n v2 webhook (port 5680)**
- Dedicated webhook receiver
- Trigger endpoints voor elk agent

**PostgreSQL 16**
- Backend voor N8n workflows
- Status data
- Historische metrics
- Mission data (later voor Black Ledger)

**Redis 7**
- Queue voor async jobs
- Cache layer
- Rate limiting

**MinIO (ports 19000/19001)**
- S3-compatible object storage
- Asset versioning
- Build artifacts
- Backup storage

**Qdrant (port 6333)**
- Vector database
- Canon search (Surilians, Black Ledger)
- Asset similarity
- Style reference library

**Agent containers**
- Elk agent in eigen container
- Python 3.11 + FastAPI
- Interne port (8xxx)
- Verbonden via nova-v2-network

### Client layer (jouw PC)

**Ollama**
- Local AI inference
- Modellen: Codestral, llama3.2:3b (straks: Qwen 9B + Nemotron 4B)
- Port 11434

**Game dev tools**
- Godot 4.6.2
- Blender 4.x
- FreeCAD 1.x
- Aseprite
- Krita, GIMP, Inkscape

**Cursor IDE**
- Development environment
- Composer voor autonome tasks
- Git integratie

### Network layer

**Tailscale**
- Private mesh netwerk
- PC ↔ Hetzner secure
- Agent containers bereiken PC Ollama via tailnet

## Data flow

### Agent invocation

```
Cursor/User
    ↓
PowerShell / HTTP POST
    ↓
N8n v2 webhook (5680)
    ↓
Route naar agent container
    ↓
Agent FastAPI service
    ↓
[Ollama call indien nodig, via tailscale]
    ↓
Response via webhook
    ↓
Status update in PostgreSQL
    ↓
Output naar MinIO (indien artifact)
```

### Asset pipeline

```
Concept
    ↓
Design Fase Agent (palette)
    ↓
FreeCAD Parametric (3D components)
    ↓
Blender Game Renderer (multi-angle sprites)
    ↓
Aseprite Processor (pixel-art polish)
    ↓
Sprite Jury (quality gate)
    ↓ (accept)
PyQt5 Assembly (sprite sheets)
    ↓
Godot Import (game-ready resources)
    ↓
In Godot project
```

## Principes

### Jury-Judge pattern

Elke kritische agent heeft multiple jury members die parallel reviewen:
- Elk jury member focust op één specifiek aspect
- Judge aggregeert verdicten
- Drie outcomes: accept / revise / reject
- Revise levert specifieke feedback

### Fallback first

Elke agent heeft fallback mode:
- Als externe tool (Ollama, Blender) niet beschikbaar: deterministische versie
- Als API key rate-limited: cache hit
- Als container crashed: Error Agent detecteert, probeert restart

### Stateless services

Agents slaan geen permanent state op in container:
- PostgreSQL voor persistent data
- MinIO voor assets
- Redis voor tijdelijke cache
- Containers kunnen restart zonder data verlies

### Queue over sync

Zware operaties via Redis queue:
- Upload job naar queue
- Agent poll queue
- Async processing
- Callback bij completion

Voorkomt timeouts op webhooks.

## Security

### Authentication

- V2 N8n: API key (in secrets file)
- Ollama: lokaal, geen external
- SSH: key-only naar Hetzner
- UFW firewall actief

### Network

- PostgreSQL: alleen internal Docker network
- Redis: alleen internal
- Qdrant: alleen internal (6333 niet publiek open)
- MinIO S3 API (19000): alleen internal voor nu
- Publiek: 5679, 5680, 19001 (MinIO console)

### Secrets

- Lokaal in `L:\!Nova V2\secrets\`
- Hetzner in `.env` (chmod 600)
- Never in code, chat, logs
- Bitwarden voor backup (persoonlijk)

## Schaalbaarheid

### Horizontaal

Binnen Hetzner €8/maand server:
- Tot ~10 concurrent agents OK
- Ollama calls naar PC (24/7) nemen load
- PostgreSQL blijft snel tot ~100k records

### Vertikaal

Upgrades mogelijk:
- Hetzner grotere server (meer RAM/CPU) voor €20-30/maand
- Dedicated GPU server (€184+/maand) voor heavy AI
- Apart PC voor Ollama als jouw PC tekort komt

### Toekomst

Bij schaling naar klanten:
- Reverse proxy (Caddy) voor HTTPS
- Multiple agent instances via Docker Swarm
- Load balancer
- CDN voor asset delivery

Dit is buiten scope voor nu.

## Integratie met Black Ledger

Later package zal bouwen:
- Godot game project op PC
- Content productie via NOVA v2 agents
- Balance data in PostgreSQL
- Assets in MinIO
- Builds automatisch via Game Master Agent

Pipeline blijft hetzelfde, alleen nieuwe workflows specifiek voor Black Ledger content.

## Architecturale beslissingen

### Waarom Python/FastAPI

- Bestaande NOVA stack (V1 in Python)
- Rich ecosystem voor AI/data processing
- Async support via FastAPI
- Simpele Docker containerisatie

### Waarom N8n

- V1 bewezen met 68 agents
- Visual workflow editor (debug-friendly)
- API voor alles (automation mogelijk)
- Webhook native support
- PostgreSQL backend voor v2 (betrouwbaarder dan SQLite)

### Waarom Hetzner + PC hybride

- Hetzner: 24/7 server voor €8/mnd
- PC: GPU voor AI + development tools
- Tailscale: veilige verbinding
- Beste van beide: predictable costs + krachtige hardware

### Waarom Docker voor agents

- Isolatie per agent
- Makkelijk updaten
- Dependency management
- Reproducible deployments
- Schaalbaar

### Waarom open source tools

- Geen vendor lock-in
- Kosten €0
- Past bij NOVA filosofie
- Community support
- Jij controleert pipeline

## Anti-patterns (niet doen)

- Geen secrets in Git
- Geen V1 agents wijzigen tijdens V2 werk
- Geen synchrone heavy operaties (>30s) op webhook
- Geen publieke exposure Postgres/Redis
- Geen hardcoded paths in agent code (gebruik nova_config.yaml)
- Geen agents zonder fallback mode
- Geen containers zonder healthcheck
