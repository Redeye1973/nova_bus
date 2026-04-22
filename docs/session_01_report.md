# Sessie 01 Rapport

- **Timestamp:** 2026-04-22 (UTC sessie)
- **V1 API key toegevoegd:** **nee** — regel `N8N_V1_API_KEY=` ontbreekt nog; Alex moet key in n8n V1 UI aanmaken en **handmatig** in `secrets\nova_v2_passwords.txt` zetten (zie `01_V1_API_KEY.md`).
- **V1 connectivity test:** niet uitgevoerd (geen key om `X-N8N-API-KEY` mee te sturen).
- **V2 API key aanwezig:** **ja** (actieve `N8N_V2_API_KEY=` regel aanwezig).
- **V2 connectivity test:** niet herhaald in deze mini-run (optioneel: zelfde `Invoke-RestMethod` tegen `:5679` met V2-key).
- **URL-regels secrets:** toegevoegd indien ontbrak — `N8N_V1_URL`, `N8N_V2_WEBHOOK_URL` (non-secret); `N8N_V2_URL` stond al.
- **icacls:** opdracht met `:F` toegepast op `nova_v2_passwords.txt` (inheritance verwijderd, alleen huidige gebruiker).
- **Status:** **PARTIAL** — wacht op V1 key van Alex.
- **Next session klaar: 02 (Bridge fix):** **JA** — bridge draait al op `:8500` uit eerdere fix; sessie 02 is desondanks “klaar” voor verificatie/herhaling.

## Wat jij nog doet (1 minuut)

1. Browser → `http://178.104.207.194:5678` → Settings → n8n API → Create key → naam bv. `NOVA v2 build Cursor`.
2. In `L:\!Nova V2\secrets\nova_v2_passwords.txt` op **eigen regel** (geen spaties rond `=`):

   `N8N_V1_API_KEY=<plak hier de key>`

3. Daarna in PowerShell (key wordt niet geprint):

```powershell
$v1key = (Get-Content "L:\!Nova V2\secrets\nova_v2_passwords.txt" | Select-String "^N8N_V1_API_KEY=").ToString().Split("=",2)[1]
$r = Invoke-RestMethod -Uri "http://178.104.207.194:5678/api/v1/workflows?limit=250" -Headers @{"X-N8N-API-KEY"=$v1key} -Method GET
"V1 workflows count: $($r.data.Count)"
```

Verwacht: **≥ 50** (productie ~68).

## Opmerking voor Cursor-sessie in het doc

Het originele “Stap 1: vraag de key” blok is voor **Composer** met user-in-the-loop. In **deze chat** zonder geplakte key: alleen secrets-URLs + rapport + icacls gedaan.
