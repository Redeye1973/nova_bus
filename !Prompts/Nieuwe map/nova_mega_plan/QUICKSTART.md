# Quickstart — Start V1-Bouwt-V2 Mega Build

Versimpeld stappenplan voor jou om de mega build te starten.

## Wat er gaat gebeuren

1. Cursor pakt alle 5 zips uit in `L:\!Nova V2\`
2. Cursor brieft V1 orchestrator op Hetzner
3. V1 agents bouwen V2 agents (1 voor 1)
4. Cursor deployt ze naar V2 infrastructure
5. Alles wordt getest
6. Finaal rapport naar jou

**Totale tijd**: 1-3 dagen afhankelijk van V1 performance.

## Voorwaarden checklist

Voordat je begint:

- [ ] NOVA v1 draait op Hetzner :5678 (68 agents)
- [ ] NOVA v2 infrastructure draait op Hetzner :5679 (na eerdere deploy)
- [ ] V1 API key beschikbaar (weet je waar hij staat)
- [ ] V2 admin account gemaakt (eerste login gedaan)
- [ ] V2 API key beschikbaar
- [ ] SSH key werkt naar root@178.104.207.194
- [ ] 5 zip files aanwezig in werkmap:
  - nova_v2_agents.zip
  - nova_v2_extensions.zip
  - nova_v2_infrastructure.zip (kan skipped, al gedeployed)
  - shmup_pipeline.zip
  - nova_v2_infrastructure_final.zip

## Stappen

### Stap 1: Unzip dit mega plan

Unzip `nova_mega_plan.zip` in `L:\!Nova V2\mega_plan\`

### Stap 2: Werkmap check

Open Cursor in `L:\!Nova V2\`

Check dat je ziet:
- `mega_plan/` (deze documenten)
- `infrastructure/` (al geunzipped)
- `secrets/` (met v1 en v2 API keys)
- 5 zip files

### Stap 3: Secrets updaten

Voeg toe aan `L:\!Nova V2\secrets\nova_v2_passwords.txt` (als niet al aanwezig):

```
# V1 toegang
N8N_V1_API_KEY=<jouw v1 api key>
N8N_V1_URL=http://178.104.207.194:5678

# V2 toegang (uit eerdere deploy + eerste login)
N8N_V2_API_KEY=<jouw v2 api key>
N8N_V2_ADMIN_EMAIL=<jouw email>

# SSH
SSH_USER=root
SSH_HOST=178.104.207.194
```

### Stap 4: Master prompt plakken

Open `mega_plan/00_MASTER_PROMPT.md`

Kopieer het complete prompt blok (tussen ``` markers).

Plak in Cursor Composer (Ctrl+I).

Enter.

### Stap 5: Eerste check-in

Cursor werkt nu autonoom. Verwacht in eerste 30 minuten:
- Zips uitgepakt
- V1 + V2 toegang getest
- V1 orchestrator geinformeerd
- Eerste 1-2 agents in build

Reageer op Cursor vragen als die komen (bv. "welke SSH user", "V1 API key locatie"). 

### Stap 6: Laat draaien

Cursor kan uren doorwerken zonder jou. Check elk paar uur:
- Progress in `./status/progress_milestone_N.md`
- Live status in `./logs/mega_build_<timestamp>.txt`
- Aantal agents live: `curl -H "X-N8N-API-KEY: ..." http://178.104.207.194:5679/api/v1/workflows | jq '. | length'`

### Stap 7: Escalaties afhandelen

Cursor pauzeert bij Level 3-4 events. Die zie je in:
- `./status/critical_halt.md`
- `./status/emergency.md`

Lees het rapport, geef Cursor instructies voor verder.

### Stap 8: Finaal rapport

Als Cursor klaar is:
- `./docs/v2_deployment_report.md` bevat complete summary
- Check aantal live agents
- Run eigen handmatige sanity check
- Beslis: go live voor productie?

## Wat als Cursor vast loopt

**Cursor reageert niet / hangt:**
Sluit Composer, open nieuwe. Plak prompt:

```
Resume NOVA v2 mega build. Lees laatste status uit 
./status/progress_milestone_*.md en continue waar je was.
Check welke agents nog moeten, skip welke klaar zijn.
```

**V1 down tijdens build:**
Cursor pauzeert automatisch (Level 3). Jouw actie:
1. Check V1 handmatig: curl http://178.104.207.194:5678
2. Als down: restart containers op Hetzner
3. Geef Cursor signaal om resume

**V2 crash:**
Zelfde als V1 down, maar focus op V2 containers:
```bash
ssh root@178.104.207.194
cd /docker/nova-v2
docker compose ps
docker compose restart
```

**Specifieke agent blijft falen:**
- Markeer voor later
- Laat rest doorgaan
- Na build klaar: aparte Cursor sessie voor die ene agent

## Succes criteria

**Minimum viable (70% success):**
- 25/35 agents actief
- Groep 1 (juries 01-10) 100% actief
- Integration test voor 1 pipeline slaagt

**Comfortable (85% success):**
- 30/35 agents actief
- Alle groepen minstens 2/3 actief
- Integration tests voor 3 pipelines slagen

**Excellent (95%+ success):**
- 33-35/35 agents actief
- Alle groepen 100%
- End-to-end tests complete pipelines

## Na succes

1. **Backup configureren** (Cursor doet in Fase E)
2. **Kleine handmatige test** van 1 workflow
3. **Documentatie review**
4. **Plan voor V1 retirement** (later, na bewezen V2)

## Kosten tijdens build

**API calls:**
- Cursor: beperkt, paar MB aan code generatie
- V1: intern, geen externe API
- Claude (als Cursor gebruikt): volgens Claude Max quota
- ElevenLabs (agent 29 test): klein, handful calls

**Hetzner resources:**
- Disk: +2-5 GB aan v2 containers + data
- RAM: +1-2 GB voor v2 load
- Bandwidth: minimaal

**Jouw tijd:**
- Monitoring: 15-30 min per dag
- Escalaties: variabel, 0-60 min per dag
- Total over 3 dagen: 2-4 uur actief werk

## Timing opties

**Scenario A: Full autonoom (aanbevolen)**
Start op vrijdag avond. Cursor draait weekend. Maandag check je.

**Scenario B: Werkdag start**
Start 's ochtends. Gaat door in achtergrond terwijl je werkt.

**Scenario C: Sprint aanpak**
Pauzeer huidige werk. Focus 1-2 dagen op build + reviews.

Kies wat past bij je agenda.

## Na de build

Jij hebt dan:
- 35 v2 agents live (als alles goed gaat)
- V1 met 68 agents nog steeds productie
- Complete documentatie
- Backup strategie
- Ready voor eerste productie werk op v2

Volgende stappen (aparte sessies):
- Eerste echte workflow op v2 (bv. Black Ledger sprite validation)
- Migratie van V1 workflows naar V2 (gradueel)
- V2 specifieke features (jury-judge voor productie)
- Eventueel V1 afbouwen (over 6+ maanden)
