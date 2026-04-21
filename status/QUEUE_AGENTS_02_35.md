# Resterende agents (02–35)

Agent **01** is afgerond (zie `agent_01_status.json`). Voor elke volgende agent hetzelfde patroon:

1. Spec lezen: `agents/nova_v2_agents/...` of `extensions/nova_v2_extensions/...`
2. `v2_services/<NN>_<name>/` + spiegel naar `infrastructure/services/<short_name>/`
3. Service toevoegen aan `infrastructure/docker-compose.yml` (eigen poort, `nova-v2-network`)
4. `scp` compose + service map → `/docker/nova-v2/`, `docker compose up -d --build <service>`
5. Workflow JSON → `POST /api/v1/workflows`, `POST .../activate` met `Content-Type` + `{}`
6. `status/agent_<NN>_status.json`
7. Elke 5 agents: `progress_milestone_*.md`

| NN | Naam | Spec-pad (indicatief) |
|----|------|------------------------|
| 02 | code_jury | `agents/nova_v2_agents/jury_judge/02_code_jury.md` |
| 03 | audio_jury | `agents/nova_v2_agents/jury_judge/03_audio_jury.md` |
| … | … | … |
| 35 | raster_2d_processor | `extensions/nova_v2_extensions/raster2d/35_raster_2d_processor_agent.md` |

Zie `mega_plan/agent_volgorde.md` voor volgorde en rationale.
