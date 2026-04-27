# Nova Reference Layer — Cursor Prompts, fase 6 hardening

**Voor:** A. Meter, Nova Platform  
**Datum:** April 2026  
**Context:** Fase 4-5 (Wikidata + PDOK + router + sprite pilot) staat. Deze fase 6 maakt het systeem productiewaardig en duurzaam — backup, observability, rollback-paden, audit, kostenbewust.

---

## INSTRUCTIES AAN CURSOR — LEES EERST

Dit bestand bevat **6 prompts**, plus een handmatige acties-bijlage onderaan. Werk ze **sequentieel** af in deze exacte volgorde:

1. Backup & restore
2. Dead letter queue
3. Schema versioning + idempotency
4. Audit log voor mutaties
5. Centrale rollback via feature flags
6. Observability uitbreiding

**Regels:**
- Per prompt: schrijf code → run tests → commit → smoke test → DAARNA pas door naar volgende
- Vraag mij expliciet om akkoord NA elke commit voordat je aan de volgende prompt begint, tenzij ik in de eerste boodschap "voer alles achter elkaar uit" heb gezegd
- Bij vastlopen na 3 pogingen op hetzelfde technische probleem: STOP, zoek alternatief via documentatie of web, ga niet eindeloos circles draaien
- Geen scope creep: als een prompt een specifiek bestand niet noemt, raak het niet aan
- Bij elke "NIET DOEN"-clausule: lees, begrijp, respecteer

**Niet-code acties** (jij doet zelf, niet Cursor): zie bijlage onderaan dit document.

---

## Prompt 1 — Postgres backup & restore

```
Implementeer een geautomatiseerde backup en bewezen restore voor de nova-ref Postgres
instance. Doel: bij dataverlies (corrupte schijf, ransomware, per ongeluk DROP TABLE)
verlies maximaal 24 uur data en heb je een restore-pad dat je niet improviseert
tijdens een crisis.

NIEUWE BESTANDEN:

1. infrastructure/scripts/nova_ref_backup.sh
   Vervang door: infrastructure/scripts/nova_ref_backup.ps1 (PowerShell) dat:
   - pg_dump van nova_ref_db draait (custom format -Fc, niet plain SQL)
   - Output gzipt naar /backup/nova_ref/$(date +%Y-%m-%d_%H%M).dump.gz
   - Oudere backups dan 30 dagen verwijdert
   - Bij failure een non-zero exit code geeft (zodat cron het kan signaleren)
   - Schrijft een logregel naar /var/log/nova/backup.log met grootte en duur
   
   Geen wachtwoord-prompts; lees credentials uit /etc/nova/backup.env (chmod 600,
   eigenaar root). Gebruik PGPASSWORD env var, geen .pgpass.

2. infrastructure/scripts/nova_ref_restore.ps1
   PowerShell script dat:
   - Argument verwacht: pad naar backup file
   - VRAAGT EXPLICIET BEVESTIGING: "Type 'RESTORE' to confirm overwrite of nova_ref_db: "
   - Drop+recreate van nova_ref_db (niet alleen drop tables, ook schema's)
   - pg_restore -Fc met --clean --create flags
   - Verifieert na afloop dat cache.entities en learn.build_runs bestaan
   
   Dit script moet IDIOTPROOF zijn — het is wat je gebruikt om 03:00 's nachts
   na een crash. Geen tools assumed beschikbaar behalve pg_restore en bash.

3. infrastructure/scripts/install_backup_tasks.ps1
   Registreert Windows Scheduled Tasks:
   - Daily 03:30 local: nova_ref_backup.ps1
   - Logging naar C:\nova\logs\backup.log

OFFSITE COMPONENT:

4. infrastructure/scripts/nova_ref_offsite_sync.ps1
   PowerShell script dat de laatste backup naar een offsite locatie schopt. Twee opties,
   kies die met laagste setup-kosten:
   - Optie A: rsync naar tweede Hetzner Storage Box (€3/maand, 1TB)
   - Optie B: rclone naar Backblaze B2 bucket (encrypt at rest met rclone crypt)
   
   Voor MVP: kies optie A (rsync). Voeg een placeholder voor B2 toe als comment
   voor latere migratie. Cron: dagelijks om 04:00 UTC, na lokale backup.

DOCUMENTATIE:

5. infrastructure/scripts/RESTORE_RUNBOOK.md
   Een korte runbook (max 1 A4) met EXACT de stappen om een restore uit te voeren:
   - Welke service stoppen voor restore (nova-ref, nova-learn)
   - Welk backup-bestand kiezen
   - Welk commando draaien
   - Hoe verifiëren dat het werkt (curl /health, query cache.entities count)
   - Welke services weer opstarten en in welke volgorde
   
   Schrijf dit in de imperatief ("Stop nova-ref"), niet in beschrijvende taal.
   Dit lees je in paniek.

Extra Windows eis:
- Backup target pad moet expliciet geconfigureerd zijn (bijv. D:\ of T:\).
- Vraag Alex om de exacte drive-letter voordat offsite sync wordt geactiveerd.

VERIFICATIE — schrijf deze test, draai hem ECHT (niet mocked):

6. infrastructure/tests/test_backup_restore_cycle.ps1
   PowerShell script dat:
   a) Insert een herkenbare row in cache.entities (id='backup_test_marker')
   b) Draait backup script
   c) DROP TABLE cache.entities
   d) Draait restore script (auto-bevestigd voor test)
   e) Query op id='backup_test_marker' → verwacht de row terug
   f) Cleanup
   
   Dit script moet groen draaien voor je commit. Anders is je backup theater.

NIET DOEN:
- Geen Postgres replica setup nu (dat is fase 7+)
- Geen wal-e of barman — overkill voor jouw scale
- Geen ondoorzichtige Docker-init magic — bash scripts die een mens kan lezen

COMMIT MESSAGE:
"feat(infra): nova-ref Postgres backup, offsite sync, and verified restore runbook"
```

