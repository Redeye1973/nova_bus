---
created: 2026-04-25
type: reference
status: active
---

# Architecture Decision Records (ADR)

## Format

```
ADR = Architecture Decision Record
Naming: ADR-NNN-short-description.md

Secties:
- Context (waarom besluit nodig)
- Decision (wat besloten)
- Consequences (gevolgen)
- Alternatives considered
- Status (proposed/accepted/superseded)
```

## Voorbeeld

```markdown
# ADR-001: FastAPI voor alle agents

## Context
We hebben een framework nodig voor 36+ microservices.

## Decision
FastAPI met Pydantic v2 voor alle agents.

## Consequences
- Async support out of the box
- Auto-generated OpenAPI docs
- Type safety via Pydantic

## Alternatives
- Flask (te basic, geen async)
- Django (te zwaar voor microservices)

## Status
Accepted
```
