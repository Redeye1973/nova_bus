---
created: 2026-04-25
project: nova
type: ADR
status: accepted
---

# ADR-005: Tier-based Staggered Container Startup

## Context
54 containers tegelijk starten veroorzaakt server overload (load >9.0)
en tijdelijke onbereikbaarheid (3-5 min). Optreedt bij reboot en full restart.

## Decision
Tier-based startup met health checks en cooldowns:
- 5 tiers: foundation -> core -> critical -> processors -> juries
- Per tier: wait_after_seconds delay + wait for healthy
- depends_on met service_healthy condition in compose
- Custom script staggered_startup.sh
- Systemd service voor reboot scenarios

## Consequences
- Total startup time: 3-5 min ipv alles tegelijk
- Server load piek significant lager
- SSH bereikbaar gedurende startup
- Predictable failure modes (tier kan failen, lower tiers blijven werken)
