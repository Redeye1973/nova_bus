# Pipeline E2E Bugtest — Resultaat Rapport

- **Datum:** 2026-04-25T10:58 UTC
- **Test asset:** ship_sprite helios scout 02 clean (test_mode)
- **Pipeline run ID:** `29a99400-7ecb-48ad-aa48-1a012043972f`
- **Test ID:** `c14a60a2-862d-415d-a865-fb43bfc63483`

## Stage status

| Stage | Status | Notes |
|-------|--------|-------|
| 1 Pipeline Start | PASS | `POST /pipeline/start` (Agent 11) |
| 2 Budget Check | PASS | `POST /budget/check` shmup_sprite proxy (Agent 16 + Postgres) |
| 2b Audit | PASS | `POST /audit` (Agent 11 + audit_log) |
| 3 Prompt Select | PASS | `POST /invoke` list (Agent 18) |
| 4 Blender Render | SKIP | Bridge: `host.docker.internal:8500` niet resolvable op Hetzner — **test limitation** |
| 5 Aseprite Polish | SKIP | Zelfde bridge-limitatie |
| 6 Sprite Jury | PASS | `POST /v1/verdict` → accept |
| 6b Quality Gate | PASS | experiment + bypass (Agent 11) |
| 7 Asset Lineage | PASS | `POST /assets/register` (Agent 12) |
| 7b Notify Hub | PASS | Agent 61 (info → geen externe channels, wel 200) |
| 8 Checkpoint | (implicit) | `POST /checkpoint` — geen error in run |
| 8 Pipeline Finish | PASS | `POST /pipeline/finish` success |

## Kernpad (8 stappen zoals opdracht)

| # | Stage | Status |
|---|--------|--------|
| 1 | Pipeline orchestration | PASS |
| 2 | Cost / budget | PASS |
| 3 | Prompt director | PASS |
| 4 | Blender (bridge) | SKIP — geen PC-bridge vanaf cloud |
| 5 | Aseprite (bridge) | SKIP — idem |
| 6 | Jury verdict | PASS |
| 7 | Asset lineage | PASS |
| 8 | Pipeline finish | PASS |

**Effectief: 6/8 PASS, 2/8 SKIP (geen FAIL op integratie-code).**

## Issues / observaties

1. **Bridge** — `host.docker.internal` op Linux/Hetzner lost niet naar Alex’ PC. Geen pipeline-bug; voor echte render: VPN/tunnel of run render-stap op machine waar bridge draait.
2. **Budget type** — Opdracht noemde `ship_sprite_test`; DB heeft `shmup_sprite`. Test gebruikt `shmup_sprite` als budget-key. Optioneel: `INSERT` extra rij `ship_sprite_test` in `pipeline_budgets`.
3. **MinIO** — Geen expliciete upload in deze run; lineage bevat `minio_path` placeholder. Volgende stap: MinIO put na echte asset.
4. **Memory curator** — Append naar `sessions/cursor_reports/2026-04-25_pipeline_e2e_test.md` werkt.

## Performance

- Totale test ~3s HTTP round-trips intern Docker-netwerk.
- Server load tijdens test verwaarloosbaar (preflight + E2E).

## Volgende stappen voor Black Ledger productie

1. Bridge bereikbaar maken vanaf server (of render-stap alleen via N8n op PC).
2. Echte `.blend` / `.aseprite` paden op bridge-host; dan stage 4–5 opnieuw draaien.
3. Optioneel: `ship_sprite_test` budgetregel toevoegen.
4. MinIO upload na succesvolle binary output.