---

## Prompt 2 — Dead letter queue voor Redis Streams

```
Bouw een dead letter queue (DLQ) mechanisme voor nova-learn. Doel: events die na
N retries niet verwerkt kunnen worden, gaan naar een aparte stream waar ze
zichtbaar zijn zonder de hoofdverwerking te blokkeren.

CONTEXT:
- Hoofdstream: nova_ref_events
- Consumer group: nova_learn_group  
- Bestaande consumer in nova-learn/src/nova_learn/consumer.py

WIJZIGINGEN:

1. nova-learn/src/nova_learn/consumer.py
   Voeg toe:
   - max_delivery_count = 3 (configureerbaar via env: NOVA_LEARN_MAX_DELIVERIES)
   - Bij elke XREADGROUP, check XPENDING voor het message_id
   - Als delivery_count > max_delivery_count: 
     a) XADD naar nova_ref_events_dlq met original payload + reason + first_failed_at
     b) XACK op originele stream (zodat het uit PEL gaat)
     c) Log structlog warning met message_id + reden
     d) Increment Prometheus counter: nova_learn_dlq_total{reason}
   - Het verwerken zelf is unchanged

2. nova-learn/src/nova_learn/dlq_inspector.py (NIEUW)
   FastAPI router met endpoints:
   
   GET /dlq/messages?limit=50
   → Lees laatste N messages uit nova_ref_events_dlq, return JSON
   
   GET /dlq/messages/{message_id}
   → Detail van één message inclusief original payload en error reden
   
   POST /dlq/messages/{message_id}/replay
   → Lees uit DLQ, XADD opnieuw naar nova_ref_events, XDEL uit DLQ
   → Body: {"reset_delivery_count": true} (default)
   → Voor handmatige recovery na een bug-fix
   
   POST /dlq/messages/{message_id}/discard
   → XDEL uit DLQ permanent. Vereist body {"confirm": "yes"}.
   
   Mount op nova-learn FastAPI app onder /dlq prefix.

3. Configuratie (.env.example):
   NOVA_LEARN_MAX_DELIVERIES=3
   NOVA_LEARN_DLQ_STREAM=nova_ref_events_dlq
   NOVA_LEARN_DLQ_MAX_LENGTH=10000  (XADD MAXLEN ~ approx)

4. Health endpoint uitbreiding:
   /ready endpoint van nova-learn moet falen met 503 als nova_ref_events_dlq
   meer dan 100 messages bevat. Reden: dat betekent dat er een systematisch
   probleem is dat aandacht vraagt, niet een incident.

TESTS:

In nova-learn/tests/test_dlq.py:

- test_message_below_threshold_processed_normally:
  delivery_count=1, success → XACK naar main, geen DLQ entry
- test_message_at_threshold_goes_to_dlq:
  delivery_count=4 (boven max=3), failure → DLQ entry + XACK main
- test_dlq_replay_endpoint_re_adds_to_main:
  seed DLQ entry, POST /replay, verifieer XADD op main + XDEL op DLQ
- test_dlq_discard_requires_confirmation:
  POST /discard zonder body → 400, met body {"confirm":"no"} → 400, 
  met {"confirm":"yes"} → 200
- test_ready_endpoint_unhealthy_when_dlq_overflowing:
  vul DLQ met 101 messages (mocked), GET /ready → 503

OBSERVABILITY:
- Counter: nova_learn_dlq_total{reason}
- Gauge: nova_learn_dlq_size (huidige aantal messages)
- Update gauge elke 30 seconden via background task

NIET DOEN:
- Geen automatische replay na X uur — handmatige actie, met opzet
- Geen email notifications over DLQ events — Telegram via bestaande nova bot,
  alleen bij eerste DLQ event van de dag (voorkomt notification fatigue)
  Dit laatste optioneel; als het te veel werk is, sla het over

COMMIT MESSAGE:
"feat(nova-learn): dead letter queue with replay/discard endpoints and overflow alerting"
```

