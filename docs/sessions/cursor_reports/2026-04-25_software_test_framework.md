# Software Test Framework — First Run

- Datum: 25 april 2026
- Status: eerste **echte** run uitgevoerd (Agent 64 skeleton + runner)
- Run ID: `run-20260425-135530`

## Resultaten (lokaal, Python 3.14)

| Metriek | Waarde |
|--------|--------|
| Totaal tools | 18 |
| Pass | 7 |
| Fail | 1 (`freecad` — STL-export; script daarna aangepast) |
| Skip | 10 (geen Blender/Inkscape/Aseprite/GIMP/QGIS/GRASS op PATH, geen `DATABASE_URL`/`MINIO` lokaal, ollama-model `tinyllama` ontbrak, DAZ niet geautomatiseerd) |

## Geslaagd (artifacts)

- `data_ldtk`, `infrastructure_n8n`, `infrastructure_qdrant`, `audio_pyqt5`, `audio_sox`, `audio_supercollider`, `image_krita_pyqt`

## Outputmap

`L:\! 2 Nova v2  OUTPUT !\Z New NOva 1st test\_runs\2026-04-25_first_test\`

## Postgres

SQL toegepast op server: `software_test_runs`, `software_test_results`, `software_test_diffs` (zie `scripts/create_software_test_tables.sql`). Lokale run schreef nog **niet** naar Postgres (geen `DATABASE_URL` in shell).

## Windows / stabiliteit

- Unicode checkmarks vervangen door `[OK]` / `[FAIL]` / `[SKIP]` (cp1252 console).
- `SOFTTEST_SEQUENTIAL=1` aanbevolen op Windows i.p.v. parallel (native extensies).
- `pyqt5`-test gebruikt **Pillow-only** om PyQt-binary crashes op Python 3.14 te vermijden.

## Volgende stappen

- Optioneel: `DATABASE_URL` + MinIO env zodat infra-tests volledig **pass** worden.
- Zware tools installeren of paden zetten → minder skips.
- Na succesvolle run: `_runs\…` kopiëren naar `_baseline\` voor vergelijking.
- Agent 64 FastAPI + Docker + poort 8064: nog te deployen (runner CLI werkt nu).

## Cursor rule

Zie `.cursor/rules/08_software_testing.mdc`.
