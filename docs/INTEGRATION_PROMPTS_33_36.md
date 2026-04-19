# Integratie (prompts 33–36)

Deze prompts beschrijven **keten-E2E-tests** over bestaande webhooks; ze voegen geen aparte Docker-service toe.

| Prompt | Focus | Hoofd-webhooks |
|--------|--------|------------------|
| 33 | Sprite pipeline | `design-fase` → … → `godot-import` |
| 34 | GIS pipeline | `pdok-download` → … → `gis-review` |
| 35 | Story/audio | `narrative-review`, `audio-*`, `prompt-direct` |
| 36 | Cross-agent | `monitor`, `cost-track`, `error-handler`, `distribute` |

Voer na bulk-deploy handmatig de POST-requests uit die in elk prompt-bestand staan, en bewaar uitvoer in `logs/` indien gewenst.