---

## Prompt 3 — Schema versioning + idempotency keys

```
Twee kleine maar belangrijke wijzigingen aan core data modellen. Beide goedkoop
nu, peperduur over zes maanden als ze ontbreken.

WIJZIGING 1: schema_version op Entity

In nova-ref/src/nova_ref/models/entity.py:

class Entity(BaseModel):
    schema_version: int = 1                 # NIEUW — eerste veld
    id: str
    # ...rest unchanged...

Migratie-strategie:
- Bestaande entities in DB: assume schema_version=1 (alle huidige data IS v1)
- ALTER TABLE cache.entities ADD COLUMN schema_version INT NOT NULL DEFAULT 1;
- Voeg dit toe aan een nieuwe Alembic migration: 002_schema_version.sql
- In normalize() van elke adapter: zet schema_version=1 expliciet (geen impliciet default)
- Dump/load: bij JSON serialization moet schema_version eerste veld zijn (Pydantic
  field ordering)

Geen logica nu om versies te migreren — dat komt pas als we ooit een v2 nodig
hebben. Maar het veld bestaat, en dat is het hele punt.

WIJZIGING 2: idempotency_key op LookupRequest

In nova-ref/src/nova_ref/models/lookup.py:

class LookupRequest(BaseModel):
    # ...bestaande velden...
    idempotency_key: str | None = None      # NIEUW

Logica in nova-ref/src/nova_ref/api/lookup.py:

- Als request.idempotency_key gegeven is:
  a) Check Redis: GET nova_ref:idempo:{key}
  b) Hit → return cached response (deserialiseer LookupResponse)
  c) Miss → voer normale lookup uit, SETEX nova_ref:idempo:{key} 60 {response_json}
  d) TTL = 60 seconden (configureerbaar via NOVA_REF_IDEMPO_TTL)
- Als geen key gegeven: gedraag als voorheen (geen idempotency check)

Belangrijk: idempotency cache is SCHEDULER-LEVEL (Redis), NIET database-level.
Reden: idempotency gaat over "voorkom dubbele werk binnen seconden", niet over
"zelfde antwoord voor altijd". De Postgres cache.entities tabel doet dat tweede.

Header support:
- Accept ook HTTP header X-Idempotency-Key als alternatief voor body-veld
- Body-veld heeft voorrang als beide aanwezig zijn

TESTS:

In nova-ref/tests/test_lookup.py:

- test_schema_version_in_response:
  do lookup, response.entity.schema_version == 1
- test_idempotency_key_returns_cached_response:
  doe lookup met key="abc", noteer response, doe direct opnieuw → identieke response
  inclusief duration_ms (proof dat geen werk gedaan)
- test_idempotency_key_expires_after_ttl:
  do lookup met key="xyz", wacht 65 seconden (mocked time), doe opnieuw →
  cache_hit=False want idempo verlopen
- test_idempotency_header_works:
  do lookup met X-Idempotency-Key header (geen body-veld), zelfde gedrag
- test_idempotency_body_overrides_header:
  body-key="A", header-key="B" → "A" wordt gebruikt

VALIDATIE:
- Bestaande tests moeten groen blijven na schema_version toevoeging
- Alembic migration draait schoon op een fresh DB
- Smoke test: doe twee identieke lookups met zelfde idempotency_key, tweede
  retourneert binnen 50ms

COMMIT MESSAGE:
"feat(models): Entity schema versioning and LookupRequest idempotency keys"

NIET DOEN:
- Geen idempotency op feedback endpoint (komt later, andere use case)
- Geen schema_version=2 logica nu — alleen het veld
- Geen lange TTL op idempotency (60s is genoeg voor race conditions, langer
  maakt het een verkapte cache)
```

