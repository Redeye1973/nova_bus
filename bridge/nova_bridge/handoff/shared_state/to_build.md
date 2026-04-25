# To build — resterend werk (na V2 production baseline)

**Last update:** 2026-04-22 (sessie 09)

## Bridge / host — hoge prioriteit

- [ ] **22** Blender Renderer — echte bridge-render i.p.v. stub 503  
- [ ] **23** Aseprite Processor — bridge batch  
- [ ] **25** PyQt Assembly — bridge  
- [ ] **26** Godot Import — bridge + forwarder hardening  
- [ ] **31** QGIS Analysis — bridge  
- [ ] **32** GRASS GIS — bridge  
- [ ] **33** Blender arch walkthrough — bridge  
- [ ] **35** Raster 2D — bridge  
- [ ] **14** Blender Baker — headless bake via `nova_host_bridge` `/blender/*`  
- [ ] **15** QGIS Processor — `qgis_process` via bridge  

## Fase H — DAZ (Ren’Py **niet**)

- [ ] `nova_host_bridge`: DAZ-routes in `main.py` + tests  
- [ ] Agents **38, 40, 41, 42, 43** (orchestrator, scene, freebies, char registry, prompt craftsman)  

## Fase G — operatie

- [ ] Hetzner: cron uit `scripts/hetzner_backup_cron_templates.sh` activeren + `mc` mirror testen  
- [ ] N8n: import `pipelines/pipeline_*_master.json` + webhook-test  

## Nice-to-have

- [ ] Pipeline runner → Postgres inserts (`psycopg`) i.p.v. alleen JSON-artefact  
- [ ] DR-maandtest (day build D2) koppelen aan Monitor Agent  
