# 11. Monitor Agent

## Doel
Bewaakt data-bronnen, pipeline gezondheid, en gebruiker-feedback. Adviseert wanneer bake-cycli nodig zijn en detecteert problemen vroegtijdig.

## Scope
- PDOK dataset updates (BAG mutaties wekelijks, BGT updates)
- NDW changes (verkeersborden additions/removals)
- Pipeline service health (N8n, Ollama, databases)
- Gebruiker-feedback queue (bug reports, wijzigingsverzoeken)
- Cost tracking (API calls, storage)

## Functionaliteit

**1. Data Source Watcher**
- Check PDOK download service wekelijks voor nieuwe BAG mutatie bestanden
- Parse delta count per postcode-gebied
- Trigger alerts bij grote veranderingen

**2. Pipeline Health Monitor**
- Heartbeat checks op alle services
- Latency trends
- Error rate tracking
- Alert bij degradatie

**3. Feedback Aggregator**
- Verzamelt gebruiker-feedback uit verschillende kanalen
- Categoriseer: bug, feature request, data issue
- Prioriteert op basis van severity + frequency

**4. Bake Recommendation Engine**
- Combineert signals (data delta, user reports, age of last bake)
- Adviseert welke steden bake-cyclus nodig hebben
- Prioriteert op basis van gebruikersaantal

**5. Cost Tracking**
- Monitors API spending
- Storage growth
- GPU uren
- Alert bij budget overschrijding

## N8n Workflow

```
Cron Trigger (elke uur)
    ↓
Parallel branches:
    ├─ PDOK BAG delta check
    ├─ NDW updates check
    ├─ Service health pings
    ├─ Feedback queue analysis
    ├─ Cost metrics poll
    └─ Storage usage check
    ↓
Merge + Analyze
    ↓
Code node: generate recommendations
    ↓
Switch:
    ├─ Action needed → trigger specific workflow
    ├─ Alert needed → Telegram/Discord notify
    ├─ Scheduled task → queue for later
    └─ Nothing → log only
    ↓
Dashboard update (PostgreSQL)
```

## Cursor Prompt

```
Bouw een NOVA v2 Monitor Agent systeem:

1. Python service `monitor/pdok_watcher.py`:
   - FastAPI POST /check-updates
   - Download PDOK BAG mutatie bestand (wekelijkse diff)
   - Parse per postcode hoeveel mutaties
   - Store delta counts in PostgreSQL per postcode
   - Output: {postcodes_with_changes: [{postcode, delta_count}]}

2. Python service `monitor/ndw_watcher.py`:
   - Check NDW API voor verkeersbord updates
   - Detect borden added/removed per regio
   - Output: {changed_regions: [...]}

3. Python service `monitor/health_monitor.py`:
   - Ping all critical services (N8n, Ollama, PostgreSQL, MinIO)
   - Track latency, error rates
   - Output: {services: {name: status}, issues: []}

4. Python service `monitor/feedback_aggregator.py`:
   - Read feedback table uit PostgreSQL
   - Categorize en prioritize
   - Ollama voor category classification
   - Output: {top_issues: [...], critical: [...]}

5. Python service `monitor/bake_recommender.py`:
   - Input: delta counts + age of last bake + user activity per city
   - Algorithm: schedule_priority = (age_factor * delta_factor * activity_factor)
   - Output: {recommendations: [{city, priority, reason}]}

6. Python service `monitor/cost_tracker.py`:
   - Read API usage logs (Claude, OpenAI if used, Meshy credits)
   - Calculate spending vs budget
   - Storage growth detection
   - Output: {current_spend, projected_monthly, alerts: []}

7. Python service `monitor/alert_manager.py`:
   - Input: all monitor signals
   - Deduplicate alerts
   - Route: Telegram voor urgent, Discord voor info, email voor weekly digest
   - Output: delivery confirmations

8. N8n workflow `monitor_agent_workflow.json`:
   - Cron trigger elke uur
   - Parallel health checks
   - Aggregate into status dashboard
   - Trigger actions based on rules
   - Daily summary om 08:00
   - Weekly report op maandag

9. Grafana dashboard config:
   - Service uptime
   - Latency graphs per service
   - Cost trend graph
   - Top feedback categories
   - Bake queue status

10. PostgreSQL schema voor monitor metrics

Gebruik Python 3.11, FastAPI, psycopg3, httpx.
```

## Alert Severity Levels

**Critical** (direct Telegram):
- Service down > 5 min
- Cost overrun imminent
- Data integrity issue detected

**Warning** (Discord within hour):
- Degraded performance
- Storage > 80%
- Feedback backlog growing

**Info** (daily digest):
- Normal bake recommendations
- Routine updates available
- Weekly cost summary

## Integratie met andere agents

- Monitor triggert Bake Orchestrator bij recommendations
- Monitor triggert Error Agent bij service issues
- Monitor voedt Cost Guard met spending data
- Monitor escaleert naar Alex bij critical alerts

## Success Metrics

- False alert rate < 5%
- Critical issue detection < 10 min after occurrence
- Bake recommendations aligned met actual need 80%+
- Dashboard uptime 99.9%
