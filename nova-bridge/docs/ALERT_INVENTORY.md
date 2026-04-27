# Alert Inventory (Current State)

Generated: 2026-04-27

## 1) N8n workflows that fire Telegram/Discord

### Runtime n8n databases checked
- `infrastructure/n8n-main/database.sqlite`
- `infrastructure/n8n-secondary/database.sqlite`

### Findings
- `workflow_entity` search for `telegram|discord|alert|notify` in node JSON: **0 active hits** in both runtime DBs.
- `credentials_entity` search for Telegram/Discord/Webhook credentials: **0 hits** in runtime DB.

### Template/workflow files in repo
- Found infra monitor templates with critical alert node:
  - `agents/nova_v2_agents/templates/monitor_workflow.json`
  - `!Prompts/Nieuwe map/nova_v2_agents/templates/monitor_workflow.json`
- These are now routed to `http://localhost:8088/notify` (nova-bridge), `kind=infrastructure`.

---

## 2) Uptime Kuma notification channels configured

### Runtime DB checked
- `infrastructure/uptime-kuma/kuma.db`

### Findings
- `notification` table: **empty**
- `monitor_notification` table count: **0**

No direct Telegram/Discord channel is currently configured in Kuma runtime DB.

Target routing for new Kuma notifications:
- URL: `http://localhost:8088/notify`
- Payload (example):
```json
{
  "kind": "infrastructure",
  "severity": "warning",
  "title": "Kuma monitor down",
  "detail": "service X unreachable",
  "channels": ["telegram", "discord"],
  "source": "uptime-kuma"
}
```

---

## 3) Python services with direct bot/API tokens

Detected direct token/webhook usage:
- `v2_services/agent_61_notification_hub/main.py`
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`
  - `DISCORD_WEBHOOK_URL`
- `v2_services/agent_70_factory_worker/main.py`
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`

---

## 4) Per-channel routing decision (bridge or bypass)

| Channel/source | Via bridge suppressor? | Decision |
|---|---:|---|
| Uptime Kuma infra down/up alerts | YES | Route via `nova-bridge /notify` (`kind=infrastructure`) |
| N8n infra monitor "critical" alerts | YES | Route via `nova-bridge /notify` (`kind=infrastructure`) |
| User-bound Telegram chat messages (Alex interactions) | NO | Keep bypass path (`kind=user_message`) |
| Discord bot command replies | NO | Keep direct reply path (not infra monitoring) |
| Critical safety alerts (disk 95% etc.) | YES, but bypass quiet mode | Use `kind=critical_alert` |

---

## 5) What was changed in this pass

- Added nova-bridge infra notify endpoint with quiet-mode suppression check.
- Added user-message bypass behavior and critical-alert bypass behavior.
- Updated monitor workflow templates to send infra alerts to bridge `/notify`.
- Added/updated tests to verify suppression and bypass logic.

## 6) Manual follow-up required

- Configure Uptime Kuma notification(s) in UI to call bridge `/notify`.
- If additional n8n workflows are imported later, ensure infra alerts use bridge `/notify` with `kind=infrastructure`.
