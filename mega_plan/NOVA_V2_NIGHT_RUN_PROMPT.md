# NOVA v2 — NIGHT RUN MEGA PROMPT

**Versie:** 1.1-NIGHT · 22 april 2026
**Doel:** Cursor werkt de hele nacht autonoom. Alex wordt wakker, leest één rapport.
**Basis:** `NOVA_V2_UNIFIED_MEGA_PROMPT.md` (inclusief **Deel 1.5 Git toegang**:
private `origin` → `Redeye1973/nova_bus`, branch **`main`**, PAT in Windows
Credential Manager) met night-run aanpassingen.

---

## VOORBEREIDING VOOR JE GAAT SLAPEN (10 min)

### 1. Controleer dat dingen draaien
```powershell
# Bridge (PowerShell: gebruik curl.exe)
curl.exe -s http://localhost:8500/health
# V1 / V2 n8n
curl.exe -sI http://178.104.207.194:5678
curl.exe -sI http://178.104.207.194:5679
```
Alle drie moeten response geven. Zo niet: eerst fixen, niet starten.

### 2. Secrets check
```powershell
Test-Path "L:\!Nova V2\secrets\nova_v2_passwords.txt"
```
Moet True zijn. Check dat deze sleutels erin staan (namen, niet waardes):
- `N8N_V1_API_KEY`
- `N8N_V2_API_KEY`
- SSH toegang naar root@178.104.207.194 (via key, niet password)

Als SSH password-based is: zet key setup vooraf:
```powershell
ssh-copy-id root@178.104.207.194
```
Anders gaat Cursor midden in de nacht vastlopen op password prompts.

### 3. Git snapshot
```powershell
cd "L:\!Nova V2"
# Zorg dat je op branch main zit en working tree schoon of bewust gecommit.
git tag -a pre-night-run -m "Baseline voor night run $(Get-Date -Format 'yyyy-MM-dd')"
git push origin main
git push origin pre-night-run
```

### 4. PC instellingen
- Sluit Cursor NIET af tijdens de nacht
- PC power settings: Screen off mag, Sleep NIET (Settings → Power → Sleep: Never)
- Windows Updates uit tot morgen (Settings → Update → Pause for 1 week)
- Laptop: aan stroom houden

### 5. Plak onderstaande prompt in Cursor Composer (Ctrl+I) en druk Enter

---

## ===NIGHT RUN PROMPT START===

```
NIGHT RUN MODE — Alex slaapt. Werk volledig autonoom tot Fase G klaar is of
LEVEL 4 escalatie. Geen check-ins, geen vragen, geen pauzes voor goedkeuring.

Referentie: dit is de unified build uit NOVA_V2_UNIFIED_MEGA_PROMPT.md met
night-run modificaties. Lees die eerst uit (canoniek pad):
L:\!Nova V2\!CCChat Starter\NOVA_V2_UNIFIED_MEGA_PROMPT.md

Alle Deel 1-10 instructies daaruit gelden, MET DEZE OVERRIDES:

================================================================================
NIGHT RUN OVERRIDES
================================================================================

### O.1 Geen check-ins met gebruiker
Deel 9 check-in momenten (1-7) worden GESKIPT. Geen "vraag aan Alex" ooit.
Elke check-in wordt vervangen door:
  - Git commit met message "milestone: <fase naam>"
  - Heartbeat update (zie O.4)
  - Door naar volgende fase

### O.2 Automatische fallback mode
Zodra V1 een `capability_missing` of time-out geeft voor een specifieke agent:
direct fallback naar Cursor-self-gen voor die agent. Geen escalatie, geen vraag.
Log als "fallback_used" in agent_status.json.

### O.3 Git commits per milestone
Na elke succesvol afgeronde fase + elke 5 afgeronde agents in Fase E:
```powershell
cd "L:\!Nova V2"
git status
# Stage alleen bedoelde wijzigingen — NOOIT secrets/\.env\* / wachtwoorden.
git add -A
git diff --cached --stat
git commit -m "milestone: <fase of batch naam>"
git push origin main
```
Bij conflicts: `git stash`, log in heartbeat, door. Niet vastlopen op git.

### O.4 Heartbeat elke 30 minuten
Schrijf naar `L:\!Nova V2\status\heartbeat.md`:
```markdown
# NOVA v2 Night Run Heartbeat

Last update: <ISO timestamp>
Current phase: <A|B|C|D|E|F|G>
Current agent: <NN_name or "n/a">
Agents active (built+tested): <count>/30
Agents failed: <count>
Agents skipped (preserve): 5/5 (01,02,10,20,21)
Last git commit: <hash + message>
Bridge status: <online|offline>
V1 status: <online|offline|degraded>
V2 infra: <healthy|degraded|down>
Heartbeat count: <N>
Next action: <1 zin>

