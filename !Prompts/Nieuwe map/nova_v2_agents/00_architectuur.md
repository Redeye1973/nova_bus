# NOVA v2 Architectuur — Agent Ontwerp

## Kernprincipes

**Jury-Judge Patroon**: Meerdere specialisten beoordelen onafhankelijk, judge synthesiseert eindoordeel.

**Lokaal-First**: Ollama vision modellen als jury leden op RTX 5060 Ti. Claude alleen voor kalibratie of fallback bij twijfel.

**Modulair**: Elke agent is standalone inzetbaar en vervangbaar.

**N8n Orchestratie**: Alle agents draaien als N8n workflows of subworkflows.

**Pull Model**: Lokale PC haalt werk op van Hetzner, rapporteert terug. Geen inbound connecties.

## Technische Stack per Agent

**Lokale Inference** (jury leden):
- Ollama met Qwen 2.5 VL 7B voor visuele beoordeling
- Llama 3.2 Vision 11B voor alternatieve perspectieven
- Moondream 2 voor snelle basis-checks
- Codestral 22B voor code-jury
- Qwen 2.5 72B voor semantisch begrip

**Cloud Inference** (alleen voor judge bij complexe gevallen):
- Claude Opus 4.7 via API (spaarzaam, alleen escalatie)

**Orchestratie**:
- N8n op Hetzner (queue mode met Redis + PostgreSQL)
- nova_poller.py op lokale PC voor job pickup
- Shared storage via MinIO (S3 compatible)

**Utilities**:
- PostgreSQL voor state en metrics
- Redis voor queue en caching
- Qdrant voor vector similarity (assets vergelijken)

## Agent Communicatie Protocol

Elk jury-judge workflow krijgt als input:
```json
{
  "job_id": "unique-id",
  "domain": "sprite|code|audio|3d|gis|cad|narrative|character|2d|balance",
  "artifact": {
    "type": "file|url|data",
    "path": "...",
    "metadata": {}
  },
  "context": {
    "project": "...",
    "criteria": {...}
  }
}
```

En levert terug:
```json
{
  "job_id": "unique-id",
  "verdict": "accept|reject|review|experimental",
  "scores": {
    "jury_member_1": {"score": 8, "reason": "..."},
    "jury_member_2": {"score": 6, "reason": "..."}
  },
  "judge_decision": {
    "final_score": 7.2,
    "reasoning": "...",
    "recommendations": [...]
  },
  "timestamp": "..."
}
```

## Verdict Categorieën

- **accept**: alle jury groen, direct naar productie
- **experimental**: gemengd maar interessant, naar experimentele bucket
- **review**: grenswaarden, menselijke check nodig
- **reject**: onder drempel, log en weggooien

## Escalatie Paden

Als lokale jury het oneens is (standaard deviatie > threshold):
1. Eerst proberen met extra lokaal model
2. Als nog oneens, Claude API als tiebreaker
3. Als Claude ook onduidelijk, naar human review queue

## Kostenbeheersing

Cost Guard agent monitort:
- Claude API calls per dag (budget cap)
- Storage groei (cleanup triggers)
- GPU tijd (warnings bij lange runs)
- Bandwith richting klanten

## Observability

Elke agent logt naar:
- PostgreSQL voor metrics (latency, success rate, verdict distribution)
- Grafana voor visualisatie
- Alertmanager voor incidents
- Langfuse voor LLM-specifieke tracing

## Versioning

Elke agent heeft:
- Version tag in N8n workflow naam
- Changelog in git
- A/B test mogelijkheid via N8n Switch node
- Rollback procedure gedocumenteerd