---

## Prompt 4 — Audit log voor data-mutaties

```
Bouw een audit trail voor alle WRITE operaties op cache.entities die NIET via
adapters komen. Concreet: /ingest endpoint en handmatige edits via een toekomstige
admin UI. Reden: Surilians Codex en handmatig geïngeste entities zijn waardevol
en oncacheable — verlies of corruptie ervan kost dagen worldbuilding-werk.

NIEUW SCHEMA:

1. nova-ref/sql/003_audit.sql
   
   CREATE SCHEMA IF NOT EXISTS audit;
   
   CREATE TABLE audit.entity_changes (
       id              BIGSERIAL PRIMARY KEY,
       entity_id       TEXT NOT NULL,
       operation       TEXT NOT NULL CHECK (operation IN ('insert','update','delete')),
       actor           TEXT NOT NULL,           -- 'api:ingest', 'admin:user@email', 'system:adapter'
       before_state    JSONB,                   -- NULL voor insert
       after_state     JSONB,                   -- NULL voor delete
       changed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       request_id      TEXT,                    -- correlatie met API call logs
       reason          TEXT                     -- optionele uitleg, vooral bij deletes
   );
   
   CREATE INDEX idx_audit_entity ON audit.entity_changes(entity_id, changed_at DESC);
   CREATE INDEX idx_audit_actor ON audit.entity_changes(actor, changed_at DESC);
   CREATE INDEX idx_audit_operation_time ON audit.entity_changes(operation, changed_at DESC);

   -- Append-only enforcement: revoke UPDATE/DELETE rechten op deze tabel
   REVOKE UPDATE, DELETE ON audit.entity_changes FROM nova_ref;
   GRANT INSERT, SELECT ON audit.entity_changes TO nova_ref;

   Belangrijk: nova_ref user kan ALLEEN inserten en lezen, NIET wijzigen of
   verwijderen. Zo is de audit trail forensisch betrouwbaar zelfs als nova-ref
   zelf gecompromitteerd zou raken.

NIEUWE MODULE:

2. nova-ref/src/nova_ref/core/audit.py

   class AuditLogger:
       async def record_insert(self, entity: Entity, actor: str, request_id: str | None = None)
       async def record_update(self, before: Entity, after: Entity, actor: str, request_id: str | None = None)
       async def record_delete(self, entity: Entity, actor: str, reason: str, request_id: str | None = None)
   
   Operations:
   - record_insert: schrijf rij met operation='insert', after_state=entity.model_dump()
   - record_update: schrijf rij met before_state én after_state. Als ze identiek zijn (no-op),
     SKIP de log — anders pollute je je audit trail met ruis.
   - record_delete: vereist non-empty reason. Schrijf alleen before_state.
   
   Alle methodes zijn async, gebruiken connection pool, falen NIET de calling
   operation als audit-write faalt — log alleen een structlog ERROR. Reden:
   audit mag de feature niet stoppen, maar moet wel waarneembaar zijn.

INTEGRATIE IN /ingest ENDPOINT:

3. nova-ref/src/nova_ref/api/ingest.py
   
   @router.post("/ingest")
   async def ingest(payload: IngestRequest, x_actor: str = Header(...), 
                    x_request_id: str | None = Header(None)):
       # Bestaande validatie
       existing = await cache.get(payload.entity.id)
       if existing:
           await cache.update(payload.entity)
           await audit.record_update(existing, payload.entity, actor=x_actor, request_id=x_request_id)
       else:
           await cache.insert(payload.entity)
           await audit.record_insert(payload.entity, actor=x_actor, request_id=x_request_id)
       return {"id": payload.entity.id, "status": "ingested"}
   
   X-Actor header is VERPLICHT (Header(...) zonder default). Format: "api:ingest",
   "admin:alex", "agent:codex_sync", etc. Anonieme writes worden afgewezen met 400.

NIEUWE READ-ONLY ENDPOINT:

4. nova-ref/src/nova_ref/api/audit.py
   
   GET /audit/entity/{entity_id}?limit=50
   → Return change history voor één entity, nieuwste eerst
   
   GET /audit/recent?actor={actor}&operation={op}&since={iso_time}&limit=100
   → Bredere zoek voor incident response
   
   Beide endpoints zijn read-only. Geen wijzigingen mogelijk via API.

TESTS:

In nova-ref/tests/test_audit.py:

- test_ingest_new_entity_creates_audit_insert:
  POST /ingest, query audit table, verifieer 1 rij operation='insert'
- test_ingest_existing_entity_creates_audit_update:
  ingest hetzelfde entity twee keer met andere description, verifieer
  before_state en after_state correct gevuld
- test_ingest_identical_entity_skips_audit:
  ingest hetzelfde entity twee keer identiek, verifieer maar 1 audit rij
- test_ingest_without_actor_header_returns_400:
  POST /ingest zonder X-Actor → 400
- test_audit_table_is_append_only:
  Probeer DELETE FROM audit.entity_changes als nova_ref user → permission denied
- test_audit_endpoint_returns_history:
  Doe 3 updates op zelfde entity, GET /audit/entity/{id} → 3 entries chronologisch

NIET DOEN:
- Geen audit op cache writes door adapters — die zijn herbouwbaar uit bron, geen
  kritieke data. Alleen op /ingest en toekomstige admin paths
- Geen volledige denormalized snapshots in audit — alleen what changed via
  before/after. Ruimte beheersbaar houden.
- Geen audit op cache reads (GDPR-zorgen voor real-world entities zijn N.V.T.,
  alle data is publiek)

COMMIT MESSAGE:
"feat(audit): append-only audit log for /ingest mutations with read endpoints"
```