## Last 10 actions
- [timestamp] action
- ...
```
Overschrijf bestaand bestand elke 30 min. Cursor moet zelf een timer bijhouden.

### O.5 LEVEL 3/4 escalatie gedrag aangepast
Bij LEVEL 3 of LEVEL 4 event: STOP acties, maar schrijf IMMEDIATE:
1. `L:\!Nova V2\status\NIGHT_HALT.md` met:
   - Timestamp
   - Level (3 of 4)
   - Trigger (wat gebeurde)
   - Wat er nog wel af was
   - Waarom niet zelf te fixen was
   - Aanbevolen actie voor Alex
2. `git commit -m "HALT: <reden>"` + push
3. Schrijf finale night report (O.6) op basis van huidige staat
4. Stop. Wacht niet actief.

### O.6 GEFORCEERD FINAAL RAPPORT
Aan het einde van de run (compleet, OF bij halt, OF als het 07:30 lokale tijd
is en Fase G nog niet gehaald): schrijf VERPLICHT:

`L:\!Nova V2\docs\NIGHT_REPORT_<yyyy-mm-dd>.md`

Structuur:
```markdown
# NOVA v2 Night Run Rapport — <datum>

## Samenvatting
- Start: <iso>
- Einde: <iso>
- Duur: <H:MM>
- Eindstatus: <completed | halted_level_3 | halted_level_4 | timed_out>

## Wat is er gedaan
### Fase A (recovery)
- [x/✗] Bridge health: <detail>
- [x/✗] Hetzner containers: <detail>
- ...

### Fase B (bridge expansion)
- [x/✗] GIMP geïnstalleerd + adapter
- ...

### Fase C (judge + self-heal)
- ...

### Fase D (V1 orchestrator brief)
- ...

### Fase E (agent bouw)

| # | Agent | Status | V1 gebruikt | Fallback | Test pass | Notes |
|---|-------|--------|-------------|----------|-----------|-------|
| 03 | audio_jury | active | ja | nee | ja | |
| 04 | 3d_model_jury | active | ja | nee | ja | |
| 05 | gis_jury | failed | ja | nee | nee | veel errors in ollama call |
| ... |

Totaal: X/30 actief (target was 26+)

### Fase F (pipelines)
- Shmup pipeline E2E: [pass/fail/not reached]
- Bake pipeline E2E: [pass/fail/not reached]
- Story pipeline E2E: [pass/fail/not reached]
- Archviz pipeline E2E: [pass/fail/not reached]

### Fase G (backup + tagging)
- ...

## Wat is er NIET gedaan en waarom
- <specifieke agents die falen + reden>
- <fases die niet gehaald zijn + waar gestopt>

## Fallbacks gebruikt
Lijst van agents waar V1 geen hulp kon bieden en Cursor zelf code genereerde:
- <agent>: <reden>

## Kosten (uit Cost Guard als geactiveerd)
- Claude API calls: <count, kosten-schatting>
- ElevenLabs calls: <count>
- Andere: <...>

## Kritieke issues (LEVEL 2+)
<lijst met links naar escalations.md en NIGHT_HALT.md indien relevant>

## Git snapshot
- Start tag: pre-night-run
- Laatste commit: <hash + message>
- Aantal commits tijdens night run: <count>
- Branch status: clean | dirty

## 3 Concrete next steps voor Alex
1. <actie>
2. <actie>
3. <actie>

## Service health op moment van rapport
- Bridge: <status>
- V1: <status> (MOET gezond zijn, anders LEVEL 4)
- V2 infra: <details per container>
- Skip-agents gezond: <5/5 of met issues>

