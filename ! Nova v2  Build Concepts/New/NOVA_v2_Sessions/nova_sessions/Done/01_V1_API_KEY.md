# SESSIE 01 — V1 API key + Secrets verificatie

**Doel:** Zorgen dat Cursor in latere sessies V1 kan aanspreken als bouwmachine.
**Tijd:** 5-10 minuten (deels handwerk)
**Afhankelijkheden:** Geen

---

## HANDWERK VOORAF (niet voor Cursor)

1. Open browser → http://178.104.207.194:5678
2. Log in op N8n v1
3. Klik rechtsboven op je profiel → Settings
4. Klik "n8n API"
5. Klik "Create an API key"
6. Geef naam: "NOVA v2 build Cursor"
7. Kopieer de key (begint met `n8n_api_...` — je ziet 'm maar één keer)

## DAARNA: Cursor Composer sessie

Plak alles tussen markers in Cursor Composer (Ctrl+I):

### ===SESSION 01 START===

```
SESSIE 01 van 7 — V1 API key toevoegen aan secrets + verificatie.

Werk autonoom. Vraag Alex alleen naar de V1 API key (die heeft hij net
gegenereerd in de browser).

## Stap 1: vraag de key
Stel Alex één vraag:
"Plak de V1 API key (begint met n8n_api_)"

Wacht op antwoord. Lees de key. NOOIT echoen in output of logs.

## Stap 2: secrets file updaten
Open L:\!Nova V2\secrets\nova_v2_passwords.txt.

Voeg toe (of update als bestaat):
N8N_V1_API_KEY=<key van Alex>
N8N_V1_URL=http://178.104.207.194:5678

Voeg ook toe indien ontbrekend (deze moeten er al zijn):
N8N_V2_URL=http://178.104.207.194:5679
N8N_V2_WEBHOOK_URL=http://178.104.207.194:5680

Zet file permissions restrictief:
icacls "L:\!Nova V2\secrets\nova_v2_passwords.txt" /inheritance:r /grant:r "$env:USERNAME:F"

## Stap 3: verifieer V1 key werkt
Load V1 key in env var (niet printen):
$v1key = (Get-Content "L:\!Nova V2\secrets\nova_v2_passwords.txt" |
  Select-String "^N8N_V1_API_KEY=").ToString().Split("=",2)[1]

Test tegen V1:
$r = Invoke-RestMethod -Uri "http://178.104.207.194:5678/api/v1/workflows" `
  -Headers @{"X-N8N-API-KEY"=$v1key} -Method GET

Write-Host "V1 workflows count: $($r.data.Count)"

Verwacht: minstens 50 workflows. Als <50: waarschuwing in rapport.

## Stap 4: check V2 API key
Kijk of N8N_V2_API_KEY ook in secrets staat.
Zo nee: melden aan Alex, hij moet ook V2 key genereren via :5679 UI.
Zo ja: zelfde test doen tegen :5679.

## Stap 5: write session report
File: L:\!Nova V2\docs\session_01_report.md

Inhoud:
# Sessie 01 Rapport
- Timestamp: <iso>
- V1 API key toegevoegd: ja
- V1 connectivity test: <aantal workflows>
- V2 API key aanwezig: ja/nee
- V2 connectivity test: <resultaat of "key ontbreekt">
- Status: SUCCESS / PARTIAL / FAILED
- Next session klaar: 02 (Bridge fix) JA/NEE

## Stap 6: commit
cd "L:\!Nova V2"
git add docs/session_01_report.md
git commit -m "session 01: V1 API key verified"
git push origin main

## Stap 7: signal klaar
Print: "SESSION 01 COMPLETE — next: sessie 02 bridge fix"

REGELS:
- API keys nooit in chat/logs/commits
- Max 2 retries op V1 ping, dan rapporteer connectivity issue in report
- Als V1 ping faalt met 401: key verkeerd, vraag Alex nog eens
- Als V1 ping faalt met timeout: Hetzner issue, LEVEL 3 flag in report

Ga.
```

### ===SESSION 01 EINDE===

---

## OUTPUT

- `L:\!Nova V2\secrets\nova_v2_passwords.txt` bevat V1 en V2 API keys
- `L:\!Nova V2\docs\session_01_report.md` met status
- Git commit "session 01: V1 API key verified"

## VERIFIEREN

Na sessie:
```powershell
Get-Content "L:\!Nova V2\docs\session_01_report.md"
```

Als "Status: SUCCESS" → door naar sessie 02.
Anders: lees rapport, fix issue, draai sessie 01 opnieuw.