---

## Prompt 5 — Centrale rollback via feature flags

```
Bouw één centraal mechanisme om Reference Layer integraties uit te zetten zonder
code te deployen. Doel: als blijkt dat sprite-pipeline opeens slechte sprites
maakt door een Reference Layer regression, kun je via één commando alle builds
terug naar pre-Nova-Ref gedrag.

ARCHITECTUUR:

Eén Postgres-tabel als source of truth, gelezen door alle services. Bewust
geen LaunchDarkly of complexe feature-flag service — de flags zijn weinig en
de updates komen van jou via Telegram.

NIEUW SCHEMA:

1. nova-ref/sql/004_feature_flags.sql

   CREATE SCHEMA IF NOT EXISTS flags;
   
   CREATE TABLE flags.feature_flags (
       flag_name       TEXT PRIMARY KEY,
       enabled         BOOLEAN NOT NULL,
       updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       updated_by      TEXT NOT NULL,
       reason          TEXT
   );
   
   -- Initiële flags
   INSERT INTO flags.feature_flags (flag_name, enabled, updated_by, reason) VALUES
     ('reference_layer_global',       TRUE, 'system:init', 'Master kill switch'),
     ('sprite_pipeline_use_ref',      TRUE, 'system:init', 'Sprite pipeline lookup'),
     ('sprite_pipeline_send_feedback', TRUE, 'system:init', 'Sprite pipeline feedback events'),
     ('learn_pattern_application',    TRUE, 'system:init', 'Apply learned patterns in router');

NIEUWE SHARED LIBRARY:

2. nova-ref/src/nova_ref/core/flags.py
   
   class FlagClient:
       """In-memory cached flag reader, refresh elke 30s."""
       
       async def is_enabled(self, flag_name: str, default: bool = False) -> bool:
           # Check in-memory cache, refresh if stale
           # Bij DB-fout: return default (fail-safe gedrag)
       
       async def set(self, flag_name: str, enabled: bool, actor: str, reason: str):
           # UPDATE flags.feature_flags
           # Invalideer in-memory cache
           # Audit log via AuditLogger als die beschikbaar is
   
   Het belangrijke: bij DB-fout terug naar default. Default voor 
   'reference_layer_global' is TRUE (niet uitzetten op netwerkblip), default 
   voor 'sprite_pipeline_use_ref' is FALSE (conservative — als je niet zeker 
   weet, gebruik geen lookup).

INTEGRATIE IN NOVA-REF:

3. /lookup endpoint:
   - Eerste regel: check flag 'reference_layer_global'. Als FALSE: return 503
     met body {"status": "disabled", "reason": "..."}
   - Past consumers door middle gracefully om naar oude gedrag terug te vallen

INTEGRATIE IN SPRITE-PIPELINE:

4. sprite_pipeline/reference_client.py
   - Vóór elke lookup-call: check flag 'sprite_pipeline_use_ref'. Als FALSE: 
     skip lookup, return None (alsof er geen reference is)
   - Vóór elke feedback-call: check flag 'sprite_pipeline_send_feedback'. Als 
     FALSE: skip feedback emit
   
   Beide flags reads zijn cached lokaal voor 30s, dus geen latency-impact.

NIEUWE API ENDPOINTS (in nova-ref):

5. nova-ref/src/nova_ref/api/flags.py
   
   GET /flags
   → Lijst van alle flags met status
   
   GET /flags/{name}
   → Één flag detail
   
   PUT /flags/{name}
   Body: {"enabled": bool, "actor": str, "reason": str}
   → Update flag, schrijft audit
   → Vereist localhost-only middleware (zelfde patroon als andere /admin routes)

TELEGRAM-INTEGRATIE:

6. Voeg aan bestaande Nova Telegram bot toe (vermoedelijk in N8n of een aparte
   service — als pad onduidelijk: vraag mij eerst):
   
   Commando's:
   /flag list                                  → toon alle flags + status
   /flag off <name> <reason>                   → zet flag op false
   /flag on <name> <reason>                    → zet flag op true
   /flag panic                                 → zet 'reference_layer_global' op false
                                                  ('panic button' voor noodgevallen)
   
   Auth: alleen mijn (Alex's) chat-id mag deze commando's uitvoeren. Hardcode 
   chat-id check, geen rolesystem.

TESTS:

- test_global_flag_off_returns_503_on_lookup
- test_sprite_pipeline_skips_lookup_when_flag_off
- test_flag_change_audited
- test_flag_db_outage_returns_default
- test_flag_cache_refreshes_after_30s
- test_admin_endpoint_requires_bearer_token
- test_admin_endpoint_requires_localhost

VALIDATIE:

Smoke test scenario (handmatig):
1. Genereer sprite met flag aan → entity gebruikt
2. PUT /flags/sprite_pipeline_use_ref enabled=false
3. Wacht 35 seconden
4. Genereer zelfde sprite → geen entity, geen lookup-call in logs
5. Zet flag terug op true
6. Genereer → entity weer gebruikt

COMMIT MESSAGE:
"feat(flags): centralized feature flag system with Telegram control and panic switch"

NIET DOEN:
- Geen percentage-rollout features ("zet voor 10% van requests aan") — overkill
- Geen flags voor adapter-niveau toggles — daar is cache.adapter_status.enabled voor
- Geen integration met externe feature flag SaaS — Postgres is genoeg

PATCH voor Prompt 3 (idempotency):
- Voeg config toe: NOVA_REF_IDEMPO_TTL (default 60s, max 600s hard cap).

PATCH voor Prompt 4 (audit):
- Gebruik realistische X-Actor voorbeelden in docs/tests:
  "agent:sprite_pipeline", "human:alex_telegram", "system:backfill_job".
```

