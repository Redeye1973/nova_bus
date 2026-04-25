---
title: DR Runbook — Anthropic API Down
severity: medium
expected_time: 5 min
---

# Anthropic API Down

## Detectie
- Agent 62 Service Router logs: "anthropic provider failed"
- Pipeline failures bij LLM calls
- status.anthropic.com toont incident

## Stappen

1. **Check Agent 62 fallback**
   ```bash
   curl -s http://localhost:8062/stats | python3 -m json.tool
   ```
   Agent 62 schakelt automatisch over naar OpenAI als fallback.

2. **Als alle providers down**
   - Pauzeer LLM-afhankelijke pipelines
   - Notify via Agent 61
   - Wacht op provider recovery

3. **Handmatige provider switch**
   ```bash
   # Check welke providers beschikbaar zijn
   curl -s http://localhost:8062/providers
   ```

## Impact
- Automatische failover via Agent 62 fallback chain
- Alleen als ALLE providers down: pipelines pauzeren
