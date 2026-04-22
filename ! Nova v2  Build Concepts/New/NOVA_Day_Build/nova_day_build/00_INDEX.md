# NOVA Day Build — Backup + Bridge Verzekering

**Gemaakt:** 22 april 2026 nacht
**Doel:** Hetzner Storage Box backup + bridge 99%+ uptime zonder betaalde services
**Totaal tijd:** ~4-6 uur verdeeld over 5 sessies

---

## Waarom deze build

Twee doelen tegelijk:

1. **Backup naar externe locatie** — Hetzner Storage Box Finland. Als prod Hetzner crasht, alles terug.
2. **Bridge verzekerd laten werken** — 4 lagen bescherming, allemaal gratis.

## Bridge "verzekeringsplan"

| Laag | Tool | Kosten | Recovery tijd |
|------|------|--------|---------------|
| 1 | NSSM Windows Service + auto-restart | €0 | <5 sec |
| 2 | Lokale Python watchdog | €0 | <60 sec |
| 3 | UptimeRobot externe push heartbeat | €0 | 5 min alert |
| 4 | Uptime Kuma self-hosted status page | €0 | continu visibility |

Totaal: €0/maand, >99% uptime mogelijk.
Paid alternatieven (€18/mnd Better Stack) geven geen betere uptime, alleen nicetohaves.

## Sessie overzicht

| # | Sessie | Tijd | Handwerk? | Autonoom? |
|---|--------|------|-----------|-----------|
| D1 | Hetzner Storage Box + Borg backup | 60-90 min | Ja (order Storage Box) | Daarna ja |
| D2 | DR restore test automation | 45-60 min | Nee | Volledig |
| D3 | Bridge NSSM Service + lokale watchdog | 45-60 min | Ja (NSSM download) | Daarna ja |
| D4 | UptimeRobot external + Uptime Kuma | 60-90 min | Ja (UptimeRobot account) | Daarna ja |
| D5 | Integratie Monitor Agent + DR drill | 45-60 min | Nee | Volledig |

## Volgorde

**Strikt.** Elke sessie hangt af van de vorige.

D1 eerst omdat backup het belangrijkste is. D3 voor D4 omdat je bridge stabiel moet hebben voor external monitoring nuttig is.

## Werkwijze

Zelfde als night build sessies:

1. Open sessie `.md`
2. Doe handwerk stappen als die zijn (bovenaan markered)
3. Kopieer block tussen `===SESSION DX START===` en `===SESSION DX EINDE===`
4. Plak in Cursor Composer (Ctrl+I)
5. Enter, wacht op "SESSION DX COMPLETE"
6. Lees `docs/session_DX_report.md`
7. Volgende

## Totale kosten

**Eenmalig:**
- NSSM download = gratis
- UptimeRobot account = gratis
- Uptime Kuma Docker image = gratis

**Maandelijks:**
- Hetzner Storage Box BX11 (1TB Finland) = ~€3-4/mnd (check console.hetzner.com voor actuele prijs)
- Rest = €0

**Totaal extra:** ~€3-4/maand bovenop je bestaande €123/mnd.

## Output na alle sessies

- Automated daily backup naar Hetzner Storage Box Finland
- Monthly automated restore test
- Bridge als Windows Service (NSSM)
- Lokale watchdog die restart triggert
- External heartbeat monitoring (UptimeRobot)
- Self-hosted status page (Uptime Kuma)
- Agent 11 Monitor uitgebreid met alle health data
- DR drill procedure gedocumenteerd

## Afhankelijkheden van NIGHT BUILD

Dit werkt het best **nadat** je minimaal night-sessies 01-04 hebt gedraaid (API keys + bridge + Judge layer). Agent 11 Monitor uit sessie 06 is optioneel — zonder die werkt de meeste van deze day build nog steeds, alleen geen centrale aggregator.

Als Night Build nog niet gedraaid is: D1 kan altijd (staat los). D3+ werkt alleen als bridge in elk geval ooit heeft gedraaid.
