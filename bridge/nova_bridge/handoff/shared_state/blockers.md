# Active Blockers

**Last update**: 2026-04-19

## Current blockers

Geen actieve blockers.

## Recent resolved

### 2026-04-19: V2 N8n password kwijt
**Resolution**: `docker exec nova-v2-n8n-main n8n user-management:reset`, nieuw owner account aangemaakt, password + API key opgeslagen in L:\!Nova V2\secrets\nova_v2_passwords.txt
**Status**: Resolved

### 2026-04-19: agent_validator.py faalde op agent_01
**Resolution**: Status file schema drift. Agent 01 gebruikte `n8n_v2.webhook_path`, validator verwacht `webhook_url`. Status file bijgewerkt.
**Status**: Resolved - let op: potentiele drift bij andere legacy agents.

---

## Format voor nieuwe blockers

```
### [Date]: [Title]
**Impact**: [wat werkt niet]
**Root cause**: [waarom]
**Attempts**: [wat is geprobeerd]
**Next steps**: [wat te doen]
**Owner**: claude.ai | Cursor | human
**Status**: open | in progress | waiting | resolved
```
