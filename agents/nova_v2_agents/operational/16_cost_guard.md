# 16. Cost Guard Agent

## Doel
Bewaakt betaalde resources (API calls, cloud storage, third-party services). Voorkomt budget overruns.

## Scope
- Claude API (Anthropic)
- Meshy API credits
- OpenAI API (indien gebruikt)
- Hetzner GPU uren
- Storage groei (lokaal + cloud)
- Bandwidth verbruik

## Functionaliteit

**1. Usage Tracking**
- Log elke API call met kosten schatting
- PostgreSQL table: service, timestamp, cost_estimate_usd

**2. Budget Management**
- Daily/monthly budgets per service
- Soft warnings bij 70%, hard stops bij 95%
- Alert escalatie bij overschrijding

**3. Cost Optimization Suggestions**
- Analyseer usage patterns
- Identify expensive operations
- Suggest alternatives (bijv. lokale Ollama vs Claude)

**4. Projection**
- Voorspel einde-maand kosten op basis van trend
- Alert bij projectie boven budget

## Cursor Prompt

```
Bouw een NOVA v2 Cost Guard:

1. Python service `cost_guard/tracker.py`:
   - FastAPI POST /log
   - Input: {service, tokens_in, tokens_out, cost_estimate}
   - Write naar PostgreSQL
   - Also write naar Redis voor real-time summing

2. Python service `cost_guard/budget_manager.py`:
   - Load budgets from config
   - Current period spending calculation
   - Projection based on burn rate
   - Output: {current, projected, budget, pct_used}

3. Python middleware `cost_guard/proxy.py`:
   - Optional: proxy between services en AI APIs
   - Auto-logs elke call
   - Can enforce circuit breakers

4. Python service `cost_guard/optimizer.py`:
   - Analyze last 30 days usage
   - Identify: high-cost operations, redundant calls
   - Suggest: caching, lokale fallback, batching
   - Output: report met recommendations

5. Python service `cost_guard/alerter.py`:
   - Watch thresholds
   - Route alerts: Telegram urgent, Discord warning, email daily digest
   - Include context: what caused spike

6. Grafana dashboard:
   - Spending per service over tijd
   - Budget burn-down
   - Top 10 expensive operations
   - Projection lines

7. CLI tool:
   - `nova-cost status`
   - `nova-cost forecast --month`
   - `nova-cost top --limit 20`

8. Integration: hook into alle AI API calls
   - Wrapper functions voor Anthropic, OpenAI, Meshy
   - Auto-logging zonder extra code per caller

Gebruik Python 3.11, FastAPI, PostgreSQL, Redis.
```

## Budget Tiers

**Phase 1 (huidig, pre-revenue):**
- Claude API: $20/maand (beperkt gebruik boven Max subscription)
- Meshy: $0 (gebruikt bestaande credits)
- Totale API budget: $30/maand cap
- Storage: gratis tier

**Phase 2 (eerste revenue):**
- Claude API: $50/maand
- Alerts scaled up

**Phase 3 (break-even):**
- Normale business budgets
- Cost per customer metrics

## Alert Configuratie

| Threshold | Action |
|-----------|--------|
| 50% | Dashboard only |
| 70% | Discord notification |
| 85% | Telegram alert |
| 95% | Telegram urgent + pause expensive operations |
| 100% | Hard stop (circuit breaker) |

## Test Scenario's

1. Normale dag: binnen budget, dashboard updates
2. Sudden spike: alert geactiveerd, investigeer cause
3. Slow creep: projection voorspelt overrun → early warning
4. Budget reached: circuit breaker, fallback naar lokaal

## Success Metrics

- Budget overrun incidents: 0
- Alert latency < 5 min na threshold hit
- Optimization suggestions leading to 10%+ savings