---

## Prompt 6 — Observability uitbreiding

```
Maak Reference Layer en Learning Agent gedegen waarneembaar. Doel: over een maand 
moet je niet hoeven raden waarom iets werkt of niet werkt. Logs, metrics en een 
basis-dashboard.

DRIE LAGEN:

LAAG 1 — Structured logging (al deels aanwezig, completeren)

1. Standaardiseer log structuur in nova-ref/src/nova_ref/core/logging.py
   
   Configureer structlog met deze processors:
   - structlog.contextvars.merge_contextvars       # request_id propagation
   - structlog.processors.add_log_level
   - structlog.processors.TimeStamper(fmt="iso")
   - structlog.processors.dict_tracebacks
   - structlog.processors.JSONRenderer()           # JSON output naar stdout
   
   Verplichte velden in elke log line:
   - timestamp (ISO 8601 UTC)
   - level (debug/info/warning/error)
   - service (nova-ref or nova-learn)
   - event (snake_case event name, e.g. "lookup.cache_hit")
   - request_id (als beschikbaar via ContextVar)
   
   Niet 'msg' als generieke string — gebruik event name + key/value pairs.

2. Middleware voor request_id (nova-ref/src/nova_ref/api/middleware.py):
   - Lees X-Request-ID header, of genereer UUIDv4 als afwezig
   - Set in ContextVar zodat alle logs binnen die request hem hebben
   - Echo terug in response header

LAAG 2 — Prometheus metrics

3. nova-ref/src/nova_ref/core/metrics.py
   
   Definieer (alleen wat je daadwerkelijk gaat lezen — geen vanity metrics):
   
   # Request niveau
   nova_ref_lookup_total{build, category, outcome}                    # counter
   nova_ref_lookup_duration_seconds{build, category}                  # histogram
   nova_ref_cache_hits_total{category}                                # counter
   nova_ref_cache_misses_total{category}                              # counter
   
   # Adapter niveau
   nova_ref_adapter_calls_total{adapter, outcome}                     # counter
   nova_ref_adapter_duration_seconds{adapter}                         # histogram
   nova_ref_adapter_health{adapter}                                   # gauge (0/1)
   
   # Router niveau (uit prompt 4 vorige fase)
   nova_ref_router_selections_total{adapter, position}                # counter
   
   # Database
   nova_ref_db_pool_connections_active                                # gauge
   nova_ref_db_pool_connections_idle                                  # gauge
   
   /metrics endpoint serveert in Prometheus exposition format.

4. Identieke set voor nova-learn:
   nova_learn_events_processed_total{outcome}
   nova_learn_dlq_messages_total                                      # gauge
   nova_learn_pattern_mining_duration_seconds                         # histogram (later, prompt zal nog komen)

LAAG 3 — Dashboard

5. infrastructure/grafana/dashboards/nova_reference_layer.json
   
   Een Grafana dashboard met deze panels (in deze volgorde):
   
   Row 1: Health
   - Lookup rate (req/sec)
   - Lookup p50 / p95 latency
   - Cache hit rate %
   - Active adapters (gauge sum)
   
   Row 2: Per build
   - Lookup rate per build (stacked area)
   - Success rate per build
   
   Row 3: Per adapter
   - Adapter call rate
   - Adapter latency p95
   - Adapter health status (table, één rij per adapter, kleur op gauge)
   
   Row 4: Errors
   - 5xx rate per adapter
   - Timeouts per adapter
   - DLQ size (van nova-learn)
   
   Geen alerting in Grafana zelf — dat doet Uptime Kuma. Dashboard is voor analyse,
   niet voor monitoring.
   
   Sla op als JSON, importable in Grafana via "Import dashboard" UI.

6. Uptime Kuma monitors (handmatig configureren, lever YAML/instructie):
   
   infrastructure/uptime_kuma/monitors.md met instructies:
   - PUSH monitor waar mogelijk; HTTP monitors alleen waar push niet kan.
   - HTTP monitor op http://nova-ref:8400/health (interval 60s)
   - HTTP monitor op http://nova-ref:8400/ready (interval 60s, kritischer)
   - HTTP monitor op http://nova-learn:8401/health (interval 60s)
   - HTTP monitor op http://nova-learn:8401/ready (interval 60s)
   - Push monitor 'backup_completed' (heartbeat van backup script)
   - Telegram notification kanaal koppelen aan al deze monitors

INTEGRATIE met bestaande nova-ref code:

7. Update belangrijkste paden om metrics te emitteren:
   - lookup endpoint: increment counter, observeer duration
   - elke adapter call (in BaseAdapter): increment counter, observeer duration
   - elke router-decision: increment counter
   - elke cache hit/miss: increment counter

TESTS:

- test_metrics_endpoint_serves_prometheus_format:
  GET /metrics → Content-Type text/plain, bevat # HELP en # TYPE lines
- test_lookup_increments_counter:
  doe 3 lookups, /metrics toont nova_ref_lookup_total{...}=3
- test_request_id_propagation:
  send request met X-Request-ID=abc, alle log lines tijdens die request 
  hebben request_id="abc"
- test_request_id_generated_when_missing:
  geen header → response heeft X-Request-ID met valide UUID

VALIDATIE:

Handmatige smoke:
1. Doe 50 lookups via een loop-script
2. Open Grafana dashboard, importeer JSON
3. Verifieer dat alle panels data tonen
4. Trigger handmatige adapter failure (zet wikidata_endpoint naar localhost:9999)
5. Verifieer dat error rate panel kleurt

COMMIT MESSAGE:
"feat(observability): structured logging, Prometheus metrics, Grafana dashboard, Uptime Kuma monitors"

NIET DOEN:
- Geen Loki/Elasticsearch nu — JSON-naar-stdout is genoeg, Docker logs is je 
  log aggregator voor MVP
- Geen distributed tracing (Jaeger, Tempo) — overkill voor deze schaal
- Geen custom Grafana plugins — alleen built-in panels
- Geen alerting rules in Prometheus — Uptime Kuma is je alert kanaal

NIEUWE TOEVOEGING — Operational README:
- Maak C:\nova\OPERATIONAL_README.md met:
  - credentials locaties
  - start/stop volgorde services
  - restore procedure
  - monitor checklist bij incidenten
  - contact en DR scenario's
```

