# Error Escalation Protocol

Wanneer Cursor moet stoppen en jou erbij halen, versus zelf doorgaan.

## Escalation levels

### Level 1: Log en doorgaan
Cursor hoeft niet te stoppen, documenteert in logs.

Voorbeelden:
- Agent faalt met standaard issue (fix via retry)
- Tijdelijke netwerk hiccup (retry succeeded)
- Kleine inconsistentie in agent spec (Cursor fixt zelf)
- Warning van V1 die niet kritiek is

Actie Cursor: Log, go on, include in final report.

### Level 2: Pauzeer en rapporteer
Cursor pauzeert, schrijft report, wacht niet actief maar continue in ander gebied.

Voorbeelden:
- Één agent faalt na 2 retries
- V1 geeft capability_missing response (specifiek voor 1 agent)
- Non-kritieke dependency ontbreekt (bv. optional library)
- Test slaagt niet maar agent deployt wel

Actie Cursor: 
- Mark agent als "needs_manual_review"
- Schrijf naar ./status/escalations.md
- Ga door met andere agents
- Aan einde: toon lijst aan gebruiker

### Level 3: Stop en wacht
Cursor stopt actief werk, wacht op jou.

Voorbeelden:
- V1 productie workflows falen (v1 zelf breekt)
- Hetzner server down
- V2 infrastructure down
- Secrets file corrupted/missing
- Disk space kritiek laag
- V1 orchestrator niet meer responsive

Actie Cursor:
- Stop alle nieuwe tasks
- Huidige taken laten afronden
- Alert naar mij via Telegram/Discord (als configured) of console
- Schrijf critical_halt.md met details
- Wacht op mijn input

### Level 4: Emergency rollback
Cursor rolt automatisch terug.

Voorbeelden:
- V1 agents zijn geraakt door v2 bouw (accidentally modified)
- V2 deploy brak V1 connectiviteit
- Data corruption gedetecteerd
- Ongeoorloofde credentials change

Actie Cursor:
- Execute emergency_rollback.sh
- Restore V1 .env van backup
- Stop alle V2 services
- Alert CRITICAL naar mij
- Geen verdere acties tot mijn input

## Specifieke scenarios

### "V1 API returnt 401 Unauthorized"

Level: 3

Cause: API key invalid of expired

Cursor actie:
1. Check secrets file voor actuele key
2. Test key met curl
3. Als key niet werkt: vraag aan mij via chat prompt
4. Wacht op nieuwe key voor verder gaat

### "Agent build duurt > 30 minuten"

Level: 2

Cause: V1 waarschijnlijk overloaded of capability ontbreekt

Cursor actie:
1. Check V1 status
2. Als V1 healthy: verlengen naar 45 min, 1 extra retry
3. Als V1 overloaded: wacht tot minder busy
4. Als V1 ongezond: activeer fallback mode voor deze agent

### "Disk space op Hetzner < 2GB"

Level: 3

Cause: v2 build files accumuleren

Cursor actie:
1. Stop alle active builds
2. Run cleanup script (rm -rf tempfiles)
3. Check opnieuw
4. Als nog steeds laag: vraag mij upgrade of cleanup

### "V2 N8n workflow import faalt"

Level: 2

Cause: Workflow JSON format issue of dependency ontbreekt

Cursor actie:
1. Log de exacte error
2. Probeer JSON validatie lokaal
3. Als syntax OK: mogelijk dependency missing, rapporteer
4. Skip workflow, continue met andere

### "V1 agent genereert niet-compileerbare code"

Level: 2

Cause: V1 capability niet op niveau voor dit agent

Cursor actie:
1. Capture output
2. Vraag V1 1x revisie met error context
3. Als nog fout: fallback mode voor dit agent
4. Cursor genereert zelf code voor deze agent

### "Integration test end-to-end faalt"

Level: 3 (als systemic) of 2 (als specifiek)

Systematic (alle tests falen): Level 3, stop
Specifieke (1 pipeline faalt): Level 2, rapporteer, continue

### "Hetzner server herstart spontaan"

Level: 4 (tijdens build)

Cause: Hetzner onderhoud, crash, attack

Cursor actie:
1. Alle builds gaan kapot
2. Wacht tot server up is
3. Check state van v2 containers (herstart automatisch via restart: unless-stopped)
4. V1 ook check
5. Als beide OK: resume build
6. Als v1 kapot: emergency escalation

## Escalatie kanalen

**Primair: Cursor console**
Cursor toont directe message in Composer chat.

**Secundair: Status files**
./status/escalations.md met detailed info
./status/critical_halt.md bij level 3
./status/emergency.md bij level 4

**Tertiair (optioneel): Telegram/Discord**
Als configured met webhooks in N8n, push notifications naar jou.

**Altijd: Logs**
./logs/mega_build_<timestamp>.txt met volledige trace.

## Het escalatie format

Cursor schrijft altijd dezelfde structuur:

```markdown
# Escalation Report [level X]

**Timestamp**: ISO datetime
**Level**: 1-4
**Component**: naam (agent_01_sprite_jury, v1_orchestrator, etc)

## What happened

Korte beschrijving in 1-2 zinnen.

## Context

Wat Cursor aan het doen was.

## Error details

Exacte foutmelding, stack trace, relevant log.

## Cursor's actie

Wat Cursor al heeft geprobeerd (retries, alternatieven).

## Recommended action (voor mij)

Wat ik concreet moet doen:
- [ ] Check specifiek ding X
- [ ] Geef Cursor nieuwe info Y
- [ ] Beslis over scope Z

## Current state

Wat draait nog wel:
- X werkt
- Y pending

Wat ligt stil:
- Z gepauzeerd

## Resume instructie

Wat Cursor nodig heeft om verder te gaan.
```

## Escalatie budget

Om niet elk klein dingetje te escaleren:
- Max 1 Level 2 escalation per 5 agents
- Max 3 Level 2 totaal voor hele bouw
- Level 3: altijd, ongeacht hoeveel

Als Cursor 3 Level 2's heeft: overweeg pauze, review aanpak.

## Automatische recovery attempts

Voordat escaleren, probeer:

**Netwerk issue:**
- Retry 3x met exponential backoff (5s, 15s, 45s)

**V1 overload:**
- Sleep 60s
- Retry met helft concurrent tasks
- Als werkt: continue met verlaagde concurrency

**API rate limit:**
- Check rate limit headers
- Sleep volgens recommended wait
- Continue

**Disk full:**
- Auto-cleanup old logs (> 7 dagen)
- Temp files removal
- Als nog steeds: escaleer

## Post-mortem per escalatie

Na Level 3/4 escalatie, bij herstart:
- Schrijf post_mortem.md met wat er gebeurde
- Wat oorzaak was
- Wat preventief maatregel is
- Voeg toe aan error_agent (17) training data

Continuous improvement van het systeem.
