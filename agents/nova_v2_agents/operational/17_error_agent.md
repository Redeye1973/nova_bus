# 17. Error Agent

## Doel
Centrale error detectie, classificatie, en auto-recovery voor NOVA v2 pipeline. Uitbreiding van bestaande UE5 debugger naar platform-breed error management.

## Scope
- Alle pipeline services (jury-judge, operationele agents)
- N8n workflow failures
- Cursor/Claude Code generated code errors
- Runtime errors in games en apps
- Data pipeline failures (PDOK, QGIS, Blender)

## Functionaliteit

**1. Error Ingestion**
- Centrale endpoint voor error reports
- Structured logging format
- Correlation IDs voor trace-ability

**2. Classification**
- Pattern matching bekende error types
- Severity assessment
- Retry-able vs fatal classification

**3. Auto-Recovery**
- Retry logic met exponential backoff
- Fallback paths (lokale Ollama als Claude faalt)
- Circuit breakers voor cascading failures

**4. Root Cause Analysis**
- Ollama analyse op stack traces
- Link gerelateerde errors
- Suggest fixes

**5. Escalation**
- Auto-fix attempts eerst
- Cursor prompt generation bij fixable bugs
- Human escalation bij onbekend

## Cursor Prompt

```
Bouw een NOVA v2 Error Agent:

1. Python service `error_agent/ingestor.py`:
   - FastAPI POST /error
   - Input: {service, severity, message, stack_trace, context, correlation_id}
   - Store in PostgreSQL met timestamp
   - Trigger classification async

2. Python service `error_agent/classifier.py`:
   - Pattern library in YAML config
   - Match tegen bekende error patterns
   - Use Ollama voor onbekende errors
   - Output: {category, severity_calibrated, retry_able: bool}

3. Python service `error_agent/recovery.py`:
   - Retry logic met exponential backoff
   - Configurable per service type
   - Fallback paths defined per category
   - Track retry attempts in DB

4. Python service `error_agent/root_cause_analyzer.py`:
   - Input: error + related errors (correlation)
   - Ollama deep analysis
   - Generate hypothesis about root cause
   - Suggest diagnostic steps

5. Python service `error_agent/auto_fixer.py`:
   - Bij fixable errors: genereer Cursor prompt
   - Specifieke instructies based on error type
   - Write naar .cursor/prompts/ voor quick apply
   - Track fix success rate

6. Python service `error_agent/escalator.py`:
   - When auto-fix fails
   - Format comprehensive report voor Alex
   - Send via Telegram met actionable context
   - Include: error, attempts, hypotheses, suggested actions

7. Python service `error_agent/pattern_learner.py`:
   - Weekly analysis van error patterns
   - Detect new recurring issues
   - Auto-add to pattern library
   - Flag for human review

8. N8n workflow `error_agent_workflow.json`:
   - Trigger: webhook van services
   - Also: N8n's own Error Trigger node routes here
   - Classification → Recovery → Escalation pipeline

9. CLI tools:
   - `nova-error list --service <name> --since 1h`
   - `nova-error show <id>`
   - `nova-error retry <id>`
   - `nova-error patterns`

10. Dashboard view:
    - Error rate per service (real-time)
    - Error categories (pie chart)
    - Auto-fix success rate
    - Unresolved errors queue

Gebruik Python 3.11, FastAPI, PostgreSQL, Ollama.
Pattern library in YAML voor makkelijke editing.
```

## Error Pattern Library (examples)

```yaml
patterns:
  - name: "ollama_connection_refused"
    match: "ConnectionError.*11434"
    severity: high
    retry_able: true
    fix: "restart_ollama_service"
    
  - name: "pdok_rate_limit"
    match: "429.*PDOK"
    severity: medium
    retry_able: true
    fix: "exponential_backoff_5min"
    
  - name: "blender_out_of_memory"
    match: "MemoryError.*bpy"
    severity: high
    retry_able: true
    fix: "split_job_into_chunks"
    
  - name: "godot_null_reference"
    match: "Attempt to call.*on.*null"
    severity: high
    retry_able: false
    fix: "cursor_prompt_null_check"
    
  - name: "disk_full"
    match: "No space left on device"
    severity: critical
    retry_able: false
    fix: "cleanup_temp_files"
```

## Integration Points

- **Receives from**: alle andere agents via HTTP POST
- **Triggers**: Recovery actions, Cursor prompts, human escalation
- **Integrates met**: Monitor agent voor system health, Cost Guard voor API failures

## Test Scenario's

1. Known error (Ollama down) → auto-recovery succeeds
2. Unknown error → Ollama analyse + human escalation
3. Cascading errors → circuit breaker prevents overload
4. Fixable code bug → Cursor prompt generated

## Success Metrics

- Auto-recovery success rate: > 70%
- Classification accuracy: > 85%
- Mean time to detection: < 30 sec
- False escalation rate: < 10%