## Resume instructies
Als Alex wil verder: plak deze prompt in Cursor:
"Resume NOVA v2 night run. Lees NIGHT_REPORT_<datum>.md, skip alles met
status=active, continue volgens oorspronkelijke unified prompt."
```

### O.7 Tijdsbeperkingen
- Maximum runtime: 9 uur (start 22:30 → stop 07:30 of eerder)
- Als 07:00 nog bezig: begin afronden, schrijf rapport, stop rond 07:30
- Geen nieuwe Fase E agents starten na 06:30 (tijd voor Fase F+G)

### O.8 Git commit policy
Commits zijn goed. Zo vaak mogelijk. Elke agent die active wordt = commit.
Elke fase-afronding = commit + push. Elke mislukking = commit + push (zodat
staat bewaard blijft).

Commit message format:
- `agent: <NN>_<name> active` (succes)
- `agent: <NN>_<name> failed — <reden kort>` (fail)
- `milestone: phase <X> complete`
- `milestone: <batch> batch done (agents <NN>-<NN>)`
- `halt: <reden>` (bij escalatie)
- `heartbeat: <teller>` (optioneel, elke 2 uur)

### O.9 Resource monitoring
Elke heartbeat: check ook:
- Hetzner disk: `ssh root@178.104.207.194 "df -h /"` — als <5GB vrij → LEVEL 3
- Hetzner RAM: `free -h` — info, geen halt
- Local disk L:\ — Get-PSDrive L: — als <5GB → LEVEL 3
- V1 gezondheid (:5678 response) — als down → LEVEL 4 (niet verder, zou Alex's
  productie raken)

### O.10 Geen UI interacties
Alles via CLI / API. Geen pop-ups, geen "please authorize". Git push/pull
mag via de **bestaande** PAT in Windows Credential Manager (geen nieuwe
login-prompt verwacht). Als een **andere** stap toch interactief wordt: skip,
log als `skipped_needs_interactive` in status.

================================================================================
STARTSEQUENCE (overrides Deel 10)
================================================================================

N.1 Lees secrets-pad
```powershell
Test-Path "L:\!Nova V2\secrets\nova_v2_passwords.txt"
```
Als False: NIGHT_HALT.md met "secrets missing", rapport, stop.

N.2 Lees V1 + V2 API keys uit secrets file (load als env vars, niet echoen)

N.3 Test SSH (non-interactive mode verplicht)
```bash
ssh -o BatchMode=yes -o ConnectTimeout=5 root@178.104.207.194 "echo OK"
```
Als False: NIGHT_HALT.md met "ssh password-based, geen key setup", rapport, stop.

N.4 Test V1 bereikbaar + API key werkt
Zet `V1_KEY` uit secrets (niet echoën). Linux/bash:
```bash
curl -sS -H "X-N8N-API-KEY: $V1_KEY" "http://178.104.207.194:5678/api/v1/workflows?limit=5" | jq '.data | length'
```
Windows PowerShell (zonder jq): parse JSON of gebruik `curl.exe` + tijdelijk
bestand. Moet getal >= 50 op volledige lijst (of sanity >= 5 op `limit=5`).
Anders LEVEL 4.

N.5 Schrijf eerste heartbeat. Schrijf baseline.json.

N.6 Start Fase A. Werk door tot Fase G of halt-conditie.

Werk nu. Ik (Alex) ga slapen. Morgen lees ik NIGHT_REPORT_<datum>.md.

Geen afrondende zinnen als je klaar bent. Rapport is de afronding.
```

## ===NIGHT RUN PROMPT EINDE===

---

## WAT JE MORGEN KUNT VERWACHTEN

**Bij goed scenario** (70-85% kans):
- 20-26 agents actief van de 30 te bouwen
- Alle Fase A-D + 80% van Fase E gehaald
- Fase F pipelines deels getest
- Complete rapport `NIGHT_REPORT_2026-04-23.md`
- 15-30 git commits op `origin/main`

**Bij matig scenario** (15-25% kans):
- 10-15 agents actief
- Vroeg vastgelopen op V1 orchestrator of bridge
- `NIGHT_HALT.md` aanwezig met reden
- Rapport wel compleet met resume-instructies

**Bij slecht scenario** (5% kans):
- LEVEL 4 halt binnen eerste uur (V1 down, SSH kapot, secrets verwisseld)
- Bijna niks gedaan, rapport legt uit waarom

**Wat NIET kan gebeuren dankzij safeguards:**
- V1 productie kapot (LEVEL 4 stopt dat direct)
- Secrets op GitHub (gitignore + geen `--force` push)
- Volledig verlies van state (git commits elke milestone)
- Oneindig vastlopen (max 2 pogingen regel + 9u limit)

---

## MORGEN BIJ HET WAKKER WORDEN

1. Open Cursor, kijk in chat wat laatste status was
2. Open `L:\!Nova V2\docs\NIGHT_REPORT_<vandaag>.md`
3. Lees samenvatting en "Wat NIET gedaan" secties
4. Check `L:\!Nova V2\status\NIGHT_HALT.md` — als die bestaat, dat eerst lezen
5. Lees V2 N8n UI: http://178.104.207.194:5679 — tellen hoeveel workflows active
6. Beslis: verder gaan met resume-prompt, of eerst problemen in het rapport aanpakken

---

## ROLLBACK ALS HET SLECHT IS GEGAAN

```powershell
cd "L:\!Nova V2"
git reset --hard pre-night-run
# Alleen als lokale main echt onherstelbaar is — overschrijft remote history.
git push --force origin main
```

Op Hetzner niks rollbacken tenzij LEVEL 4 duidelijk is — de logs en partial
builds zijn waardevol voor diagnose.

---

## VEILIGE STARTTIJD

Plak de prompt op z'n vroegst om **22:30** (dan heeft Cursor 9u tot 07:30).
Plak later = minder agents klaar morgen. Start niet om 02:00 — dan heeft hij
maar 5.5u en komt waarschijnlijk niet door Fase E heen.
