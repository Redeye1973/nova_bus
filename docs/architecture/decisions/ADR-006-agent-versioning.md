---
created: 2026-04-25
project: nova
type: ADR
status: accepted
---

# ADR-006: Agent API Versioning Strategy

## Context
Agents evolueren. Breaking changes in API endpoints breken pipelines.
Nodig: strategie voor backwards-compatible changes.

## Decision

### API Versioning
- Huidige endpoints = v1 (impliciet, geen prefix)
- Breaking changes: nieuwe versie onder `/v2/` prefix
- Oude versie blijft minimaal 30 dagen beschikbaar
- Agent health endpoint rapporteert `api_versions: ["v1", "v2"]`

### Blue-Green Deploy
- `docker-compose.yml`: current production
- `docker-compose.green.yml`: next version (wanneer nodig)
- Switch via service name aliasing in compose
- Rollback = switch terug naar blue

### Image Tagging
- `ghcr.io/redeye1973/nova-agent_XX:latest` — current prod
- `ghcr.io/redeye1973/nova-agent_XX:<git-sha>` — specific version
- `ghcr.io/redeye1973/nova-agent_XX:v2` — major version tag

## When to Version
- Endpoint signature change (parameters, response shape)
- Dependency change that affects callers
- Database schema migration that's not backwards-compatible

## When NOT to Version
- Bug fixes
- New endpoints (additive, non-breaking)
- Internal refactoring
- Performance improvements

## Implementation
- Deferred until first breaking change needed
- Structure and conventions documented here for reference
