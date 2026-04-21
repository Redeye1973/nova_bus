# Fase 3-4 Prompt: Secrets + .env bouwen (zonder SSH)

Voor gebruik nadat Fase 1 al is uitgevoerd en voordat SSH beschikbaar is.

## Wat deze prompt doet

- Genereert 6 strong passwords lokaal
- Slaat op in `L:\!Nova V2\secrets\nova_v2_passwords.txt`
- Bouwt `L:\!Nova V2\infrastructure\.env` op basis van `.env.template`
- Valideert dat alle `CHANGE_ME` placeholders zijn vervangen
- Logt voortgang naar `logs/deploy_log.txt`
- Toont NOOIT secrets in chat

Fase 5-8 (SSH/upload/deploy) worden NIET uitgevoerd.

## De prompt voor Cursor

Plak dit in Cursor Composer:

```
Voer NOVA v2 Fase 3-4 lokaal uit. Fase 5-8 pauzeer tot ik SSH credentials aangeef.

CONTEXT:
- Werkmap: huidige Cursor working directory (L:\!Nova V2\)
- Structuur plat: infrastructure/docker-compose.yml (GEEN docker/ submap)
- Fase 1 is klaar: logs/ en secrets/ folders bestaan al
- Stappenplan staat in infrastructure/DEPLOY_STAPPENPLAN.md of vergelijkbaar

== FASE 3: SECRETS GENEREREN ==

3.1 Genereer 6 sterke passwords via PowerShell:

Voor base64 passwords (POSTGRES_PASSWORD, POSTGRES_NON_ROOT_PASSWORD, 
REDIS_PASSWORD, MINIO_ROOT_PASSWORD):

$bytes = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$password = [Convert]::ToBase64String($bytes)

Voor hex secrets (N8N_ENCRYPTION_KEY, N8N_JWT_SECRET):

$bytes = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$hex = ($bytes | ForEach-Object { $_.ToString('x2') }) -join ''

Alternatief: als openssl aanwezig is in WSL of Git Bash, gebruik:
- openssl rand -base64 32
- openssl rand -hex 32

3.2 Schrijf secrets file naar L:\!Nova V2\secrets\nova_v2_passwords.txt

Formaat (vul gegenereerde waardes in):

# NOVA v2 Secrets - Gegenereerd: [ISO timestamp]
# NIET committen, NIET delen, NIET in chat tonen

# PostgreSQL (N8n backend)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<base64_32_1>
POSTGRES_DB=n8n_v2
POSTGRES_NON_ROOT_USER=n8n_user
POSTGRES_NON_ROOT_PASSWORD=<base64_32_2>

# Redis (queue + cache)
REDIS_PASSWORD=<base64_32_3>

# N8n
N8N_HOST=178.104.207.194
N8N_PORT=5679
N8N_PROTOCOL=http
WEBHOOK_URL=http://178.104.207.194:5680/
N8N_ENCRYPTION_KEY=<hex_32_1>
N8N_JWT_SECRET=<hex_32_2>

# MinIO
MINIO_ROOT_USER=nova_admin
MINIO_ROOT_PASSWORD=<base64_32_4>

# URLs na deploy
N8N_MAIN_URL=http://178.104.207.194:5679
N8N_WEBHOOK_URL=http://178.104.207.194:5680
MINIO_CONSOLE=http://178.104.207.194:9001
QDRANT_URL=http://178.104.207.194:6333

# API Key wordt later toegevoegd:
# N8N_V2_API_KEY=<in te vullen na eerste N8n login>

3.3 Set Windows file permissies restrictief:

icacls "L:\!Nova V2\secrets\nova_v2_passwords.txt" /inheritance:r
icacls "L:\!Nova V2\secrets\nova_v2_passwords.txt" /grant:r "$env:USERNAME:F"

Dit zorgt dat alleen huidige user het bestand kan lezen.

3.4 Valideer secrets file:
- Bestand bestaat
- Alle 6 gegenereerde waardes zijn ingevuld (geen lege strings)
- Geen <placeholder> tags over
- File size > 500 bytes (redelijke inhoud)

== FASE 4: BOUW INFRASTRUCTURE/.env ==

4.1 Kopieer template:
Copy-Item infrastructure\.env.template infrastructure\.env

4.2 Lees gegenereerde passwords uit secrets file (in-memory, niet in log).

4.3 Vervang alle CHANGE_ME placeholders in infrastructure\.env met gegenereerde waardes.

Gebruik regex-based replacement:
- CHANGE_ME_STRONG_PASSWORD_32_CHARS → $POSTGRES_PASSWORD
- CHANGE_ME_ANOTHER_STRONG_PASS_32 → $POSTGRES_NON_ROOT_PASSWORD
- CHANGE_ME_REDIS_PASSWORD_32_CHARS → $REDIS_PASSWORD
- CHANGE_ME_64_CHAR_HEX_STRING (eerste) → $N8N_ENCRYPTION_KEY
- CHANGE_ME_64_CHAR_HEX_STRING (tweede) → $N8N_JWT_SECRET
- CHANGE_ME_STRONG_PASSWORD_32_CHARS (laatste voor MinIO) → $MINIO_ROOT_PASSWORD

4.4 Validatie:
- Run: (Get-Content infrastructure\.env) -match "CHANGE_ME"
- Resultaat moet leeg zijn (geen CHANGE_ME meer)
- Check alle 13 expected variables aanwezig:
  POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_NON_ROOT_USER,
  POSTGRES_NON_ROOT_PASSWORD, REDIS_PASSWORD, N8N_HOST, N8N_PORT,
  N8N_PROTOCOL, WEBHOOK_URL, N8N_ENCRYPTION_KEY, N8N_JWT_SECRET,
  MINIO_ROOT_USER, MINIO_ROOT_PASSWORD

4.5 Set Windows permissies op .env:
icacls "infrastructure\.env" /inheritance:r
icacls "infrastructure\.env" /grant:r "$env:USERNAME:F"

4.6 Voeg infrastructure/.env toe aan .gitignore (als nog niet staat):
Check eerst of infrastructure/.gitignore .env al bevat.
Zo niet: append ".env" aan file.

== LOGGING ==

Schrijf naar L:\!Nova V2\logs\deploy_log.txt (APPEND, niet overschrijven):

[ISO timestamp] | 3.1 | Passwords generated | SUCCESS (6 secrets)
[ISO timestamp] | 3.2 | Secrets file written | SUCCESS (L:\!Nova V2\secrets\nova_v2_passwords.txt)
[ISO timestamp] | 3.3 | Permissions set | SUCCESS (user-only)
[ISO timestamp] | 3.4 | Validation passed | SUCCESS
[ISO timestamp] | 4.1 | .env template copied | SUCCESS
[ISO timestamp] | 4.2 | Passwords loaded | SUCCESS (in-memory)
[ISO timestamp] | 4.3 | Placeholders replaced | SUCCESS (6 replacements)
[ISO timestamp] | 4.4 | No CHANGE_ME remaining | SUCCESS
[ISO timestamp] | 4.5 | .env permissions set | SUCCESS
[ISO timestamp] | 4.6 | .gitignore updated | SUCCESS/SKIPPED (reeds aanwezig)

BELANGRIJK: Log GEEN secrets, alleen success/fail status.

== RAPPORT IN CHAT ==

Toon alleen:
- Success / Fail per stap
- Locatie van secrets file
- Locatie van .env file
- File sizes (validation dat inhoud aanwezig is)
- "Klaar voor Fase 5-8 zodra SSH user beschikbaar"

TOON GEEN WACHTWOORDEN OF KEYS IN CHAT.

== STOPPEN NA FASE 4 ==

Na successful Fase 4:
- Niet proberen SSH te maken
- Niet uploaden naar Hetzner
- Niet docker commando's uitvoeren
- Wacht op mijn instructie met SSH user

Ga aan de slag met Fase 3 en 4. Rapporteer wanneer klaar.
```