---

## BIJLAGE — Niet-code acties (jij doet, niet Cursor)

Deze drie dingen kun je zelf doen, parallel aan of tussen de prompts. Ze hebben geen code nodig maar wél bewuste aandacht.

### A. Schrijf een Nova design-doc

Maximaal twee A4. Niet meer. In `/opt/nova/docs/NOVA_DESIGN.md`. Bevat:

- **Wat is Nova** — één paragraaf. Niet "een AI platform" — concreet.
- **Voor wie** — jij, jouw werk bij Buro Hollema, jouw Surilians-project. Niet "voor iedereen".
- **Wat doet Nova wel** — drie tot vijf categorieën taken. Bijvoorbeeld: GIS-kaartautomatisering, sprite-generatie met referentiedata, worldbuilding-assistentie, agent-orchestratie.
- **Wat doet Nova bewust niet** — minstens vijf dingen. Bijvoorbeeld: geen real-time chatbot voor klanten, geen training van eigen modellen, geen autonomous agents zonder menselijke approval, geen code production deploys, geen financiële transacties.
- **De drie principes** — kies drie korte regels die conflicten oplossen wanneer features onderling botsen. Suggestie: (1) observability boven features, (2) restartbaar boven elegant, (3) leesbaar boven slim.

Lees dit document elke eerste van de maand opnieuw. Update alleen met goeie reden.

