# Audio Stack Install Report

- **Datum:** 2026-04-25
- **Status:** PARTIAL (2/3 volledig werkend)

## SuperCollider
- **Versie:** 3.14.1
- **Locatie:** `L:\ZZZ Software\Super Collider\`
- **scsynth headless test:** PASS (help output, versie output)
- **sclang NRT render test:** PASS (laser.wav 176 KB gegenereerd)
- **Status:** VOLLEDIG WERKEND

## SoX
- **Versie:** 14.4.2
- **Locatie:** `L:\ZZZ Software\SoX\sox-14.4.2\`
- **sox --version test:** PASS
- **Normalize + fade test:** PASS (laser_processed.wav)
- **OGG conversion test:** PASS (laser.ogg)
- **Status:** VOLLEDIG WERKEND

## Audiocraft
- **Versie:** 1.4.0a2 (git source)
- **Locatie:** `L:\ZZZ Software\Audiocraft\venv\` (Python 3.13)
- **Import test:** FAIL
- **Root cause:** PyTorch version mismatch
  - xformers 0.0.35 trok torch 2.11 mee
  - torchaudio 2.6.0+cu124 verwacht torch 2.6.0+cu124
  - audiocraft 1.4.0a2 verwacht torch==2.1.0 (streng gepin)
- **Fix:** Handmatig venv opnieuw opbouwen met precies torch==2.1.0+cu121
  ```
  pip install torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu121
  pip install xformers==0.0.22.post7
  ```
  Dit vereist Python 3.11 (niet 3.13).
- **Status:** PARTIAL — geinstalleerd maar niet import-ready

## Test Artifacts
- `tests/audio/laser.wav` — SuperCollider NRT generated
- `tests/audio/laser_processed.wav` — SoX normalized
- `tests/audio/laser.ogg` — SoX OGG conversion
- `tests/audio/test_supercollider.scd` — SC test script

## Tool Paths Config
- Bijgewerkt in `config/tool_paths.yaml`

## Volgende Stappen
- Audiocraft: venv herinstalleren met Python 3.11 + torch 2.1.0 (handmatig)
- Agents 54-57 bouwen wanneer audio pipeline nodig is
