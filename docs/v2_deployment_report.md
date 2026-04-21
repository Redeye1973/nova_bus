# NOVA v2 — deployment report (Mega Build — lopend)

**Laatste update:** 2026-04-19

## Samenvatting

| Metric | Waarde |
|--------|--------|
| Agents gebouwd & actief (POC) | 1 / 35 |
| Stack | Hetzner `178.104.207.194`, `/docker/nova-v2/` |
| n8n V2 UI | `http://178.104.207.194:5679` |

## Live services (agent-gebonden)

| # | Agent | Compose service | Container | Interne URL |
|---|--------|------------------|------------|-------------|
| 01 | Sprite Jury | `sprite-jury-v2` | `nova-v2-sprite-jury` | `http://sprite-jury-v2:8101` |

## n8n V2 workflows (geïmporteerd)

| Workflow | ID | Webhook (test) |
|----------|-----|----------------|
| NOVA v2 — Sprite Jury POC | `RG7kvtJECmWOePMT` | `POST /webhook/sprite-review-poc` |

*(IDs zijn geen secrets; API key blijft in `secrets/`.)*

## Known limitations (POC)

- Sprite Jury gebruikt deterministische jury + PIL pixel check; Ollama/Qwen jury-leden uit de volledige spec zijn **nog niet** geïntegreerd.
- Overige agents (02–35): **nog te bouwen** — zelfde patroon als agent 01.

## Volgende stappen

1. Agent 02 (`code_jury`) implementeren en deployen.
2. Elke 5 agents: milestone-bestand in `status/`.
3. Fase D/E na voltooiing of bewuste partial release.