### B. Definieer pilot-succescriteria

Vóór je sprite-pipeline pilot start, schrijf in `/opt/nova/docs/PILOT_CRITERIA.md`:

- **Duur**: exact 14 dagen, geen verlenging
- **Concreet meetbaar**: cache hit rate >70% bij steady state, p95 lookup latency <500ms, ten minste 5 succesvolle build_runs met quality_score>=0.8 per dag, geen onverklaarde nova-ref crashes
- **Go/no-go criterium**: als alle bovenstaande gehaald → tweede build aansluiten. Als één faalt → diagnose, fix, opnieuw 14 dagen.
- **Wat je NIET meet als succes**: tevredenheid ("ziet er beter uit"), aantal features, lijntjes code

Dit document staat boven je gevoel als beslismoment komt. Anders schuif je de deadline op.

### C. Surilians Codex naar git

Niet nu in code; wel in workflow:

```bash
cd /opt/nova/codex/surilians
git init
git add .
git commit -m "Initial Surilians worldbuilding canon, version snapshot"
git remote add origin <jouw-private-repo-of-keuze>  # GitLab self-hosted of Gitea op Hetzner
git push -u origin main
```

Workflow vanaf nu: edit een markdown-bestand → commit → push. Reference Layer leest read-only uit de map. Sudowrite kan gewoon files openen. Branches voor "wat-als" scenarios, tags voor canonical versies per gepubliceerd hoofdstuk.

Optioneel: voeg een pre-commit hook toe die markdown-syntax valideert (frontmatter aanwezig, geen broken internal links). Klein scriptje in `/opt/nova/codex/surilians/.git/hooks/pre-commit`.

---

## SLOT

Zes prompts, zes commits, zes groene CI-runs. Plus drie handmatige acties die je zonder Cursor doet.

Volgorde-discipline: niet vooruitlopen, niet samenvoegen, niet "ik heb nog tijd dus ik doe ook even...". Bij twijfel stoppen en mij raadplegen.

Na deze fase 6 is Reference Layer productiewaardig en kun je rustig laten meedraaien terwijl je je sprite-pipeline pilot evalueert. Pas dan komt fase 7 (pattern miner activeren, tweede build aansluiten, eventueel embedding-zoek service afsplitsen).