## Wat je krijgt na deze prompt

**Op schijf:**
- `L:\!Nova V2\secrets\nova_v2_passwords.txt` — 6 sterke passwords
- `L:\!Nova V2\infrastructure\.env` — volledig ingevuld, geen CHANGE_ME
- `L:\!Nova V2\logs\deploy_log.txt` — voortgang gelogd

**In chat:**
- Bevestiging per stap
- File locaties
- Geen secrets zichtbaar

## Voor jou om parallel te doen

Terwijl Cursor Fase 3-4 afwerkt, test SSH handmatig in een nieuwe PowerShell:

```powershell
ssh root@178.104.207.194
```

Probeer `root` eerst. Als dat werkt: je bent in Hetzner terminal. Type `exit`.

Als `root` niet werkt: probeer andere users die je eerder hebt gebruikt voor v1 deploy.

Zodra je SSH user weet: verdere prompt om Fase 5-8 te starten.

## Vervolgprompt (Fase 5-8, na SSH test)

Als SSH werkt en Fase 3-4 klaar is:

```
SSH user is [jouw_user]. Fase 3-4 is klaar (.env gevuld, secrets opgeslagen).
Voer nu Fase 5-8 uit uit DEPLOY_STAPPENPLAN.md:
- Upload infrastructure/ content naar /docker/nova-v2/ op Hetzner
- docker compose pull + up -d
- Health validatie
- Firewall (5679, 5680, 9001)
- V1 niet raken
- Rapport naar logs/
```

Cursor heeft dan alle context en kan doorgaan.
