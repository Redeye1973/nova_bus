---
created: 2026-04-25
project: nova
type: ADR
status: accepted
---

# ADR-004: Build Local, Deploy Remote

## Context
Server overbelast 3x tijdens Docker builds. 4 vCPU / 8 GB Hetzner server raakt
onbereikbaar bij parallelle builds van 40+ containers. SSH timeouts, load average >200.

## Decision
- Builds gebeuren NIET op productie
- GitHub Actions bouwt images bij push naar main (alleen gewijzigde agents)
- Push naar ghcr.io/redeye1973/nova-*
- Productie server doet alleen `docker compose pull` + rolling restart
- Resource limits per container verplicht in docker-compose
- SSH altijd met retry logic en timeout

## Consequences
- Server kan met 4 vCPU / 8 GB blijven werken (geen upgrade nodig)
- Deploy tijd iets langer (push + pull) maar zero overlast
- Image storage gratis op GHCR (private repo)
- CI/CD wordt verplicht stap voor productie deploy

## Alternatives considered
- Server upgrade naar 8 vCPU / 16 GB: duur, niet nodig met deze fix
- Build serieel met sleep: hielp deels, fundamenteel patroon zelfde
- Docker BuildKit remote: te complex voor huidige setup
